#!/bin/bash
# Install pip packages.
# Runs on ALL base images (including those that already ship with Python).
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: pip-packages.sh [--preserve-existing]

Options:
  --preserve-existing  Constrain every already installed distribution to its version
  -h, --help           Show this help
EOF
}

PRESERVE_EXISTING=0
if ! PARSED=$(getopt -o h -l help,preserve-existing -n "$(basename "$0")" -- "$@"); then
    usage >&2
    exit 64
fi
eval set -- "$PARSED"
while true; do
    case "$1" in
        --preserve-existing)
            PRESERVE_EXISTING=1
            shift
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
    esac
done
if [ "$#" -ne 0 ]; then
    echo "pip-packages.sh: unexpected positional arguments: $*" >&2
    usage >&2
    exit 64
fi

pip_options=()
if [ "${PRESERVE_EXISTING}" -eq 1 ]; then
    # Preserve the vendor stack without importing torch_npu on builders without NPU drivers.
    install -d /opt/image-python
    python3 -m pip list --format=freeze >/opt/image-python/base-constraints.txt
    pip_options+=(--constraint /opt/image-python/base-constraints.txt)
else
    # Debian's psutil has no pip RECORD metadata. A pip-owned copy avoids uninstalling apt files.
    python3 -m pip install --no-cache-dir --break-system-packages --ignore-installed psutil
fi

python3 -m pip install --no-cache-dir --break-system-packages \
    "${pip_options[@]}" \
    setuptools pandas numpy ipython polars seaborn \
    pytest pytest-xdist pytest-html pytest-mock \
    pytest-randomly pytest-timeout coverage pytest-cov filelock \
    pre-commit rich BeautifulSoup4 allure-pytest \
    plottable matplotlib openpyxl \
    flake8 ruff ty mypy delegator.py build \
    psycopg2-binary peewee python-calamine \
    loguru fastapi aiofiles "uvicorn[standard]" python-multipart "celery[redis]" \
    "pybind11[global]" uv

if [ "${PRESERVE_EXISTING}" -eq 1 ]; then
    python3 -m pip check
fi
