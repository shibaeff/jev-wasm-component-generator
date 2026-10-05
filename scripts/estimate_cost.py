#!/usr/bin/env python3
"""Estimate completed-run cost from a jev-wasm JSON trace."""
from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path

# USD per million tokens. Snapshot verified 2026-10-05.
RATES = {
    "Jev 1.13": (Decimal("0.042"), Decimal("0")),
    "Claude Haiku 4.5": (Decimal("1"), Decimal("5")),
    "Claude Sonnet 5.5": (Decimal("2"), Decimal("10")),
    "Claude Sonnet 4.6": (Decimal("3"), Decimal("15")),
    "Claude Opus 4.6": (Decimal("5"), Decimal("25")),
}
MILLION = Decimal(1_000_000)


def estimate(input_tokens: int, output_tokens: int) -> list[dict[str, object]]:
    rows = []
    jev_cost = Decimal(input_tokens) * RATES["Jev 1.13"][0] / MILLION
    for model, (input_rate, output_rate) in RATES.items():
        cost = (Decimal(input_tokens) * input_rate + Decimal(output_tokens) * output_rate) / MILLION
        rows.append({
            "model": model,
            "input_rate_per_million": float(input_rate),
            "output_rate_per_million": float(output_rate),
            "cost_usd": float(cost),
            "multiple_of_jev": float(cost / jev_cost) if jev_cost else None,
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    trace = json.loads(args.trace.read_text(encoding="utf-8"))
    usage = trace.get("usage")
    if not isinstance(usage, dict):
        parser.error("trace has no usage object; generate it with the current CLI")
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    if not isinstance(input_tokens, int) or not isinstance(output_tokens, int) or input_tokens < 0 or output_tokens < 0:
        parser.error("trace usage must contain non-negative integer token counts")

    rows = estimate(input_tokens, output_tokens)
    result = {
        "pricing_snapshot": "2026-10-05",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "rows": rows,
    }
    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Token envelope: {input_tokens:,} input + {output_tokens:,} output")
        for row in rows:
            multiple = row["multiple_of_jev"]
            suffix = "" if multiple is None else f" ({multiple:.1f}x Jev)"
            print(f"{row['model']:<20} ${row['cost_usd']:.9f}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
