# CUDA development image

This family builds parameterized Linux amd64 development images from digest-pinned NVIDIA CUDA
images. See `image.yml` for the supported CUDA/Ubuntu combinations. The image includes the CUDA
compiler, a version-pinned CMake 4.3.2 installation, Ninja, GCC, clangd, GDB, Git LFS, Python 3,
pip, virtual-environment support, OpenCV development libraries, common network tools, and modern
command-line utilities such as ripgrep, fd, and bat.

CMake is downloaded from its exact HTTPS release URL. This family intentionally does not verify a
checksum for that archive.

The default interactive user is `root`, no additional login account is created, the working
directory is `/work`, and the package mirror is upstream. Password SSH and root login are enabled
for this family, but the root account remains locked until a password is supplied at runtime. No
password is stored in the image.

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

`DEFAULT_USER=root` selects the existing root account and does not create another user. Any other
valid Linux username creates that account from `DEFAULT_UID` and `DEFAULT_GID`, makes it the final
Docker user, and gives it passwordless sudo. For example:

```yaml
build_args:
  DEFAULT_USER: developer
  DEFAULT_UID: 1000
  DEFAULT_GID: 1000
runtime:
  ssh:
    default: password
    login_user: default
```

`runtime.ssh.login_user` accepts `default` or `root`. The `default` selector follows
`DEFAULT_USER`; `root` explicitly selects root. In password mode, `SSH_PASSWORD_FILE` sets the
password of the resolved login account at container startup. In key-only mode, mount
`authorized_keys` in that account's home directory.
