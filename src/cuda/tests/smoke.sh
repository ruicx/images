#!/bin/bash
# Smoke-test the CUDA development image from inside the built container.
set -euo pipefail

test "$(uname -m)" = "x86_64"
test "$(id -u)" -eq 0
test "$(id -un)" = "root"
test "${DEFAULT_USER}" = "root"
test "${WORKSPACE_DIR}" = "/work"
test "${PWD}" = "${WORKSPACE_DIR}"
test "${SSH_MODE}" = "password"
test "${PACKAGE_MIRROR}" = "upstream"
command -v nvcc >/dev/null
nvcc --version
python3 --version
python --version
python3 -m pip --version
python -m pip --version
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
test -d "${WORKSPACE_DIR}"
test -w "${WORKSPACE_DIR}"
if getent passwd luciole >/dev/null; then
    echo "the root-only CUDA variant must not create the legacy luciole user" >&2
    exit 1
fi
test -x /usr/local/bin/docker-entrypoint
test "$(getent passwd root | cut -d: -f7)" = "/bin/zsh"
command -v zsh >/dev/null
command -v nvim >/dev/null
command -v ty >/dev/null
ty --version
grep -Fq 'cmd = { "ty", "server" }' "${HOME}/.config/nvim/lua/configs/lspconfig.lua"
grep -Fq 'vim.lsp.enable({ "html", "cssls", "ty" })' \
    "${HOME}/.config/nvim/lua/configs/lspconfig.lua"
command -v eza >/dev/null
command -v starship >/dev/null
test -x "${HOME}/.fzf/bin/fzf"
test -x "${HOME}/.local/bin/sheldon"
test -x "${HOME}/.local/bin/zoxide"
grep -Fx "PasswordAuthentication yes" /etc/ssh/sshd_config.d/99-dev-image.conf
grep -Fx "PermitRootLogin yes" /etc/ssh/sshd_config.d/99-dev-image.conf
grep -Fx "AllowUsers root" /etc/ssh/sshd_config.d/99-dev-image.conf
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

# Key-only mode uses root because it is the selected SSH login account.
printf '%s\n' 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGeneratedForSmokeTestOnly image-test' \
    >/root/.ssh/authorized_keys
SSH_MODE=key-only /usr/local/bin/docker-entrypoint true
pgrep -x sshd >/dev/null
pkill -x sshd
: >/root/.ssh/authorized_keys

# Password mode starts sshd with root login enabled while root remains locked by default.
test "$(passwd --status root | awk '{print $2}')" = "L"
SSH_MODE=password /usr/local/bin/docker-entrypoint true
pgrep -x sshd >/dev/null
test "$(passwd --status root | awk '{print $2}')" = "L"
pkill -x sshd

# A runtime-mounted password file unlocks root without storing a password in the image.
password_file="$(mktemp)"
trap 'rm -f "${password_file}"' EXIT
printf '%s' 'SmokeTestOnly-ChangeMe-9384' >"${password_file}"
SSH_MODE=password SSH_PASSWORD_FILE="${password_file}" \
    /usr/local/bin/docker-entrypoint true
pgrep -x sshd >/dev/null
test "$(passwd --status root | awk '{print $2}')" = "P"
pkill -x sshd
