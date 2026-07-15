#!/usr/bin/env bash
set -euo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

INFISICAL_CREDS_FILE="${INFISICAL_CREDS_FILE:-$HOME/.config/lifeos/infisical-machine.env}"
if [[ ! -r "$INFISICAL_CREDS_FILE" ]]; then
    printf 'ERROR: Infisical credentials file is missing or unreadable: %s\n' "$INFISICAL_CREDS_FILE" >&2
    exit 1
fi

# shellcheck source=/dev/null
source "$INFISICAL_CREDS_FILE"
: "${INFISICAL_CLIENT_ID:?INFISICAL_CLIENT_ID is required}"
: "${INFISICAL_CLIENT_SECRET:?INFISICAL_CLIENT_SECRET is required}"
: "${INFISICAL_DOMAIN:?INFISICAL_DOMAIN is required}"
: "${INFISICAL_PROJECT_ID:?INFISICAL_PROJECT_ID is required}"

INFISICAL_BIN="${INFISICAL_BIN:-$(command -v infisical || true)}"
if [[ -z "$INFISICAL_BIN" || ! -x "$INFISICAL_BIN" ]]; then
    printf 'ERROR: Infisical CLI not found. Set INFISICAL_BIN or install the CLI.\n' >&2
    exit 1
fi

AUTH_DOMAIN="${INFISICAL_DOMAIN%/api}"
API_DOMAIN="${AUTH_DOMAIN}/api"

if [[ $# -gt 0 ]]; then
    bot_command=("$@")
elif [[ -x "$SCRIPT_DIR/.venv/bin/claude-telegram-bot" ]]; then
    bot_command=("$SCRIPT_DIR/.venv/bin/claude-telegram-bot")
elif command -v poetry >/dev/null 2>&1; then
    bot_command=(poetry run claude-telegram-bot)
else
    printf 'ERROR: Bot runtime not found. Create .venv or install Poetry dependencies.\n' >&2
    exit 1
fi

INFISICAL_TOKEN="$({
    INFISICAL_UNIVERSAL_AUTH_CLIENT_ID="$INFISICAL_CLIENT_ID" \
    INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET="$INFISICAL_CLIENT_SECRET" \
    "$INFISICAL_BIN" login \
        --method=universal-auth \
        --domain="$AUTH_DOMAIN" \
        --silent \
        --plain
} 2>/dev/null)"

if [[ -z "$INFISICAL_TOKEN" ]]; then
    printf 'ERROR: Infisical universal-auth login returned no access token.\n' >&2
    exit 1
fi

export INFISICAL_TOKEN
unset INFISICAL_CLIENT_ID INFISICAL_CLIENT_SECRET

exec "$INFISICAL_BIN" run \
    --domain "$API_DOMAIN" \
    --projectId "$INFISICAL_PROJECT_ID" \
    --env "${INFISICAL_ENV:-prod}" \
    -- bash -c '
        set -euo pipefail
        : "${TELEGRAM_BOT2_TOKEN:?TELEGRAM_BOT2_TOKEN is missing from Infisical}"
        : "${TELEGRAM_BOT2_NAME:?TELEGRAM_BOT2_NAME is missing from Infisical}"
        : "${TELEGRAM_USER_ID:?TELEGRAM_USER_ID is missing from Infisical}"

        export TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT2_TOKEN"
        export TELEGRAM_BOT_USERNAME="${TELEGRAM_BOT2_NAME#@}"
        export ALLOWED_USERS="$TELEGRAM_USER_ID"
        export APPROVED_DIRECTORY="${BOT2_APPROVED_DIRECTORY:-${APPROVED_DIRECTORY:-/Users/LPS/META_Projects}}"
        export DATABASE_URL="${BOT2_DATABASE_URL:-${DATABASE_URL:-sqlite:///data/bot.db}}"
        export USE_SDK="${BOT2_USE_SDK:-true}"
        export DEVELOPMENT_MODE="${BOT2_DEVELOPMENT_MODE:-false}"
        export DEBUG="${BOT2_DEBUG:-false}"

        unset TELEGRAM_BOT2_TOKEN TELEGRAM_BOT2_NAME TELEGRAM_USER_ID
        unset INFISICAL_TOKEN \
            INFISICAL_UNIVERSAL_AUTH_ACCESS_TOKEN \
            INFISICAL_UNIVERSAL_AUTH_CLIENT_ID \
            INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET

        exec "$@"
    ' bash "${bot_command[@]}"
