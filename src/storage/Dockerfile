FROM zenko/cloudserver:latest-7.10.19

ENV S3DATA=multiple \
    REMOTE_MANAGEMENT_DISABLE=true

RUN set -ex && \
    apt-get update && \
    apt-get install -y --no-install-recommends curl unzip && \
    curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
         -o /tmp/awscliv2.zip && \
    unzip -q /tmp/awscliv2.zip -d /tmp && \
    /tmp/aws/install && \
    rm -rf /tmp/aws /tmp/awscliv2.zip && \
    apt-get purge -y --auto-remove curl unzip

WORKDIR /usr/src/app
COPY . .

RUN mv entrypoint.sh /root/wrapper-entrypoint.sh
RUN chmod +x /root/wrapper-entrypoint.sh

ENTRYPOINT ["/root/wrapper-entrypoint.sh"]
CMD ["yarn", "start"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
 CMD /bin/sh -c \
     'AWS_ACCESS_KEY_ID="$STORAGE_USER" \
      AWS_SECRET_ACCESS_KEY="$STORAGE_PASSWORD" \
      aws --endpoint-url http://127.0.0.1:8000 \
          s3api head-bucket --bucket metastore \
       || exit 1'