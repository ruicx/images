# Development Images

[![Pull request images](https://github.com/ruicx/images/actions/workflows/pull-request.yml/badge.svg)](https://github.com/ruicx/images/actions/workflows/pull-request.yml)
[![Publish images](https://github.com/ruicx/images/actions/workflows/publish.yml/badge.svg)](https://github.com/ruicx/images/actions/workflows/publish.yml)

This repository builds public development images with GitHub Actions. Each
`src/<family>/image.yml` is the release contract for one independently published image family.
Variants share a Dockerfile and differ through explicit base-image policies and build arguments.
Each base uses an exact tag and either a digest pin for reproducibility or an explicit null digest
to follow updates published under that tag.

The source repository is public at [ruicx/images](https://github.com/ruicx/images). The initial
family is `cuda`, published as `ghcr.io/ruicx/cuda`. A build produces an immutable
`<variant>-<12-character-git-sha>` tag and then promotes `<variant>` to the same digest. There is no
global `latest` tag.

## Available variants

| Family | Variant | Floating image reference |
| --- | --- | --- |
| `cuda` | `12.6.3-devel-ubuntu24.04` | `ghcr.io/ruicx/cuda:12.6.3-devel-ubuntu24.04` |
| `cuda` | `12.8.1-devel-ubuntu24.04` | `ghcr.io/ruicx/cuda:12.8.1-devel-ubuntu24.04` |

For reproducible environments, replace the floating variant tag with an immutable
`<variant>-<12-character-git-sha>` tag or a digest.

## Quick start

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

Read [Architecture](docs/architecture.md), [Manifest reference](docs/manifest-reference.md),
[CLI reference](docs/cli-reference.md), [CI/CD behavior](docs/ci-cd.md),
[Development guide](docs/development.md), [Release guide](docs/release.md),
[Lifecycle policy](docs/lifecycle.md), and [Troubleshooting](docs/troubleshooting.md) before adding
an image. The Chinese version is in [README_zh.md](README_zh.md).

## GHCR visibility

The GitHub source repository is public, but GitHub manages repository and container-package
visibility separately. A newly created GHCR package may still be private. After the first
successful publication, an owner must open the package settings, change visibility to **Public**,
and verify an anonymous pull:

```bash
docker logout ghcr.io
docker pull ghcr.io/ruicx/cuda:12.8.1-devel-ubuntu24.04
```

Automation never deletes immutable tags. Removing a variant from its manifest only stops future
builds.
