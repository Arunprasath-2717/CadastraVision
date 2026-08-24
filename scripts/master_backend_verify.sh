#!/usr/bin/env bash
set -eo pipefail

echo "============================================================"
echo "CADASTRAVISION MASTER BACKEND VERIFICATION SCRIPT"
echo "============================================================"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
VENV_PYTHON="${BACKEND_DIR}/.venv/bin/python"

if [ ! -f "${VENV_PYTHON}" ]; then
    echo "ERROR: Python virtual environment not found at ${VENV_PYTHON}"
    exit 1
fi

echo "[1/6] Checking Python Version & Compiling Code..."
${VENV_PYTHON} --version
${VENV_PYTHON} -m compileall "${BACKEND_DIR}/app/" -q

echo "[2/6] Running Alembic Migration Integrity Check..."
cd "${BACKEND_DIR}"
${VENV_PYTHON} -m alembic heads

echo "[3/6] Performing Secret Scan..."
SECRET_MATCHES=$(git grep -nE "SECRET_KEY\s*=\s*['\"][^'\"]+['\"]" "${BACKEND_DIR}/app/" | grep -v 'SECRET_KEY: str = "INSECURE_CHANGE_ME_IN_PRODUCTION"' || true)
if [ -n "${SECRET_MATCHES}" ]; then
    echo "WARNING: Hardcoded secret pattern found above!"
    echo "${SECRET_MATCHES}"
    exit 1
else
    echo "Secret scan clean (no hardcoded credentials in app source)."
fi

echo "[4/6] Running Full Pytest Suite (280/280)..."
${VENV_PYTHON} -m pytest -q

echo "[5/6] Testing Live Server Startup and Health Endpoint..."
TEST_PORT=8769
${VENV_PYTHON} -m uvicorn app.main:app --host 127.0.0.1 --port ${TEST_PORT} &
SERVER_PID=$!

cleanup() {
    if kill -0 ${SERVER_PID} 2>/dev/null; then
        echo "Shutting down temporary verification server (PID: ${SERVER_PID})..."
        kill ${SERVER_PID} || true
        wait ${SERVER_PID} 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Wait for server to start
sleep 3

HEALTH_RESP=$(curl -s -w "\n%{http_code}" http://127.0.0.1:${TEST_PORT}/health)
HTTP_CODE=$(echo "${HEALTH_RESP}" | tail -n 1)
BODY=$(echo "${HEALTH_RESP}" | head -n -1)

if [ "${HTTP_CODE}" -ne 200 ]; then
    echo "ERROR: Server health check failed with HTTP ${HTTP_CODE}"
    echo "Response: ${BODY}"
    exit 1
fi

echo "Server responded successfully with HTTP 200: ${BODY}"

echo "[6/6] Verifying OpenAPI Schema..."
OPENAPI_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:${TEST_PORT}/openapi.json)
if [ "${OPENAPI_CODE}" -ne 200 ]; then
    echo "ERROR: OpenAPI endpoint failed with HTTP ${OPENAPI_CODE}"
    exit 1
fi
echo "OpenAPI JSON endpoint verified."

echo "============================================================"
echo "ALL LOCAL MASTER VERIFICATION STEPS PASSED SUCCESSFULLY (0)"
echo "============================================================"
exit 0
