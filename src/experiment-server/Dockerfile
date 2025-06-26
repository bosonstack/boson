FROM aimstack/aim

WORKDIR /app

COPY ./experiment-server ./experiment-server

RUN mv ./experiment-server/entrypoint.sh /root/entrypoint.sh
RUN chmod +x /root/entrypoint.sh
ENTRYPOINT ["/root/entrypoint.sh"]

HEALTHCHECK --interval=5s \
            --timeout=3s \
            --start-period=5s \
            --retries=5 \
 CMD aim runs --repo aim://localhost:53800 ls || exit 1