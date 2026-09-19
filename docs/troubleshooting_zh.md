# 故障排查

## 本地复现校验

```bash
python -m pip install -e ".[dev]"
python -m ruff check tools
python -m ruff format --check tools
python -m mypy tools/images
python -m pytest
python -m tools.images validate
bash tools/shell-tests/install-arguments.sh
```

使用 `images plan --all --output build-plan.json` 和根 README 的快速开始 Bake 命令复现镜像
构建。生成的 JSON 文件均可丢弃。

## 常见失败

- **清单路径没有匹配文件：** 修正路径或补充文件。`inputs` 必须描述真实构建输入，避免变更
  检测静默漏掉依赖。
- **报告未知依赖或 DAG 环：** 检查 `family` 和 `variant`，然后删除使目标传递依赖自身的边。
- **命名 context 无法解析：** 使 `dependencies[].context` 与 Dockerfile 的
  `FROM <context>` 名称完全一致。
- **Fork PR 无法推送或写缓存：** 这是预期行为。PR 使用只读权限本地构建，只有可信的 main
  或手动工作流会写 Registry 镜像和缓存。
- **GHCR 返回 permission denied：** 检查 Actions 包权限、仓库与包的连接，以及发布任务的
  `packages: write`。不要用长期 token 替换 `GITHUB_TOKEN`。
- **报告不可变标签冲突：** 禁止覆盖。调查为什么同一 Git SHA 产生不同 manifest digest，
  然后从修正后的提交发布。
- **不可变标签被跳过：** 远端 digest 与预检结果相同，属于安全的幂等重试。
- **发布后匿名拉取失败：** 新 GHCR 包可能是私有的。把包设为 Public，执行
  `docker logout ghcr.io` 后重试。
- **一个图失败后其他图继续：** 这是有意的失败隔离。全部独立组件尝试完成后命令返回非零。
- **SSH 启动报错：** `key-only` 要求挂载非空 `authorized_keys`；`password` 只能通过
  `SSH_PASSWORD_FILE` 为 `DEFAULT_USER` 提供可选密码。请检查该变体的 `runtime.ssh.mode` 和
  对应镜像族 README。

回滚时让消费者使用之前已知的不可变 SHA 标签或 digest。不要删除或覆盖错误的不可变标签；
保留它用于审计，并排查产生该产物的构建。
