#!/usr/bin/env bash
# Vacation hardening checks for a live Sara host.
# Usage:
#   export SARA_VM=ubuntu@IP
#   export SARA_PUBLIC_URL=https://sara.example.com
#   bash scripts/deploy/vacation-hardening.sh
set -euo pipefail

if [[ -z "${SARA_VM:-}" || -z "${SARA_PUBLIC_URL:-}" ]]; then
  echo "Set SARA_VM=ubuntu@IP and SARA_PUBLIC_URL=https://hostname"
  exit 1
fi

BASE="${SARA_PUBLIC_URL%/}"

echo "==> Remote compose status"
ssh "$SARA_VM" 'cd ~/sara-agent && docker compose -f docker-compose.prod.yml --profile tunnel ps'

echo "==> Restart policy"
ssh "$SARA_VM" 'docker inspect sara-agent sara-tunnel --format "{{.Name}} restart={{.HostConfig.RestartPolicy.Name}}" 2>/dev/null || true'

echo "==> Public checks"
bash "$(cd "$(dirname "$0")" && pwd)/cutover-checklist.sh" "$BASE"

echo "==> Offline .env backup reminder"
echo "Confirm you have a copy of .env outside the VM (1Password / encrypted drive)."
echo "If the Always Free VM is reclaimed, you will need it to redeploy."

echo "==> Optional reboot test (skipped unless SARA_REBOOT_TEST=1)"
if [[ "${SARA_REBOOT_TEST:-}" == "1" ]]; then
  ssh "$SARA_VM" 'sudo reboot' || true
  echo "Waiting 90s for reboot..."
  sleep 90
  for i in $(seq 1 30); do
    if ssh -o ConnectTimeout=5 "$SARA_VM" 'curl -sf http://127.0.0.1:5005/ >/dev/null'; then
      echo "Sara returned after reboot"
      exit 0
    fi
    sleep 5
  done
  echo "Sara did not return after reboot"
  exit 1
fi

echo "Hardening checks finished."
