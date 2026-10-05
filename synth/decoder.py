"""Autonomous closed-candidate reconstruction of WAT components."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from .compiler import validate_wat
from .library import Candidate
from .model import Choice

END = "END"


class ChoiceModel(Protocol):
    def choose(self, spec: str, prefix: str, options: Mapping[str, str]) -> Choice: ...


@dataclass(frozen=True)
class DecodeResult:
    candidate: Candidate
    source: str
    trace: dict[str, Any]


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _next_blocks(prefix: str, candidates: tuple[Candidate, ...]) -> tuple[list[str], bool]:
    offered: list[str] = []
    complete = False
    for candidate in candidates:
        built = ""
        for index, block in enumerate(candidate.blocks):
            if built == prefix and block not in offered:
                offered.append(block)
            built += block
        if built == prefix:
            complete = True
    return offered, complete


def _validate_choice(choice: Choice, options: Mapping[str, str]) -> None:
    if choice.option_id not in options:
        raise ValueError("model chose an unknown option ID")
    if set(choice.probabilities) != set(options):
        raise ValueError("model probabilities do not match offered option IDs")
    if any(value < 0 or value > 1 for value in choice.probabilities.values()):
        raise ValueError("model returned an invalid probability")


def decode(spec: str, candidates: tuple[Candidate, ...], model: ChoiceModel) -> DecodeResult:
    """Generate from empty prefix using only Jev-ranked library blocks and END."""
    if not spec.strip():
        raise ValueError("specification must not be empty")
    if not candidates:
        raise ValueError("component library is empty")
    sources = [item.source for item in candidates]
    if len(sources) != len(set(sources)):
        raise ValueError("library candidates must have unique source")

    prefix = ""
    steps: list[dict[str, Any]] = []
    max_steps = max(len(item.blocks) for item in candidates) + 2
    for number in range(1, max_steps + 1):
        blocks, complete = _next_blocks(prefix, candidates)
        actions = blocks + [END]
        opaque = {f"option_{index:03d}": value for index, value in enumerate(actions)}
        choice = model.choose(spec, prefix, opaque)
        _validate_choice(choice, opaque)
        selected_id = choice.option_id
        selected_action = opaque[selected_id]
        rejected_end = False

        if selected_action == END:
            compiled = prefix in sources
            if compiled:
                try:
                    validate_wat(prefix)
                except (OSError, ValueError):
                    compiled = False
            if not compiled:
                ranked = sorted(
                    (key for key, value in opaque.items() if value != END),
                    key=lambda key: choice.probabilities[key],
                    reverse=True,
                )
                if not ranked:
                    raise ValueError("model chose END before any compilable completion")
                selected_id = ranked[0]
                selected_action = opaque[selected_id]
                rejected_end = True

        step = {
            "step": number,
            "prefix_sha256": _digest(prefix),
            "options": [
                {"id": key, **({"sentinel": END} if value == END else {"wat_sha256": _digest(value)})}
                for key, value in opaque.items()
            ],
            "model_choice": choice.option_id,
            "effective_choice": selected_id,
            "early_end_rejected": rejected_end,
            "probabilities": dict(choice.probabilities),
            "model": choice.model,
            "usage": dict(choice.usage),
        }
        steps.append(step)

        if selected_action == END:
            if not complete or prefix not in sources:
                raise ValueError("compiled completion is not an exact library component")
            selected = candidates[sources.index(prefix)]
            trace = {
                "schema_version": 2,
                "mode": "autonomous-closed-candidate-wat-block-reconstruction",
                "classification": "retrieval/imitation (exact library reconstruction)",
                "candidate_source": "library/*.wat JEV blocks only",
                "teacher_forcing": False,
                "spec_sha256": _digest(spec),
                "api_call_count": len(steps),
                "usage": {
                    "input_tokens": sum(step["usage"].get("input_tokens", 0) for step in steps),
                    "output_tokens": sum(step["usage"].get("output_tokens", 0) for step in steps),
                },
                "steps": steps,
                "termination": END,
                "selected": {"name": selected.name, "file": selected.filename, "sha256": _digest(prefix)},
                "compile_validation": "passed",
                "exact_library_match": True,
            }
            return DecodeResult(selected, prefix, trace)

        prefix += selected_action

    raise ValueError("decoder exhausted its bounded autonomous loop without valid END")
