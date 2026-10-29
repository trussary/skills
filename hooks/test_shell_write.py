"""Tests for shell-write.py: python3 -m unittest discover -s hooks -p 'test_*.py'."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shell-write.py")
WT = "/repo/.claude/worktrees/t1"


def run(cmd, cwd=WT, tool="Bash"):
    payload = {"cwd": cwd, "tool_name": tool, "tool_input": {"command": cmd}}
    p = subprocess.run(
        [sys.executable, HOOK], input=json.dumps(payload), capture_output=True, text=True
    )
    return p.returncode, p.stderr


class Blocks(unittest.TestCase):
    def test_sed_in_place_on_source(self):
        code, err = run(f"cd {WT} && sed -i '' 's/a/b/' apps/api/src/app/x.py")
        self.assertEqual(code, 2)
        self.assertIn("Edit", err)

    def test_redirect_onto_source(self):
        self.assertEqual(run(f"cat > {WT}/apps/api/tests/test_x.py <<'E'\nx = 1\nE")[0], 2)

    def test_append_from_inside_apps(self):
        self.assertEqual(run("echo x >> styles.css", cwd=f"{WT}/apps/web/src")[0], 2)

    def test_tee_onto_source(self):
        self.assertEqual(run(f"echo x | tee {WT}/packages/ds/tokens.json")[0], 2)

    def test_python_heredoc_naming_a_source_path(self):
        cmd = f"cd {WT} && python3 - <<'E'\np='apps/api/src/app/x.py'\ns=open(p).read()\nopen(p,'w').write(s)\nE"
        self.assertEqual(run(cmd)[0], 2)

    def test_python_heredoc_run_from_inside_apps(self):
        cmd = "python3 - <<'EOF'\np='test_chat.py'\ns=open(p).read()\nopen(p,'w').write(s)\nEOF"
        self.assertEqual(run(cmd, cwd=f"{WT}/apps/api/tests")[0], 2)

    def test_redirect_after_heredoc_marker(self):
        self.assertEqual(run(f"cat <<'E' > {WT}/apps/api/x.py\nx = 1\nE")[0], 2)

    def test_sed_after_a_heredoc(self):
        cmd = f"cat <<'E'\nnote\nE\nsed -i '' 's/a/b/' {WT}/apps/api/x.py"
        self.assertEqual(run(cmd)[0], 2)

    def test_python_heredoc_without_dash(self):
        cmd = f"python3 <<'E'\nopen('{WT}/apps/api/x.py','w').write('')\nE"
        self.assertEqual(run(cmd)[0], 2)

    def test_uv_run_python_c(self):
        script = f"open('{WT}/apps/api/x.py','w').write('')"
        self.assertEqual(run(f'uv run --directory {WT}/apps/api python -c "{script}"')[0], 2)

    def test_env_prefix_and_ampersand_redirect(self):
        self.assertEqual(run(f"FOO=1 sed -i '' 's/a/b/' {WT}/apps/web/a.ts")[0], 2)
        self.assertEqual(run(f"make x &> {WT}/apps/web/log.ts")[0], 2)

    def test_perl_in_place(self):
        self.assertEqual(run(f"perl -pi -e 's/a/b/' {WT}/apps/web/src/a.ts")[0], 2)


class Allows(unittest.TestCase):
    def test_sed_read(self):
        self.assertEqual(run(f"sed -n 1,40p {WT}/apps/api/src/app/x.py")[0], 0)

    def test_stderr_and_dev_null(self):
        self.assertEqual(run(f"rg -n foo {WT}/apps 2>/dev/null > /dev/null")[0], 0)

    def test_scratchpad_write(self):
        self.assertEqual(run("cat > /private/tmp/scratch/notes.md <<'E'\napps/api\nE")[0], 0)

    def test_python_that_only_reads(self):
        self.assertEqual(run(f"python3 - <<'E'\nprint(open('{WT}/apps/api/x.py').read())\nE")[0], 0)

    def test_python_writing_outside_source(self):
        cmd = "python3 - <<'E'\nopen('/private/tmp/s/out.json','w').write('{}')\nE"
        self.assertEqual(run(cmd)[0], 0)

    def test_stdout_write_from_inside_apps(self):
        cmd = 'python3 -c "import sys; sys.stdout.write(1)"'
        self.assertEqual(run(cmd, cwd=f"{WT}/apps/api")[0], 0)

    def test_apps_dir_outside_the_checkout(self):
        with tempfile.TemporaryDirectory() as repo:
            os.mkdir(os.path.join(repo, ".git"))
            self.assertEqual(run("echo x > /private/tmp/scratch/apps/notes.md", cwd=repo)[0], 0)
            self.assertEqual(run(f"echo x > {repo}/apps/api/x.py", cwd=repo)[0], 2)

    def test_skill_and_docs_files(self):
        self.assertEqual(run(f"sed -i '' 's/a/b/' {WT}/docs/agents/models.md")[0], 0)

    def test_node_modules(self):
        self.assertEqual(run(f"echo x > {WT}/apps/web/node_modules/a.js")[0], 0)

    def test_other_tools(self):
        self.assertEqual(run("anything", tool="Read")[0], 0)

    def test_bad_input_passes(self):
        p = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
