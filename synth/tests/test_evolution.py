from __future__ import annotations

import json
import subprocess
import tempfile
import unittest

from pathlib import Path

from synth.evolution import EditOperation, ScriptedEditModel, evolve, load_program
from synth.model import Choice
from synth.jev.client import JevClient

ROOT = Path(__file__).resolve().parents[2]


class LastEditModel:
    def choose_edit(self, spec, current_source, target_source, options):
        actionable = [key for key, value in options.items() if value != "END"]
        selected = actionable[-1] if actionable else next(iter(options))
        probabilities = {key: 0.0 for key in options}
        probabilities[selected] = 1.0
        return Choice(selected, probabilities, "last-edit-test")


class SecondEditModel:
    def choose_edit(self, spec, current_source, target_source, options):
        actionable = [key for key, value in options.items() if value != "END"]
        selected = actionable[min(1, len(actionable) - 1)] if actionable else next(iter(options))
        probabilities = {key: 0.0 for key in options}
        probabilities[selected] = 1.0
        return Choice(selected, probabilities, "second-edit-test")


class EditOperationTests(unittest.TestCase):
    def test_insert_remove_and_replace_use_current_block_positions(self):
        blocks = ("open", "insertion", "wrapper", "close")

        inserted = EditOperation("insert", 1, 0, ("swap",)).apply(blocks)
        self.assertEqual(inserted, ("open", "swap", "insertion", "wrapper", "close"))

        replaced = EditOperation("replace", 2, 1, ("quicksort",)).apply(blocks)
        self.assertEqual(replaced, ("open", "insertion", "quicksort", "close"))

        removed = EditOperation("remove", 1, 1, ()).apply(blocks)
        self.assertEqual(removed, ("open", "wrapper", "close"))

    def test_offline_evolution_reaches_quicksort_with_positioned_diff_ops(self):
        initial = load_program(ROOT / "examples/sort-evolution/insertion_sort.wat")
        target = load_program(ROOT / "examples/sort-evolution/quicksort.wat")

        result = evolve(
            "Replace insertion sort with quicksort while preserving sort(offset, length)",
            initial,
            target,
            ScriptedEditModel(),
        )

        self.assertEqual(result.source, target.source)
        self.assertEqual(
            [step["selected_edit"]["kind"] for step in result.trace["steps"][:-1]],
            ["insert", "insert", "insert", "replace", "remove"],
        )
        self.assertEqual(
            [step["selected_edit"]["position"] for step in result.trace["steps"][:-1]],
            [1, 2, 3, 5, 4],
        )
        self.assertEqual(result.trace["termination"], "END")
        self.assertEqual(result.trace["compile_validation"], "passed")
        self.assertFalse(result.trace["teacher_forcing"])
        self.assertEqual(result.trace["initial_algorithm"], "insertion-sort")
        self.assertEqual(result.trace["target_algorithm"], "quicksort")

    def test_every_offered_edit_remains_on_a_compiler_valid_path_to_target(self):
        initial = load_program(ROOT / "examples/sort-evolution/insertion_sort.wat")
        target = load_program(ROOT / "examples/sort-evolution/quicksort.wat")
        for model in (LastEditModel(), SecondEditModel()):
            with self.subTest(model=type(model).__name__):
                result = evolve("transition insertion sort to quicksort", initial, target, model)
                self.assertEqual(result.source, target.source)
                self.assertTrue(result.trace["exact_target_match"])

    def test_live_edit_request_sends_whole_program_and_structured_position(self):
        captured = {}

        def transport(url, headers, body, timeout):
            import json
            captured.update(json.loads(body))
            return {
                "model": "jev-test",
                "usage": {"input_tokens": 12, "output_tokens": 3},
                "answers": {"next_edit": {
                    "type": "choice",
                    "choice": "option_000",
                    "confidence": 0.75,
                    "probabilities": {"option_000": 0.75, "option_001": 0.25},
                }},
            }

        current = ";; JEV BLOCK: current\n(module)\n"
        target = ";; JEV BLOCK: target\n(module)\n"
        criteria = {
            "option_000": {
                "operation": "insert",
                "position": 1,
                "delete_count": 0,
                "inserted_wat_blocks": [";; JEV BLOCK: helper\n  (func $helper)\n"],
            },
            "option_001": {"sentinel": "END"},
        }
        choice = JevClient("not-a-real-key", transport=transport).score_edit(
            "transition insertion sort to quicksort", current, target, criteria
        )

        self.assertEqual(choice.option_id, "option_000")
        self.assertEqual(captured["state"]["current_wat"], current)
        self.assertEqual(captured["state"]["target_wat"], target)
        self.assertEqual(
            captured["questions"]["next_edit"]["criteria"]["option_000"]["position"], 1
        )

    def test_offline_cli_writes_quicksort_and_edit_trace(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "sort.wat"
            trace = Path(directory) / "trace.json"
            process = subprocess.run(
                [
                    str(ROOT / "jev-wasm-evolve"),
                    "--initial", str(ROOT / "examples/sort-evolution/insertion_sort.wat"),
                    "--target", str(ROOT / "examples/sort-evolution/quicksort.wat"),
                    "--output", str(output),
                    "--trace", str(trace),
                    "transition insertion sort to quicksort",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(output.read_text(), (ROOT / "examples/sort-evolution/quicksort.wat").read_text())
            payload = json.loads(trace.read_text())
            self.assertEqual(payload["mode"], "autonomous-closed-candidate-whole-program-wat-editing")
            self.assertEqual(payload["api_call_count"], 6)


if __name__ == "__main__":
    unittest.main()
