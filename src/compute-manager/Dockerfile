FROM python:3.12-slim AS builder

WORKDIR /app

# Copy build context
COPY ./ ./

# Install Python dependencies
RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

FROM python:3.12-slim AS runtime

# install curl
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# install yq
RUN curl -L https://github.com/mikefarah/yq/releases/download/v4.35.1/yq_linux_amd64 \
     -o /usr/local/bin/yq && \
    chmod +x /usr/local/bin/yq

WORKDIR /app

# Inject dependencies
COPY --from=builder /usr/local/lib/python3.12/site-packages \
                    /usr/local/lib/python3.12/site-packages
COPY --from=builder /app /app

RUN mv /app/entrypoint.sh /root/entrypoint.sh
RUN chmod +x /root/entrypoint.sh
ENTRYPOINT ["/root/entrypoint.sh"]

HEALTHCHECK --interval=30s \
            --timeout=5s \
            --start-period=5s \
            --retries=3 \
 CMD curl --fail http://127.0.0.1:8000/health || exit 1