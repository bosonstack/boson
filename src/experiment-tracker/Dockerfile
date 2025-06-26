FROM aimstack/aim:3.29.1

COPY ./ ./

# Configure S3FS
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      s3fs fuse libfuse2 && \
    rm -rf /var/lib/apt/lists/*
RUN mkdir -p /mnt/metastore

RUN mv ./entrypoint.sh /root/entrypoint.sh
RUN chmod +x /root/entrypoint.sh
ENTRYPOINT ["/root/entrypoint.sh"]