#!/usr/bin/env bash

set -euo pipefail

BASE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || exit 1
APP_MODE="${1:-run}"
APP_FILE="src/pi_lights"

case "$APP_MODE" in
    dev)
	ARGS=(--host 0.0.0.0 --reload)
	;;
    run)
	ARGS=()
	;;
    *)
	echo "Usage: $0 [dev|run]" >&2
	exit 2
esac


echo "Changing directory to $BASE_DIR"
cd -- "$BASE_DIR"

exec uv run fastapi "$APP_MODE" "${ARGS[@]}" "$APP_FILE"
