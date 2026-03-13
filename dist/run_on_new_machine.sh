#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "${SCRIPT_DIR}"

IMAGE_NAME=${IMAGE_NAME:-}
IMAGE_TAG=${IMAGE_TAG:-}
HOST_PORT=${HOST_PORT:-3154}
CONTAINER_NAME=${CONTAINER_NAME:-ipc-perfcalc}
DB_PATH=${DB_PATH:-"./ipc_perfcalc.db"}

TAR_FILE=""

if [[ -z "${IMAGE_NAME}" || -z "${IMAGE_TAG}" ]]; then
  # Auto-detect tar file starting with ipc-perfcalc
  for f in ipc-perfcalc*.tar; do
    if [[ -f "${f}" ]]; then
      TAR_FILE="${f}"
      break
    fi
  done
  if [[ -z "${TAR_FILE}" ]]; then
    echo "Image tar not found: ipc-perfcalc*.tar"
    exit 1
  fi

  base="${TAR_FILE%.tar}"
  if [[ "${base}" == *"_"* ]]; then
    IMAGE_NAME="${base%_*}"
    IMAGE_TAG="${base##*_}"
  else
    IMAGE_NAME="${base}"
    IMAGE_TAG="latest"
  fi
else
  TAR_FILE="${IMAGE_NAME}_${IMAGE_TAG}.tar"
  if [[ ! -f "${TAR_FILE}" ]]; then
    echo "Image tar not found: ${TAR_FILE}"
    exit 1
  fi
fi

echo "==> Loading image ${TAR_FILE}"
docker load -i "${TAR_FILE}"

# remove existing container if present
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "==> Removing existing container ${CONTAINER_NAME}"
  docker rm -f "${CONTAINER_NAME}"
fi

DB_MOUNT=()
if [[ -f "${DB_PATH}" ]]; then
  DB_MOUNT=("-v" "$(realpath "${DB_PATH}"):/app/data/ipc_perfcalc.db")
fi

echo "==> Running container ${CONTAINER_NAME} from ${IMAGE_NAME}:${IMAGE_TAG}"
docker run -d --name "${CONTAINER_NAME}" \
  -p "${HOST_PORT}:3154" \
  "${DB_MOUNT[@]}" \
  "${IMAGE_NAME}:${IMAGE_TAG}"

echo "Container started. Frontend: http://localhost:${HOST_PORT}/"
