FROM python:3.12-slim

ENV FLINT_CONTROL_PLANE_ENDPOINT=http://reverse-proxy

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy project files
COPY ../common-lib/flint ./common-lib/flint
COPY ./catalog-explorer ./catalog-explorer

WORKDIR /app/catalog-explorer

# Install dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-root

# Inject entrypoint
RUN mv ./entrypoint.sh /root/entrypoint.sh

ENTRYPOINT ["/root/entrypoint.sh"]