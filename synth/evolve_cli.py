"""CLI for compiler-validated whole-program WAT edit evolution."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .cli import _atomic_write
from .evolution import END, EditOperation, ScriptedEditModel, evolve, load_program
from .jev.client import JevClient

ROOT = Path(__file__).resolve().parents[1]


class LiveEditModel:
    def __init__(self, name: str):
        key = os.environ.get("JEV_API_KEY") or os.environ.get("TYPESAFE_API_KEY")
        if not key:
            raise ValueError("JEV_API_KEY or TYPESAFE_API_KEY is required for a live model")
        self.client = JevClient(key, model=name)

    def choose_edit(self, spec, current_source, target_source, options):
        criteria = {}
        for option_id, action in options.items():
            if action == END:
                criteria[option_id] = {"sentinel": END}
            else:
                assert isinstance(action, EditOperation)
                criteria[option_id] = {
                    "operation": action.kind,
                    "position": action.position,
                    "delete_count": action.delete_count,
                    "inserted_wat_blocks": list(action.blocks),
                }
        return self.client.score_edit(spec, current_source, target_source, criteria)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jev-wasm-evolve",
        description="Iteratively transform a full compiling WAT program with positioned Jev-ranked edits",
    )
    parser.add_argument("spec", nargs="?", help="transition objective")
    parser.add_argument("--spec-file", type=Path)
    parser.add_argument(
        "--initial", type=Path,
        default=ROOT / "examples/sort-evolution/insertion_sort.wat",
        help="initial compiling block-segmented WAT program",
    )
    parser.add_argument(
        "--target", type=Path,
        default=ROOT / "examples/sort-evolution/quicksort.wat",
        help="reference target WAT program",
    )
    parser.add_argument("--output", type=Path, default=Path("generated/evolved-sort.wat"))
    parser.add_argument("--trace", type=Path, default=Path("generated/evolution-trace.json"))
    parser.add_argument("--model", default="offline", help="offline or a live Jev model alias")
    return parser


def _read_spec(args) -> str:
    if args.spec is not None and args.spec_file is not None:
        raise ValueError("use exactly one of inline spec or --spec-file")
    if args.spec_file is not None:
        value = args.spec_file.read_text(encoding="utf-8")
    elif args.spec is not None:
        value = args.spec
    elif not sys.stdin.isatty():
        value = sys.stdin.read()
    else:
        value = "transition insertion sort to quicksort while preserving sort(offset, length)"
    if not value.strip():
        raise ValueError("evolution specification must not be empty")
    return value


def main(argv=None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        model = ScriptedEditModel() if args.model == "offline" else LiveEditModel(args.model)
        result = evolve(_read_spec(args), load_program(args.initial), load_program(args.target), model)
        _atomic_write(args.output, result.source)
        _atomic_write(args.trace, json.dumps(result.trace, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(1, f"jev-wasm-evolve: {exc}\n")
    edits = [step["selected_edit"] for step in result.trace["steps"] if step["selected_edit"]]
    print(f"applied {len(edits)} edits; wrote {args.output} and {args.trace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
