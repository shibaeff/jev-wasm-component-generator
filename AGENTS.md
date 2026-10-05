# Repository guidance

Use `.agents/skills/jev-wasm-component-generator/SKILL.md` for generator or library work.

Hard invariant: Jev may rank only ordered `;; JEV BLOCK:` WebAssembly Text from `library/*.wat` and explicit `END`. Host code orchestrates and validates; it is never Jev output. Preserve opaque IDs, full-prefix model calls, no teacher forcing, model-selected final `END`, exact-library matching, compile-before-write, bounded decoding, and sanitized traces.

Run `make test && make audit`. Never commit credentials, generated outputs, binaries, or machine paths. Describe exact reconstruction as retrieval/imitation, not novel synthesis.
