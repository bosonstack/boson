FROM python:3.12-slim AS builder

WORKDIR /app

# Copy build context
COPY ../common-lib/flint ./common-lib/flint
COPY ./catalog-explorer ./catalog-explorer

WORKDIR /app/catalog-explorer

# Install Python dependencies
RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

FROM python:3.12-slim AS runtime

ENV FLINT_CONTROL_PLANE_ENDPOINT=http://reverse-proxy
WORKDIR /app

# Inject dependencies
COPY --from=builder /usr/local/lib/python3.12/site-packages \
                    /usr/local/lib/python3.12/site-packages
COPY --from=builder /app/catalog-explorer /app

RUN mv /app/entrypoint.sh /root/entrypoint.sh
RUN chmod +x /root/entrypoint.sh
ENTRYPOINT ["/root/entrypoint.sh"]