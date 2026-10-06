---
name: jev-wasm-component-generator
description: Use when reconstructing or iteratively editing WAT with Jev.
---

# Jev WAT component generator

Jev is a closed-candidate decision model. It may rank only WebAssembly Text blocks, structured WAT edit operations, and explicit `END`. Host Python/JavaScript/shell orchestrates, compiles, and tests; it is never Jev-generated output.

## Prefix reconstruction

```sh
./jev-wasm --model jev-latest "PROGRAM SPEC"
```

This mode starts empty and selects ordered `;; JEV BLOCK:` sections from `library/*.wat`.

## Whole-program edit evolution

```sh
./jev-wasm-evolve --model jev-latest \
  --initial examples/sort-evolution/insertion_sort.wat \
  --target examples/sort-evolution/quicksort.wat \
  "transition insertion sort to quicksort while preserving sort(offset, length)"
```

At every iteration:

1. Give Jev the complete current WAT and complete reference target WAT.
2. Symbolically propose compiler-valid `insert`, `replace`, and `remove` operations over zero-based `;; JEV BLOCK:` positions, plus `END`.
3. Map operations to opaque `option_NNN` IDs.
4. Apply only the selected operation; never accept free-form model text.
5. Compile the complete intermediate WAT.
6. Continue until Jev selects `END` at an exact target match.
7. Trace operation kind, current position, delete count, inserted-block hashes, probabilities, model, and token usage.

The included demonstration begins with working insertion sort and reaches working quicksort through three inserts, one replacement, and one removal. Every intermediate program compiles. Because the target is supplied, classify the result as **reference-guided transformation**, not novel synthesis.

## Hard rules

- Jev-generated/selected source remains WAT only.
- Keep operation positions relative to the current block sequence; do not reuse stale positions after edits.
- Send full current and target programs on every edit decision.
- Keep opaque IDs and validate the returned probability map exactly.
- Reject premature `END`.
- Never silently repair selected WAT with host-generated source.
- Validate initial, target, every intermediate, and final WAT.
- Store credentials only in `JEV_API_KEY` or `TYPESAFE_API_KEY`; never source, prompts, traces, or commits.
- Run `make test && make audit` after any change.

Read `docs/WORKFLOW.md` for both protocols. Exact library reconstruction is retrieval/imitation; target-supplied editing is reference-guided transformation; neither is novel synthesis.
