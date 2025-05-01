FROM python:3.12-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    jq \
    s3fs \
    fuse \
    git && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean

# Install Poetry
RUN pip install --no-cache-dir poetry
RUN pip install aim

COPY README.md README.md
COPY pyproject.toml pyproject.toml
COPY kernel/ kernel/
RUN poetry config virtualenvs.create false
RUN poetry install

# Inject local dependencies
COPY jupyter_notebook_config.py /root/.jupyter/jupyter_notebook_config.py

RUN mkdir -p /root/.jupyter
RUN mkdir -p /root/.ipython/profile_default/startup
COPY kernel/globals.py /root/.ipython/profile_default/startup/00-load-globals.py

# Install Jupyter extensions

COPY jupyter-lab-ext/experiment-tracker /root/.jupyter-extensions/experiment-tracker
WORKDIR /root/.jupyter-extensions/experiment-tracker
RUN npm install && \
    npm run build && \
    jupyter labextension install .

COPY jupyter-lab-ext/delta-explorer /root/.jupyter-extensions/delta-explorer
WORKDIR /root/.jupyter-extensions/delta-explorer
RUN npm install && \
    npm run build && \
    jupyter labextension install .


RUN jupyter labextension disable @jupyterlab/apputils-extension:splash

COPY jupyter-lab-ext/theme /root/.jupyter-extensions/theme
WORKDIR /root/.jupyter-extensions/theme
RUN npm install && \
    npm run build && \
    jupyter labextension install .

# Override Jupyter source
COPY jupyter-lab-ext/favicon.ico /usr/local/lib/python3.12/site-packages/jupyter_server/static/favicons/favicon.ico
COPY jupyter-lab-ext/favicon.ico /usr/local/lib/python3.12/site-packages/jupyter_server/static/favicons/favicon-busy-1.ico

# Inject mount instructions
COPY mount-cloud-storage.sh /root/.mount-cloud-storage.sh

WORKDIR /workspace