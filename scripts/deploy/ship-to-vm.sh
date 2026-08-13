#!/usr/bin/env bash
# From your Mac: push code to GitHub is assumed done; this ships .env + models
# to an already-created Oracle Ubuntu VM and runs bootstrap.
#
# Usage:
#   export SARA_VM=ubuntu@130.61.x.x
#   export CLOUDFLARE_TUNNEL_TOKEN='eyJ...'   # optional if already in remote .env
#   bash scripts/deploy/ship-to-vm.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ -z "${SARA_VM:-}" ]]; then
  echo "Set SARA_VM=ubuntu@YOUR_ORACLE_PUBLIC_IP"
  echo "Create the Always Free Ampere VM first — see DEPLOY.md section 1."
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "Missing .env"
  exit 1
fi

bash scripts/deploy/package-release.sh

echo "==> Ensuring remote dir"
ssh "$SARA_VM" 'mkdir -p ~/sara-agent/models'

echo "==> Clone or update repo on VM"
ssh "$SARA_VM" 'bash -s' <<'REMOTE'
set -euo pipefail
if [[ -d ~/sara-agent/.git ]]; then
  git -C ~/sara-agent fetch --all --prune
  git -C ~/sara-agent checkout main
  git -C ~/sara-agent pull --ff-only origin main
else
  git clone https://github.com/RasaHQ/sara-agent.git ~/sara-agent
fi
REMOTE

echo "==> Copy .env and models (secrets over SSH only)"
scp .env "$SARA_VM:~/sara-agent/.env"
scp dist/sara-release/models/*.tar.gz "$SARA_VM:~/sara-agent/models/"

if [[ -n "${CLOUDFLARE_TUNNEL_TOKEN:-}" ]]; then
  ssh "$SARA_VM" "grep -q '^CLOUDFLARE_TUNNEL_TOKEN=' ~/sara-agent/.env \
    && sed -i.bak 's|^CLOUDFLARE_TUNNEL_TOKEN=.*|CLOUDFLARE_TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}|' ~/sara-agent/.env \
    || echo \"CLOUDFLARE_TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}\" >> ~/sara-agent/.env"
fi

echo "==> Bootstrap on VM"
ssh -t "$SARA_VM" 'bash ~/sara-agent/scripts/deploy/bootstrap-vm.sh'

echo "Done. Point Slack Event Subscriptions at:"
echo "  https://YOUR_TUNNEL_HOSTNAME/webhooks/slack/webhook"
echo "Then: bash scripts/deploy/cutover-checklist.sh https://YOUR_TUNNEL_HOSTNAME"
