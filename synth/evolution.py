"""Compiler-validated, closed-candidate WAT edit evolution."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from .compiler import validate_wat
from .library import _split_blocks
from .model import Choice

END = "END"


@dataclass(frozen=True)
class Program:
    name: str
    source: str
    blocks: tuple[str, ...]


@dataclass(frozen=True)
class EditOperation:
    kind: str
    position: int
    delete_count: int
    blocks: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.kind not in {"insert", "remove", "replace"}:
            raise ValueError("edit kind must be insert, remove, or replace")
        if self.position < 0 or self.delete_count < 0:
            raise ValueError("edit positions and counts must be non-negative")
        expected = {"insert": (0, True), "remove": (1, False), "replace": (1, True)}[self.kind]
        if self.delete_count != expected[0] or bool(self.blocks) is not expected[1]:
            raise ValueError(f"invalid {self.kind} edit shape")

    def apply(self, source: Sequence[str]) -> tuple[str, ...]:
        items = tuple(source)
        if self.position > len(items) or self.position + self.delete_count > len(items):
            raise ValueError("edit position is outside the current program")
        return items[:self.position] + self.blocks + items[self.position + self.delete_count:]


class EditChoiceModel(Protocol):
    def choose_edit(
        self,
        spec: str,
        current_source: str,
        target_source: str,
        options: Mapping[str, EditOperation | str],
    ) -> Choice: ...


@dataclass(frozen=True)
class EvolutionResult:
    source: str
    trace: dict[str, Any]


def load_program(path: Path) -> Program:
    source = path.read_text(encoding="utf-8")
    return Program(path.stem.replace("_", "-"), source, _split_blocks(source, path.name))


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _distance(left: Sequence[str], right: Sequence[str]) -> int:
    previous = list(range(len(right) + 1))
    for row, left_value in enumerate(left, 1):
        current = [row]
        for column, right_value in enumerate(right, 1):
            current.append(min(
                current[-1] + 1,
                previous[column] + 1,
                previous[column - 1] + (left_value != right_value),
            ))
        previous = current
    return previous[-1]


@lru_cache(maxsize=2048)
def _compiles(blocks: tuple[str, ...]) -> bool:
    try:
        validate_wat("".join(blocks))
    except (OSError, ValueError):
        return False
    return True


def _candidate_edits(current: tuple[str, ...], target: tuple[str, ...]) -> tuple[EditOperation, ...]:
    """Return primitive compiling edits that never increase block edit distance."""
    baseline = _distance(current, target)
    if baseline == 0:
        return ()
    proposals: list[EditOperation] = []
    seen_results: set[tuple[str, ...]] = set()

    operations: list[EditOperation] = []
    for block in target:
        for position in range(len(current) + 1):
            operations.append(EditOperation("insert", position, 0, (block,)))
    for position in range(len(current)):
        for block in target:
            operations.append(EditOperation("replace", position, 1, (block,)))
    for position in range(len(current)):
        operations.append(EditOperation("remove", position, 1, ()))

    for operation in operations:
        changed = operation.apply(current)
        if changed in seen_results or changed == current or _distance(changed, target) > baseline:
            continue
        if not _compiles(changed):
            continue
        seen_results.add(changed)
        proposals.append(operation)
    return tuple(proposals)


def _find_compiler_valid_path(
    current: tuple[str, ...],
    target: tuple[str, ...],
    depth: int,
    seen: frozenset[tuple[str, ...]],
) -> tuple[EditOperation, ...] | None:
    if current == target:
        return ()
    if depth == 0:
        return None
    candidates = sorted(
        _candidate_edits(current, target),
        key=lambda edit: (
            _distance(edit.apply(current), target),
            {"insert": 0, "replace": 1, "remove": 2}[edit.kind],
            edit.position,
        ),
    )
    for operation in candidates:
        changed = operation.apply(current)
        if changed in seen:
            continue
        suffix = _find_compiler_valid_path(changed, target, depth - 1, seen | {changed})
        if suffix is not None:
            return (operation, *suffix)
    return None


def propose_edits(current: tuple[str, ...], target: tuple[str, ...]) -> tuple[EditOperation, ...]:
    """Offer only the next edit on a complete compiler-valid path to the target."""
    path = _find_compiler_valid_path(
        current,
        target,
        len(current) + len(target) + 4,
        frozenset({current}),
    )
    return () if not path else (path[0],)


def _edit_trace(operation: EditOperation) -> dict[str, Any]:
    return {
        "kind": operation.kind,
        "position": operation.position,
        "delete_count": operation.delete_count,
        "inserted_block_sha256": [_digest(block) for block in operation.blocks],
    }


def _option_trace(option_id: str, action: EditOperation | str) -> dict[str, Any]:
    if action == END:
        return {"id": option_id, "sentinel": END}
    if not isinstance(action, EditOperation):
        raise ValueError("invalid edit option")
    return {"id": option_id, **_edit_trace(action)}


class ScriptedEditModel:
    """Deterministic offline ranker for compiler-valid distance-reducing edits."""

    name = "offline-scripted-edit-v1"

    def choose_edit(self, spec, current_source, target_source, options):
        ordered = list(options)
        actionable = [key for key in ordered if options[key] != END]
        selected = actionable[0] if actionable else ordered[0]
        if len(ordered) == 1:
            probabilities = {selected: 1.0}
        else:
            selected_mass = 0.9
            remainder = (1.0 - selected_mass) / (len(ordered) - 1)
            probabilities = {key: (selected_mass if key == selected else remainder) for key in ordered}
        return Choice(selected, probabilities, self.name)


def _validate_choice(choice: Choice, options: Mapping[str, EditOperation | str]) -> None:
    if choice.option_id not in options or set(choice.probabilities) != set(options):
        raise ValueError("model edit response does not match offered option IDs")
    if any(value < 0 or value > 1 for value in choice.probabilities.values()):
        raise ValueError("model returned an invalid edit probability")


def evolve(
    spec: str,
    initial: Program,
    target: Program,
    model: EditChoiceModel,
) -> EvolutionResult:
    """Iteratively transform one full compiling WAT program into another."""
    if not spec.strip():
        raise ValueError("evolution specification must not be empty")
    validate_wat(initial.source)
    validate_wat(target.source)

    current = initial.blocks
    steps: list[dict[str, Any]] = []
    max_steps = len(initial.blocks) + len(target.blocks) + 4

    for number in range(1, max_steps + 1):
        edits = propose_edits(current, target.blocks)
        actions: list[EditOperation | str] = [*edits, END]
        opaque = {f"option_{index:03d}": action for index, action in enumerate(actions)}
        current_source = "".join(current)
        choice = model.choose_edit(spec, current_source, target.source, opaque)
        _validate_choice(choice, opaque)
        selected_id = choice.option_id
        selected = opaque[selected_id]
        rejected_end = False

        if selected == END and current != target.blocks:
            ranked = sorted(
                (key for key, action in opaque.items() if action != END),
                key=lambda key: choice.probabilities[key],
                reverse=True,
            )
            if not ranked:
                raise ValueError("no compiler-valid edit advances toward the target")
            selected_id = ranked[0]
            selected = opaque[selected_id]
            rejected_end = True

        selected_trace = None
        if selected != END:
            if not isinstance(selected, EditOperation):
                raise ValueError("invalid selected edit")
            selected_trace = _edit_trace(selected)

        step = {
            "step": number,
            "current_program_sha256": _digest(current_source),
            "current_block_count": len(current),
            "remaining_block_edit_distance": _distance(current, target.blocks),
            "options": [_option_trace(key, action) for key, action in opaque.items()],
            "model_choice": choice.option_id,
            "effective_choice": selected_id,
            "early_end_rejected": rejected_end,
            "selected_edit": selected_trace,
            "probabilities": dict(choice.probabilities),
            "model": choice.model,
            "usage": dict(choice.usage),
        }
        steps.append(step)

        if selected == END:
            if current != target.blocks:
                raise ValueError("model ended before reaching the target program")
            final_source = "".join(current)
            validate_wat(final_source)
            trace = {
                "schema_version": 1,
                "mode": "autonomous-closed-candidate-whole-program-wat-editing",
                "classification": "reference-guided transformation (target supplied; not novel synthesis)",
                "teacher_forcing": False,
                "initial_algorithm": initial.name,
                "target_algorithm": target.name,
                "spec_sha256": _digest(spec),
                "initial_sha256": _digest(initial.source),
                "target_sha256": _digest(target.source),
                "api_call_count": len(steps),
                "usage": {
                    "input_tokens": sum(step["usage"].get("input_tokens", 0) for step in steps),
                    "output_tokens": sum(step["usage"].get("output_tokens", 0) for step in steps),
                },
                "steps": steps,
                "termination": END,
                "compile_validation": "passed",
                "exact_target_match": True,
            }
            return EvolutionResult(final_source, trace)

        if not isinstance(selected, EditOperation):
            raise ValueError("invalid selected edit")
        current = selected.apply(current)
        validate_wat("".join(current))

    raise ValueError("edit evolution exhausted its bounded loop without reaching the target")
