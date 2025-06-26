FROM python:3.12-slim AS builder

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    curl \
    nano \
    procps \
    net-tools && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy build context
COPY ../common-lib/flint ./common-lib/flint
COPY ./workspace ./workspace

WORKDIR /app/workspace

# Install Python dependencies
RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Build and install Jupyter Lab extensions
ARG EXTENSION_BACKENDS="backend/jupyter-lab-ext/experiment-tracker \
                        backend/jupyter-lab-ext/catalog-explorer \
                        backend/jupyter-lab-ext/theme"
RUN for ext in $EXTENSION_BACKENDS; do \
      mv "./$ext" "/tmp/$(basename $ext)" && \
      cd "/tmp/$(basename $ext)" && \
      npm install && npm run build && \
      TARBALL=$(npm pack --silent) && \
      jupyter labextension install $TARBALL --no-build && \
      jupyter labextension install . && \
      rm -rf "/tmp/$(basename $ext)" && \
      cd /app/workspace; \
    done
RUN jupyter labextension disable @jupyterlab/apputils-extension:splash

# Configure Jupyter Lab
RUN mkdir -p /root/.jupyter /usr/local/share/jupyter/lab/settings \
             /usr/local/lib/python3.12/site-packages/jupyter_server/static/favicons \
             /srv/workspace \
             /usr/local/share/jupyter/kernels
RUN mv ./backend/jupyter_notebook_config.py /root/.jupyter/jupyter_notebook_config.py
RUN mv ./backend/jupyter-lab-ext/favicon.ico /usr/local/lib/python3.12/site-packages/jupyter_server/static/favicons/
RUN mv ./backend/remote-kernel/ /usr/local/share/jupyter/kernels/remote-kernel/
RUN echo '{"appName":"Flint"}' \
      > /usr/local/share/jupyter/lab/settings/page_config.json && \
    jupyter kernelspec remove --f python3 && \
    jupyter lab clean && \
    jupyter lab build --dev-build=False --minimize=False --name "Flint"

FROM python:3.12-slim

# Inject dependencies
COPY --from=builder /usr/local/lib/python3.12/site-packages \
                    /usr/local/lib/python3.12/site-packages
COPY --from=builder /root/.jupyter /root/.jupyter
COPY --from=builder /usr/local/share/jupyter /usr/local/share/jupyter
COPY --from=builder /usr/local/lib/python3.12/site-packages/jupyter_server/static/favicons \
                    /usr/local/lib/python3.12/site-packages/jupyter_server/static/favicons
COPY --from=builder /usr/local/share/jupyter/kernels /usr/local/share/jupyter/kernels
COPY --from=builder /usr/local/etc/jupyter /usr/local/etc/jupyter
COPY --from=builder /app/workspace /app/workspace
COPY --from=builder /usr/local/bin /usr/local/bin

# Configure S3FS
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      s3fs fuse libfuse2 && \
    rm -rf /var/lib/apt/lists/*
RUN mkdir -p /mnt/metastore

COPY --from=builder /app/workspace/entrypoint.sh /root/entrypoint.sh
RUN chmod +x /root/entrypoint.sh
ENTRYPOINT ["/root/entrypoint.sh"]