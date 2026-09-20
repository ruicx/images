# 🛠️ Images: Development Image Collection

[![Pull request images](https://github.com/ruicx/images/actions/workflows/pull-request.yml/badge.svg)](https://github.com/ruicx/images/actions/workflows/pull-request.yml)
[![Publish images](https://github.com/ruicx/images/actions/workflows/publish.yml/badge.svg)](https://github.com/ruicx/images/actions/workflows/publish.yml)

> **Focus on development, eliminate setup overhead.** Modular development container images and tooling designed for modern systems programming.

---

## Background & Motivation

Setting up consistent, high-performance GPU development environments across physical machines and cloud instances frequently involves repetitive manual effort:

- **Tedious toolchain setup**: Initializing an environment requires repeatedly verifying GPU driver and CUDA compatibility, installing CMake, Ninja, GCC, configuring Python virtual environments, and spending substantial time tuning shells, editors, and CLI utilities;
- **Minimal upstream bases**: Official container bases provide only runtime essentials, lacking common development, diagnostic, and troubleshooting tools;
- **High maintenance cost of ad-hoc Dockerfiles**: Unstructured Dockerfiles easily become bloated and brittle over time, offering little dependency convergence, caching optimization, or reproducibility guarantees.

**This project eliminates this recurring overhead.** It provides continuously maintained, publicly accessible development container images. The initial family focuses on CUDA (providing 12.6 and 12.8 variants), integrating low-level compilers and debuggers with modern terminal productivity tools, backed by a declarative container build and management tooling suite.

> 📖 **Additional Guides**:
> - For SSH remote development, long-running containers, non-root users, and runtime credentials, see the [CUDA Image Guide](src/cuda/README.md).
> - 中文文档请参阅 [README_zh.md](README_zh.md)。

---

## 🚀 Quick Start

### Prerequisites

- A Linux amd64 container runtime;
- GPU acceleration requires a compatible host NVIDIA GPU driver and the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

### Quick Start

Taking the CUDA 12.8.2 image as an example, mount the current working directory to `/work` inside the container and start an interactive shell:

```bash
docker pull ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
docker run --rm -it \
  --gpus all \
  -e SSH_MODE=disabled \
  -v "${PWD}:/work" \
  ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
```

After starting, verify GPU access and toolchain availability:

```bash
nvidia-smi
nvcc --version
cmake --version
python3 --version
```

> [!TIP]
> **💡 Tip 1: File Ownership & Permissions**
> Published images run as `root` by default. On Linux hosts, files created inside bind mounts will be owned by root on the host side. When matching host non-root UID/GID is required, custom variants can specify `DEFAULT_USER` at build time (see [CUDA Image Guide: Build-time Customization](src/cuda/README.md#build-time-customization)).

> [!TIP]
> **💡 Tip 2: Host Driver Capability vs Container Toolkit Version**
> The `CUDA Version` reported by `nvidia-smi` indicates the **maximum CUDA version supported by the host driver**, rather than the toolkit version installed in the container. The active compiler version is determined by `nvcc --version`.

---

## 📦 Variant Selection & Image Policies

| CUDA / Ubuntu | Image | Base-Image Policy | Recommended For |
| :--- | :--- | :--- | :--- |
| **CUDA 12.6.3** / Ubuntu 24.04 | `ghcr.io/ruicx/cuda:12.6.3-devel-ubuntu24.04` | Pinned NVIDIA base digest | Projects requiring byte-level reproducible builds without upstream drift |
| **CUDA 12.8.2** / Ubuntu 24.04 | `ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04` | Tracks upstream exact tag updates | **Recommended starting point.** Balances version stability with official security updates |

### Selection Notes & Tagging Policy
1. **Driver Compatibility**: Select the CUDA version required by the target project, then consult NVIDIA's [CUDA Compatibility Guide](https://docs.nvidia.com/deploy/cuda-compatibility/) to ensure host driver compatibility. When the driver is compatible and no legacy constraints exist, `12.8.2` is the recommended default.
2. **Convenience Tags vs Immutable Pins**:
   - The short tags shown above (e.g., `12.8.2-devel-ubuntu24.04`) serve as **convenience channels** that move forward whenever an updated build is published.
   - For mission-critical CI or reproducible environments where **zero drift** is required, lock to the immutable `<variant>-<12-character-git-sha>` tag produced with each release, or pull directly by manifest digest (`ghcr.io/ruicx/cuda@sha256:<digest>`), inspectable via `docker buildx imagetools inspect <image>`.
   - 📌 *Note: This repository adheres to strict versioning principles and deliberately does not publish a global `latest` tag.*

---

## 🧰 Pre-installed Toolchain Matrix

Images come pre-equipped with a comprehensive toolchain for modern systems programming and development workflows:

- ⚡ **Core Compilers & Debugging**: CUDA Compiler (`nvcc`), GCC, CMake 4.3.2, Ninja, `clangd` language server, GDB debugger, Git LFS.
- 🐍 **Modern Python Stack**: Python 3, pip, and built-in virtual environment (`venv`) support.
- 🖼️ **Development Libraries & Networking**: OpenCV development headers/libraries and network diagnostic utilities.
- 🔍 **Modern Productivity CLI**: `ripgrep` (blazing-fast search), `fd` (ergonomic file finder), and `bat` (syntax-highlighted file viewer).
- ✨ **Developer Shell Environment (Optional)**: Pre-configured zsh, Oh My Zsh, NvChad (modern Neovim distribution), Starship prompt, plus fzf, eza, zoxide, atuin, sheldon, witr, and NVM with Node.js LTS.

For background service mode, SSH public key authentication, and runtime password secret mounts, see the [CUDA Image Guide](src/cuda/README.md).

---

## 🏗️ Build Design & Key Characteristics

In addition to providing pre-built images, this repository organizes the build and test workflows using declarative manifests:

```yaml
# Example variant definition from src/cuda/image.yml
variants:
  - id: 12.8.2-devel-ubuntu24.04
    base:
      image: nvidia/cuda:12.8.2-devel-ubuntu24.04
      digest: null
    build_args:
      DEFAULT_USER: root
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
- 🧩 **Reusable Capabilities**: Tool installations are decoupled into modular capability scripts (e.g., cmake, python, devshell) with strict argument validation; adjacent `COPY` and `RUN` steps preserve optimal BuildKit caching boundaries.
- 🧭 **Dependency-aware Incremental Builds**: `images plan` analyzes changed inputs to rebuild only affected image families and their transitive dependents; internal dependencies are always built from the same commit.
- 🔒 **Transparent Reproducibility**: External bases must specify an exact tag and declare whether they pin a digest or track upstream; publications seal immutable revision tags before updating convenience tags.
- 🛡️ **Pre-flight Validation**: Schema and semantic linters guard against circular dependencies, undeclared build arguments, or leaked secrets; all images must pass full builds and smoke tests before deployment.

Learn more about the design and schema in [Architecture](docs/architecture.md) and the [Manifest Reference](docs/manifest-reference.md).

---

## 💻 Local Development & Orchestration

The repository uses [uv](https://github.com/astral-sh/uv) to manage its Python environment. Steps for local building, testing, or contributing:

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

Architecture and technical reference documentation:

- 📐 [Architecture](docs/architecture.md) · [Manifest Reference](docs/manifest-reference.md) · [CLI Reference](docs/cli-reference.md)
- ⚙️ [CI/CD Behavior](docs/ci-cd.md) · [Development Guide](docs/development.md) · [Release Guide](docs/release.md)
- 🔄 [Lifecycle Policy](docs/lifecycle.md) · [Troubleshooting](docs/troubleshooting.md)
