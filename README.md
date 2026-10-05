# jev-wasm-component-generator

> **Give it a program spec. Jev assembles the WAT. The compiler gets the final vote.**

**3 decisions · 1,828 input tokens · $0.0000768 · valid WebAssembly**

This repository turns Jev into a tiny autonomous WebAssembly component builder. It starts from nothing, repeatedly chooses the next legal WAT block, decides when to stop, and ships the result only after exact compilation.

No free-form host code. No teacher forcing. No “looks valid” output. No fake novelty claims.

## Why this is interesting

Frontier coding models are powerful—but expensive and unconstrained. Jev costs **$0.042 per million input tokens**, returns typed probability distributions, and charges nothing for output. For bounded component families, that makes program construction a sequence of cheap, auditable decisions.

A measured live run reconstructed and compiled the checksum component with:

- **3** calls to `jev-1.13.0`
- **1,828** input tokens and **143** output tokens
- **$0.0000768** estimated Jev cost
- roughly **33×–166× cheaper** than the same token envelope on current Anthropic models

See **[the reproducible cost breakdown](docs/COSTS.md)** or run `make cost TRACE=generated/trace.json`.

## Sixty-second demo

```sh
git clone https://github.com/shibaeff/jev-wasm-component-generator.git
cd jev-wasm-component-generator
npm ci

export TYPESAFE_API_KEY='your-key'
./jev-wasm --model jev-latest \
  "Build a WebAssembly FNV-1a checksum component over exported linear memory"
```

Results:

```text
generated/component.wat   # exact compiled WAT
generated/trace.json      # every choice, probability, model and token count
```

No key yet? Run the deterministic local model:

```sh
./jev-wasm "integer clamp and greatest common divisor"
```

## Three ways to provide a specification

**Inline:**

```sh
./jev-wasm --model jev-latest "monthly subscription billing and due-date checks"
```

**File:**

```sh
./jev-wasm --model jev-latest \
  --spec-file examples/spec.txt \
  --output generated/component.wat \
  --trace generated/trace.json
```

**Standard input:**

```sh
printf '%s\n' 'integer clamp and greatest common divisor' |
  ./jev-wasm --model jev-latest --output generated/math.wat
```

The API key is read only from `JEV_API_KEY` or `TYPESAFE_API_KEY`. It is never written to source or traces.

## The loop

```text
program spec
    │
    ▼
empty WAT prefix
    │
    ▼
valid next WAT blocks ──► opaque option_NNN choices
    │                              │
    │                              ▼
    └────────────────────────── Jev ranking
                                   │
                         chosen block or END
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
              append WAT                  compile exact prefix
                    │                             │
                    └──────── repeat ─────────────┘
                                                  │
                                            verified .wat
```

1. Start with an empty prefix.
2. Propose only valid next `;; JEV BLOCK:` sections from the component library, plus explicit `END`.
3. Map actions to opaque `option_NNN` IDs.
4. Ask Jev using the specification and full current prefix.
5. Append only Jev’s selected WAT block—never a reference continuation.
6. Call Jev again for every block and the final `END`.
7. Reject premature `END` when the prefix is not an exact compiling component.
8. Atomically write WAT and a sanitized trace with token usage.

Host Python, JavaScript, and shell code orchestrate and validate. They are **never** represented as Jev-generated output.

## Included component library

- `subscription_core.wat` — recurring billing and due-date arithmetic
- `checksum.wat` — FNV-1a over exported linear memory
- `integer_math.wat` — signed clamp and unsigned GCD

Add a standalone `.wat` module, split it into ordered `;; JEV BLOCK:` sections, register it in `library/index.json`, and add behavioral tests.

## Agent skills included

One repository, three agent ecosystems:

- **Codex:** `.agents/skills/jev-wasm-component-generator/SKILL.md` + `AGENTS.md`
- **Claude Code:** `.claude/skills/jev-wasm-component-generator/SKILL.md` + `CLAUDE.md`
- **Hermes:** `.hermes/skills/jev-wasm-component-generator/SKILL.md`

Install all user-level copies:

```sh
./scripts/install-skills.sh
```

## Verification

```sh
make test
make audit
make cost TRACE=generated/trace.json
```

The test suite compiles every library module, executes its exports, checks autonomous multi-call decoding, proves that premature `END` cannot terminate invalid WAT, and audits secrets, machine paths, trace integrity, and language purity.

## The honest boundary

Today this is **autonomous retrieval/imitation over a finite WAT component library**. It does not invent arbitrary unseen algorithms. Exact reconstruction is not novel synthesis.

That boundary is the feature: the decisions are cheap, constrained, inspectable, and compiler-verified. The research path is to replace the finite continuation library with a type- and stack-valid symbolic proposer, then evaluate genuinely held-out programs.

Protocol: [docs/WORKFLOW.md](docs/WORKFLOW.md) · Costs: [docs/COSTS.md](docs/COSTS.md)
