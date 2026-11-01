# 开发准则

## 公共组件检出与升级

使用 `git clone --recurse-submodules https://github.com/ruicx/images.git` 克隆，或在已有工作副本
中运行 `git submodule update --init --recursive`，然后再校验和构建。公共脚本及资源位于
`vendor/image-kit`，它是 [ruicx/image-kit](https://github.com/ruicx/image-kit) 的子模块，
不要将其复制回 `src/`。

公共行为的修改先在 image-kit 中提交并推送。消费经过审阅的组件提交时，显式获取并检出：

```bash
git -C vendor/image-kit fetch origin
git -C vendor/image-kit checkout <reviewed-component-commit>
uv sync --extra dev
uv run images validate
uv run python -m tools.check_repository
uv run ruff check .
uv run pytest
bash vendor/image-kit/tests/install-arguments.sh
bash vendor/image-kit/tests/ascend-pip-check.sh
git add vendor/image-kit
```

发布前需完成原生镜像构建和冒烟测试。组件引用与消费端修改一起提交，且组件提交必须已在
上游可获取。升级引用会重建全部变体；回滚时恢复旧引用，再运行 `git submodule update --init`。
CI 禁止使用 `git submodule update --remote`。镜像定义、镜像专用依赖、冒烟测试、账号/文档
检查和发布策略仍留在本仓库。组件负责 Python 工具、包内 schema 和工具测试，不再保留第二份
本地构建工具。

## 新增镜像族

1. 参考 `src/cuda` 的结构创建 `src/<family>`，不要复制 CUDA 专用值。
2. 添加通过 schema 校验的 `image.yml`；清单名称必须和目录名称一致。
3. 每个外部基础镜像都必须使用明确标签并提供 `digest` 键。开发镜像使用显式 `null` 跟随
   该标签下的更新；需要固定基础镜像时使用 `sha256`。
4. 在 `inputs` 声明每个共享脚本或资产，在 `dependencies` 声明每个内部基础镜像。
5. 添加镜像族双语文档，并为每个变体提供至少一个冒烟测试脚本。
6. 运行 `images validate`、`python -m tools.check_repository`、Ruff、ty、pytest、
   ShellCheck、shfmt 和本地 Bake 构建。

## 代码规则

- 代码、标识符、注释和 Conventional Commit 信息使用英文。
- Shell 脚本使用能力名称、`#!/bin/bash`、`set -euo pipefail`、变量引用、架构检查、确定性的
  临时目录清理和 apt lists 清理。构建期配置统一使用 GNU `getopt` 长选项并提供
  `-h`/`--help`；环境变量只用于容器运行期配置。
- Python 函数和方法必须声明入参与返回值 type hint。公共模块、类、函数、方法和非平凡测试
  helper 使用英文 NumPy 风格 docstring；注释解释意图或约束，不复述代码。Python 必须通过
  Ruff、ty、pytest；面向用户的错误需指出镜像族、变体和字段。
- Dockerfile 使用固定的 BuildKit syntax 和显式非交互安装。每个可以独立变化的能力采用相邻
  的 `COPY + RUN`；不要一次复制无关脚本，以免合并它们的缓存边界。先满足依赖顺序，再优先
  放置稳定或昂贵的能力，把便宜或经常变化的能力放在后面。每次软件安装及其 apt lists 清理
  必须保留在同一个 `RUN`。
- 能力脚本负责选项校验和值分支。Dockerfile 只通过具名选项传递 `ARG` 并声明顺序，不重复
  root 处理、工作目录所有权或镜像源选择等条件。
- 镜像默认采用非 root 最终用户，并由 Bake 提供 OCI 标签。镜像族只有在双语 README 说明
  运维与凭据风险后，才可显式选择 root 最终用户。
- 每个变体都必须显式声明 `runtime.ssh.mode`，且 SSH 始终使用该变体的 `DEFAULT_USER`。该策略
  不放入 `build_args`，以保留明确的 schema 校验和安全审查入口。
- 禁止 `latest`、`master`、浮动 LTS 安装器、未固定版本的二进制下载、内置密码以及通过构建参数
  传递秘密。镜像族只有在凭据由运行时挂载文件提供，且双语 README 说明风险、启动步骤和更安全
  模式时，才可显式启用密码/root SSH。
- 下载的二进制压缩包通常需要 checksum 校验。经用户批准的例外必须保留精确版本和 HTTPS
  地址，并记录在镜像族的双语 README 中。
- 只有在镜像族双语 README 记录用户批准的可复现性与供应链例外后，滚动更新的开发 shell
  能力才可跟随上游当前 release、分支和安装器；该例外必须限定于交互式工具。
- 软件安装期间默认使用 Ubuntu/PyPI 上游源。清单的 `mirror` 只在安装结束后最终化：
  `upstream` 保持基础镜像源，`aliyun` 重写最终保留的 apt/pip 配置；禁止运行时探测切换。

## 文档规则

英文文件是规范源。修改根指南或镜像族 README 时，必须在同一个 PR 更新对应 `_zh` 文件。
用户可见行为变化必须更新受影响镜像族的 README。移除变体不代表允许删除已发布标签。
`images validate` 会强制校验所需的双语指南集合。兼容规则见[生命周期](lifecycle_zh.md)。
