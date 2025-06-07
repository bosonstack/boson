FROM python:3.12-slim

# Set workdir
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