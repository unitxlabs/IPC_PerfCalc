#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME=${IMAGE_NAME:-ipc-perfcalc}
IMAGE_TAG=${IMAGE_TAG:-latest}
CONTAINER_NAME=${CONTAINER_NAME:-ipc-perfcalc}
HOST_PORT=${HOST_PORT:-3154}
DB_VOLUME=${DB_VOLUME:-ipc-perfcalc-db}
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

# remove existing container if present
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "==> Removing existing container ${CONTAINER_NAME}"
  docker rm -f "${CONTAINER_NAME}"
fi

DB_MOUNT=("-v" "${DB_VOLUME}:/app/data")
if [[ -f "${ROOT_DIR}/ipc_perfcalc.db" ]]; then
  DB_MOUNT=("-v" "${ROOT_DIR}/ipc_perfcalc.db:/app/data/ipc_perfcalc.db")
fi

echo "==> Running container ${CONTAINER_NAME} from ${IMAGE_NAME}:${IMAGE_TAG}"
docker run -d --name "${CONTAINER_NAME}" \
  -p "${HOST_PORT}:3154" \
  "${DB_MOUNT[@]}" \
  "${IMAGE_NAME}:${IMAGE_TAG}"

echo "Container started. Frontend: http://localhost:${HOST_PORT}/"
