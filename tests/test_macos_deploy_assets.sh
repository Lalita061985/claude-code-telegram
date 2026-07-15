#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST="$ROOT_DIR/deploy/com.lifeos.claude-code-telegram.plist"
BOOTSTRAP="$ROOT_DIR/deploy/bootstrap-macos.sh"

/usr/bin/plutil -lint "$PLIST" >/dev/null
bash -n "$BOOTSTRAP"

if grep -Eqi 'token|secret|api[_-]?key|client[_-]?id' "$PLIST"; then
    printf 'FAIL: LaunchAgent must not contain credential names or values.\n' >&2
    exit 1
fi

if grep -Eq -- '--token|--client-id|--client-secret' "$BOOTSTRAP"; then
    printf 'FAIL: Bootstrap must not pass credentials in process arguments.\n' >&2
    exit 1
fi

grep -Fq '/Users/LPS/services/claude-code-telegram/run-infisical.sh' "$PLIST"
grep -Fq '/Users/LPS/Library/Logs/claude-code-telegram' "$PLIST"

printf 'PASS: Mac Mini deployment assets are valid and secret-free.\n'
