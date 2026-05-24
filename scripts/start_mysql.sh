#!/usr/bin/env bash
set -euo pipefail

MYSQL_CONTAINER_NAME="${MYSQL_CONTAINER_NAME:-x-agent-mysql}"
MYSQL_IMAGE="${MYSQL_IMAGE:-mysql:8.0}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-${MYSQL_PASSWORD:-root}}"
MYSQL_DATABASE="${MYSQL_DATABASE:-x_agent_mock_biz}"
MYSQL_STORAGE_DIR="${MYSQL_STORAGE_DIR:-$(pwd)/.data/mysql}"

mkdir -p "${MYSQL_STORAGE_DIR}"

if docker ps --format '{{.Names}}' | grep -qx "${MYSQL_CONTAINER_NAME}"; then
  echo "MySQL container ${MYSQL_CONTAINER_NAME} is already running."
else
  if docker ps -a --format '{{.Names}}' | grep -qx "${MYSQL_CONTAINER_NAME}"; then
    docker start "${MYSQL_CONTAINER_NAME}"
    echo "Started existing MySQL container ${MYSQL_CONTAINER_NAME}."
  else
    docker run -d \
      --name "${MYSQL_CONTAINER_NAME}" \
      -p "${MYSQL_PORT}:3306" \
      -e MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD}" \
      -e MYSQL_DATABASE="${MYSQL_DATABASE}" \
      -v "${MYSQL_STORAGE_DIR}:/var/lib/mysql" \
      "${MYSQL_IMAGE}"
    echo "Started MySQL at 127.0.0.1:${MYSQL_PORT}."
  fi
fi

echo "Waiting for MySQL to accept connections..."
for _ in $(seq 1 60); do
  if docker exec "${MYSQL_CONTAINER_NAME}" \
    mysqladmin ping -h127.0.0.1 -P3306 -uroot -p"${MYSQL_ROOT_PASSWORD}" --silent \
      >/dev/null 2>&1; then
    echo "MySQL is ready."
    exit 0
  fi
  sleep 1
done

echo "MySQL did not become ready in time." >&2
exit 1
