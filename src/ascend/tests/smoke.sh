#!/bin/bash
# Check the ARM64 development image without requiring host NPU devices or driver libraries.
set -euo pipefail

test "$(uname -m)" = "aarch64"
test "$(id -un)" = "luciole"
test "${DEFAULT_USER}" = "luciole"
test "${PWD}" = "${WORKSPACE_DIR}"
test "${WORKSPACE_DIR}" = "/work"
test "${SSH_MODE}" = "password"
test "${PACKAGE_MIRROR}" = "upstream"
sudo -n true
test -w "${WORKSPACE_DIR}"
test -x /usr/local/bin/ascend-entrypoint
test -x /usr/local/bin/docker-entrypoint
test -r "${ASCEND_HOME_PATH}/include/acl/acl.h"
test -d "${ASCEND_OPP_PATH}"
command -v bisheng >/dev/null
cmake --version | grep -F 'cmake version 4.3.2'
ninja --version
git lfs version
clangd --version | head -n 1
gdb --version | head -n 1
rg --version | head -n 1
fd --version
bat --version
python --version
ascend-pip-check
uv --version
ty --version

# Distribution metadata can be checked without loading driver-dependent shared objects.
python3 - <<'PYTHON'
from importlib.metadata import version
from pathlib import Path
import sys
import sysconfig
import tempfile
import venv

assert sys.version_info[:2] == (3, 12)
assert sys.prefix.startswith("/usr/local/python3.12.")
assert version("torch").split("+")[0] == "2.14.0"
assert version("torch-npu") == "2.14.0"
assert Path(sysconfig.get_path("include"), "Python.h").is_file()
with tempfile.TemporaryDirectory() as directory:
    venv.create(directory, with_pip=True)
    assert Path(directory, "bin/python").is_file()
PYTHON

test "$(getent passwd luciole | cut -d: -f7)" = "/bin/zsh"
test "$(dpkg-query -W -f='${Status}' zsh-common)" = "install ok installed"
# A clean non-login shell must recover CANN and vendor Python from zshenv alone.
# shellcheck disable=SC2016
env -i HOME="${HOME}" PATH=/usr/bin:/bin zsh -ec \
    'test -r "${ASCEND_HOME_PATH}/include/acl/acl.h"; test "$(python3 -c "import sys; print(sys.version_info.minor)")" = 12; command -v bisheng'
zsh -lc 'test "$(python3 -c "import sys; print(sys.version_info.minor)")" = 12; command -v bisheng'
bash -lc 'test "$(python3 -c "import sys; print(sys.version_info.minor)")" = 12; command -v bisheng'
test -x "${HOME}/.fzf/bin/fzf"
command -v nvim >/dev/null
command -v eza >/dev/null
command -v starship >/dev/null
grep -Fq 'cmd = { "ty", "server" }' "${HOME}/.config/nvim/lua/configs/lspconfig.lua"
grep -Fx 'AllowUsers luciole' /etc/ssh/sshd_config.d/99-dev-image.conf

# Exercise the real wrapper and SSH startup without opening an unauthenticated account.
SSH_MODE=disabled /usr/local/bin/ascend-entrypoint python3 --version
if pgrep -x sshd >/dev/null; then
    echo "sshd must not start while SSH is disabled" >&2
    exit 1
fi
set +e
SSH_MODE=key-only /usr/local/bin/ascend-entrypoint true
status=$?
set -e
test "${status}" -eq 64
SSH_MODE=password /usr/local/bin/ascend-entrypoint true
pgrep -x sshd >/dev/null
test "$(sudo -n passwd --status luciole | awk '{print $2}')" = "L"
sudo -n pkill -x sshd
