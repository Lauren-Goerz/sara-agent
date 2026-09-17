# syntax=docker/dockerfile:1.7
# Sara — Rasa Ops/HR agent (Rasa Mantle)
#
# Builds bake the trained model into the image, which the Kubernetes deployment
# REQUIRES (see the training step near the bottom for why). The secret ids below
# are the ones .github/workflows/rasa-pro.yaml already passes via the shared
# RasaHQ/infrasec-workflows build — do not rename them.
#
#   RASA_PRO_LICENSE=... OPENAI_API_KEY=... \
#     docker build --secret id=RASA_PRO_LICENSE --secret id=OPENAI_API_KEY -t sara-agent .
#
# Local build with no license to hand — ships WITHOUT a model, so the entrypoint
# trains on first container start. Never push this variant to ECR:
#
#   docker build --build-arg SKIP_TRAINING=true -t sara-agent .
#   docker run --rm -p 5005:5005 --env-file .env -v sara-models:/app/models sara-agent

# ---------- builder ----------
# Dependencies are installed into a venv here so the runtime image carries no
# compilers or pip build leftovers — just the venv, copied across.
FROM python:3.11-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Wheels cover every pinned dependency on amd64/arm64; build-essential is kept
# only so a transitive sdist cannot break the build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# rasa-pro resolves from public PyPI. To use Rasa's index instead, pass
# --build-arg PIP_INDEX_ARGS="--extra-index-url https://<token>@pypi.rasa.com/simple".
ARG PIP_INDEX_ARGS=""

COPY requirements.txt ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip setuptools wheel \
    && /opt/venv/bin/pip install ${PIP_INDEX_ARGS} -r requirements.txt

# ---------- runtime ----------
FROM python:3.11-slim-bookworm AS runtime

# The Helm values (argocd/rasa-pro/values.yaml) run this container with
# readOnlyRootFilesystem: true and only two writable mounts, /tmp and
# /app/.rasa — so every cache Rasa and its deps touch has to land in /tmp.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/opt/venv/bin:$PATH \
    HOME=/tmp \
    XDG_CACHE_HOME=/tmp/.cache \
    XDG_CONFIG_HOME=/tmp/.config \
    MPLCONFIGDIR=/tmp/.cache/matplotlib

# ca-certificates: outbound TLS to Notion/Slack/OpenAI/Deepgram/Giphy/Spotify.
# tzdata + fonts: zoneinfo lookups (lib/user_location.py) and SVG icon rendering.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        tzdata \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

# UID/GID 1001 matches podSecurityContext.runAsUser in the Helm values.
RUN groupadd --gid 1001 sara \
    && useradd --uid 1001 --gid 1001 --no-create-home --home-dir /app --shell /bin/bash sara

WORKDIR /app

# Project sources. .dockerignore keeps .env, .git, and models/ out.
COPY --chown=sara:sara agent.yml integrations.yml memory.yml ./
COPY --chown=sara:sara lib/ ./lib/
COPY --chown=sara:sara tools/ ./tools/
COPY --chown=sara:sara skills/ ./skills/
COPY --chown=sara:sara scripts/ ./scripts/
COPY --chown=sara:sara eval/ ./eval/
COPY --chown=sara:sara README.md SKILLS.md ./
COPY --chown=sara:sara docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && mkdir -p /app/models \
    && chown -R sara:sara /app

# Bake the model in. The Kubernetes deployment cannot train at runtime: it
# overrides the image ENTRYPOINT (command: [rasa] in the Helm values), mounts no
# models volume (mountModelsVolume: false), and mounts the root filesystem
# read-only — so `rasa run` there can only use a model already in the image.
# Mantle training is offline packaging + validation, so a license is all it needs.
#
# SKIP_TRAINING is referenced in the RUN on purpose: BuildKit leaves secret
# CONTENT out of the layer cache key, so without an arg that changes, a cached
# model-less layer would be reused even once a license is supplied — and the
# image would fail at runtime with exactly the ModelNotFound this is here to
# prevent. Pass --build-arg MODEL_REVISION=$(git rev-parse HEAD) to force a
# retrain when only the license changed.
ARG SKIP_TRAINING=false
ARG MODEL_REVISION=dev

USER sara
RUN --mount=type=secret,id=RASA_PRO_LICENSE,uid=1001 \
    --mount=type=secret,id=OPENAI_API_KEY,uid=1001 \
    if [ "${SKIP_TRAINING}" = "true" ]; then \
        echo "SKIP_TRAINING=true (revision ${MODEL_REVISION}) — image ships WITHOUT a model."; \
        echo "Fine locally: the entrypoint trains on first start. NOT deployable to Kubernetes."; \
    elif [ ! -s /run/secrets/RASA_PRO_LICENSE ]; then \
        echo "ERROR: no RASA_PRO_LICENSE build secret, so no model can be trained." >&2; \
        echo "       Deploy builds must pass --secret id=RASA_PRO_LICENSE." >&2; \
        echo "       For a local model-less image: --build-arg SKIP_TRAINING=true" >&2; \
        exit 1; \
    else \
        export RASA_LICENSE="$(cat /run/secrets/RASA_PRO_LICENSE)"; \
        if [ -s /run/secrets/OPENAI_API_KEY ]; then \
            export OPENAI_API_KEY="$(cat /run/secrets/OPENAI_API_KEY)"; \
        fi; \
        rasa train --fixed-model-name sara; \
        test -s /app/models/sara.tar.gz \
            || { echo "ERROR: rasa train left no model in /app/models." >&2; exit 1; }; \
    fi

EXPOSE 5005

# Slack and the REST channel both hang off this server.
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:5005/', timeout=4).status == 200 else 1)"

# Kubernetes replaces both of these via command:/args: in the Helm values;
# they are here for local runs.
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["rasa", "run", "--interface", "0.0.0.0", "--port", "5005"]
