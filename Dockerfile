# Default: public Rasa Pro image. Maestro beta (calm_v2 / 3.19.dev1) may need
# a private image from Rasa instead — set build arg RASA_IMAGE accordingly.
ARG RASA_IMAGE=rasa/rasa-pro:3.18.1
FROM ${RASA_IMAGE}

USER root

# Slack connector + SVG-to-PNG rendering for Phosphor icon delivery.
RUN pip install --no-cache-dir "slack-sdk>=3.27.0" "resvg_py>=0.3.4"

# Project code is bind-mounted at runtime; keep /app as the workdir.
WORKDIR /app
ENV PYTHONPATH=/app

# Drop back to the image's default non-root user when present.
USER 1001

EXPOSE 5005

CMD ["rasa", "run", "--enable-api", "--cors", "*", "-p", "5005"]
