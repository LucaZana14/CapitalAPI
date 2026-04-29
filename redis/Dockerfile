FROM redis:7.0.3

COPY --chown=redis:redis ./dump.rdb /data/dump.rdb

USER redis

ENTRYPOINT ["redis-server", "--dbfilename", "dump.rdb", "--dir", "/data"]