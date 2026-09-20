# 发布指南

PR 在没有 Registry 凭据的情况下校验并构建受影响依赖闭包。合并到 `main` 后重新校验、本地
构建和测试，比较不可变标签，推送缺失产物，最后提升浮动标签。手动任务可以选择全部镜像、
一个镜像族或单个变体。

准确的变更选择、缓存、权限、幂等、并发和失败隔离规则见 [CI/CD 行为](ci-cd_zh.md)，运维恢复
方法见[故障排查](troubleshooting_zh.md)。

仓库设置要求：

- 允许 GitHub Actions 使用 `GITHUB_TOKEN` 发布包。
- 保护 `main` 并要求 PR 工作流通过。
- 工作流权限默认只读；只有发布任务声明 `packages: write`。
- 首次发布后，把预期公开的包设为 Public，并测试匿名拉取。

GitHub 会分别管理源码仓库和容器包的可见性，因此公开仓库创建的容器包仍可能是私有的。每个
包首次成功发布后，仓库所有者必须打开包设置，将可见性改为 **Public**，并确认无需 Registry
凭据即可拉取镜像。例如：

```bash
docker logout ghcr.io
docker pull ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
```

自动化永不删除不可变标签。从 `image.yml` 移除变体只会停止后续构建，不会删除已经发布的
标签。

首期有意不生成 SBOM、来源证明或漏洞门禁；以后可以在不改变 `image.yml` 和标签契约的前提下
加入这些能力。
