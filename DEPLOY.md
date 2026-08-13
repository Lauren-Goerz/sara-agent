# Deploy Sara always-on (free path)

Git is already on `main`. This runbook gets Sara off your laptop onto an
**Oracle Cloud Always Free Ampere** VM with a **Cloudflare Tunnel** so Slack
keeps working while you are on vacation.

## Architecture

Slack → `https://YOUR_HOST/webhooks/slack/webhook` → Cloudflare Tunnel →
`127.0.0.1:5005` (Sara in Docker)

## 1. Create the free Oracle VM (you — one-time)

1. Sign up / log in: https://cloud.oracle.com  
   Choose **Always Free** eligible region if prompted.
2. **Compute → Instances → Create instance**
   - Name: `sara-agent`
   - Image: **Ubuntu 22.04 or 24.04**
   - Shape: **VM.Standard.A1.Flex** (Ampere) — Always Free eligible  
     Start with 2 OCPU / 12 GB RAM (or up to 4 / 24 within free limits)
   - Networking: assign a public IP (for SSH only; Slack traffic uses the tunnel)
   - SSH keys: paste your public key (`~/.ssh/id_*.pub`)
3. Create the instance. Note the **public IP**.
4. SSH in:

```bash
ssh ubuntu@VM_PUBLIC_IP
```

Open ingress **SSH (22)** in the VCN security list / NSG. You do **not** need
to open port 5005 publicly (Cloudflare Tunnel handles HTTPS).

## 2. From your Mac — ship secrets + model

```bash
cd /Users/laurengoerz/Documents/Agents/maestro-agent
source .venv/bin/activate && rasa train   # if models are stale
bash scripts/deploy/package-release.sh

# Secrets (never commit)
scp .env ubuntu@VM_PUBLIC_IP:~/sara-agent.env

# After bootstrap clones the repo, or scp into place:
ssh ubuntu@VM_PUBLIC_IP 'mkdir -p ~/sara-agent/models'
scp dist/sara-release/models/*.tar.gz ubuntu@VM_PUBLIC_IP:~/sara-agent/models/
```

## 3. Cloudflare named tunnel (you — one-time, free)

1. https://one.dash.cloudflare.com → **Networks → Tunnels → Create tunnel**
2. Name: `sara-agent`
3. Install guide will show a token — copy it.
4. **Public Hostname**
   - Subdomain + domain you control (or a Cloudflare-managed zone)
   - Service type: HTTP  
   - URL: `http://127.0.0.1:5005`
5. Save.

## 4. On the VM — bootstrap

```bash
ssh ubuntu@VM_PUBLIC_IP
git clone https://github.com/RasaHQ/sara-agent.git ~/sara-agent
mv ~/sara-agent.env ~/sara-agent/.env
# ensure models are in ~/sara-agent/models/

# Add to .env:
# CLOUDFLARE_TUNNEL_TOKEN=eyJ...

bash ~/sara-agent/scripts/deploy/bootstrap-vm.sh
```

## 5. Slack cutover

1. https://api.slack.com/apps → Sara → **Event Subscriptions**
2. Request URL:

```text
https://YOUR_PUBLIC_HOSTNAME/webhooks/slack/webhook
```

3. Verify (green check).
4. On your Mac: stop `rasa run` and **ngrok** so only the VM answers.
5. Smoke-test: DM Sara; try a policy question; optional `#helpdesk` ping.

```bash
bash scripts/deploy/cutover-checklist.sh https://YOUR_PUBLIC_HOSTNAME
```

## 6. Vacation hardening

- `restart: unless-stopped` is set for `sara` and `tunnel`
- Reboot the VM once and confirm both containers return:  
  `docker compose -f docker-compose.prod.yml --profile tunnel ps`
- Keep an offline backup of `.env`
- Optional: free uptime ping on `https://YOUR_PUBLIC_HOSTNAME/`

## Fallback

If Oracle signup fails, use **Fly.io** with the same `Dockerfile` and secrets;
avoid Render-style free tiers that sleep (Slack will miss events).

## Files

| File | Purpose |
|---|---|
| [docker-compose.prod.yml](docker-compose.prod.yml) | Sara + cloudflared on the VM |
| [scripts/deploy/bootstrap-vm.sh](scripts/deploy/bootstrap-vm.sh) | Install Docker, pull, `compose up` |
| [scripts/deploy/package-release.sh](scripts/deploy/package-release.sh) | Pack latest model for `scp` |
| [scripts/deploy/cutover-checklist.sh](scripts/deploy/cutover-checklist.sh) | Webhook + cutover checks |
