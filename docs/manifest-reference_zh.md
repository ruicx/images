# 镜像清单参考

共享的 schema 与清单契约在 [image-kit](https://github.com/ruicx/image-kit/blob/main/docs/manifest-reference_zh.md) 维护。
本仓库从固定提交的子模块安装组件，初始化或升级后运行 `uv sync --extra dev`。
现有 `images` 命令保持可用，模块入口改为 `python -m image_kit`。

在 `uv run images validate` 之后运行 `uv run python -m tools.check_repository`，
检查本仓库的账号契约、显式 `mirror` 和 `runtime.ssh.mode` 配置以及双语文档。
组件不会要求其他使用者遵循这些仓库策略。

注册表及缓存默认值、额外重建输入和 shell 校验输入在根 `pyproject.toml` 的
`[tool.image-kit]` 中声明。GitHub Actions 保留本仓库的权限、原生 worker 矩阵、
不可变发布标签和发布顺序。
