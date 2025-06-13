FROM aimstack/aim:3.29.1

COPY ./ ./

RUN mv ./entrypoint.sh /root/entrypoint.sh
RUN chmod +x /root/entrypoint.sh
ENTRYPOINT ["/root/entrypoint.sh"]