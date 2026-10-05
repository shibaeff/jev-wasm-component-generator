# jev-wasm-component-generator

A reusable Jev workflow that reconstructs **only WebAssembly Text (WAT)** from a local component library. A human supplies a program specification; Jev repeatedly ranks the valid next WAT blocks or `END`, starting from an empty prefix. The exact result must compile before it is written.

> Scientific claim boundary: the shipped workflow performs autonomous closed-candidate retrieval/imitation. Exact reconstruction of a library component is not novel program synthesis.

## Quick start

```sh
npm ci

# Deterministic offline smoke test
./jev-wasm "FNV-1a checksum over bytes"

# Live Jev
export TYPESAFE_API_KEY='your-key'
./jev-wasm --model jev-latest "monthly subscription billing and due-date checks"

# Specification file
./jev-wasm --model jev-latest --spec-file examples/spec.txt \
  --output generated/component.wat --trace generated/trace.json

# Standard input
printf '%s\n' 'integer clamp and greatest common divisor' | \
  ./jev-wasm --model jev-latest --output generated/math.wat
```

`--output` defaults to `generated/component.wat`; `--trace` defaults to `generated/trace.json`. Inline text, `--spec-file`, and stdin are mutually exclusive. The key is read only from `JEV_API_KEY` or `TYPESAFE_API_KEY`; it is never written to traces.

## What the loop does

1. Starts with an empty WAT prefix.
2. Finds valid next blocks from `library/*.wat` whose preceding blocks exactly match the prefix.
3. Sends the program spec, current prefix, and opaque `option_NNN` choices to Jev.
4. Appends only the chosen WAT block. No reference/teacher continuation is injected.
5. Repeats until Jev chooses explicit `END`.
6. Accepts `END` only if the exact prefix compiles and exactly matches a library component.
7. Writes the WAT and a sanitized JSON probability trace atomically.

Every model-facing source candidate is either a WAT block beginning with `;; JEV BLOCK:` or the `END` sentinel. Host Python, JavaScript, and shell code only orchestrate and validate; they are never presented as Jev-generated output.

## Included component demonstrations

- `subscription_core.wat` — recurring billing and due-date arithmetic
- `checksum.wat` — FNV-1a over exported linear memory
- `integer_math.wat` — signed clamp and unsigned GCD

Add a self-contained `.wat` module to `library/`, divide it into ordered `;; JEV BLOCK:` sections, add its manifest entry, and add behavior tests. The current system can reconstruct only paths represented in this finite library; arbitrary unseen algorithms require extending the proposer/library.

## Agent packages

- Codex: `.agents/skills/jev-wasm-component-generator/SKILL.md` + `AGENTS.md`
- Claude Code: `.claude/skills/jev-wasm-component-generator/SKILL.md` + `CLAUDE.md`
- Hermes: `.hermes/skills/jev-wasm-component-generator/SKILL.md`

Install all three user-level copies:

```sh
./scripts/install-skills.sh
```

## Verification

```sh
make test       # Python loop/CLI tests + compiled Wasm behavior tests
make audit      # WAT purity, compilation, traces, secrets, machine paths
```

CI runs only deterministic offline checks and needs no API key. See [docs/WORKFLOW.md](docs/WORKFLOW.md) for the protocol and failure rules.
