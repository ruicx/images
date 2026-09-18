#!/bin/bash
# Minimal system bootstrap: package metadata, timezone, and locale.
# Developer CLI tools are installed separately by dev-tools.sh, and GUI / WSLg
# deps by wslg.sh, to keep each layer's cache independent.
# Reads TZ (default: Asia/Shanghai).
set -euo pipefail

TZ_VAL="${TZ:-Asia/Shanghai}"

case "$(uname -m)" in
    x86_64) ;;
    *)
        echo "system.sh: unsupported architecture; expected x86_64" >&2
        exit 1
        ;;
esac

chmod 777 /tmp

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends \
    ca-certificates tzdata lsb-release wget software-properties-common gnupg locales

ln -snf "/usr/share/zoneinfo/${TZ_VAL}" /etc/localtime
echo "${TZ_VAL}" >/etc/timezone
locale-gen en_US.UTF-8

rm -rf /var/lib/apt/lists/*
