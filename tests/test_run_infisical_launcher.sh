#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

FAKE_AUDIT="$TMP_DIR/infisical-argv.log"
FAKE_INFISICAL="$TMP_DIR/infisical"
FAKE_CREDS="$TMP_DIR/infisical-machine.env"

cat >"$FAKE_INFISICAL" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$FAKE_AUDIT"

case "${1:-}" in
    login)
        : "${INFISICAL_UNIVERSAL_AUTH_CLIENT_ID:?missing auth client id}"
        : "${INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET:?missing auth client secret}"
        printf '%s' 'fake-access-token'
        ;;
    run)
        while [[ $# -gt 0 && "$1" != "--" ]]; do
            shift
        done
        [[ "${1:-}" == "--" ]]
        shift
        export TELEGRAM_BOT2_TOKEN='fake-bot2-token'
        export TELEGRAM_BOT2_NAME='@Claude_619IIBot'
        export TELEGRAM_USER_ID='123456789'
        export ANTHROPIC_API_KEY='fake-anthropic-key'
        exec "$@"
        ;;
    *)
        printf 'unexpected fake Infisical command: %s\n' "${1:-}" >&2
        exit 2
        ;;
esac
SH
chmod 700 "$FAKE_INFISICAL"

cat >"$FAKE_CREDS" <<'ENV'
export INFISICAL_CLIENT_ID='fake-client-id'
export INFISICAL_CLIENT_SECRET='fake-client-secret'
export INFISICAL_DOMAIN='http://infisical.test'
export INFISICAL_PROJECT_ID='fake-project-id'
ENV
chmod 600 "$FAKE_CREDS"

export FAKE_AUDIT
INFISICAL_BIN="$FAKE_INFISICAL" \
INFISICAL_CREDS_FILE="$FAKE_CREDS" \
BOT2_APPROVED_DIRECTORY="$TMP_DIR" \
bash "$ROOT_DIR/run-infisical.sh" bash -c '
    [[ "$TELEGRAM_BOT_TOKEN" == "fake-bot2-token" ]]
    [[ "$TELEGRAM_BOT_USERNAME" == "Claude_619IIBot" ]]
    [[ "$ALLOWED_USERS" == "[123456789]" ]]
    [[ "$APPROVED_DIRECTORY" == "'"$TMP_DIR"'" ]]
    [[ "$DATABASE_URL" == "sqlite:///data/bot.db" ]]
    [[ "$USE_SDK" == "true" ]]
    [[ "$ENVIRONMENT" == "production" ]]
    [[ "$DEVELOPMENT_MODE" == "false" ]]
    [[ "$DEBUG" == "false" ]]
    [[ -z "${TELEGRAM_BOT2_TOKEN:-}" ]]
    [[ -z "${INFISICAL_TOKEN:-}" ]]
    [[ -z "${INFISICAL_UNIVERSAL_AUTH_CLIENT_ID:-}" ]]
    [[ -z "${INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET:-}" ]]
'

if grep -Eq -- '--token|--client-id|--client-secret' "$FAKE_AUDIT"; then
    printf 'FAIL: credential-bearing Infisical flag appeared in argv.\n' >&2
    exit 1
fi

printf 'PASS: Bot 2 Infisical launcher maps vault names and keeps credentials out of argv.\n'
