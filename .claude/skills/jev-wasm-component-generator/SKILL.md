---
name: jev-wasm-component-generator
description: Use when generating or extending components with the Jev WAT-only autonomous reconstruction loop.
---

# Jev WAT component generator

## Invariant

Jev may rank only `;; JEV BLOCK:` WebAssembly Text sections from `library/*.wat` and explicit `END`. Claude may edit orchestration and tests, but must never present host code as Jev-generated source.

## Commands

```sh
npm ci
./jev-wasm --model jev-latest "PROGRAM SPEC"
make test && make audit
```

For file input use `--spec-file`; for output use `--output` and `--trace`. Credentials come only from `JEV_API_KEY` or `TYPESAFE_API_KEY` and must never be persisted.

Before modifying the loop, read `docs/WORKFLOW.md`, `library/index.json`, and `synth/decoder.py`. Preserve opaque IDs, full-prefix decisions, no teacher forcing, model-selected final `END`, exact compilation, bounded decoding, and sanitized traces. Add behavior tests for every new WAT module.

Fail closed on malformed responses, invalid or non-exact WAT, secrets, machine paths, and purity violations. Describe exact library reconstruction as retrieval/imitation, not novel synthesis.
