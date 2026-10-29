#!/usr/bin/env python3
"""Estimate a ticket's read budget from the files it touches (the to-tickets skill).

Usage: tools/read-budget.py <file or directory>... [--budget K] [--skip PATH]...

Counts the lines of each source file named (a directory counts every source file under it) at
~10 tokens a line and compares the total with the read budget (default 45k; pass the one in the
`## Planning` section of docs/agents/project.md with --budget). Name the files the slice changes
and their tests, the docs it reads, and the prototype file. Leave out a generated file agents
grep rather than read with --skip <path> (repeatable; matches any file whose path ends with it).
Exits 1 when the total is over budget, so a slice that needs splitting is visible.
"""

import argparse
import sys
from pathlib import Path

EXTS = {".py", ".ts", ".tsx", ".js", ".mjs", ".css", ".md", ".json", ".sql", ".toml"}
SKIP = {"node_modules", ".venv", "__pycache__", "dist", ".next"}
TOKENS_PER_LINE = 10


def files(path: Path):
    if path.is_file():
        yield path
    elif path.is_dir():
        for p in sorted(path.rglob("*")):
            if p.is_file() and p.suffix in EXTS and not set(p.parts) & SKIP:
                yield p


def lines(path: Path) -> int:
    with open(path, "rb") as f:
        return sum(1 for _ in f)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="+")
    ap.add_argument(
        "--budget", type=int, default=45, help="read budget in k tokens (default 45; override per repo)"
    )
    ap.add_argument(
        "--skip",
        action="append",
        default=[],
        metavar="PATH",
        help="leave out files whose path ends with PATH, e.g. a generated schema (repeatable)",
    )
    args = ap.parse_args()
    skips = [s.strip("/") for s in args.skip]
    total, seen, missing = 0, set(), []
    for arg in args.paths:
        path = Path(arg)
        if not path.exists():
            missing.append(arg)
            continue
        n = 0
        for f in files(path):
            p = f.as_posix()
            if any(p == s or p.endswith("/" + s) for s in skips) or f.resolve() in seen:
                continue
            seen.add(f.resolve())
            n += lines(f)
        total += n
        print(f"{n * TOKENS_PER_LINE / 1000:6.1f}k  {arg}")
    k = total * TOKENS_PER_LINE / 1000
    verdict = "over budget: split the slice" if k > args.budget else "within budget"
    print(f"{k:6.1f}k  total, {len(seen)} files ({verdict}, budget {args.budget}k)")
    for arg in missing:
        print(f"  not found: {arg}", file=sys.stderr)
    return 1 if k > args.budget else 0


if __name__ == "__main__":
    sys.exit(main())
