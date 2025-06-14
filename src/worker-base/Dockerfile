FROM python:3.12-slim

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    curl \
    nano \
    procps \
    net-tools \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Copy build context
WORKDIR /app
COPY ../common-lib/flint ./common-lib/flint
COPY ./worker-base ./worker-base
WORKDIR /app/worker-base

# Install Poetry
RUN pip install --no-cache-dir poetry

# Install Python dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-root

# Copy startup scripts
COPY ./worker-base/startup/watchdog.py /root/watchdog.py

RUN mkdir -p /root/.ipython/profile_default/startup
COPY ./worker-base/startup/00-flint-init.py /root/.ipython/profile_default/startup/00-flint-init.py