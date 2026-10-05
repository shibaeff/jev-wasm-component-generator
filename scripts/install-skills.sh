#!/bin/sh
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
install_one() {
  source_file=$1
  target_dir=$2
  mkdir -p "$target_dir"
  cp "$source_file" "$target_dir/SKILL.md"
  printf 'Installed %s\n' "$target_dir/SKILL.md"
}

install_one "$repo_dir/.agents/skills/jev-wasm-component-generator/SKILL.md" \
  "${CODEX_HOME:-$HOME/.codex}/skills/jev-wasm-component-generator"
install_one "$repo_dir/.claude/skills/jev-wasm-component-generator/SKILL.md" \
  "${CLAUDE_HOME:-$HOME/.claude}/skills/jev-wasm-component-generator"
install_one "$repo_dir/.hermes/skills/jev-wasm-component-generator/SKILL.md" \
  "${HERMES_HOME:-$HOME/.hermes}/skills/jev-wasm-component-generator"
