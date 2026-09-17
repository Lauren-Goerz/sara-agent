#!/usr/bin/env bash
# Trains a model on first boot (models/ is a volume, so this happens once),
# then hands off to CMD — usually `rasa run`.
set -euo pipefail

if [ -z "${RASA_LICENSE:-}" ]; then
  echo "docker-entrypoint: RASA_LICENSE is not set — pass --env-file .env" >&2
  exit 1
fi

# Only auto-train for the server command; `rasa train`, `rasa shell`,
# `python scripts/check_notion_access.py` etc. are run as-is.
case "${1:-}" in
  rasa)
    if [ "${2:-}" = "run" ] && [ "${SARA_SKIP_TRAIN:-}" != "1" ]; then
      if ! compgen -G "/app/models/*.tar.gz" > /dev/null; then
        echo "docker-entrypoint: no model in /app/models — running rasa train"
        rasa train
      fi
    fi
    ;;
esac

exec "$@"
