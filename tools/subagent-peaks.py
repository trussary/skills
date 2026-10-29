#!/usr/bin/env python3
"""Measure the true peak context of each subagent in a Claude Code session.

Usage: tools/subagent-peaks.py [session id | path to .jsonl | --spec N] [--json] [--over K] [--limit K]

With --spec N, reads the newest session of the current git toplevel whose subagent prompts name
`spec #N`; with no argument, the most recently modified one (wrong when sessions run in parallel).
Feeds the `Peak context` field of the Run record (docs/agents/models.md#run-record) and the
context-budget slice rule of the to-tickets skill; --limit sets that budget (default 150k).

Context of one API call is input + cache_read + cache_creation tokens. A message id repeats on
several log lines and the last one wins. When `usage.iterations` exists the top-level usage SUMS
the iterations, advisor copies included, so each non-advisor iteration is read on its own.
A compacted subagent needed more than its peak: the peak is a lower bound (">=").
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime

ROLES = (("QA pass", "qa"), ("merger", "merger"), ("fixer", "fixer"), ("review", "review"))
# Plugin agent types, matched bare ("qa") or plugin-prefixed ("trussary-skills:qa").
AGENT_TYPES = {"qa": "qa", "merger": "merger", "reviewer": "review"}
HEAD = 200  # the role is named at the start of the prompt; later text mentions other roles


def projects_dir() -> str:
    return os.path.expanduser("~/.claude/projects")


def names_spec(session: str, spec: int) -> bool:
    needle = re.compile(rf"spec\W*#?{spec}\b|#{spec}\b")
    for p in glob.glob(os.path.join(session[: -len(".jsonl")], "subagents", "agent-*.jsonl")):
        with open(p, encoding="utf-8") as f:
            if needle.search(f.read(4000)):
                return True
    return False


def resolve_session(arg: str | None, spec: int | None = None) -> str:
    if arg and os.path.exists(arg):
        return arg
    if arg:
        hits = glob.glob(os.path.join(projects_dir(), "*", arg + ".jsonl"))
        if not hits:
            sys.exit(f"no session {arg} under {projects_dir()}")
        return hits[0]
    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
    ).stdout.strip()
    slug = re.sub(r"[/.]", "-", top)
    sessions = glob.glob(os.path.join(projects_dir(), slug, "*.jsonl"))
    if not sessions:
        sys.exit(f"no sessions under {os.path.join(projects_dir(), slug)}")
    sessions.sort(key=os.path.getmtime, reverse=True)
    if spec is None:
        return sessions[0]
    hit = next((s for s in sessions if names_spec(s, spec)), None)
    if not hit:
        sys.exit(
            f"no session under {os.path.join(projects_dir(), slug)} has subagents for spec #{spec}"
        )
    return hit


def context(usage: dict) -> int:
    return sum(
        usage.get(k) or 0
        for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
    )


def first_prompt(entry: dict) -> str:
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, list):
        content = " ".join(b.get("text", "") for b in content if isinstance(b, dict))
    return content if isinstance(content, str) else ""


def role_of(prompt: str) -> str:
    prompt = prompt[:HEAD]
    m = re.match(r"\s*Ticket\W*(\d+)", prompt)
    if m:
        return f"implementer #{m.group(1)}"
    if prompt.lstrip().startswith("Ticket"):
        return "implementer"
    for needle, role in ROLES:
        if needle.lower() in prompt.lower():
            return role
    return "other"


def measure(path: str, limit: int) -> dict:
    last_usage: dict[str, dict] = {}
    order: list[str] = []
    prompt = None
    compactions = 0
    stamps: list[str] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if (
                e.get("type") == "system"
                and "compact" in f"{e.get('subtype', '')} {e.get('content', '')}".lower()
            ):
                compactions += 1
            if e.get("timestamp"):
                stamps.append(e["timestamp"])
            if e.get("type") == "user" and prompt is None:
                prompt = first_prompt(e)
            msg = e.get("message") or {}
            if e.get("type") == "assistant" and isinstance(msg.get("usage"), dict):
                mid = msg.get("id") or e.get("uuid")
                if mid not in last_usage:
                    order.append(mid)
                last_usage[mid] = msg["usage"]
    calls: list[int] = []
    advisor = 0
    total = 0
    for mid in order:
        usage = last_usage[mid]
        total += context(usage) + (usage.get("output_tokens") or 0)
        its = usage.get("iterations")
        if its:
            for it in its:
                if it.get("type") == "advisor_message":
                    advisor += 1
                else:
                    calls.append(context(it))
        else:
            calls.append(context(usage))
    meta = {}
    try:
        with open(path[: -len(".jsonl")] + ".meta.json", encoding="utf-8") as f:
            meta = json.load(f)
    except (OSError, ValueError):
        pass
    return {
        "agent": os.path.basename(path)[: -len(".jsonl")],
        "role": AGENT_TYPES.get((meta.get("agentType") or "").split(":")[-1], "")
        or role_of(prompt or ""),
        "description": meta.get("description", ""),
        "model": meta.get("model", ""),
        "first": calls[0] if calls else 0,
        "peak": max(calls, default=0),
        "calls": len(calls),
        "advisor_calls": advisor,
        "compactions": compactions,
        "over": max(calls, default=0) > limit,
        "tokens": total,
        "minutes": minutes(stamps),
    }


def minutes(stamps: list[str]) -> float:
    """Minutes between the first and the last timestamp of a log."""
    if not stamps:
        return 0.0
    times = sorted(datetime.fromisoformat(t.replace("Z", "+00:00")) for t in stamps)
    return (times[-1] - times[0]).total_seconds() / 60


def k(n: int) -> str:
    return f"{round(n / 1000)}k"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("session", nargs="?")
    ap.add_argument(
        "--spec", type=int, metavar="N", help="newest session whose subagents work on spec #N"
    )
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--over", type=int, metavar="K", help="only subagents whose peak exceeds K thousand tokens"
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=150,
        metavar="K",
        help="context budget in k tokens that marks a peak as over (default 150)",
    )
    args = ap.parse_args()
    limit = args.limit * 1000
    session = resolve_session(args.session, args.spec)
    files = glob.glob(os.path.join(session[: -len(".jsonl")], "subagents", "agent-*.jsonl"))
    rows = [measure(p, limit) for p in files]
    if args.over is not None:
        rows = [r for r in rows if r["peak"] > args.over * 1000]
    rows.sort(key=lambda r: r["peak"], reverse=True)
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    print(
        f"{'role':<18} {'peak':>6} {'first':>6} {'calls':>5} {'adv':>3} {'comp':>4} {'>' + k(limit):<5}  model   description"
    )
    for r in rows:
        bound = ">=" if r["compactions"] else "  "
        print(
            f"{r['role']:<18} {bound}{k(r['peak']):>5} {k(r['first']):>6} {r['calls']:>5} {r['advisor_calls']:>3} "
            f"{r['compactions']:>4} {'yes' if r['over'] else 'no':<5}  {r['model']:<7} {r['description']}"
        )
    summary(session, rows, limit)
    return 0


def summary(session: str, rows: list[dict], limit: int) -> None:
    """Totals for the Run record: tokens (cache reads included) and minutes per role, and the
    orchestrator's own session, whose first to last line is the Wall-clock."""
    main_row = measure(session, limit)
    roles: dict[str, list[float]] = {}
    for r in rows:
        t = roles.setdefault(r["role"].split(" #")[0], [0, 0, 0])
        t[0], t[1], t[2] = t[0] + 1, t[1] + r["tokens"], t[2] + r["minutes"]
    print(f"\n{'role':<18} {'agents':>6} {'tokens':>8} {'agent-min':>9}")
    for role, (n, tokens, mins) in sorted(roles.items(), key=lambda kv: -kv[1][1]):
        print(f"{role:<18} {n:>6} {tokens / 1e6:>7.1f}M {mins:>9.0f}")
    total = sum(r["tokens"] for r in rows) + main_row["tokens"]
    print(f"{'orchestrator':<18} {1:>6} {main_row['tokens'] / 1e6:>7.1f}M")
    print(f"Tokens: {total / 1e6:.0f}M   Wall-clock: {main_row['minutes'] / 60:.1f}h")


if __name__ == "__main__":
    sys.exit(main())
