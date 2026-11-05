#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/app"
MYSQL_DATA_DIR="/var/lib/mysql"
MYSQL_SOCKET="/run/mysqld/mysqld.sock"
MYSQL_INIT_PID="/run/mysqld/mysqld-init.pid"
PYTHON_BIN="/opt/venv/bin/python"

cd "${APP_DIR}"

if [[ -f "${APP_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${APP_DIR}/.env"
  set +a
fi
if [[ -f "${APP_DIR}/.env.local" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${APP_DIR}/.env.local"
  set +a
fi

: "${DB_MODE:=internal}"
: "${DB_HOST:=127.0.0.1}"
: "${DB_PORT:=3306}"
: "${DB_USER:=root}"
: "${DB_PASSWORD:=}"
: "${DB_NAME:=db}"
: "${DB_CHARSET:=utf8mb4}"

if [[ "${DB_MODE}" != "internal" && "${DB_MODE}" != "external" ]]; then
  echo "Invalid DB_MODE=${DB_MODE}. Expected: internal or external."
  exit 1
fi

if [[ "${DB_MODE}" == "external" ]]; then
  echo "DB_MODE=external, skip internal MariaDB and start Flask only."
  exec "${PYTHON_BIN}" -m flask --app api:app run --host=0.0.0.0 --port=11232 --no-debugger --no-reload
fi

mkdir -p /run/mysqld "${MYSQL_DATA_DIR}"
chown -R mysql:mysql /run/mysqld "${MYSQL_DATA_DIR}"

if [[ ! -d "${MYSQL_DATA_DIR}/mysql" ]]; then
  mariadb-install-db \
    --user=mysql \
    --datadir="${MYSQL_DATA_DIR}" \
    --skip-test-db \
    --auth-root-authentication-method=normal
fi

echo "Starting temporary MariaDB for initialization..."
/usr/sbin/mariadbd \
  --user=mysql \
  --datadir="${MYSQL_DATA_DIR}" \
  --socket="${MYSQL_SOCKET}" \
  --skip-networking \
  --pid-file="${MYSQL_INIT_PID}" &

for _ in {1..60}; do
  if mariadb-admin --protocol=socket --socket="${MYSQL_SOCKET}" ping --silent >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! mariadb-admin --protocol=socket --socket="${MYSQL_SOCKET}" ping --silent >/dev/null 2>&1; then
  echo "MariaDB initialization startup failed."
  exit 1
fi

ROOT_AUTH_ARGS=(-uroot)
if [[ -n "${DB_PASSWORD}" ]]; then
  ROOT_AUTH_ARGS+=("-p${DB_PASSWORD}")
fi

ROOT_SQL_ARGS=("${ROOT_AUTH_ARGS[@]}")
if ! mariadb --protocol=socket --socket="${MYSQL_SOCKET}" "${ROOT_SQL_ARGS[@]}" -e "SELECT 1;" >/dev/null 2>&1; then
  ROOT_SQL_ARGS=(-uroot)
fi

# root 与业务账号都初始化为环境变量指定密码，确保 Flask 可通过 TCP 连接。
mariadb --protocol=socket --socket="${MYSQL_SOCKET}" "${ROOT_SQL_ARGS[@]}" <<SQL
ALTER USER 'root'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET ${DB_CHARSET};
CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'%';
FLUSH PRIVILEGES;
SQL

mariadb-admin \
  --protocol=socket \
  --socket="${MYSQL_SOCKET}" \
  "${ROOT_AUTH_ARGS[@]}" \
  shutdown

echo "MariaDB initialization complete. Starting supervisord..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/shifanxitong.conf
