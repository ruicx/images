# Development images

[![Pull request images](https://github.com/ruicx/images/actions/workflows/pull-request.yml/badge.svg)](https://github.com/ruicx/images/actions/workflows/pull-request.yml)
[![Publish images](https://github.com/ruicx/images/actions/workflows/publish.yml/badge.svg)](https://github.com/ruicx/images/actions/workflows/publish.yml)

Ready-to-use development environments published as public container images. The first image family
provides a CUDA toolchain, common C/C++ and Python development tools, and an optional SSH service.

Use this page to select and start an image. See the [CUDA image guide](src/cuda/README.md) for SSH,
background-container, customization, and security instructions. The Chinese version is in
[README_zh.md](README_zh.md).

## Use an image

You need a Linux amd64 container environment. GPU access also requires a compatible NVIDIA driver
and the NVIDIA Container Toolkit on the host.

Pull the CUDA 12.8.2 image and open a Bash shell with the current directory mounted at `/work`:

```bash
docker pull ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
docker run --rm -it \
  --gpus all \
  -e SSH_MODE=disabled \
  -v "${PWD}:/work" \
  ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
```

Inside the container, verify the GPU and toolchain:

```bash
nvidia-smi
nvcc --version
cmake --version
python3 --version
```

The published variants run as `root`. On a Linux host, files created in a bind-mounted directory
will therefore normally be owned by root. Build a custom variant with a non-root `DEFAULT_USER` if
host-side ownership matters.

## Choose a variant

| CUDA / Ubuntu | Image | Base-image policy |
| --- | --- | --- |
| CUDA 12.6.3 / Ubuntu 24.04 | `ghcr.io/ruicx/cuda:12.6.3-devel-ubuntu24.04` | Pinned NVIDIA base digest |
| CUDA 12.8.2 / Ubuntu 24.04 | `ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04` | Tracks updates to the exact NVIDIA tag |

Use the CUDA version required by your project, then confirm that the host driver supports it in
NVIDIA's [CUDA compatibility guide](https://docs.nvidia.com/deploy/cuda-compatibility/). The
`CUDA Version` shown by `nvidia-smi` is the newest CUDA version supported by the driver, not the
toolkit installed in this image. If the project has no version constraint and the driver is
compatible, start with the 12.8.2 variant.

Each published build also receives an immutable `<variant>-<12-character-git-sha>` tag. Use that
tag or an image digest for a reproducible environment. The shorter variant tags above are
convenience channels and can move after a successful publication. There is no global `latest` tag.
Use `docker buildx imagetools inspect <image>` to discover the published manifest digest, then pull
it with `docker pull ghcr.io/ruicx/cuda@sha256:<digest>`.

## What's included

The CUDA family includes the CUDA compiler, CMake 4.3.2, Ninja, GCC, clangd, GDB, Git LFS, Python
3, pip, virtual-environment support, OpenCV development libraries, network tools, and command-line
utilities including ripgrep, fd, and bat. Its optional developer shell adds zsh, NvChad, NVM with
the current Node.js LTS, fzf, eza, Starship, Sheldon, Zoxide, Witr, and Atuin.

See the [CUDA image guide](src/cuda/README.md) for the complete defaults, known reproducibility
exceptions, and examples for:

- running a long-lived development container;
- connecting with an SSH key or a runtime-mounted password;
- changing the user, workspace, package mirror, or developer shell at build time.

## Design highlights

The build matrix is declarative rather than hard-coded in CI. Each image family has one
`src/<family>/image.yml` release contract that declares its variants, exact base tags and digest
policy, build arguments, internal dependencies, runtime policy, shared inputs, and smoke tests. For
example:

```yaml
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

- **Manifest-driven variants:** one parameterized Dockerfile serves every variant in a family;
  adding a supported combination normally changes YAML rather than CI workflow code.
- **Reusable capabilities:** shared installation scripts own one capability and its validation,
  while Dockerfiles declare selection and order. Adjacent `COPY` and `RUN` steps preserve useful
  BuildKit cache boundaries.
- **Dependency-aware builds:** `images plan` maps changed manifest inputs to affected families,
  includes required ancestors, and expands transitive dependents. Internal dependencies are built
  from the same commit instead of pulled from an older registry image.
- **Explicit reproducibility:** every external base uses an exact tag and must deliberately pin a
  digest or declare `null` to track that tag. Publications create immutable revision tags before
  moving convenient variant tags.
- **Validation before publication:** schema and semantic checks reject invalid manifests, dependency
  cycles, secret-like build arguments, and missing inputs; selected images are then built and smoke
  tested before publication.

See [Architecture](docs/architecture.md) and the [Manifest reference](docs/manifest-reference.md)
for the full design and schema.

## Develop this repository

The repository source is at [ruicx/images](https://github.com/ruicx/images).

To validate and build every variant locally:

```bash
git clone https://github.com/ruicx/images.git
cd images
python -m pip install -e ".[dev]"
images validate
images list
images plan --all --output build-plan.json
revision="$(git rev-parse HEAD)"
images bake --plan build-plan.json --owner ruicx --repository ruicx/images --revision "$revision" --mode load --output docker-bake.generated.json
images build-test --plan build-plan.json --bake docker-bake.generated.json --owner ruicx --revision "$revision"
```

Before adding or changing an image, read [Architecture](docs/architecture.md),
[Manifest reference](docs/manifest-reference.md), [CLI reference](docs/cli-reference.md),
[CI/CD behavior](docs/ci-cd.md), [Development guide](docs/development.md),
[Release guide](docs/release.md), [Lifecycle policy](docs/lifecycle.md), and
[Troubleshooting](docs/troubleshooting.md).
