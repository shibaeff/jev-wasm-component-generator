---
name: jev-wasm-component-generator
description: Use when generating or extending components with the Jev WAT-only autonomous reconstruction loop.
---

# Jev WAT component generator

## Invariant

Jev may rank only `;; JEV BLOCK:` WebAssembly Text sections from `library/*.wat` and the explicit `END` action. Host code orchestrates and validates; it is never Jev output.

## Generate

```sh
npm ci
./jev-wasm --model jev-latest "PROGRAM SPEC"
./jev-wasm --model jev-latest --spec-file SPEC.txt --output generated/component.wat --trace generated/trace.json
```

Use `JEV_API_KEY` or `TYPESAFE_API_KEY`. Never put keys in source, prompts, traces, examples, or commits.

## Extend

Read `docs/WORKFLOW.md`, `library/index.json`, and `synth/decoder.py`. Add standalone compiling WAT with at least two ordered `;; JEV BLOCK:` sections, register it, and add behavioral tests.

Preserve opaque option IDs, full-prefix scoring, no teacher forcing, a model-called final `END`, exact-source compilation, bounded steps, and sanitized probability traces. Do not add host-language candidates or repair WAT after decoding.

## Verify and report

Run `make test && make audit`. Report exact library reconstruction as **retrieval/imitation**, never novel synthesis. Fail closed on malformed model responses, invalid WAT, non-exact output, secrets, or purity violations.
