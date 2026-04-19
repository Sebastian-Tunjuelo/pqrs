# PostGIS (geometrías) + extensión pgvector para búsqueda semántica.
FROM postgis/postgis:16-3.4

USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    build-essential \
    postgresql-server-dev-16 \
  && cd /tmp \
  && git clone --depth 1 --branch v0.7.4 https://github.com/pgvector/pgvector.git \
  && cd pgvector \
  && make \
  && make install \
  && cd / \
  && rm -rf /tmp/pgvector \
  && apt-get purge -y git build-essential postgresql-server-dev-16 \
  && apt-get autoremove -y \
  && rm -rf /var/lib/apt/lists/*

USER postgres
