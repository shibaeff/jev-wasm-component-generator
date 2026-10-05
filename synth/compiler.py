"""Compile validation for exact generated WAT."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate_wat(source: str) -> None:
    with tempfile.TemporaryDirectory(prefix="jev-wasm-") as directory:
        candidate = Path(directory) / "candidate.wat"
        candidate.write_text(source, encoding="utf-8")
        process = subprocess.run(
            ["node", "scripts/compile-wat.js", str(candidate)],
            cwd=ROOT, text=True, capture_output=True, timeout=30, check=False,
        )
    if process.returncode:
        message = (process.stderr or process.stdout or "WAT compilation failed").strip()
        raise ValueError(message[-2000:])
