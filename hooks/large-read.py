#!/usr/bin/env python3
"""PreToolUse hook: stop agents from re-reading big source files in the transcript.

Contract (https://code.claude.com/docs/en/hooks): JSON on stdin with session_id, cwd,
tool_name, tool_input (Read: file_path/offset/limit; Bash: command). Exit 2 with the
reason on stderr blocks the call and the reason reaches the model. Any failure exits 0.
"""

import json
import os
import re
import shlex
import sys
import tempfile

EXTS = {".py", ".ts", ".tsx", ".js", ".mjs"}
SKIP_PARTS = {"node_modules", ".venv"}
# Generated files never to Read whole (grep them instead): TRUSSARY_NEVER_READ, comma separated
# repo-relative paths, e.g. "apps/web/src/api/schema.d.ts". Empty by default.
NEVER_READ = tuple(p.strip() for p in os.environ.get("TRUSSARY_NEVER_READ", "").split(",") if p.strip())
BIG = 400
MAX_RANGE = 200
MAX_READS = 6
SEPS = {"&&", "||", ";", "|", "&", ";;", "|&"}
HINT = (
    "If a codegraph MCP server is configured, query `codegraph_explore` with the symbol names you "
    "need (it returns their source, line-numbered); otherwise find them with `rg -n` and Read with "
    "offset/limit <= 200 on the exact lines."
)
PROTO_HINT = (
    "Prototype files are not in codegraph: take the lines from the prototype skill's scout brief, "
    "find them with `grep -n`, or Read with offset/limit <= 200."
)


def hint(path):
    return PROTO_HINT if "/prototypes/" in "/" + path.replace(os.sep, "/") else HINT


def line_count(path):
    with open(path, "rb") as f:
        data = f.read()
    return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def relevant(path):
    if not os.path.isfile(path):
        return False
    p = path.replace(os.sep, "/")
    if NEVER_READ and p.endswith(NEVER_READ):
        return True
    if os.path.splitext(p)[1] not in EXTS:
        return False
    return not (set(p.split("/")) & SKIP_PARTS)


def is_schema(path):
    return bool(NEVER_READ) and path.replace(os.sep, "/").endswith(NEVER_READ)


def classify(path, kind, span):
    """kind: 'whole' or 'range'; span: lines requested (range). Returns (reason|None, counted)."""
    if not relevant(path):
        return None, False
    if is_schema(path):
        return (
            f"{path} is a generated schema; do not read it. grep for the type name "
            f"(`rg -n 'TypeName' {path}`) or use codegraph_explore.",
            False,
        )
    n = line_count(path)
    if n <= BIG:
        return None, False
    if kind == "whole":
        return f"{path} has {n} lines and would be read whole. {hint(path)}", True
    if span > MAX_RANGE:
        return f"{path} has {n} lines; a {span}-line range is too wide. {hint(path)}", True
    return None, True


def tokenize(cmd):
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    return list(lex)


def segments(tokens):
    segs, cur = [], []
    for t in tokens:
        if t in SEPS:
            segs.append((cur, t))
            cur = []
        else:
            cur.append(t)
    segs.append((cur, None))
    return segs


def resolve(p, cwd):
    return os.path.normpath(os.path.join(cwd, os.path.expanduser(p)))


def clean_redirects(toks):
    """Drop redirect tokens; return (tokens, writes_to_file)."""
    out, writes, skip = [], False, False
    for t in toks:
        if skip:
            skip = False
            continue
        if t and set(t) <= set("<>&|;()") or re.fullmatch(r"\d?[<>]+&?", t or ""):
            if t in (">", ">>") and out and out[-1] == "2":
                out.pop()  # 2>file: stderr only, stdout still reaches the transcript
                skip = True
                continue
            if t.startswith(">") and "&" not in t or t in (">", ">>"):
                writes = True
            skip = "&" not in t
            continue
        out.append(t)
    return out, writes


def sed_span(toks):
    """Line count of `sed -n 'a,bp'` with no file argument, else None."""
    if not toks or os.path.basename(toks[0]) != "sed" or "-n" not in toks:
        return None
    rest = [t for t in toks[1:] if t != "-n"]
    if len(rest) != 1 or not re.fullmatch(r"\d+,\d+p", rest[0]):
        return None
    a, b = map(int, rest[0][:-1].split(","))
    return b - a + 1


def bash_reads(cmd, cwd):
    """Yield (path, kind, span) for reads whose output reaches the transcript."""
    segs = segments(tokenize(cmd))
    for i, (toks, sep) in enumerate(segs):
        toks, writes = clean_redirects(toks)
        if not toks:
            continue
        if toks[0] == "cd" and len(toks) >= 2:
            cwd = resolve(toks[1], cwd)
            continue
        if writes:
            continue
        prog, args = os.path.basename(toks[0]), toks[1:]
        if sep in ("|", "|&"):
            nxt = segs[i + 1][0] if i + 1 < len(segs) else []
            span = sed_span(nxt)
            if prog in ("cat", "nl") and span:
                # cat -n f | sed -n 'a,bp': a ranged read of f
                for a in args:
                    if not a.startswith("-"):
                        yield resolve(a, cwd), "range", span
                continue
            if not nxt or os.path.basename(nxt[0]) not in ("head", "tail"):
                continue
        if prog == "cat":
            for a in args:
                if not a.startswith("-"):
                    yield resolve(a, cwd), "whole", 0
        elif prog == "less":
            for a in args:
                if not a.startswith("-"):
                    yield resolve(a, cwd), "whole", 0
        elif prog in ("head", "tail"):
            n, files, j = 10, [], 0
            while j < len(args):
                a = args[j]
                if a in ("-n", "--lines") and j + 1 < len(args):
                    n, j = args[j + 1], j + 1
                elif re.fullmatch(r"-\d+", a):
                    n = a[1:]
                elif a.startswith("-n") and len(a) > 2:
                    n = a[2:]
                elif a.startswith("-"):
                    pass
                else:
                    files.append(a)
                j += 1
            if isinstance(n, str) and not n.isdigit():
                continue  # +N and other forms: don't parse
            if int(n) > MAX_RANGE:
                for f in files:
                    yield resolve(f, cwd), "whole", 0
            else:
                for f in files:
                    yield resolve(f, cwd), "range", int(n)
        elif prog == "sed" and "-n" in args:
            rest = [a for a in args if a != "-n"]
            script = next((a for a in rest if re.fullmatch(r"\d+,\d+p", a)), None)
            if not script:
                continue
            a, b = map(int, script[:-1].split(","))
            for f in rest:
                if f != script and not f.startswith("-"):
                    yield resolve(f, cwd), "range", b - a + 1


def bump(key, path):
    d = os.path.join(tempfile.gettempdir(), "claude-large-read")
    os.makedirs(d, exist_ok=True)
    fp = os.path.join(d, re.sub(r"[^\w.-]", "_", key or "nosession") + ".json")
    try:
        with open(fp) as f:
            counts = json.load(f)
    except Exception:
        counts = {}
    counts[path] = counts.get(path, 0) + 1
    try:
        with open(fp, "w") as f:
            json.dump(counts, f)
    except Exception:
        pass
    return counts[path]


def main():
    data = json.load(sys.stdin)
    tool, ti = data.get("tool_name"), data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    if tool == "Read":
        fp = ti.get("file_path")
        if not fp:
            return 0
        lim = ti.get("limit")
        reads = [
            (resolve(fp, cwd), "whole", 0) if lim is None else (resolve(fp, cwd), "range", int(lim))
        ]
    elif tool == "Bash":
        reads = list(bash_reads(ti.get("command") or "", cwd))
    else:
        return 0
    for path, kind, span in reads:
        reason, counted = classify(path, kind, span)
        if reason is None and counted:
            # Subagents share the session id; count per agent.
            k = bump(f"{data.get('session_id')}-{data.get('agent_id') or 'main'}", path)
            if k > MAX_READS:
                reason = (
                    f"You've read {path} {k - 1} times this session. Query `codegraph_explore` "
                    "with the symbol names instead (if configured), or re-read only the lines you "
                    "changed via `git diff`."
                )
        if reason:
            sys.stderr.write(reason + "\n")
            return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
