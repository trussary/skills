import json
import os
import subprocess
import sys
import tempfile
import unittest

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "large-read.py")


def run(payload, raw=None):
    env = dict(os.environ, TMPDIR=TMP, TRUSSARY_NEVER_READ="apps/web/src/api/schema.d.ts")
    p = subprocess.run(
        [sys.executable, HOOK],
        input=raw if raw is not None else json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    return p.returncode, p.stderr


TMP = tempfile.mkdtemp()
D = tempfile.mkdtemp()
BIG = os.path.join(D, "big.py")
SMALL = os.path.join(D, "small.py")
MD = os.path.join(D, "notes.md")
for path, n in ((BIG, 500), (SMALL, 50), (MD, 500)):
    with open(path, "w") as f:
        f.write("x = 1\n" * n)


def bash(cmd, sid="s"):
    return {"session_id": sid, "cwd": D, "tool_name": "Bash", "tool_input": {"command": cmd}}


def read(path, sid="s", **kw):
    return {
        "session_id": sid,
        "cwd": D,
        "tool_name": "Read",
        "tool_input": {"file_path": path, **kw},
    }


class T(unittest.TestCase):
    def denied(self, p):
        code, err = run(p)
        self.assertEqual(code, 2, err)
        return err

    def allowed(self, p):
        code, err = run(p)
        self.assertEqual(code, 0, err)

    def test_whole_read_denied(self):
        self.assertIn("500 lines", self.denied(read(BIG, "a")))

    def test_small_limit_allowed(self):
        self.allowed(read(BIG, "b", offset=10, limit=100))

    def test_wide_limit_denied(self):
        self.denied(read(BIG, "c", limit=300))

    def test_sed_wide_denied(self):
        self.denied(bash(f"cd {D} && sed -n 1,300p big.py", "d"))

    def test_sed_quoted_narrow_allowed(self):
        self.allowed(bash("sed -n '1,100p' " + BIG, "e"))

    def test_cat_small_allowed(self):
        self.allowed(bash("cat small.py", "f"))

    def test_cat_big_denied(self):
        self.denied(bash("cd . ; cat big.py", "f2"))

    def test_head_tail(self):
        self.denied(bash("head -n 300 big.py", "g"))
        self.allowed(bash("head -n 50 big.py", "g2"))

    def test_rg_allowed(self):
        self.allowed(bash("rg foo big.py", "h"))
        self.allowed(bash("cat big.py | rg foo", "h2"))
        self.allowed(bash("cat big.py | wc -l", "h3"))

    def test_stderr_redirect_and_cat_pipe_count(self):
        # 2>/dev/null and cat -n | sed -n still put the lines in the transcript.
        self.denied(bash("sed -n 1,300p big.py 2>/dev/null", "o"))
        self.denied(bash("cat -n big.py | sed -n 1,300p", "o2"))
        for _ in range(6):
            self.allowed(bash("nl big.py | sed -n 1,50p", "o3"))
        self.denied(bash("nl big.py | sed -n 1,50p", "o3"))

    def test_seventh_read_denied(self):
        for _ in range(6):
            self.allowed(read(BIG, "i", offset=1, limit=50))
        err = self.denied(read(BIG, "i", offset=1, limit=50))
        self.assertIn("codegraph_explore", err)

    def test_reads_counted_per_agent(self):
        for agent in ("a1", "a2"):
            for _ in range(6):
                self.allowed({**read(BIG, "k", offset=1, limit=50), "agent_id": agent})

    def test_malformed_allowed(self):
        code, _ = run(None, raw="not json")
        self.assertEqual(code, 0)
        code, _ = run(
            None, raw='{"tool_name": "Bash", "tool_input": {"command": "echo \'unterminated"}}'
        )
        self.assertEqual(code, 0)

    def test_non_source_allowed(self):
        self.allowed(read(MD, "j"))
        self.allowed(bash(f"cat {MD}", "j2"))

    def test_schema_always_denied(self):
        sd = os.path.join(D, "apps/web/src/api")
        os.makedirs(sd)
        p = os.path.join(sd, "schema.d.ts")
        open(p, "w").write("x\n")
        self.denied(read(p, "k", limit=20))

    def test_prototypes_checked(self):
        pd = os.path.join(D, "prototypes")
        os.makedirs(pd, exist_ok=True)
        p = os.path.join(pd, "app.js")
        open(p, "w").write("x\n" * 600)
        self.assertIn("scout brief", self.denied(read(p, "l")))
        self.allowed(read(p, "l2", offset=1, limit=150))


if __name__ == "__main__":
    unittest.main()
