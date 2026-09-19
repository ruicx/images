# 开发镜像

[![PR 镜像验证](https://github.com/ruicx/images/actions/workflows/pull-request.yml/badge.svg)](https://github.com/ruicx/images/actions/workflows/pull-request.yml)
[![镜像发布](https://github.com/ruicx/images/actions/workflows/publish.yml/badge.svg)](https://github.com/ruicx/images/actions/workflows/publish.yml)

本仓库通过 GitHub Actions 构建公开的开发镜像。每个
`src/<family>/image.yml` 都是一个独立发布镜像族的发行契约。同一镜像族的变体共享
Dockerfile，通过显式基础镜像策略和构建参数表达差异。每个基础镜像都使用明确版本标签，
并选择用 digest 获得可复现构建，或显式使用空 digest 跟随该标签的更新。

源码仓库已公开发布在 [ruicx/images](https://github.com/ruicx/images)。首个镜像族为 `cuda`，
发布地址是 `ghcr.io/ruicx/cuda`。每次构建先产生不可变的
`<variant>-<12位-git-sha>` 标签，再把 `<variant>` 提升到同一 digest。本仓库不发布全局
`latest` 标签。

## 可用变体

| 镜像族 | 变体 | 浮动镜像引用 |
| --- | --- | --- |
| `cuda` | `12.6.3-devel-ubuntu24.04` | `ghcr.io/ruicx/cuda:12.6.3-devel-ubuntu24.04` |
| `cuda` | `12.8.1-devel-ubuntu24.04` | `ghcr.io/ruicx/cuda:12.8.1-devel-ubuntu24.04` |

需要可复现环境时，请把浮动变体标签替换为不可变的
`<variant>-<12位-git-sha>` 标签或 digest。

## 快速开始

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

新增镜像前请阅读[架构](docs/architecture_zh.md)、[清单参考](docs/manifest-reference_zh.md)、
[CLI 参考](docs/cli-reference_zh.md)、[CI/CD 行为](docs/ci-cd_zh.md)、
[开发准则](docs/development_zh.md)、[发布指南](docs/release_zh.md)、
[生命周期](docs/lifecycle_zh.md)和[故障排查](docs/troubleshooting_zh.md)。英文入口见
[README.md](README.md)。

## GHCR 可见性

GitHub 源码仓库已经公开，但 GitHub 会分别管理仓库和容器包的可见性。新创建的 GHCR 包仍
可能是私有的。第一次成功发布后，仓库所有者需要在包设置中将可见性改为 **Public**，并验证匿名拉取：

```bash
docker logout ghcr.io
docker pull ghcr.io/ruicx/cuda:12.8.1-devel-ubuntu24.04
```

自动化永不删除不可变标签。从清单移除变体只会停止后续构建。
