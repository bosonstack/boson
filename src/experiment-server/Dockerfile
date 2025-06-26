FROM aimstack/aim

ENV FLINT_CONTROL_PLANE_ENDPOINT=http://reverse-proxy

WORKDIR /app

COPY ./experiment-server ./experiment-server

# Configure S3FS
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      s3fs fuse libfuse2 && \
    rm -rf /var/lib/apt/lists/*
RUN mkdir -p /mnt/metastore

RUN mv ./experiment-server/entrypoint.sh /root/entrypoint.sh
RUN chmod +x /root/entrypoint.sh
ENTRYPOINT ["/root/entrypoint.sh"]

HEALTHCHECK --interval=10s \
            --timeout=3s \
            --start-period=5s \
            --retries=6 \
 CMD aim runs --repo aim://localhost:53800 ls || exit 1