#!/usr/bin/env bash
set -euo pipefail

QDRANT_CONTAINER_NAME="${QDRANT_CONTAINER_NAME:-x-agent-qdrant}"
QDRANT_IMAGE="${QDRANT_IMAGE:-qdrant/qdrant:latest}"
QDRANT_HTTP_PORT="${QDRANT_HTTP_PORT:-6333}"
QDRANT_GRPC_PORT="${QDRANT_GRPC_PORT:-6334}"
QDRANT_STORAGE_DIR="${QDRANT_STORAGE_DIR:-$(pwd)/.data/qdrant}"

mkdir -p "${QDRANT_STORAGE_DIR}"

if docker ps --format '{{.Names}}' | grep -qx "${QDRANT_CONTAINER_NAME}"; then
  echo "Qdrant container ${QDRANT_CONTAINER_NAME} is already running."
  exit 0
fi

if docker ps -a --format '{{.Names}}' | grep -qx "${QDRANT_CONTAINER_NAME}"; then
  docker start "${QDRANT_CONTAINER_NAME}"
  echo "Started existing Qdrant container ${QDRANT_CONTAINER_NAME}."
  exit 0
fi

docker run -d \
  --name "${QDRANT_CONTAINER_NAME}" \
  -p "${QDRANT_HTTP_PORT}:6333" \
  -p "${QDRANT_GRPC_PORT}:6334" \
  -v "${QDRANT_STORAGE_DIR}:/qdrant/storage" \
  "${QDRANT_IMAGE}"

echo "Started Qdrant at http://127.0.0.1:${QDRANT_HTTP_PORT}."
