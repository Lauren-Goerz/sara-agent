#!/usr/bin/env bash
# Package models for upload to the VM (never packs .env into git).
# Usage (from repo root on your Mac):
#   bash scripts/deploy/package-release.sh
#   scp -r dist/sara-release/* ubuntu@VM_IP:~/sara-agent/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
OUT="$ROOT/dist/sara-release"
mkdir -p "$OUT/models"

LATEST="$(ls -t models/*.tar.gz | head -1)"
if [[ -z "$LATEST" ]]; then
  echo "No models/*.tar.gz — run: source .venv/bin/activate && rasa train"
  exit 1
fi

cp "$LATEST" "$OUT/models/"
# Keep last 2 models for rollback
ls -t models/*.tar.gz | sed -n '2,2p' | while read -r f; do
  [[ -n "$f" ]] && cp "$f" "$OUT/models/" || true
done

cat > "$OUT/UPLOAD.txt" <<EOF
Sara release package
====================
Model included: $(basename "$LATEST")

On the VM (after bootstrap created ~/sara-agent):
  1. Copy .env (secrets) — do this yourself, never via git:
       scp .env ubuntu@VM_IP:~/sara-agent/.env
  2. Copy models from this package:
       scp models/*.tar.gz ubuntu@VM_IP:~/sara-agent/models/
  3. Add CLOUDFLARE_TUNNEL_TOKEN to the VM .env
  4. Run:
       bash ~/sara-agent/scripts/deploy/bootstrap-vm.sh
EOF

echo "Packed $OUT"
echo "Latest model: $LATEST"
ls -lh "$OUT/models"
