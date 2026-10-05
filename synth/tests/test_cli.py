from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "jev-wasm"


class CliTests(unittest.TestCase):
    def run_cli(self, arguments, stdin=None):
        return subprocess.run(
            [str(CLI), *arguments], cwd=ROOT, input=stdin,
            text=True, capture_output=True, timeout=30, check=False,
        )

    def assert_generation(self, args, expected, stdin=None):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "component.wat"
            trace = Path(directory) / "trace.json"
            result = self.run_cli([*args, "--output", str(output), "--trace", str(trace)], stdin)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(expected, output.read_text(encoding="utf-8"))
            report = json.loads(trace.read_text(encoding="utf-8"))
            self.assertEqual(report["termination"], "END")
            self.assertEqual(report["compile_validation"], "passed")

    def test_inline_spec(self):
        self.assert_generation(["checksum hash"], "fnv1a_32")

    def test_spec_file(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = Path(directory) / "spec.txt"
            spec.write_text("integer clamp and gcd", encoding="utf-8")
            self.assert_generation(["--spec-file", str(spec)], "gcd_u32")

    def test_stdin_spec(self):
        self.assert_generation([], "monthly_cents", "subscription billing\n")

    def test_rejects_ambiguous_input(self):
        result = self.run_cli(["inline", "--spec-file", "missing.txt"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly one", result.stderr)


if __name__ == "__main__":
    unittest.main()
