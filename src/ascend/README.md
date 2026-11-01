# Ascend 910B development image

Shared installation scripts and assets are supplied by the commit-pinned `vendor/image-kit`
submodule. Run `git submodule update --init --recursive` from the repository root before
building. Image configuration and smoke tests remain in this repository.

An ARM64 development environment for Kunpeng CPUs and Ascend 910B NPUs, based on
`ascendai/torch-npu:2.14.0-cann9.2.0-910b-ubuntu22.04-py3.12`. The manifest tracks updates under
that exact tag with `digest: null`; this family builds only `linux/arm64`. See [中文说明](README_zh.md).

## Contents and defaults

The base supplies Ubuntu 22.04, CANN 9.2.0 Toolkit/910B operators/NNAL, PyTorch 2.14.0,
TorchNPU 2.14.0, and Python 3.12.15. The CPU PyTorch wheel uses TorchNPU for NPU execution.
We preserve the vendor interpreter, headers, pip, and installed Python package versions. The
distribution Python may also be installed as an apt dependency; `/usr/bin/python3` remains owned
by Ubuntu. User-facing `python` and `python3` select the vendor interpreter.

The additional development tools match the CUDA family: CMake 4.3.2, Ninja, GCC, clangd, GDB,
Git LFS, OpenCV development libraries, network tools, ripgrep, fd, bat, Python development
packages, uv, and the zsh/Oh My Zsh/NvChad/Node.js developer shell. Both families use the same
unversioned package list in `vendor/image-kit/assets/python-dev-requirements.txt`, including pip-installed uv.
Ascend uses its own `vendor/image-kit/scripts/python/ascend-pip-packages.sh` installer, passing this file through
`--requirements`. It constrains every package already supplied by the selected base; resolution
fails instead of replacing the vendor stack. CUDA uses an independent `cuda-pip-packages.sh` installer.
The effective constraints are retained at `/opt/image-python/base-constraints.txt` for inspection
and printed in build logs so resolver failures can be reproduced with the complete baseline.

The Ascend installer also installs missing vendor-tool dependencies: `plotly`, the Python `ninja`
distribution, `colorlog`, and `msguard`.
The apt `ninja-build` executable alone does not satisfy Python package metadata.
The base's `protobuf 3.20.0` is preserved. The gRPC/HTTP OpenTelemetry OTLP exporters required by
`ms-service-profiler 26.0.0` need protobuf >=5, so these exporters are not installed.
Builds and smoke tests both run `ascend-pip-check`. With user approval, it emits warnings and
permits exactly three known upstream dependency diagnostics:

- `mindstudio-kl 26.2.0` requires `numpy<=1.26.4`, but the base supplies `numpy 2.5.4`.
- `ms-service-profiler 26.0.0` is missing `opentelemetry-exporter-otlp-proto-grpc`.
- `ms-service-profiler 26.0.0` is missing `opentelemetry-exporter-otlp-proto-http`.

All vendor packages retain their original versions. All other dependency failures, changes to the
approved diagnostics, and pip execution errors remain fatal, including an installed OpenTelemetry
package incompatible with protobuf. These exceptions do not validate msKL compatibility with
NumPy 2.5.4 or the service profiler's OTLP functionality. Neither is covered by this image's tests;
resolve the corresponding dependencies before using those features.

| Setting | Manifest default |
| --- | --- |
| Platform | `linux/arm64` |
| Default user | `root` (UID/GID `0`) |
| Supplementary groups | None |
| Workspace | `/work` |
| Developer shell | Enabled; default container command is Bash, login shell is zsh |
| Time zone | `Asia/Shanghai` |
| Package mirror | `upstream` (preserves upstream base configuration) |
| SSH mode | `key-only`; supply an authorized key or set `SSH_MODE=disabled` |

The wrapper preserves the upstream CANN, Bisheng, and NNAL initialization before applying shared
SSH policy. Bash login and zsh sessions restore the vendor development environment, including
the Python path. Plain `docker exec` commands inherit the base image's environment. Device
visibility and Ascend runtime options must be set when starting the container, rather than baked
into the image.

Shell environment integration runs after the optional developer shell installation. It appends
the CANN startup hook to the installed `/etc/zsh/zshenv`, preserving the package's default
configuration and avoiding a dpkg configuration-file prompt during zsh installation. When zsh
is absent, it creates only the Bash login profile and leaves the zsh configuration file absent.

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
The container runs as root by default and can write root-owned files into bind mounts. Limit
mounted host paths to those the container needs. Do not make device nodes world-writable.

The [upstream TorchNPU example](https://hub.docker.com/r/ascendai/torch-npu) explicitly passes
`--device` and `-v` options for manual mounting. This Compose file selects `runtime: ascend`
instead. With `ASCEND_VISIBLE_DEVICES` set, Ascend Docker Runtime mounts the selected NPU device
nodes and the driver paths listed in the host's `/etc/ascend-docker-runtime.d/base.list`; those
runtime mounts are therefore absent from the Compose file. See the
[runtime mount documentation](https://www.hiascend.com/document/detail/en/mindcluster/2610/clustersched/schedulingug/docs/en/scheduling/04_usage/00_containerization/01_configuring_custom_mounted_content.md).

For a persistent container with every NPU on the host, run this Compose example from the
repository root. The command collects every `/dev/davinciN` device ID and passes the full list
to Ascend Docker Runtime; the runtime mounts the devices and driver files. An empty list makes
Compose stop before starting the container.

```bash
docker info --format '{{json .Runtimes}}'  # Confirm that ascend is registered.
mkdir -p src/ascend/secret
sudo chown 0:0 src/ascend/secret
sudo chmod 700 src/ascend/secret
export ASCEND_VISIBLE_DEVICES="$(
  find /dev -maxdepth 1 -regextype posix-extended -regex '/dev/davinci[0-9]+' \
    -printf '%f\n' | sed 's/^davinci//' | sort -n | paste -sd, -
)"
docker compose -f src/ascend/compose.yaml up -d
docker compose -f src/ascend/compose.yaml exec ascend zsh
```

After startup, verify the devices and driver tool inside the container:

```bash
docker compose -f src/ascend/compose.yaml exec ascend sh -lc \
  'ls /dev/davinci[0-9]* /dev/davinci_manager && npu-smi info'
```

The example uses the same image tag, 8 GiB shared memory, key-only SSH on host port `8101`, and a
repository bind mount at `/work`. Port `8101` listens on all host interfaces; restrict access to
trusted networks. The SSH daemon starts before a key is added, but password authentication remains
disabled. Inside the container, run `cat >> ~/.ssh/authorized_keys`, paste your public key as one
line, press Ctrl-D, and run `chmod 600 ~/.ssh/authorized_keys`. Then connect with
`ssh -p 8101 root@<host>`. The host's `src/ascend/secret/`
directory is bind-mounted to `/root/.ssh`, so authorized keys survive container recreation;
its contents are ignored by Git. Root ownership and mode 700 let the container user write
keys while satisfying SSH file-permission checks. This opt-in behavior requires an image built
with the updated entrypoint. The host must have Ascend Docker Runtime registered as `ascend`. See the
[Ascend Docker Runtime device selection guide](https://www.hiascend.com/document/detail/en/mindcluster/2600/clustersched/schedulingug/docs/en/scheduling/usage/containerization/04_usage_on_the_containerd_client.md)
for supported device ID formats.

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
as root (UID/GID 0); use a custom manifest for a non-root account if necessary. Mount read-only
project inputs with `:ro` when appropriate. Stopping a container started with `--rm` deletes it.

For key authentication, use the same NPU options and add:

```bash
-e SSH_MODE=key-only \
-p 127.0.0.1:2222:22 \
-v "${HOME}/.ssh/id_ed25519.pub:/root/.ssh/authorized_keys:ro"
```

Start with `sleep infinity` and connect using `ssh -p 2222 root@localhost`. A missing or empty
authorized key causes startup to fail unless the Compose example's explicit opt-in is used. For
password authentication, create a password file outside
the project and mount it at runtime:

```bash
read -rsp 'SSH password: ' ASCEND_DEV_PASSWORD && printf '\n'
printf '%s' "${ASCEND_DEV_PASSWORD}" > "${HOME}/.ascend-dev-ssh-password"
unset ASCEND_DEV_PASSWORD
chmod 600 "${HOME}/.ascend-dev-ssh-password"
```

Add `-e SSH_MODE=password -e SSH_PASSWORD_FILE=/run/secrets/ssh-password` and
`-v "${HOME}/.ascend-dev-ssh-password:/run/secrets/ssh-password:ro"`, publish the port on a trusted
interface, and connect as `root`. Delete the password file when no longer needed. Passwords
are never built into the image. **Root SSH grants full container control to anyone with the key
or password, and root can modify writable host bind mounts.** Restrict the published port to
trusted networks; prefer key authentication or leave SSH disabled. The manifest omits UID/GID
because root reuses the base image's existing account.

## Build and reproducibility

`image.yml` is the source of truth. Follow the [repository development guide](../../docs/development.md)
on a native ARM64 Docker builder and select:

```bash
python -m image_kit plan --family ascend --platform linux/arm64 --output build-plan.json
```

Standard CI builds and runs `tests/smoke.sh` on a native ARM64 runner without NPU hardware. This
checks tools, Python metadata and venv, shell environments, and SSH policy; it does not import
TorchNPU or claim hardware compatibility. Run `tests/npu.sh` separately on the intended server.

The base follows its exact upstream tag, and generated Bake targets check for updates with
`pull: true`. The ARM64 CMake archive is verified against its manifest SHA-256. At the
user's request, added Python packages follow the unversioned shared package list, while constraints
retain the vendor stack's installed versions. This approved rolling Python-package policy means
rebuilds can select different added packages and transitive dependencies. Apt packages are also
not locked. Matching the CUDA development experience also reuses its
user-approved rolling interactive developer-shell exception: current upstream releases, branches,
installers, and plugins may change without version or checksum pins. This exception applies only
to developer-shell tooling, not CANN, PyTorch, TorchNPU, or application dependencies. Rebuilding
the same commit is therefore not guaranteed to reproduce identical bytes. Set `DEVSHELL: false`
to omit the interactive shell installation. CI retains each build, including reruns of the same
commit, as `<variant>-<short-sha>-<run-id>-<attempt>`. These immutable tags and image digests identify
the actual built artifacts for rollback; no global `latest` tag is published.
