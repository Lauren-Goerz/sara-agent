#!/usr/bin/env bash
# Print / verify vacation go-live checklist against a running host.
# Usage:
#   bash scripts/deploy/cutover-checklist.sh https://sara.example.com
set -euo pipefail

BASE="${1:-}"
if [[ -z "$BASE" ]]; then
  echo "Usage: $0 https://YOUR_PUBLIC_HOSTNAME"
  exit 1
fi
BASE="${BASE%/}"
WEBHOOK="$BASE/webhooks/slack/webhook"

echo "==> Public root"
code="$(curl -s -o /dev/null -w "%{http_code}" "$BASE/" || true)"
echo "GET $BASE/ → HTTP $code (any response from Sara/tunnel is progress)"

echo "==> Slack webhook endpoint (expect 400/405 without Slack signature, not 502/000)"
wcode="$(curl -s -o /dev/null -w "%{http_code}" -X POST "$WEBHOOK" || true)"
echo "POST $WEBHOOK → HTTP $wcode"

echo ""
echo "Manual Slack steps:"
echo "  1. api.slack.com/apps → your Sara app → Event Subscriptions"
echo "  2. Request URL = $WEBHOOK"
echo "  3. Save; challenge must verify (green)"
echo "  4. Quit local: stop rasa run + ngrok on your laptop"
echo "  5. Smoke: DM Sara 'code of conduct' and a #helpdesk test"
echo ""
echo "Vacation hardening:"
echo "  - docker compose -f docker-compose.prod.yml ps  (both sara + tunnel Up)"
echo "  - restart: unless-stopped already set"
echo "  - keep offline backup of .env"
echo "  - optional: uptime monitor on $BASE/"
