#!/usr/bin/env python3
"""Repository audit for candidate purity, secrets, and generated traces."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .compiler import validate_wat
from .library import load_library

ROOT = Path(__file__).resolve().parents[1]
SECRET = re.compile(r"(?i)(?:jev|typesafe)[_-]?api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9._-]{12,}")
BEARER = re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{12,}")
MACHINE_PATH = re.compile(r"/(?:Users|home)/[^/\s]+/")
HOST_MARKERS = (
    re.compile(r"\brequire\s*\("), re.compile(r"\bmodule\.exports\b"),
    re.compile(r"^\s*(?:def|class)\s+", re.MULTILINE),
    re.compile(r"^\s*(?:from\s+\S+\s+)?import\s+", re.MULTILINE),
)


def audit(root: Path = ROOT) -> None:
    candidates = load_library(root / "library")
    if len(candidates) < 3:
        raise ValueError("at least three WAT candidates are required")
    for candidate in candidates:
        for marker in HOST_MARKERS:
            if marker.search(candidate.source):
                raise ValueError(f"host-language marker in {candidate.filename}")
        validate_wat(candidate.source)

    ignored = {".git", "node_modules", "__pycache__", "generated"}
    for path in root.rglob("*"):
        if not path.is_file() or any(part in ignored for part in path.parts):
            continue
        if path.suffix not in {"", ".md", ".py", ".js", ".json", ".yml", ".yaml", ".sh", ".wat"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if SECRET.search(text) or BEARER.search(text):
            raise ValueError(f"secret-like value in {path.relative_to(root)}")
        if MACHINE_PATH.search(text):
            raise ValueError(f"machine-specific absolute path in {path.relative_to(root)}")

    for trace in (root / "generated").glob("*.json") if (root / "generated").exists() else ():
        payload = json.loads(trace.read_text(encoding="utf-8"))
        if payload.get("teacher_forcing") is not False or payload.get("termination") != "END":
            raise ValueError(f"invalid decoder trace: {trace.name}")
        if payload.get("compile_validation") != "passed":
            raise ValueError(f"unvalidated output trace: {trace.name}")


def main() -> int:
    try:
        audit()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"audit failed: {exc}", file=sys.stderr)
        return 1
    print("audit passed: WAT-only library, compile validation, and no embedded secrets or machine paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Kept as the live-client boundary check: candidate-bearing fields must contain WAT or END.
def audit_payload(payload, source_context: bool = False) -> None:
    source_keys = {
        "wat_source_block", "generated_wat_prefix", "source", "block", "blocks",
        "current_wat", "target_wat", "inserted_wat_blocks",
    }
    if isinstance(payload, dict):
        for key, value in payload.items():
            audit_payload(value, source_context or key in source_keys)
    elif isinstance(payload, list):
        for value in payload:
            audit_payload(value, source_context)
    elif isinstance(payload, str) and source_context and payload not in {"", "END"}:
        if "(module" not in payload and not payload.lstrip().startswith(";;"):
            raise ValueError("non-WAT value crossed the model source boundary")
