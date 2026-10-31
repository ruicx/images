# Ascend 910B development image

An ARM64 development environment for Kunpeng CPUs and Ascend 910B NPUs, based on
`ascendai/torch-npu:2.14.0-cann9.2.0-910b-ubuntu22.04-py3.12`. The manifest pins the upstream
multi-platform index digest; this family builds only `linux/arm64`. See [中文说明](README_zh.md).

## Contents and defaults

The base supplies Ubuntu 22.04, CANN 9.2.0 Toolkit/910B operators/NNAL, PyTorch 2.14.0,
TorchNPU 2.14.0, and Python 3.12.15. The CPU PyTorch wheel uses TorchNPU for NPU execution.
We preserve the vendor interpreter, headers, pip, and installed Python package versions. The
distribution Python may also be installed as an apt dependency; `/usr/bin/python3` remains owned
by Ubuntu. User-facing `python` and `python3` select the vendor interpreter.

The additional development tools match the CUDA family: CMake 4.3.2, Ninja, GCC, clangd, GDB,
Git LFS, OpenCV development libraries, network tools, ripgrep, fd, bat, Python development
packages, uv, and the zsh/Oh My Zsh/NvChad/Node.js developer shell. Both families use the same
unversioned package list in `src/_scripts/pip-packages.sh`, including pip-installed uv. Ascend
passes `--preserve-existing --profile ascend`: build-time constraints preserve every package
already supplied by the pinned base; resolution fails instead of replacing the vendor stack.
The effective constraints are retained at `/opt/image-python/base-constraints.txt` for inspection.

The Ascend profile also installs missing vendor-tool dependencies: `plotly`, the Python `ninja`
distribution, `colorlog`, `msguard`, and the gRPC/HTTP OpenTelemetry OTLP exporters (>=1.33.1,<2.0.0).
The apt `ninja-build` executable alone does not satisfy Python package metadata.
Builds and smoke tests both run `ascend-pip-check`. With user approval, this checker emits a warning
and permits exactly the pinned base's `mindstudio-kl 26.2.0` requirement `numpy<=1.26.4` with
installed `numpy 2.5.4`. Both vendor packages are retained at their original versions. All other
dependency failures, changed versions, and pip execution errors remain fatal. This exception does
not validate msKL compatibility with NumPy 2.5.4; msKL kernel invocation and auto-tuning are not
covered by this image's tests. Resolve that compatibility before using msKL.

| Setting | Manifest default |
| --- | --- |
| Platform | `linux/arm64` |
| Default user | `luciole` (UID/GID `1000`, passwordless sudo) |
| Workspace | `/work` |
| Developer shell | Enabled; default container command is Bash, login shell is zsh |
| Time zone | `Asia/Shanghai` |
| Package mirror | `upstream` (preserves upstream base configuration) |
| SSH mode | `password`; account locked until a password file is supplied |

The wrapper preserves the upstream CANN, Bisheng, and NNAL initialization before applying shared
SSH policy. Bash login and zsh sessions restore the vendor development environment, including
the Python path. Plain `docker exec` commands inherit the base image's environment. Device
visibility and Ascend runtime options must be set when starting the container, rather than baked
into the image.

## Host requirements and interactive use

Use an ARM64 Linux host with compatible Ascend 910B firmware and drivers. Check the actual host
versions against the [CANN compatibility information](https://www.hiascend.com/developer/download/compatibility)
before starting workloads. The image does not install or upgrade host drivers or firmware.

With Ascend Docker Runtime installed and registered as `ascend`, expose one NPU and disable SSH:

```bash
IMAGE=ghcr.io/ruicx/ascend:2.14.0-cann9.2.0-910b-ubuntu22.04-py3.12
docker run --rm -it \
  --runtime=ascend \
  -e ASCEND_VISIBLE_DEVICES=0 \
  -e SSH_MODE=disabled \
  --shm-size=8g \
  -v "${PWD}:/work" \
  "$IMAGE"
```

Adjust shared memory for the workload. For several NPUs, use an explicit list such as
`ASCEND_VISIBLE_DEVICES=0,1`; device count and topology belong to the server configuration.
For the non-root user, configure host device access groups or matching supplemental GIDs as
required by the installed runtime and driver. Do not make device nodes world-writable.

If Ascend Docker Runtime is unavailable, a single-device manual mounting example is:

```bash
docker run --rm -it \
  --device /dev/davinci0 \
  --device /dev/davinci_manager \
  --device /dev/devmm_svm \
  --device /dev/hisi_hdc \
  -v /usr/local/dcmi:/usr/local/dcmi:ro \
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi:ro \
  -v /usr/local/Ascend/driver:/usr/local/Ascend/driver:ro \
  -v /etc/ascend_install.info:/etc/ascend_install.info:ro \
  -e SSH_MODE=disabled \
  --shm-size=8g \
  -v "${PWD}:/work" \
  "$IMAGE"
```

Check these paths on the host first; adapt them to its driver layout and device permissions.
Mount the driver rather than the host's entire `/usr/local/Ascend`, which would hide the
container's CANN installation. See the [upstream image guide](https://hub.docker.com/r/ascendai/torch-npu).

Verify `npu-smi info`, `python3 --version`, and `cmake --version` in the container. To run the
hardware test from this repository, redirect it into a container with the same device/runtime
options, for example:

```bash
docker run --rm -i --runtime=ascend \
  -e ASCEND_VISIBLE_DEVICES=0 -e SSH_MODE=disabled \
  "$IMAGE" bash -s < src/ascend/tests/npu.sh
```

This checks device visibility and a small matrix multiplication against a CPU result. Multi-card
HCCL communication and application performance still require workload-specific server tests.

## Persistent containers and SSH

Replace the interactive flags with `-d --name ascend-dev` and append `sleep infinity` for a
background container, then use `docker exec -it ascend-dev zsh`. Bind-mounted files are written
as UID/GID 1000; match the host user through a custom manifest if necessary. Mount read-only
project inputs with `:ro` when appropriate. Stopping a container started with `--rm` deletes it.

For key authentication, use the same NPU options and add:

```bash
-e SSH_MODE=key-only \
-p 127.0.0.1:2222:22 \
-v "${HOME}/.ssh/id_ed25519.pub:/home/luciole/.ssh/authorized_keys:ro"
```

Start with `sleep infinity` and connect using `ssh -p 2222 luciole@localhost`. A missing or empty
authorized key causes startup to fail. For password authentication, create a password file outside
the project and mount it at runtime:

```bash
read -rsp 'SSH password: ' ASCEND_DEV_PASSWORD && printf '\n'
printf '%s' "${ASCEND_DEV_PASSWORD}" > "${HOME}/.ascend-dev-ssh-password"
unset ASCEND_DEV_PASSWORD
chmod 600 "${HOME}/.ascend-dev-ssh-password"
```

Add `-e SSH_MODE=password -e SSH_PASSWORD_FILE=/run/secrets/ssh-password` and
`-v "${HOME}/.ascend-dev-ssh-password:/run/secrets/ssh-password:ro"`, publish the port on a trusted
interface, and connect as `luciole`. Delete the password file when no longer needed. Passwords
are never built into the image. Passwordless sudo gives this account full container control;
password SSH exposes that control to anyone possessing the credential. Prefer key authentication
or disable SSH. Enabling root requires a custom manifest and carries the same control and
bind-mount risks; omit UID/GID when selecting root.

## Build and reproducibility

`image.yml` is the source of truth. Follow the [repository development guide](../../docs/development.md)
on a native ARM64 Docker builder and select:

```bash
python -m tools.images plan --family ascend --platform linux/arm64 --output build-plan.json
```

Standard CI builds and runs `tests/smoke.sh` on a native ARM64 runner without NPU hardware. This
checks tools, Python metadata and venv, shell environments, and SSH policy; it does not import
TorchNPU or claim hardware compatibility. Run `tests/npu.sh` separately on the intended server.

The base is pinned, and the ARM64 CMake archive is verified against its manifest SHA-256. At the
user's request, added Python packages follow the unversioned shared package list, while constraints
retain the vendor stack's installed versions. This approved rolling Python-package policy means
rebuilds can select different added packages and transitive dependencies. Apt packages are also
not locked. Matching the CUDA development experience also reuses its
user-approved rolling interactive developer-shell exception: current upstream releases, branches,
installers, and plugins may change without version or checksum pins. This exception applies only
to developer-shell tooling, not CANN, PyTorch, TorchNPU, or application dependencies. Rebuilding
the same commit is therefore not guaranteed to reproduce identical bytes. Set `DEVSHELL: false`
to omit the interactive shell installation. Published immutable revision tags and digests identify
the actual built artifacts; no global `latest` tag is published.
