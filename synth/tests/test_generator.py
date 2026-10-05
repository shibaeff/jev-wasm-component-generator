from __future__ import annotations

import json
import unittest
from pathlib import Path

from synth.decoder import END, decode
from synth.library import load_library
from synth.model import Choice, ScriptedModel
from synth.jev.client import JevClient

ROOT = Path(__file__).resolve().parents[2]


class RecordingModel:
    def __init__(self):
        self.inner = ScriptedModel()
        self.calls = []

    def choose(self, spec, prefix, options):
        self.calls.append((prefix, dict(options)))
        return self.inner.choose(spec, prefix, options)


class EarlyEndModel:
    def __init__(self):
        self.inner = ScriptedModel()
        self.first = True

    def choose(self, spec, prefix, options):
        if self.first:
            self.first = False
            baseline = self.inner.choose(spec, prefix, options)
            end_id = next(key for key, value in options.items() if value == END)
            others = [key for key in options if key != end_id]
            subtotal = sum(baseline.probabilities[key] for key in others)
            probabilities = {
                key: 0.4 * baseline.probabilities[key] / subtotal for key in others
            }
            probabilities[end_id] = 0.6
            return Choice(end_id, probabilities, "early-end-test")
        return self.inner.choose(spec, prefix, options)


class GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library = load_library(ROOT / "library")

    def test_library_has_three_unique_blocked_modules(self):
        self.assertEqual(len(self.library), 3)
        self.assertEqual(len({item.source for item in self.library}), 3)
        for item in self.library:
            self.assertGreaterEqual(len(item.blocks), 2)
            self.assertEqual("".join(item.blocks), item.source)
            self.assertTrue(all(block.startswith(";; JEV BLOCK:") for block in item.blocks))

    def test_offline_model_reconstructs_each_domain(self):
        cases = {
            "monthly subscription billing and due dates": "subscription-core",
            "FNV checksum hash bytes": "checksum",
            "integer math gcd clamp": "integer-math",
        }
        for spec, expected in cases.items():
            with self.subTest(spec=spec):
                model = RecordingModel()
                result = decode(spec, self.library, model)
                self.assertEqual(result.candidate.name, expected)
                self.assertEqual(result.source, result.candidate.source)
                self.assertEqual(result.trace["termination"], END)
                self.assertFalse(result.trace["teacher_forcing"])
                self.assertEqual(result.trace["compile_validation"], "passed")
                self.assertEqual(result.trace["api_call_count"], len(model.calls))
                self.assertEqual(len(model.calls), len(result.candidate.blocks) + 1)
                self.assertEqual(result.trace["steps"][-1]["model_choice"], "option_000")
                self.assertEqual(model.calls[-1][1], {"option_000": END})

    def test_early_end_is_rejected_until_wat_compiles(self):
        result = decode("checksum hash", self.library, EarlyEndModel())
        self.assertEqual(result.candidate.name, "checksum")
        self.assertTrue(result.trace["steps"][0]["early_end_rejected"])
        self.assertEqual(result.trace["termination"], END)
        self.assertGreaterEqual(result.trace["api_call_count"], 3)

    def test_option_ids_are_opaque_and_trace_contains_only_hashes(self):
        trace = decode("checksum", self.library, ScriptedModel()).trace
        options = trace["steps"][0]["options"]
        self.assertTrue(all(item["id"].startswith("option_") for item in options))
        encoded = json.dumps(options)
        self.assertNotIn("checksum.wat", encoded)
        self.assertNotIn("integer_math.wat", encoded)
        self.assertNotIn("(module", encoded)

    def test_live_client_accepts_one_option_end_step(self):
        def transport(url, headers, body, timeout):
            return {
                "model": "jev-test",
                "usage": {"input_tokens": 1, "output_tokens": 1},
                "answers": {"next_block": {
                    "type": "choice", "choice": "option_000", "confidence": 1.0,
                    "probabilities": {"option_000": 1.0},
                }},
            }

        prediction = JevClient("not-a-real-key", transport=transport).score_next(
            "finish", "(module)", [END]
        )
        self.assertEqual(prediction.top_prediction, END)
        self.assertEqual(prediction.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()
