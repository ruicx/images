#!/bin/bash
# Smoke-test the CUDA development image from inside the built container.
set -euo pipefail

test "$(uname -m)" = "x86_64"
test "$(id -u)" -ne 0
test "${PWD}" = "/home/${USERNAME}"
test "${SSH_MODE}" = "disabled"
test "${PACKAGE_MIRROR}" = "upstream"
command -v nvcc >/dev/null
nvcc --version
test -x /usr/local/bin/docker-entrypoint
grep -Fx "PasswordAuthentication no" /etc/ssh/sshd_config.d/99-dev-image.conf
grep -Fx "PermitRootLogin no" /etc/ssh/sshd_config.d/99-dev-image.conf
if pgrep -x sshd >/dev/null; then
    echo "sshd must not run when SSH_MODE=disabled" >&2
    exit 1
fi

# Key-only mode must fail closed without a mounted key.
set +e
SSH_MODE=key-only /usr/local/bin/docker-entrypoint true
status=$?
set -e
test "${status}" -eq 64

# A mounted public key enables sshd while PID 1 remains the non-root user.
printf '%s\n' 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGeneratedForSmokeTestOnly image-test' \
    >"${HOME}/.ssh/authorized_keys"
SSH_MODE=key-only /usr/local/bin/docker-entrypoint true
pgrep -x sshd >/dev/null
sudo -n pkill -x sshd
: >"${HOME}/.ssh/authorized_keys"
