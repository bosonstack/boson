FROM python:3.12-slim

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

# Copy build context
WORKDIR /app
COPY ../common-lib/flint ./common-lib/flint
COPY ./workspace ./workspace
WORKDIR /app/workspace
RUN mv /app/workspace/entrypoint.sh /root/entrypoint.sh

# Install Poetry
RUN pip install --no-cache-dir poetry

# Install Python dependencies
RUN poetry config virtualenvs.create false
RUN poetry install

# Install Jupyter extensions
RUN mv ./backend/jupyter-lab-ext/experiment-tracker /tmp/experiment-tracker
RUN cd /tmp/experiment-tracker && \
    npm install && \
    npm run build && \
    TARBALL=$(npm pack --silent) && \
    jupyter labextension install $TARBALL --no-build && \
    jupyter labextension install . && \
    rm -rf /tmp/experiment-tracker

RUN mv ./backend/jupyter-lab-ext/catalog-explorer /tmp/catalog-explorer
RUN cd /tmp/catalog-explorer && \
    npm install && \
    npm run build && \
    TARBALL=$(npm pack --silent) && \
    jupyter labextension install $TARBALL --no-build && \
    jupyter labextension install . && \
    rm -rf /tmp/catalog-explorer

RUN jupyter labextension disable @jupyterlab/apputils-extension:splash

RUN mv ./backend/jupyter-lab-ext/theme /tmp/theme
RUN cd /tmp/theme && \
    npm install && \
    npm run build && \
    TARBALL=$(npm pack --silent) && \
    jupyter labextension install $TARBALL --no-build && \
    jupyter labextension install . && \
    rm -rf /tmp/theme
    
# Configure Jupyter
RUN mkdir -p /root/.jupyter/
RUN mv ./backend/jupyter_notebook_config.py /root/.jupyter/jupyter_notebook_config.py

RUN mkdir -p /usr/local/share/jupyter/lab/settings/
RUN echo "{\"appName\": \"Flint\"}" > /usr/local/share/jupyter/lab/settings/page_config.json

RUN mkdir -p /usr/local/lib/python3.12/site-packages/jupyter_server/static/favicons/
RUN cp ./backend/jupyter-lab-ext/favicon.ico /usr/local/lib/python3.12/site-packages/jupyter_server/static/favicons/favicon.ico
RUN cp ./backend/jupyter-lab-ext/favicon.ico /usr/local/lib/python3.12/site-packages/jupyter_server/static/favicons/favicon-busy-1.ico

# This where workspace files (e.g. notebooks) will be stored
RUN mkdir /srv/workspace

# Register custom kernel
RUN mkdir -p /usr/local/share/jupyter/kernels/remote-kernel/
RUN mv ./backend/remote-kernel/kernel.json /usr/local/share/jupyter/kernels/remote-kernel/kernel.json
RUN mv ./backend/remote-kernel/logo-64x64.png /usr/local/share/jupyter/kernels/remote-kernel/logo-64x64.png
RUN jupyter kernelspec remove --f python3

# Apply Jupyter Lab changes and config
RUN jupyter lab clean
RUN jupyter lab build --dev-build=False --minimize=False --name "Flint"

ENTRYPOINT ["/root/entrypoint.sh"]