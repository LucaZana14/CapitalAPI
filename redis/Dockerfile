FROM redis:7.0.3

COPY --chown=redis:redis ./dump.rdb /data/dump.rdb

USER redis

ENTRYPOINT ["redis-server", "--dbfilename", "dump.rdb", "--dir", "/data"]

# Chiede a Redis se è vivo inviando un "ping". Se non risponde, il container è "unhealthy"
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD redis-cli ping || exit 1