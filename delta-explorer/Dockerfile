FROM python:3.12-slim

# Set workdir
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy project files
COPY . .

# Install dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-root