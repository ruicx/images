#!/bin/bash
# Smoke-test the CUDA development image from inside the built container.
set -euo pipefail

test "$(uname -m)" = "x86_64"
test "$(id -u)" -ne 0
test "${PWD}" = "/work"
test "${SSH_MODE}" = "password"
test "${PACKAGE_MIRROR}" = "upstream"
command -v nvcc >/dev/null
nvcc --version
python3 --version
python3 -m pip --version
cmake --version | grep -F "cmake version 4.3.2"
ninja --version
git --version
git lfs version
gdb --version | head -n 1
clangd --version | head -n 1
rg --version | head -n 1
fd --version
bat --version
sudo -n true
test -d /work
test -w /work
test -x /usr/local/bin/docker-entrypoint
grep -Fx "PasswordAuthentication yes" /etc/ssh/sshd_config.d/99-dev-image.conf
grep -Fx "PermitRootLogin yes" /etc/ssh/sshd_config.d/99-dev-image.conf
if pgrep -x sshd >/dev/null; then
    echo "sshd must not run when the entrypoint is bypassed" >&2
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

# Password mode starts sshd with root login enabled while root remains locked by default.
SSH_MODE=password /usr/local/bin/docker-entrypoint true
pgrep -x sshd >/dev/null
test "$(sudo -n passwd --status root | awk '{print $2}')" = "L"
sudo -n pkill -x sshd
