#!/bin/bash
# Install pip packages.
# Runs on ALL base images (including those that already ship with Python).
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: pip-packages.sh

Options:
  -h, --help  Show this help
EOF
}

if ! PARSED=$(getopt -o h -l help -n "$(basename "$0")" -- "$@"); then
    usage >&2
    exit 64
fi
eval set -- "$PARSED"
while true; do
    case "$1" in
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

# pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple/

python3 -m pip install --no-cache-dir --break-system-packages \
    setuptools pandas numpy ipython polars seaborn \
    pytest pytest-xdist pytest-html pytest-mock \
    pytest-randomly pytest-timeout coverage pytest-cov filelock \
    pre-commit rich BeautifulSoup4 allure-pytest \
    plottable matplotlib openpyxl \
    flake8 ruff ty mypy delegator.py build \
    psycopg2-binary peewee python-calamine \
    loguru fastapi aiofiles "uvicorn[standard]" python-multipart "celery[redis]" \
    "pybind11[global]"

curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin INSTALLER_NO_MODIFY_PATH=1 sh
