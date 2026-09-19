#!/bin/bash
# Install and configure the optional SSH server (BUILD-TIME only).
#
# Runs during `docker build`. Everything here must be declarative / persisted
# to disk — a build layer **cannot** actually run a daemon. Starting sshd at
# runtime is the entrypoint's job (see src/_assets/docker-entrypoint.sh).
#
# What this script does:
#   - Installs openssh-server.
#   - Configures key-only or password/root authentication explicitly.
#   - Prepares the non-root user's authorized_keys mount point.
# Host keys are generated at runtime only when SSH is enabled.
#
# Options: --username and --mode.
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: ssh.sh [--username <name>] [--mode <mode>]

Options:
  --username <value>  Existing non-root user (default: luciole)
  --mode <value>      SSH policy: disabled, key-only, or password (default: disabled)
  -h, --help          Show this help
EOF
}

USERNAME_VAL="luciole"
SSH_MODE_VAL="disabled"

if ! PARSED=$(getopt -o h -l help,username:,mode: -n "$(basename "$0")" -- "$@"); then
    usage >&2
    exit 64
fi
eval set -- "$PARSED"
while true; do
    case "$1" in
        --username)
            USERNAME_VAL="$2"
            shift 2
            ;;
        --mode)
            SSH_MODE_VAL="$2"
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
    echo "ssh.sh: unexpected positional arguments: $*" >&2
    usage >&2
    exit 64
fi
case "${SSH_MODE_VAL}" in
    disabled | key-only | password) ;;
    *)
        echo "ssh.sh: unsupported mode '${SSH_MODE_VAL}'" >&2
        exit 64
        ;;
esac

case "$(uname -m)" in
    x86_64) ;;
    *)
        echo "ssh.sh: unsupported architecture; expected x86_64" >&2
        exit 1
        ;;
esac

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends openssh-server
rm -rf /var/lib/apt/lists/*

# /run/sshd is where sshd chroots its priv-separated child at runtime.
# Create it here so the entrypoint doesn't need root-only mkdir work.
mkdir -p /run/sshd
chmod 0755 /run/sshd

cat >/etc/ssh/sshd_config.d/99-dev-image.conf <<EOF
PubkeyAuthentication yes
PasswordAuthentication $([ "${SSH_MODE_VAL}" = "password" ] && echo yes || echo no)
KbdInteractiveAuthentication no
PermitEmptyPasswords no
PermitRootLogin $([ "${SSH_MODE_VAL}" = "password" ] && echo yes || echo no)
EOF

# Seed authorized_keys for the non-root user (if the account already exists —
# in the base image ssh.sh runs before user.sh, so the user may not exist yet;
# in that case user.sh is responsible for the directory).
if ! id "${USERNAME_VAL}" >/dev/null 2>&1; then
    echo "ssh.sh: user '${USERNAME_VAL}' must exist before SSH setup" >&2
    exit 1
fi
USER_HOME="$(getent passwd "${USERNAME_VAL}" | cut -d: -f6)"
mkdir -p "${USER_HOME}/.ssh"
touch "${USER_HOME}/.ssh/authorized_keys"
chmod 0700 "${USER_HOME}/.ssh"
chmod 0600 "${USER_HOME}/.ssh/authorized_keys"
chown -R "${USERNAME_VAL}":"$(id -gn "${USERNAME_VAL}")" "${USER_HOME}/.ssh"

# NOTE: do NOT call `service ssh start` / `systemctl start ssh` here — a build
# layer has no init and the daemon would die the moment the layer commits.
# Starting sshd is the entrypoint's job at container runtime when explicitly enabled.
