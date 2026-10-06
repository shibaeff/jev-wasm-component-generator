"""Strict Python-stdlib client for the TypeSafe System One choice API."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from synth.audit import audit_payload
from synth.model import Choice

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
QUESTION = "next_block"


class JevError(RuntimeError):
    pass


class MalformedResponseError(JevError):
    pass


@dataclass(frozen=True)
class CandidateProbability:
    candidate: str
    probability: float

    def to_dict(self) -> dict[str, object]:
        return {"candidate": self.candidate, "probability": self.probability}


@dataclass(frozen=True)
class Prediction:
    probabilities: tuple[CandidateProbability, ...]
    top_prediction: str
    confidence: float
    model: str
    usage: Mapping[str, int]

    def to_dict(self) -> dict[str, object]:
        return {"probabilities": [item.to_dict() for item in self.probabilities],
                "top_prediction": self.top_prediction, "confidence": self.confidence,
                "model": self.model, "usage": dict(self.usage)}


Transport = Callable[[str, Mapping[str, str], bytes, float], Mapping[str, Any]]


def _transport(url: str, headers: Mapping[str, str], body: bytes, timeout: float) -> Mapping[str, Any]:
    with urlopen(Request(url, data=body, headers=dict(headers), method="POST"), timeout=timeout) as response:
        try:
            value = json.loads(response.read().decode())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MalformedResponseError("Jev returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise MalformedResponseError("Jev returned a non-object response")
    return value


class JevClient:
    def __init__(self, api_key: str, *, model: str = "jev-latest", endpoint: str = ENDPOINT,
                 timeout: float = 45.0, transport: Transport = _transport):
        if not api_key:
            raise ValueError("api_key must not be empty")
        self._key, self.model, self.endpoint = api_key, model, endpoint
        self.timeout, self._transport = timeout, transport

    def score_next(self, task: str, prefix: str, candidates: Sequence[str], *,
                   demonstrations: Sequence[Mapping[str, Any]] | None = None) -> Prediction:
        candidates = list(candidates)
        if not 1 <= len(candidates) <= 255 or len(set(candidates)) != len(candidates) or candidates.count("END") != 1:
            raise ValueError("candidates must be 1..255 unique values including END exactly once")
        options = {f"option_{index:03d}": candidate for index, candidate in enumerate(candidates)}
        state = {"task": task, "generated_wat_prefix": prefix,
                 "method": "autonomous retrieval/imitation", "demonstrations": list(demonstrations or ())}
        payload = {"state": state, "model": self.model, "questions": {QUESTION: {
            "type": "choice",
            "instructions": "Choose the most likely next complete WebAssembly Text source block. END means the WAT module is complete.",
            "criteria": {option: {"wat_source_block": block} for option, block in options.items()},
        }}}
        audit_payload(payload)
        try:
            response = self._transport(self.endpoint, {"Authorization": "Bearer " + self._key,
                "Content-Type": "application/json", "Accept": "application/json",
                "User-Agent": "jev-wasm-component-generator/1.0"}, json.dumps(payload).encode(), self.timeout)
        except HTTPError as exc:
            raise JevError(f"Jev API request failed with HTTP {exc.code}") from exc
        except URLError as exc:
            raise JevError("Jev API request failed: network error") from exc
        except MalformedResponseError:
            raise
        except Exception as exc:
            raise JevError("Jev API request failed") from exc
        return _decode(response, options)

    def score_edit(
        self,
        task: str,
        current_wat: str,
        target_wat: str,
        criteria: Mapping[str, Mapping[str, Any]],
    ) -> Choice:
        """Rank structured insert/remove/replace operations over a full WAT program."""
        expected = set(criteria)
        if not expected or len(expected) > 255 or any(not key.startswith("option_") for key in expected):
            raise ValueError("edit criteria require 1..255 opaque option IDs")
        end_count = sum(value == {"sentinel": "END"} for value in criteria.values())
        if end_count != 1:
            raise ValueError("edit criteria must contain END exactly once")
        state = {
            "task": task,
            "current_wat": current_wat,
            "target_wat": target_wat,
            "method": "reference-guided whole-program WAT edit transformation",
        }
        payload = {"state": state, "model": self.model, "questions": {"next_edit": {
            "type": "choice",
            "instructions": (
                "Choose the best next compiler-valid WAT edit. Positions are zero-based block "
                "indices in current_wat. END means current_wat exactly matches target_wat."
            ),
            "criteria": dict(criteria),
        }}}
        audit_payload(payload)
        try:
            response = self._transport(self.endpoint, {"Authorization": "Bearer " + self._key,
                "Content-Type": "application/json", "Accept": "application/json",
                "User-Agent": "jev-wasm-component-generator/1.0"}, json.dumps(payload).encode(), self.timeout)
        except HTTPError as exc:
            raise JevError(f"Jev API request failed with HTTP {exc.code}") from exc
        except URLError as exc:
            raise JevError("Jev API request failed: network error") from exc
        except MalformedResponseError:
            raise
        except Exception as exc:
            raise JevError("Jev API request failed") from exc
        return _decode_choice(response, "next_edit", expected)


def _decode_choice(response: Mapping[str, Any], question: str, expected: set[str]) -> Choice:
    try:
        model, usage = response["model"], response["usage"]
        answer = response["answers"][question]
        selected, probabilities = answer["choice"], answer["probabilities"]
    except (KeyError, TypeError) as exc:
        raise MalformedResponseError("Jev response missing required fields") from exc
    valid = (
        isinstance(model, str) and bool(model) and isinstance(answer, dict)
        and answer.get("type") == "choice" and selected in expected
        and isinstance(probabilities, dict) and set(probabilities) == expected
    )
    if not valid or any(not _number(value) or not 0 <= value <= 1 for value in probabilities.values()):
        raise MalformedResponseError("invalid Jev choice response")
    if not math.isclose(sum(probabilities.values()), 1, abs_tol=1e-6):
        raise MalformedResponseError("invalid Jev probabilities")
    if not isinstance(usage, dict) or set(usage) != {"input_tokens", "output_tokens"} or any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in usage.values()):
        raise MalformedResponseError("invalid Jev usage")
    return Choice(selected, {key: float(probabilities[key]) for key in probabilities}, model, dict(usage))


def _number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _decode(response: Mapping[str, Any], options: Mapping[str, str]) -> Prediction:
    try:
        model, usage = response["model"], response["usage"]
        answer = response["answers"][QUESTION]
        choice, confidence, probabilities = answer["choice"], answer["confidence"], answer["probabilities"]
    except (KeyError, TypeError) as exc:
        raise MalformedResponseError("Jev response missing required fields") from exc
    expected = set(options)
    valid = (isinstance(model, str) and bool(model) and isinstance(answer, dict) and answer.get("type") == "choice"
             and choice in expected and _number(confidence) and 0 <= confidence <= 1
             and isinstance(probabilities, dict) and set(probabilities) == expected)
    if not valid or any(not _number(value) or not 0 <= value <= 1 for value in probabilities.values()):
        raise MalformedResponseError("invalid Jev choice response")
    if not math.isclose(sum(probabilities.values()), 1, abs_tol=1e-6):
        raise MalformedResponseError("invalid Jev probabilities")
    if not isinstance(usage, dict) or set(usage) != {"input_tokens", "output_tokens"} or any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in usage.values()):
        raise MalformedResponseError("invalid Jev usage")
    decoded = tuple(CandidateProbability(options[key], float(probabilities[key])) for key in options)
    return Prediction(decoded, options[choice], float(confidence), model, dict(usage))
