#!/bin/bash
# Install a version-pinned CMake binary release for Linux amd64.
# Option: --version. The consuming image documents the checksum exception.
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
if [[ ! "${CMAKE_VERSION_VAL}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "cmake.sh: version must use numeric major.minor.patch format" >&2
    exit 64
fi
case "$(uname -m)" in
    x86_64) ;;
    *)
        echo "cmake.sh: unsupported architecture; expected x86_64" >&2
        exit 1
        ;;
esac

CMAKE_ARCHIVE="cmake-${CMAKE_VERSION_VAL}-linux-x86_64.tar.gz"
TEMP_DIRECTORY=$(mktemp -d)
trap 'rm -rf "${TEMP_DIRECTORY}"' EXIT

curl --fail --location --proto '=https' --tlsv1.2 \
    "https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION_VAL}/${CMAKE_ARCHIVE}" \
    --output "${TEMP_DIRECTORY}/${CMAKE_ARCHIVE}"
tar -xzf "${TEMP_DIRECTORY}/${CMAKE_ARCHIVE}" --strip-components=1 -C /usr/local
