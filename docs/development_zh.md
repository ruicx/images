# 开发准则

## 新增镜像族

1. 参考 `src/cuda` 的结构创建 `src/<family>`，不要复制 CUDA 专用值。
2. 添加通过 schema 校验的 `image.yml`；清单名称必须和目录名称一致。
3. 外部基础镜像必须固定精确标签和 `sha256` digest。
4. 在 `inputs` 声明每个共享脚本或资产，在 `dependencies` 声明每个内部基础镜像。
5. 添加镜像族双语文档，并为每个变体提供至少一个冒烟测试脚本。
6. 运行 `images validate`、Ruff、mypy、pytest、ShellCheck、shfmt 和本地 Bake 构建。

## 代码规则

- 代码、标识符、注释和 Conventional Commit 信息使用英文。
- Shell 脚本使用能力名称、`#!/bin/bash`、`set -euo pipefail`、变量引用、架构检查、确定性的
  临时目录清理和 apt lists 清理。
- Python 使用类型标注并通过 Ruff、mypy、pytest；面向用户的错误需指出镜像族、变体和字段。
- Dockerfile 使用 BuildKit syntax、显式非交互安装、单一清理层、非 root 最终用户，并由 Bake
  提供 OCI 标签。
- 禁止 `latest`、`master`、浮动 LTS 安装器、未校验的二进制下载、内置密码、root SSH 以及
  通过构建参数传递秘密。
- 默认使用 Ubuntu/PyPI 上游源。阿里云只能作为清单中显式的构建期选择，禁止运行时探测切换。

## 文档规则

英文文件是规范源。修改根指南或镜像族 README 时，必须在同一个 PR 更新对应 `_zh` 文件。
用户可见行为变化必须更新受影响镜像族的 README。移除变体不代表允许删除已发布标签。

