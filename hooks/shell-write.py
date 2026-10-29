#!/usr/bin/env python3
"""PreToolUse hook: source files under the guarded roots change through Edit or Write.

Guarded roots are top-level-or-nested directory names, from TRUSSARY_GUARDED_ROOTS (comma
separated, default "apps,packages,src,lib"); a project sets it in the `env` of .claude/settings.json.

Blocks a Bash command that writes into such a file: `sed -i`, `perl -i`, a `>`/`>>` redirect or
`tee` onto it, or an inline Python script (`python3 <<`, `python3 -c`, also behind `uv run`) that
writes and names a guarded path or runs from inside one. Only paths inside the
checkout count (the outermost directory above cwd holding a `.git`). Edit keeps only the changed
lines in context and fails loudly on a stale match; the shell forms do neither.

Contract (https://code.claude.com/docs/en/hooks): JSON on stdin with cwd, tool_name, tool_input
(Bash: command). Exit 2 with the reason on stderr blocks the call. Any failure exits 0.
"""

import json
import os
import re
import shlex
import sys

ROOTS = {r.strip() for r in os.environ.get("TRUSSARY_GUARDED_ROOTS", "apps,packages,src,lib").split(",") if r.strip()}
SKIP_PARTS = {"node_modules", ".venv", "dist", ".next", "test-results", "playwright-report"}
REASON = (
    "{what} writes into {path}. Change source files with Edit (Write for a "
    "new file): only the changed lines enter your context. Generated files come from their "
    "generator (a codegen script, a lockfile command). See the Shell section of the implement "
    "skill's IMPLEMENTER.md."
)
SEPS = {"&&", "||", ";", "|", "&", ";;", "|&", "(", ")"}
REDIRECTS = {">", ">>", ">|", "&>", "&>>"}
PY_WRITE = re.compile(
    r"write_text\(|write_bytes\(|(?<!stdout)(?<!stderr)\.write\(|open\([^)]*['\"][wa]b?\+?['\"]"
)
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1")
UV_OPTS_WITH_VALUE = {"--directory", "--project", "--with", "--python", "--package"}
PY_PATH = re.compile(
    r"""['"]((?:[^'"\s]*/)?(?:%s)/[^'"\s]+)['"]""" % "|".join(map(re.escape, sorted(ROOTS)))
)


def repo_root(cwd):
    """The outermost directory at or above cwd that holds a `.git`; `/` when none does."""
    root, d = "/", cwd
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            root = d
        if d == os.path.dirname(d):
            return root
        d = os.path.dirname(d)


def in_source(path, root, is_dir=False):
    """Is `path` (a file, or with is_dir a directory) under a guarded root of the checkout?"""
    if path != root and not path.startswith(root.rstrip("/") + "/"):
        return False
    parts = path.replace(os.sep, "/").split("/")
    if set(parts) & SKIP_PARTS or path in ("/dev/null", "/dev/stderr", "/dev/stdout"):
        return False
    last = len(parts) if is_dir else len(parts) - 1
    return any(p in ROOTS and i < last for i, p in enumerate(parts))


def resolve(p, cwd):
    return os.path.normpath(os.path.join(cwd, os.path.expanduser(p)))


def segments(text):
    """Commands of `text` as token lists; quoted words stay whole, operators split them."""
    lex = shlex.shlex(text, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    segs, cur = [], []
    try:
        tokens = list(lex)
    except ValueError:  # an unclosed quote: let the shell report it
        return []
    for t in tokens:
        if t in SEPS:
            segs.append(cur)
            cur = []
        else:
            cur.append(t)
    return segs + [cur]


def shell_lines(cmd):
    """`cmd` with its heredoc bodies dropped (they are data, not commands), lines joined by `;`."""
    out, end = [], None
    for line in cmd.split("\n"):
        if end is not None:
            end = None if line.strip() == end else end
            continue
        out.append(line)
        m = HEREDOC.search(line)
        if m:
            end = m.group(2)
    return " ; ".join(out)


def program(toks):
    """`toks` from the program on: env assignments and a `uv run [options]` prefix dropped."""
    while toks and re.fullmatch(r"[A-Za-z_]\w*=.*", toks[0]):
        toks = toks[1:]
    if toks[:2] == ["uv", "run"]:
        toks = toks[2:]
        while toks and toks[0].startswith("-"):
            toks = toks[2:] if toks[0] in UV_OPTS_WITH_VALUE else toks[1:]
    return toks


def writes(cmd, cwd):
    """Yield (what, path) for each write into a source file."""
    root = repo_root(cwd)
    for toks in segments(shell_lines(cmd)):
        toks = program(toks)
        if not toks:
            continue
        if toks[0] == "cd" and len(toks) >= 2:
            cwd = resolve(toks[1], cwd)
            continue
        prog = os.path.basename(toks[0])
        for i, t in enumerate(toks[:-1]):
            if t in REDIRECTS and (i == 0 or toks[i - 1] != "2"):
                if in_source(resolve(toks[i + 1], cwd), root):
                    yield "A `>` redirect", resolve(toks[i + 1], cwd)
        args = [t for t in toks[1:] if t not in REDIRECTS | {">&", "<", "<<", "<<-"}]
        if prog in ("sed", "gsed", "perl") and any(
            re.fullmatch(r"-p?i.*|--in-place.*", t) for t in args
        ):
            for t in args:
                if not t.startswith("-") and in_source(resolve(t, cwd), root):
                    yield f"`{prog} -i`", resolve(t, cwd)
        if prog == "tee":
            for t in args:
                if not t.startswith("-") and in_source(resolve(t, cwd), root):
                    yield "`tee`", resolve(t, cwd)
        stdin_script = "-" in toks[1:2] or "<<" in toks or "<<-" in toks
        if re.match(r"python3?(\.\d+)?$|py$", prog) and (stdin_script or "-c" in toks[:-1]):
            script = toks[toks.index("-c") + 1] if "-c" in toks[:-1] else cmd
            if PY_WRITE.search(script):
                if in_source(cwd, root, is_dir=True):
                    yield "An inline Python script", cwd
                for p in PY_PATH.findall(script):
                    if in_source(resolve(p, cwd), root):
                        yield "An inline Python script", resolve(p, cwd)


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return 0
    cmd = (data.get("tool_input") or {}).get("command") or ""
    for what, path in writes(cmd, data.get("cwd") or os.getcwd()):
        sys.stderr.write(REASON.format(what=what, path=path) + "\n")
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
