#!/bin/bash
# Install a recent CMake binary release. Option: --version (default: 4.3.2).
# Used by both dev and runtime images.
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: cmake.sh [--version <version>]

Options:
  --version <value>  CMake release version (default: 4.3.2)
  -h, --help         Show this help
EOF
}

CMAKE_VERSION_VAL="4.3.2"
if ! PARSED=$(getopt -o h -l help,version: -n "$(basename "$0")" -- "$@"); then
    usage >&2
    exit 64
fi
eval set -- "$PARSED"
while true; do
    case "$1" in
        --version)
            CMAKE_VERSION_VAL="$2"
            shift 2
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
    echo "cmake.sh: unexpected positional arguments: $*" >&2
    usage >&2
    exit 64
fi

ARCH=$(uname -m)
case $ARCH in
    x86_64) CMAKE_ARCH="linux-x86_64" ;;
    aarch64) CMAKE_ARCH="linux-aarch64" ;;
    *) echo "Unsupported architecture: $ARCH" && exit 1 ;;
esac

wget "https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION_VAL}/cmake-${CMAKE_VERSION_VAL}-${CMAKE_ARCH}.tar.gz"
tar -xf "cmake-${CMAKE_VERSION_VAL}-${CMAKE_ARCH}.tar.gz" --strip-components=1 -C /usr/local
rm "cmake-${CMAKE_VERSION_VAL}-${CMAKE_ARCH}.tar.gz"
