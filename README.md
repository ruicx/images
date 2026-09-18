# Development Images

This repository builds public, reproducible development images with GitHub Actions. Each
`src/<family>/image.yml` is the release contract for one independently published image family.
Variants share a Dockerfile and differ through pinned base images and explicit build arguments.

The initial family is `cuda`, published as `ghcr.io/<owner>/cuda`. A build produces an immutable
`<variant>-<12-character-git-sha>` tag and then promotes `<variant>` to the same digest. There is no
global `latest` tag.

## Quick start

```bash
python -m pip install -e ".[dev]"
images validate
images list
images plan --all --output build-plan.json
images bake --plan build-plan.json --owner example --revision 0123456789abcdef0123456789abcdef01234567 --mode load --output docker-bake.generated.json
images build-test --plan build-plan.json --bake docker-bake.generated.json --owner example --revision 0123456789abcdef0123456789abcdef01234567
```

Read [Architecture](docs/architecture.md), [Manifest reference](docs/manifest-reference.md),
[CLI reference](docs/cli-reference.md), [CI/CD behavior](docs/ci-cd.md),
[Development guide](docs/development.md), [Release guide](docs/release.md),
[Lifecycle policy](docs/lifecycle.md), and [Troubleshooting](docs/troubleshooting.md) before adding
an image. The Chinese version is in [README_zh.md](README_zh.md).

## Public GHCR bootstrap

GitHub initially creates a container package as private. After the first successful publication,
an owner must open the package settings, change visibility to **Public**, confirm the repository
link, and verify an anonymous pull:

```bash
docker logout ghcr.io
docker pull ghcr.io/<owner>/cuda:<variant>
```

Automation never deletes immutable tags. Removing a variant from its manifest only stops future
builds.
