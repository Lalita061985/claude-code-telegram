#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BREW_BIN="${BREW_BIN:-/opt/homebrew/bin/brew}"
NPM_BIN="${NPM_BIN:-/opt/homebrew/bin/npm}"

if [[ ! -x "$BREW_BIN" ]]; then
    printf 'ERROR: Homebrew is required at %s\n' "$BREW_BIN" >&2
    exit 1
fi

if ! "$BREW_BIN" list --versions python@3.12 >/dev/null 2>&1; then
    "$BREW_BIN" install python@3.12
fi

if ! "$BREW_BIN" list --versions poetry >/dev/null 2>&1; then
    "$BREW_BIN" install poetry
fi

if [[ ! -x /opt/homebrew/bin/claude ]]; then
    if [[ ! -x "$NPM_BIN" ]]; then
        printf 'ERROR: npm is required at %s\n' "$NPM_BIN" >&2
        exit 1
    fi
    "$NPM_BIN" install --global @anthropic-ai/claude-code
fi

cd "$ROOT_DIR"
POETRY_VIRTUALENVS_IN_PROJECT=true \
    /opt/homebrew/bin/poetry env use /opt/homebrew/bin/python3.12
POETRY_VIRTUALENVS_IN_PROJECT=true \
    /opt/homebrew/bin/poetry install --only main --sync --no-interaction

if [[ ! -x "$ROOT_DIR/.venv/bin/claude-telegram-bot" ]]; then
    printf 'ERROR: Bot entry point was not installed into .venv.\n' >&2
    exit 1
fi

"$ROOT_DIR/.venv/bin/python" -m compileall -q "$ROOT_DIR/src"
printf 'PASS: Mac Mini runtime is installed in %s/.venv.\n' "$ROOT_DIR"
