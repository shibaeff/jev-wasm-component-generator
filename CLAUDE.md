# Claude repository guidance

Follow `.claude/skills/jev-wasm-component-generator/SKILL.md` and `docs/WORKFLOW.md`.

Jev ranks only ordered `;; JEV BLOCK:` WebAssembly Text from `library/*.wat` plus explicit `END`; host-language orchestration is never Jev output. Preserve opaque choices, current-prefix scoring, no teacher forcing, the model-called final `END`, exact compilation, bounded decoding, and sanitized traces.

Run `make test && make audit`. Do not commit credentials, generated files, binaries, or machine paths. Call exact library reconstruction retrieval/imitation—not novel synthesis.
