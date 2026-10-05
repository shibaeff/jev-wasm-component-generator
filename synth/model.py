"""Choice models for closed-candidate WAT block decoding."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class Choice:
    option_id: str
    probabilities: Mapping[str, float]
    model: str
    usage: Mapping[str, int] = field(default_factory=dict)


class ScriptedModel:
    """Deterministic offline scorer based only on spec, prefix, and offered actions."""

    name = "offline-scripted-v2"

    def choose(self, spec: str, prefix: str, options: Mapping[str, str]) -> Choice:
        if not options:
            raise ValueError("model requires at least one option")
        wanted = set(re.findall(r"[a-z0-9_]+", spec.lower()))
        aliases = {
            "hash": {"checksum", "fnv", "fnv1a"},
            "billing": {"subscription", "monthly", "due", "cents"},
            "math": {"integer", "clamp", "gcd", "divisor"},
        }
        for word, additions in aliases.items():
            if word in wanted or wanted.intersection(additions):
                wanted.add(word)
                wanted.update(additions)
        scores: dict[str, float] = {}
        for option_id, wat in options.items():
            if wat == "END":
                scores[option_id] = 1000.0 if len(options) == 1 else -1.0
            else:
                words = set(re.findall(r"[a-z0-9_]+", wat.lower()))
                scores[option_id] = float(len(wanted & words))
        ordered = list(options)
        best = max(ordered, key=lambda key: (scores[key], -ordered.index(key)))
        minimum = min(scores.values())
        weights = {key: scores[key] - minimum + 1.0 for key in ordered}
        total = sum(weights.values())
        return Choice(best, {key: value / total for key, value in weights.items()}, self.name)
