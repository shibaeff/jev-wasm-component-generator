from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "estimate_cost.py"


class CostEstimatorTests(unittest.TestCase):
    def test_measured_envelope(self):
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "trace.json"
            trace.write_text(json.dumps({"usage": {"input_tokens": 1828, "output_tokens": 143}}))
            process = subprocess.run(
                ["python3", str(SCRIPT), "--json", str(trace)],
                cwd=ROOT, text=True, capture_output=True, check=True,
            )
            report = json.loads(process.stdout)
            rows = {row["model"]: row for row in report["rows"]}
            self.assertAlmostEqual(rows["Jev 1.13"]["cost_usd"], 0.000076776)
            self.assertAlmostEqual(rows["Claude Sonnet 4.6"]["cost_usd"], 0.007629)
            self.assertAlmostEqual(rows["Claude Sonnet 4.6"]["multiple_of_jev"], 99.36698968)

    def test_missing_usage_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "trace.json"
            trace.write_text("{}")
            process = subprocess.run(
                ["python3", str(SCRIPT), str(trace)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("no usage object", process.stderr)


if __name__ == "__main__":
    unittest.main()
