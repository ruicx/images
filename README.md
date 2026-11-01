# 🛠️ Images: Modular GPU & NPU Development Environments

[![Pull request images](https://github.com/ruicx/images/actions/workflows/pull-request.yml/badge.svg)](https://github.com/ruicx/images/actions/workflows/pull-request.yml)
[![Publish images](https://github.com/ruicx/images/actions/workflows/publish.yml/badge.svg)](https://github.com/ruicx/images/actions/workflows/publish.yml)

> **Focus on development, eliminate setup overhead.** Modular, production-ready development container images and declarative build tooling designed for modern systems programming.

---

## Background & Motivation

Configuring consistent, high-performance GPU and NPU development environments across bare-metal workstations and cloud instances often incurs substantial repetitive overhead:

- **Tedious toolchain setup**: Initializing an environment requires repeatedly verifying GPU/NPU driver compatibility, installing toolchains (CMake, Ninja, GCC, Clang), configuring Python environments, and fine-tuning shells, editors, and CLI utilities.
- **Minimal official base images**: Upstream container images typically include only minimal runtime libraries, lacking essential development, diagnostic, and debugging tools.
- **High maintenance cost of ad-hoc Dockerfiles**: Unstructured Dockerfiles quickly become bloated and fragile, offering little dependency convergence, poor layer caching, and no reproducibility guarantees.

**This project eliminates this recurring overhead.** It provides continuously maintained, publicly accessible development container images covering both NVIDIA CUDA (12.6 and 12.8 variants on x86_64) and Huawei Ascend (Kunpeng ARM64 + 910B with CANN 9.2.0 and TorchNPU 2.14.0). Each image integrates low-level compilers, profilers, and debuggers with a modern terminal productivity suite, all managed by a declarative build system.

> 📖 **Family Guides**:
> - For SSH remote development, long-running containers, non-root users, and credential mounts, see the [CUDA Image Guide](src/cuda/README.md).
> - For Kunpeng + Ascend 910B setup, device mounting, and NPU verification, see the [Ascend Image Guide](src/ascend/README.md).
> - For the Ascend PEFT package layer, see the [Ascend PEFT Guide](src/ascend-peft/README.md).
> - 中文文档请参阅 [README_zh.md](README_zh.md)。

---

## 🚀 Quick Start

### Prerequisites

- A Linux container runtime matching the target architecture: `linux/amd64` for CUDA, `linux/arm64` for Ascend.
- **NVIDIA GPU**: Host NVIDIA GPU driver and the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).
- **Huawei Ascend NPU**: Host Ascend driver, firmware, and [Ascend Docker Runtime](https://www.hiascend.com/document/detail/zh/mindx-dl/latest/clusterscheduling/dlug/dlug_installation_0007.html) (or direct device node mapping).

### Running an Interactive Container

**NVIDIA CUDA (amd64)**:
Mount the current working directory to `/work` inside the container and start an interactive shell:

```bash
docker pull ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
docker run --rm -it \
  --gpus all \
  -e SSH_MODE=disabled \
  -v "${PWD}:/work" \
  ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
```

**Huawei Ascend 910B (arm64)**:
With Ascend Docker Runtime installed, allocate an NPU and launch:

```bash
docker pull ghcr.io/ruicx/ascend:2.14.0-cann9.2.0-910b-ubuntu22.04-py3.12
docker run --rm -it \
  --runtime=ascend \
  -e ASCEND_VISIBLE_DEVICES=0 \
  -e SSH_MODE=disabled \
  --shm-size=8g \
  -v "${PWD}:/work" \
  ghcr.io/ruicx/ascend:2.14.0-cann9.2.0-910b-ubuntu22.04-py3.12
```
*(If Ascend Docker Runtime is unavailable, see the [Ascend Image Guide](src/ascend/README.md#host-requirements-and-interactive-use) for manual device and driver mounting.)*

### Verifying the Environment

After launching the container, verify hardware access and toolchain availability:

```bash
# Verify NVIDIA CUDA environment
nvidia-smi
nvcc --version
cmake --version
python3 --version

# Verify Huawei Ascend environment
npu-smi info
cmake --version
python3 --version
```

> [!TIP]
> **💡 Tip 1: File Ownership & Permissions**
> Pre-built variants run by default as non-root user `luciole` (UID/GID `1000`) with passwordless `sudo`. Files created inside bind mounts inherit this UID/GID on Linux hosts. To match your host user's UID/GID, build a customized variant with `DEFAULT_USER`, `DEFAULT_UID`, and `DEFAULT_GID` build arguments (see [CUDA Guide: Customization](src/cuda/README.md#build-time-customization)).

> [!TIP]
> **💡 Tip 2: Host Driver Capability vs Container Toolkit Version**
> The `CUDA Version` displayed at the top of `nvidia-smi` indicates the **maximum CUDA version supported by the host driver**, rather than the toolkit version inside the container. The active compiler version is determined by `nvcc --version`.

---

## 📦 Variant Selection & Image Policies

| Platform & Hardware | Image Tag | Base Image Policy | Recommended For |
| :--- | :--- | :--- | :--- |
| **CUDA 12.8.2**<br>`linux/amd64` (Ubuntu 24.04) | `ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04` | Tracks upstream exact tag | **Recommended starting point for NVIDIA GPUs.** Balances version stability with official updates. |
| **CUDA 12.6.3**<br>`linux/amd64` (Ubuntu 24.04) | `ghcr.io/ruicx/cuda:12.6.3-devel-ubuntu24.04` | Tracks the exact NVIDIA base tag | Projects using CUDA 12.6.3 with upstream fixes published under the same base tag. |
| **Ascend 910B**<br>`linux/arm64` (Ubuntu 22.04) | `ghcr.io/ruicx/ascend:2.14.0-cann9.2.0-910b-ubuntu22.04-py3.12` | Tracks the exact upstream base tag | Kunpeng ARM64 + Ascend 910B environments (CANN 9.2.0, PyTorch 2.14.0, TorchNPU 2.14.0). |
| **Ascend PEFT**<br>`linux/arm64` (Ubuntu 22.04) | `ghcr.io/ruicx/ascend-peft:2.14.0-cann9.2.0-peft-910b-ubuntu22.04-py3.12` | Built from the Ascend image in the same build graph | PEFT training packages layered over the Ascend 910B development image. |

### Selection Notes & Tagging Policy

1. **Driver Compatibility**: Select the CUDA/CANN version required by your project, then check host driver compatibility. For NVIDIA GPUs, consult the [CUDA Compatibility Guide](https://docs.nvidia.com/deploy/cuda-compatibility/). When host drivers meet requirements and no legacy constraints exist, `12.8.2` is the recommended default.
2. **Convenience Tags vs Immutable Pins**:
   - The short tags shown above (e.g., `12.8.2-devel-ubuntu24.04`) serve as **convenience channels** that automatically track newly published builds.
   - To reuse a published environment, lock to its immutable `<variant>-<12-character-git-sha>-<run-id>-<attempt>` release tag, or pull directly by manifest digest (`ghcr.io/ruicx/cuda@sha256:<digest>`), inspectable via `docker buildx imagetools inspect <image>`. Rebuilding the same source may produce a newer environment; historical images remain available for rollback.
   - 📌 *Note: This repository follows strict versioning discipline and deliberately does not publish a global `latest` tag.*

---

## 🧰 Pre-installed Toolchain Matrix

Images come pre-equipped with a comprehensive toolchain tailored for modern systems programming and development workflows:

- ⚡ **Core Compilers & Debugging**: CUDA Compiler (`nvcc`) or Ascend CANN development suite, GCC, CMake 4.3.2, Ninja, `clangd` language server, GDB debugger, Git LFS.
- 🐍 **Modern Python Stack**: Python 3, pip, and built-in virtual environment (`venv`) support with scientific and deep learning dependencies.
- 🖼️ **Development Libraries & Networking**: OpenCV development headers and libraries, curl, wget, and standard network diagnostic utilities.
- 🔍 **Modern CLI Productivity**: `ripgrep` (blazing-fast search), `fd` (ergonomic file finder), and `bat` (syntax-highlighted file viewer).
- ✨ **Developer Shell Environment (Optional)**: Pre-configured zsh, Oh My Zsh, Starship prompt, NvChad (modern Neovim distribution), fzf, eza, zoxide, sheldon, witr, and NVM with Node.js LTS.

For background service mode, SSH public key authentication, and runtime password secret mounts, see the [CUDA Image Guide](src/cuda/README.md) and [Ascend Image Guide](src/ascend/README.md).

---

## 🏗️ Build Design & Architecture

In addition to providing pre-built images, this repository organizes build and test workflows using declarative manifests:

```yaml
# Example variant definition from src/cuda/image.yml
variants:
  - id: 12.8.2-devel-ubuntu24.04
    base:
      image: nvidia/cuda:12.8.2-devel-ubuntu24.04
      digest: null
    build_args:
      DEFAULT_USER: luciole
      DEFAULT_UID: 1000
      DEFAULT_GID: 1000
      WORKSPACE_DIR: /work
    mirror: upstream
    runtime:
      ssh:
        mode: password
    dependencies: []
    tests:
      - src/cuda/tests/smoke.sh
```

- 📄 **Manifest-driven Variants**: A single parameterized Dockerfile powers an entire image family. Adding a new combination requires only a declaration in `image.yml`, without modifying CI workflow code.
- 🧩 **Reusable Capabilities**: Tool installations are decoupled into modular capability scripts (e.g., `cmake.sh`, `python-install.sh`, `devshell.sh`) with strict argument validation; adjacent `COPY` and `RUN` steps preserve optimal BuildKit caching boundaries.
- 🧭 **Dependency-aware Incremental Builds**: `images plan` analyzes changed inputs to rebuild only affected image families and their transitive dependents; internal dependencies are always built from the same commit.
- 🔒 **Transparent Reproducibility**: Development images track exact upstream base tags and check for updates on each build; publications retain immutable tags for each build batch before updating convenience tags.
- 🛡️ **Pre-flight Validation**: Schema and semantic linters guard against circular dependencies, undeclared build arguments, or leaked secrets; all images must pass full builds and smoke tests before deployment.

Learn more about the design and schema in [Architecture](docs/architecture.md) and the [Manifest Reference](docs/manifest-reference.md).

---

## 💻 Local Development & Orchestration

The repository uses [uv](https://github.com/astral-sh/uv) to manage its Python tooling environment. Steps for local building, testing, or contributing:

```bash
git clone https://github.com/ruicx/images.git
cd images

# Install dependencies and sync development environment
uv sync --extra dev

# 1. Validate manifest schemas and repository consistency
uv run images validate

# 2. Inspect supported variants and generate build plan
uv run images list
uv run images plan --all --output build-plan.json

# 3. Generate Bake definitions and run local build & smoke tests
revision="$(git rev-parse HEAD)"
uv run images bake --plan build-plan.json --owner ruicx --repository ruicx/images --revision "$revision" --mode load --output docker-bake.generated.json
uv run images build-test --plan build-plan.json --bake docker-bake.generated.json --owner ruicx --revision "$revision"
```

---

## 📚 Documentation & Guidelines

Comprehensive architectural and operational documentation:

- 📐 **Architecture & Schemas**: [Architecture](docs/architecture.md) · [Manifest Reference](docs/manifest-reference.md) · [CLI Reference](docs/cli-reference.md)
- ⚙️ **Engineering Guides**: [CI/CD Behavior](docs/ci-cd.md) · [Development Guide](docs/development.md) · [Release Guide](docs/release.md)
- 🔄 **Policies & Troubleshooting**: [Lifecycle Policy](docs/lifecycle.md) · [Troubleshooting](docs/troubleshooting.md)

> 🤖 **For AI Coding Assistants & Automated Workflows**:
> Detailed operational instructions, architectural invariants, Dockerfile caching rules, argument conventions, and commit formatting standards are specified in [AGENTS.md](AGENTS.md). All AI coding agents operating in this repository must strictly adhere to `AGENTS.md`.
