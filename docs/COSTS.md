# Cost of a completed Jev WAT run

Pricing snapshot: **2026-10-05**, USD, standard API rates.

## Measured run

The live checksum reconstruction used `jev-1.13.0` and completed successfully:

- API calls: **3**
- Input tokens: **1,828**
- Output tokens: **143**
- Result: exact checksum-library reconstruction
- Compilation: passed
- Teacher forcing: false

TypeSafe prices Jev 1.13 at **$0.042 per million input tokens** and makes output free.

```text
1,828 × $0.042 / 1,000,000 = $0.000076776
```

That is:

- **$0.0000768 per completed component**
- **0.00768 cents per component**
- **$0.0768 per 1,000 components**
- **$76.78 per million components**, if every run has the same token envelope

Official Jev pricing: https://docs.typesafe.ai/models

## Normalized Anthropic comparison

The table below prices the **same measured envelope**—1,828 input and 143 output tokens—at Anthropic’s standard rates. This isolates API pricing; actual Claude tokenization and behavior may differ.

| Model | Input / MTok | Output / MTok | Cost/run | Multiple of Jev |
|---|---:|---:|---:|---:|
| Jev 1.13 | $0.042 | $0 | $0.0000768 | 1.0× |
| Claude Haiku 4.5 | $1 | $5 | $0.002543 | 33.1× |
| Claude Sonnet 5.5 | $2 | $10 | $0.005086 | 66.2× |
| Claude Sonnet 4.6 | $3 | $15 | $0.007629 | 99.4× |
| Claude Opus 4.6 | $5 | $25 | $0.012715 | 165.6× |

Official Anthropic pricing: https://platform.claude.com/docs/en/about-claude/pricing

## Reproduce from a trace

Every live trace contains total and per-step usage:

```json
{
  "api_call_count": 3,
  "usage": {
    "input_tokens": 1828,
    "output_tokens": 143
  }
}
```

Calculate the snapshot comparison:

```sh
python3 scripts/estimate_cost.py generated/trace.json
# or
make cost TRACE=generated/trace.json
```

Machine-readable output:

```sh
python3 scripts/estimate_cost.py --json generated/trace.json
```

## What this comparison does—and does not—prove

This workflow is cheap because Jev makes constrained decisions among prewritten WAT blocks. It does not generate arbitrary source text. Claude can synthesize genuinely unseen code, so a direct Claude generation call provides a broader capability than this loop.

The current loop also resends a growing prefix. With `n` similarly sized blocks, cumulative input can approach quadratic growth because later decisions repeatedly include earlier WAT. Keep semantic blocks reasonably large, trim irrelevant candidates, and benchmark full-task cost—not only per-token price.

Treat the rates in this document as a dated snapshot. Re-run the calculator with updated rates when provider pricing changes.
