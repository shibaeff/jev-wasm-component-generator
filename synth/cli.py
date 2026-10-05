"""Command-line interface for the generic Jev WAT component generator."""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from .decoder import decode
from .library import load_library
from .model import Choice, ScriptedModel
from .jev.client import JevClient

ROOT = Path(__file__).resolve().parents[1]


class LiveModel:
    def __init__(self, name: str):
        key = os.environ.get("JEV_API_KEY") or os.environ.get("TYPESAFE_API_KEY")
        if not key:
            raise ValueError("JEV_API_KEY or TYPESAFE_API_KEY is required for a live model")
        self.client = JevClient(key, model=name)

    def choose(self, spec, prefix, options):
        ordered = list(options)
        prediction = self.client.score_next(spec, prefix, [options[key] for key in ordered])
        selected = ordered[[options[key] for key in ordered].index(prediction.top_prediction)]
        probabilities = {ordered[index]: item.probability for index, item in enumerate(prediction.probabilities)}
        return Choice(selected, probabilities, prediction.model, prediction.usage)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jev-wasm", description="Select and validate a WAT component from a closed library")
    parser.add_argument("spec", nargs="?", help="inline natural-language or JSON specification")
    parser.add_argument("--spec-file", type=Path, help="read the specification from a file")
    parser.add_argument("--output", type=Path, default=Path("generated/component.wat"), help="WAT output path")
    parser.add_argument("--trace", type=Path, default=Path("generated/trace.json"), help="JSON trace path")
    parser.add_argument("--model", default="offline", help="offline (default) or a live Jev model name")
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
        raise ValueError("provide an inline spec, --spec-file, or stdin")
    if not value.strip():
        raise ValueError("specification must not be empty")
    return value


def _atomic_write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(value)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def main(argv=None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        spec = _read_spec(args)
        model = ScriptedModel() if args.model == "offline" else LiveModel(args.model)
        result = decode(spec, load_library(ROOT / "library"), model)
        _atomic_write(args.output, result.source)
        _atomic_write(args.trace, json.dumps(result.trace, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(1, f"jev-wasm: {exc}\n")
    print(f"selected {result.candidate.name}; wrote {args.output} and {args.trace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
