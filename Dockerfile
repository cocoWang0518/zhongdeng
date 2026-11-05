FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        mariadb-server \
        mariadb-client \
        supervisor \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.6.7 /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock uv.toml /tmp/build/
WORKDIR /tmp/build
RUN uv sync --frozen --no-dev --no-install-project \
    && uv cache clean

COPY docker/entrypoint.sh /usr/local/bin/shifanxitong-entrypoint
COPY docker/supervisord.conf /etc/supervisor/conf.d/shifanxitong.conf
RUN chmod +x /usr/local/bin/shifanxitong-entrypoint

WORKDIR /app

EXPOSE 11232 3306

VOLUME ["/var/lib/mysql"]

ENTRYPOINT ["/usr/local/bin/shifanxitong-entrypoint"]
