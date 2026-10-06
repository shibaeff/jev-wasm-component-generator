# Jev WAT reconstruction protocol

## Hard invariant

Jev ranks or emits only ordered WebAssembly Text blocks from `library/*.wat`, plus the explicit `END` sentinel. Python, JavaScript, shell, JSON, agent instructions, credentials, and machine paths must never enter a model candidate as generated source.

## Autonomous loop

1. Read one specification from positional input, `--spec-file`, or stdin.
2. Start with an empty prefix.
3. For each demonstration whose prior blocks exactly equal the prefix, propose its next `;; JEV BLOCK:` section. Add `END` once.
4. Map actions to opaque `option_NNN` IDs and call the configured model with the spec and full current prefix.
5. Append only the model-selected WAT block. Never append a reference target after a prediction.
6. If the model selects an early `END`, compile the prefix. If compilation fails, record the rejection and advance with the highest-probability offered WAT block.
7. At a complete module, call the model once more with the one-option `END` choice. The live API supports this.
8. Accept only if the exact prefix compiles and byte-for-byte equals one library module.
9. Atomically write WAT and a sanitized trace containing hashes, opaque IDs, probabilities, model, and all effective decisions.

## Whole-program edit evolution

Use `jev-wasm-evolve` when the initial program already compiles and the goal is an auditable transition to a supplied reference program.

1. Segment both programs into zero-based `;; JEV BLOCK:` sequences.
2. Send the full current WAT and full target WAT to Jev at every iteration.
3. Derive closed candidates from block edit distance: `insert(position, block)`, `replace(position, delete_count=1, block)`, `remove(position, delete_count=1)`, and `END`.
4. Retain only edits whose complete resulting program compiles and whose distance does not increase. Neutral edits are allowed when needed to preserve compilation while introducing dependencies.
5. Map candidates to opaque `option_NNN` IDs. Jev never returns source or an unbounded patch.
6. Apply only the selected edit using positions in the current program. Recompute all positions after every mutation.
7. Reject `END` until the current block sequence exactly equals the target.
8. Trace operation kind, position, delete count, inserted-block hashes, full-state hashes, probability distribution, model, and token usage.
9. Compile initial, target, every intermediate, and final WAT. Never repair a selected edit afterward.

The sort example deliberately exercises all three edit kinds: three inserts add `$swap`, `$partition`, and `$quicksort`; one replacement switches the exported wrapper; one removal deletes the obsolete insertion-sort helper.

Because the full target is supplied, label this mode **reference-guided transformation**, not novel synthesis and not target-free autonomous synthesis.

## Adding a component

- Create a standalone `.wat` module in `library/`.
- Start every ordered block with `;; JEV BLOCK: <name>`; use at least two blocks.
- Add `name`, `file`, and `description` to `library/index.json`.
- Add export-level behavior tests in `tests/modules.test.js`.
- Run `make test && make audit`.

## Failure rules

- Unknown/missing option IDs, malformed probability maps, duplicate source, premature non-compiling `END` with no continuation, loop exhaustion, non-exact completion, compilation failure, host-language candidate source, a secret-like token, or a machine-specific path is a hard failure.
- Never repair model output with host-generated WAT after the decision loop.
- Never claim novelty for exact or near-exact library reconstruction. Report it as retrieval/imitation. Reserve “synthesis” for held-out tasks where the target program is absent and independently verified.
