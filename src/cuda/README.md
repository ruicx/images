# CUDA development image

Ready-to-use Linux amd64 development environments based on NVIDIA CUDA `devel` images. The
published variants include the CUDA compiler, common C/C++ and Python tools, a configured developer
shell, and optional SSH access. The Chinese version is in [README_zh.md](README_zh.md).

## Requirements

To use the GPU from a container, the host needs:

- a compatible NVIDIA GPU and driver;
- Docker with the NVIDIA Container Toolkit configured;
- an amd64 container environment.

The image can start without `--gpus all`, but GPU commands and CUDA workloads will not have access
to a host GPU.

## Start an interactive environment

Pull the image, mount the current project at `/work`, disable the unneeded SSH service, and open the
default Bash shell:

```bash
docker pull ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
docker run --rm -it \
  --gpus all \
  -e SSH_MODE=disabled \
  -v "${PWD}:/work" \
  ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
```

Verify the environment inside the container:

```bash
nvidia-smi
nvcc --version
cmake --version
python3 --version
```

The published variants run as `root`. On a Linux host, files written to a bind mount will normally
be owned by root. See [Build-time customization](#build-time-customization) if the container user
should match a host user. A writable bind mount also lets container processes modify or delete the
host files it exposes. Commit or back up important work first, and append `:ro` to the mount when
the container only needs to read it.

## Run a long-lived development container

Start the container in the background, then open the configured zsh development shell as needed:

```bash
docker run --rm -d \
  --name cuda-dev \
  --gpus all \
  -e SSH_MODE=disabled \
  -v "${PWD}:/work" \
  ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04 \
  sleep infinity

docker exec -it cuda-dev zsh
docker stop cuda-dev
```

This example is long-running but disposable: because it uses `--rm`, stopping it deletes the
container. Only data stored in bind mounts such as `/work` survives. Remove `--rm` if the stopped
container itself must be retained, but prefer rebuilding from declared inputs over accumulating
unrecorded changes inside a container.

The image's default container command remains Bash. SSH login sessions use the account's configured
zsh login shell, while `docker exec` callers explicitly select `bash`, `zsh`, or another command.

## Connect over SSH

The entrypoint starts SSH according to the runtime `SSH_MODE`. Bind the published port to a trusted
host interface and prefer key-only authentication. SSH always logs in as the image's `DEFAULT_USER`,
which is `root` in the published variants.

### Key-only authentication

Mount a non-empty public-key file as `authorized_keys`:

```bash
docker run --rm -d \
  --name cuda-dev \
  --gpus all \
  -e SSH_MODE=key-only \
  -p 127.0.0.1:2222:22 \
  -v "${HOME}/.ssh/id_ed25519.pub:/root/.ssh/authorized_keys:ro" \
  -v "${PWD}:/work" \
  ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04 \
  sleep infinity

ssh -p 2222 root@localhost
```

Replace the public-key path if necessary. Startup fails closed when the mounted `authorized_keys`
file is missing or empty. For a custom non-root image, mount the key at that user's
`~/.ssh/authorized_keys` and connect as that user instead of `root`.

### Password authentication

Password mode accepts a password only through a runtime-mounted file. No password is stored in the
image:

```bash
read -rsp 'SSH password: ' CUDA_DEV_SSH_PASSWORD && printf '\n'
printf '%s' "${CUDA_DEV_SSH_PASSWORD}" >"${HOME}/.cuda-dev-ssh-password"
unset CUDA_DEV_SSH_PASSWORD
chmod 600 "${HOME}/.cuda-dev-ssh-password"

docker run --rm -d \
  --name cuda-dev \
  --gpus all \
  -e SSH_MODE=password \
  -e SSH_PASSWORD_FILE=/run/secrets/ssh-password \
  -p 127.0.0.1:2222:22 \
  -v "${HOME}/.cuda-dev-ssh-password:/run/secrets/ssh-password:ro" \
  -v "${PWD}:/work" \
  ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04 \
  sleep infinity

ssh -p 2222 root@localhost
```

Delete `${HOME}/.cuda-dev-ssh-password` when it is no longer needed. The hidden prompt keeps the
password out of terminal output and shell history; keeping the file outside the project reduces the
risk of committing it. Without `SSH_PASSWORD_FILE`, password mode still starts sshd, but the
default root account remains locked and cannot authenticate with a password. Use
`SSH_MODE=disabled` when SSH is unnecessary.

Running the container as root and exposing password SSH gives container processes and accepted SSH
sessions full control of the container. Use a unique password, restrict the published port at the
host or network boundary, and prefer key-only or disabled mode when possible.

## Included tools and defaults

The image includes CUDA, CMake 4.3.2, Ninja, GCC, clangd, GDB, Git LFS, Python 3, pip,
virtual-environment support, OpenCV development libraries, common network tools, ripgrep, fd, and
bat.

Some apt-installed command-line tools may depend on distribution Python modules. A dedicated Python
installation step runs after those tools, reuses the distribution's default `python3`, adds matching
development headers and virtual-environment support, and bootstraps pip for that interpreter.

The developer shell adds zsh, Oh My Zsh, NvChad, NVM with the current Node.js LTS, fzf, eza,
Starship, Sheldon, Zoxide, and Witr. NvChad enables `ty` as its Python language server and starts
the pip-installed executable directly with `ty server`. The running container therefore does not
need network access to install the language server; Neovim plugins and the `ty` executable are
installed while the image is built.

| Setting | Published value | When it can be changed |
| --- | --- | --- |
| `DEFAULT_USER` | `root` | Build time |
| `DEFAULT_UID` | `1000` (unused for root) | Build time |
| `DEFAULT_GID` | `1000` (unused for root) | Build time |
| `WORKSPACE_DIR` | `/work` | Build time |
| `DEVSHELL` | `true` | Build time |
| `TZ` | `Asia/Shanghai` | Build time |
| `PACKAGE_MIRROR` | `upstream` | Build time |
| `SSH_MODE` | `password` | Build time default or runtime override |
| `SSH_PASSWORD_FILE` | unset | Runtime only |

`PACKAGE_MIRROR` accepts `upstream` or `aliyun`. `upstream` keeps the base image's package sources;
`aliyun` switches the persisted apt and pip configuration after all build-time installation has
finished. Changing the environment variable on an already built container does not rewrite those
files.

## Build-time customization

`src/cuda/image.yml` is the source of truth for published variants. For example, a custom manifest
variant can use an unprivileged user and a different workspace:

```yaml
build_args:
  DEFAULT_USER: developer
  DEFAULT_UID: 1000
  DEFAULT_GID: 1000
  WORKSPACE_DIR: /workspace
  DEVSHELL: true
mirror: upstream
runtime:
  ssh:
    mode: key-only
```

`DEFAULT_USER=root` reuses the existing root account, so `DEFAULT_UID` and `DEFAULT_GID` do not
apply. Any other valid Linux username creates that account with the declared UID and GID, makes it
the final Docker user, and grants passwordless sudo. The workspace must be an absolute path other
than `/` and is owned by `DEFAULT_USER`.

Every variant must explicitly declare `runtime.ssh.mode` as `disabled`, `key-only`, or `password`.
The manifest value chooses the default baked into the image; `docker run -e SSH_MODE=...` changes
the behavior of only that container. The planner renders the manifest policy as the image's
`SSH_MODE` build argument.

Add the complete custom variant under `variants` in `src/cuda/image.yml`, then follow the
[repository build workflow](../../README.md#develop-this-repository), replacing `plan --all` with:

```bash
images plan --family cuda --variant <variant-id> --output build-plan.json
```

In `load` mode, the resulting local image receives the floating tag
`ghcr.io/ruicx/cuda:<variant-id>` in addition to its immutable revision tag.

## Reproducibility and scope

Supported CUDA and Ubuntu combinations and their base-resolution policies are declared in
`src/cuda/image.yml`. The 12.6.3 variant pins its NVIDIA base by digest. The 12.8.2 variant uses an
explicitly tagged base with a null digest and therefore follows updates published under that tag.
Use an immutable image tag or digest when repeatability matters.

Pinning an already-published image digest makes subsequent pulls repeatable; it does not make a
fresh source rebuild byte-for-byte reproducible. Discover the digest with
`docker buildx imagetools inspect <image>` and pull it as
`ghcr.io/ruicx/cuda@sha256:<digest>`.

The developer-shell capability intentionally follows current upstream releases, branches, and
installers. This is a user-approved exception to the repository's normal reproducibility and
checksum rules. Rebuilding the same Git revision later can produce different developer-shell
contents or fail because an upstream artifact changed. Setting `DEVSHELL: false` skips this
capability.

The Python packaging capability also intentionally follows rolling upstream content. It bootstraps
pip from the current `https://bootstrap.pypa.io/get-pip.py`, installs the unpinned package set in
`src/_scripts/pip-packages.sh`, and installs uv with the current
`https://astral.sh/uv/install.sh`. At the user's request, these inputs are not version- or
checksum-pinned. Rebuilding the same Git revision can therefore select newer Python packaging tools
and libraries. Immutable image tags and digests retained in the GitHub/GHCR build history are the
rollback and audit boundary for these inputs.

CMake is downloaded from its exact HTTPS release URL. This family intentionally does not verify a
checksum for that archive. If this exception is unacceptable for your threat model, independently
audit the resulting image or replace this installation step with a checksum-verified source before
building; rebuilding the repository alone does not remove the risk.

llama.cpp is intentionally not bundled. Applications that need it should run an official
llama.cpp image as a separate service and define that orchestration in the downstream project. The
shared `llama-cpp.sh` script is an unreferenced migration capability and is not part of this
family's supported contents.
