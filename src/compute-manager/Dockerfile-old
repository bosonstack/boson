FROM python:3.12-slim

WORKDIR /app

# Install system packages: curl, ping (iputils-ping), ssh client
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        iputils-ping \
        openssh-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY ./ ./

RUN chmod +x entrypoint.sh

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root

ENTRYPOINT ["/app/entrypoint.sh"]

HEALTHCHECK --interval=30s \
            --timeout=5s \
            --start-period=5s \
            --retries=3 \
  CMD curl --fail http://127.0.0.1:8000/health || exit 1