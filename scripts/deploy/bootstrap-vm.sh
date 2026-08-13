#!/usr/bin/env bash
# Bootstrap Sara on a fresh Ubuntu VM (Oracle Always Free Ampere / similar).
# Run as a user with sudo, from an empty home or /opt:
#   curl -fsSL ... | bash   OR
#   git clone ... && cd sara-agent && bash scripts/deploy/bootstrap-vm.sh
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/RasaHQ/sara-agent.git}"
APP_DIR="${APP_DIR:-$HOME/sara-agent}"

echo "==> Installing Docker (if needed)"
if ! command -v docker >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y ca-certificates curl gnupg git
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  sudo usermod -aG docker "$USER" || true
fi

echo "==> Cloning / updating repo at $APP_DIR"
if [[ -d "$APP_DIR/.git" ]]; then
  git -C "$APP_DIR" fetch --all --prune
  git -C "$APP_DIR" checkout main
  git -C "$APP_DIR" pull --ff-only origin main
else
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

if [[ ! -f .env ]]; then
  echo "ERROR: Missing $APP_DIR/.env"
  echo "Copy your Mac .env here first, e.g.:"
  echo "  scp .env ubuntu@VM_IP:~/sara-agent/.env"
  exit 1
fi

# Ensure Cloudflare token placeholder is documented
if ! grep -q '^CLOUDFLARE_TUNNEL_TOKEN=' .env 2>/dev/null; then
  echo "" >> .env
  echo "# Cloudflare named tunnel token (Zero Trust → Networks → Tunnels)" >> .env
  echo "CLOUDFLARE_TUNNEL_TOKEN=" >> .env
fi

if [[ ! -d models ]] || [[ -z "$(ls -A models/*.tar.gz 2>/dev/null || true)" ]]; then
  echo "ERROR: No trained models in $APP_DIR/models/"
  echo "From your Mac (after rasa train):"
  echo "  scp models/2026*.tar.gz ubuntu@VM_IP:~/sara-agent/models/"
  exit 1
fi

if ! grep -qE '^CLOUDFLARE_TUNNEL_TOKEN=.+' .env; then
  echo "WARN: CLOUDFLARE_TUNNEL_TOKEN is empty."
  echo "Create a Cloudflare Tunnel that routes HTTPS → http://sara:5005"
  echo "Paste the token into .env, then re-run this script."
fi

ARCH="$(uname -m)"
COMPOSE_FILE=docker-compose.prod.yml
if [[ "$ARCH" == "x86_64" ]] || [[ "$ARCH" == "amd64" ]]; then
  # Override platform for AMD shapes if you used an AMD micro instead of Ampere
  export COMPOSE_PLATFORM_OVERRIDE=linux/amd64
  sed -i.bak 's/platform: linux\/arm64/platform: linux\/amd64/' "$COMPOSE_FILE" || true
fi

echo "==> Building and starting Sara + Cloudflare Tunnel"
# New shell group may be required for docker without sudo:
if docker info >/dev/null 2>&1; then
  DOCKER=(docker)
else
  DOCKER=(sudo docker)
fi

if ! grep -qE '^CLOUDFLARE_TUNNEL_TOKEN=.+' .env; then
  echo "ERROR: CLOUDFLARE_TUNNEL_TOKEN missing in .env — cannot start tunnel profile."
  exit 1
fi

"${DOCKER[@]}" compose -f "$COMPOSE_FILE" --profile tunnel up -d --build

echo "==> Waiting for health"
for i in $(seq 1 40); do
  if curl -sf http://127.0.0.1:5005/ >/dev/null 2>&1; then
    echo "Sara is up on :5005"
    "${DOCKER[@]}" compose -f "$COMPOSE_FILE" --profile tunnel ps
    echo ""
    echo "Next: set Slack Event Subscriptions Request URL to:"
    echo "  https://YOUR_TUNNEL_HOSTNAME/webhooks/slack/webhook"
    echo "Then stop local rasa run + ngrok on your laptop."
    exit 0
  fi
  sleep 3
done

echo "Sara did not become healthy in time. Logs:"
"${DOCKER[@]}" compose -f "$COMPOSE_FILE" --profile tunnel logs --tail=80 sara
exit 1
