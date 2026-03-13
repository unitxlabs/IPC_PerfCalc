#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME=${IMAGE_NAME:-ipc-perfcalc}
IMAGE_TAG=${IMAGE_TAG:-latest}
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
NO_CACHE=${NO_CACHE:-0}
EXPORT_DIR="${ROOT_DIR}/dist"
EXPORT_IMAGE_TAR="${EXPORT_DIR}/${IMAGE_NAME}_${IMAGE_TAG}.tar"
EXPORT_DB="${EXPORT_DIR}/ipc_perfcalc.db"
IMPORT_SCRIPT="${EXPORT_DIR}/run_on_new_machine.sh"

echo "==> Building image ${IMAGE_NAME}:${IMAGE_TAG}"
BUILD_ARGS=()
if [[ "${NO_CACHE}" == "1" ]]; then
  BUILD_ARGS+=(--no-cache)
fi
docker build "${BUILD_ARGS[@]}" -t "${IMAGE_NAME}:${IMAGE_TAG}" "${ROOT_DIR}"

echo "==> Preparing distribution artifacts"
mkdir -p "${EXPORT_DIR}"

# Export image to tar
docker save "${IMAGE_NAME}:${IMAGE_TAG}" -o "${EXPORT_IMAGE_TAR}"

# Copy DB snapshot if exists
if [[ -f "${ROOT_DIR}/ipc_perfcalc.db" ]]; then
  cp -f "${ROOT_DIR}/ipc_perfcalc.db" "${EXPORT_DB}"
fi

# Generate helper script for new machine
cat > "${IMPORT_SCRIPT}" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME=${IMAGE_NAME:-ipc-perfcalc}
IMAGE_TAG=${IMAGE_TAG:-latest}
HOST_PORT=${HOST_PORT:-3154}
CONTAINER_NAME=${CONTAINER_NAME:-ipc-perfcalc}
DB_PATH=${DB_PATH:-"./ipc_perfcalc.db"}

TAR_FILE="${IMAGE_NAME}_${IMAGE_TAG}.tar"

if [[ ! -f "${TAR_FILE}" ]]; then
  echo "Image tar not found: ${TAR_FILE}"
  exit 1
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
EOF

chmod +x "${IMPORT_SCRIPT}"

echo "Build complete."
echo "Artifacts in: ${EXPORT_DIR}"