FROM aimstack/aim

ENV FLINT_CONTROL_PLANE_ENDPOINT=http://reverse-proxy

WORKDIR /app

COPY ./experiment-server ./experiment-server

RUN mv ./experiment-server/init-server.sh /root/init-server.sh

ENTRYPOINT ["/root/init-server.sh"]

HEALTHCHECK --interval=5s \
            --timeout=3s \
            --start-period=5s \
            --retries=5 \
  CMD aim runs --repo aim://localhost:53800 ls || exit 1