---
name: jev-wasm-component-generator
description: Use when generating or extending components with the Jev WAT-only autonomous reconstruction loop.
---

# Jev WAT component generator

Jev is a closed-candidate decision model here. It may rank only ordered `;; JEV BLOCK:` WebAssembly Text from `library/*.wat` and explicit `END`. Hermes may orchestrate, compile, audit, and test with host tools, but host code is never Jev-generated output.

## Run

```sh
npm ci
./jev-wasm --model jev-latest "PROGRAM SPEC"
make test && make audit
```

Input can also come from `--spec-file` or stdin. Set `JEV_API_KEY` or `TYPESAFE_API_KEY` in the environment only. Never write credentials to source or traces.

## Change safely

Read `docs/WORKFLOW.md`. Preserve opaque option IDs, full-prefix scoring, no teacher forcing, one model call per block plus final `END`, bounded decoding, exact-source compilation, and sanitized traces. Every added component must be independently compiling WAT, have at least two block markers, be in the manifest, and have behavioral tests.

Fail closed on malformed responses, non-exact or invalid WAT, secrets, or language-purity violations. Label exact library reconstruction as retrieval/imitation, never novel synthesis.
