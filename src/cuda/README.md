# CUDA development image

This family builds parameterized Linux amd64 development images from digest-pinned NVIDIA CUDA
images. See `image.yml` for the supported CUDA/Ubuntu combinations. The image includes the CUDA
compiler, a version-pinned CMake 4.3.2 installation, Ninja, GCC, clangd, GDB, Git LFS, Python 3,
pip, virtual-environment support, OpenCV development libraries, a precompiled CUDA-enabled
llama.cpp, common network tools, and modern command-line utilities such as ripgrep, fd, and bat.

llama.cpp is installed from the official GitHub `b11046` Ubuntu x64 CUDA 12.8 release asset at
`https://github.com/ggml-org/llama.cpp/releases/download/b11046/llama-b11046-bin-ubuntu-cuda-12.8-x64.tar.gz`.
This family has a user-approved checksum exception for that exact version and HTTPS URL; replacing
an asset under the same release name is therefore an accepted supply-chain risk. The archive is
extracted to `/opt/llama.cpp`, and its `llama-*` executables are linked into `/usr/local/bin` without
changing `PATH`. The separate upstream CUDA runtime archive is intentionally omitted because this
image family already supplies CUDA 12 runtime libraries. `LLAMA_CPP_VERSION` and
`LLAMA_CPP_CUDA_VERSION` must be updated together when upgrading. The llama.cpp layer follows the
developer-shell layer so a llama.cpp version change does not invalidate the more expensive shell
setup; final mirror selection runs afterward because the shell setup installs packages.

The developer shell is enabled by default with `DEVSHELL: true`. It installs zsh, Oh My Zsh,
NvChad, NVM with the current Node.js LTS, fzf, eza, Starship, Sheldon, Zoxide, Witr, and Atuin. The
container command remains Bash. SSH sessions use the account's configured zsh login shell, while
`docker exec` callers may explicitly select `bash` or `zsh`. Setting `DEVSHELL: false` skips the
developer-shell installation.

This developer-shell capability intentionally follows current upstream releases, branches, and
installers instead of pinning every component. It is a user-approved rolling exception to the
repository's normal reproducibility and checksum rules. Rebuilding the same Git revision at a
later date can therefore produce different developer-shell contents or fail because upstream
artifacts changed.

CMake is downloaded from its exact HTTPS release URL. This family intentionally does not verify a
checksum for that archive.

The default interactive user is `root`, no additional login account is created, the package mirror
is upstream, and `WORKSPACE_DIR` selects the created working directory (`/work` by default). The
workspace must be an absolute path other than `/`; it is owned by `DEFAULT_USER`. Password SSH and
root login are enabled for this family, but the root account remains locked until a password is
supplied at runtime. No password is stored in the image.

`PACKAGE_MIRROR` accepts `upstream` or `aliyun`. The final mirror capability keeps the base image's
package sources unchanged for `upstream`; for `aliyun`, it switches the persisted apt and pip
configuration only after all build-time package installation has completed.

Running the container as root and exposing password SSH gives processes and accepted SSH sessions
full control of the container. Use a unique strong password, restrict the published SSH port at the
host or network boundary, and prefer `SSH_MODE=key-only` or `SSH_MODE=disabled` when possible.

Create a local password file and mount it read-only to start a container that accepts root SSH:

```bash
printf '%s' 'replace-with-a-private-password' >ssh-password
chmod 600 ssh-password
docker run --rm -d \
  --name cuda-dev \
  --gpus all \
  -p 2222:22 \
  -e SSH_PASSWORD_FILE=/run/secrets/ssh-password \
  -v "${PWD}/ssh-password:/run/secrets/ssh-password:ro" \
  ghcr.io/ruicx/cuda:12.8.1-devel-ubuntu24.04 \
  sleep infinity
ssh -p 2222 root@localhost
```

Delete the local password file when it is no longer needed. To disable SSH, set
`SSH_MODE=disabled`. To use the safer key-only mode, set `SSH_MODE=key-only` and mount a non-empty
public-key file at `/root/.ssh/authorized_keys`.

`DEFAULT_USER=root` makes the user setup capability reuse the existing root account and does not
create or renumber a user; `DEFAULT_UID` and `DEFAULT_GID` are not applied in this mode. Any other
valid Linux username creates that account from `DEFAULT_UID` and `DEFAULT_GID`, makes it the final
Docker user, and gives it passwordless sudo. For example:

```yaml
build_args:
  DEFAULT_USER: developer
  DEFAULT_UID: 1000
  DEFAULT_GID: 1000
  WORKSPACE_DIR: /workspace
runtime:
  ssh:
    default: password
    login_user: default
```

`runtime.ssh.login_user` accepts `default` or `root`. The `default` selector follows
`DEFAULT_USER`; `root` explicitly selects root. In password mode, `SSH_PASSWORD_FILE` sets the
password of the resolved login account at container startup. In key-only mode, mount
`authorized_keys` in that account's home directory.
