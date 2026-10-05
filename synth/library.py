"""Load ordered WAT block demonstrations from the component library."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

BLOCK_MARKER = ";; JEV BLOCK:"


@dataclass(frozen=True)
class Candidate:
    name: str
    filename: str
    description: str
    source: str
    blocks: tuple[str, ...]


def _split_blocks(source: str, filename: str) -> tuple[str, ...]:
    lines = source.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if line.startswith(BLOCK_MARKER)]
    if not starts or starts[0] != 0:
        raise ValueError(f"{filename} must start with {BLOCK_MARKER}")
    starts.append(len(lines))
    blocks = tuple("".join(lines[starts[i]:starts[i + 1]]) for i in range(len(starts) - 1))
    if len(blocks) < 2 or any(not block.strip() for block in blocks):
        raise ValueError(f"{filename} must contain at least two non-empty JEV blocks")
    if "(module" not in blocks[0] or not source.strip().endswith(")"):
        raise ValueError(f"invalid WAT module: {filename}")
    if "".join(blocks) != source:
        raise ValueError(f"block split did not preserve exact source: {filename}")
    return blocks


def load_library(directory: Path) -> tuple[Candidate, ...]:
    manifest = json.loads((directory / "index.json").read_text(encoding="utf-8"))
    entries = manifest.get("modules")
    if not isinstance(entries, list) or not entries:
        raise ValueError("library/index.json must contain a non-empty modules list")
    candidates: list[Candidate] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"name", "file", "description"}:
            raise ValueError("each library entry needs name, file, and description")
        filename = entry["file"]
        if not isinstance(filename, str) or Path(filename).name != filename or not filename.endswith(".wat"):
            raise ValueError("library file must be a local .wat basename")
        if filename in seen:
            raise ValueError("duplicate library file")
        seen.add(filename)
        source = (directory / filename).read_text(encoding="utf-8")
        blocks = _split_blocks(source, filename)
        candidates.append(Candidate(str(entry["name"]), filename, str(entry["description"]), source, blocks))
    unlisted = {path.name for path in directory.glob("*.wat")} - seen
    if unlisted:
        raise ValueError("unlisted WAT candidates: " + ", ".join(sorted(unlisted)))
    return tuple(candidates)
