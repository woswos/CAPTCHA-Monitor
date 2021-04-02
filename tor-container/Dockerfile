FROM alpine:edge

RUN apk add --no-cache curl tor

HEALTHCHECK --interval=60s --timeout=15s --start-period=20s \
    CMD curl -s --socks5 127.0.0.1:9050 'https://check.torproject.org/' | grep -qm1 Congratulations

VOLUME ["/var/lib/tor"]

USER tor

CMD ["tor"]