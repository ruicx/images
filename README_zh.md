# 开发镜像

本仓库通过 GitHub Actions 构建公开、可复现的开发镜像。每个
`src/<family>/image.yml` 都是一个独立发布镜像族的发行契约。同一镜像族的变体共享
Dockerfile，通过固定的基础镜像和显式构建参数表达差异。

首个镜像族为 `cuda`，发布地址是 `ghcr.io/<owner>/cuda`。每次构建先产生不可变的
`<variant>-<12位-git-sha>` 标签，再把 `<variant>` 提升到同一 digest。本仓库不发布全局
`latest` 标签。

## 快速开始

```bash
python -m pip install -e ".[dev]"
images validate
images list
images plan --all --output build-plan.json
images bake --plan build-plan.json --owner example --revision 0123456789abcdef0123456789abcdef01234567 --mode load --output docker-bake.generated.json
images build-test --plan build-plan.json --bake docker-bake.generated.json --owner example --revision 0123456789abcdef0123456789abcdef01234567
```

新增镜像前请阅读[架构](docs/architecture_zh.md)、[清单参考](docs/manifest-reference_zh.md)、
[CLI 参考](docs/cli-reference_zh.md)、[CI/CD 行为](docs/ci-cd_zh.md)、
[开发准则](docs/development_zh.md)、[发布指南](docs/release_zh.md)、
[生命周期](docs/lifecycle_zh.md)和[故障排查](docs/troubleshooting_zh.md)。英文入口见
[README.md](README.md)。

## 公开 GHCR 初始化

GitHub 首次创建的容器包默认为私有。第一次成功发布后，仓库所有者需要在包设置中将
可见性改为 **Public**，确认包已连接到本仓库，并验证匿名拉取：

```bash
docker logout ghcr.io
docker pull ghcr.io/<owner>/cuda:<variant>
```

自动化永不删除不可变标签。从清单移除变体只会停止后续构建。
