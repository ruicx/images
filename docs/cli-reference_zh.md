# CLI 参考

安装后使用 `images ...`，也可使用 `python -m tools.images ...`。全局 `--root` 用于选择仓库
根目录，默认是当前目录。命令成功返回 `0`；仓库、Docker 或子进程错误返回 `2`，并在标准错误
输出可操作的信息。

| 命令 | 用途 | 重要选项或输出 |
| --- | --- | --- |
| `validate` | 校验清单、路径、DAG 和双语文档。 | 不生成输出文件。 |
| `list` | 列出镜像族、变体和直接依赖。 | 人类可读的标准输出。 |
| `files --kind shell` | 列出 ShellCheck/shfmt 输入。 | 仓库相对路径。 |
| `plan` | 计算发布目标和所需上游。 | 使用 `--base/--head`、`--all` 或 `--family [--variant]`；可选 `--output`。 |
| `bake` | 从计划生成 JSON Bake 定义。 | 需要 owner、revision、mode 和 plan；模式为 `load`、`preflight`、`publish`。 |
| `test` | 对本地加载的镜像运行清单声明的冒烟测试。 | 需要 plan、owner、revision。 |
| `build-test` | 构建并测试每个独立图组件。 | 需要 plan 和 Bake 文件；汇总所有失败组件。 |
| `guard-tags` | 比较本地 metadata 与 GHCR 不可变标签。 | 输出过滤后的发布计划；冲突即失败。 |
| `promote` | 把每个浮动变体标签移动到不可变版本。 | 仅在不可变发布成功后执行。 |

`plan` 输出 schema version `1`、变更路径和拓扑排序后的目标。目标的 `publish` 字段用于区分
受影响产物和仅为满足 DAG 而构建的上游。生成的计划和 Bake 文件是临时 CI 产物，禁止手工编辑。

`bake --mode load` 把镜像载入本地 Docker，并附加浮动标签供冒烟测试使用；`preflight` 构建但
不推送，同时产生 digest metadata；`publish` 只推送计划中仍为 `publish: true` 的目标，并写入
按变体隔离的主分支缓存。

以 `images <command> --help` 作为权威选项列表。命令名、计划 schema 和退出码含义均属于需
保持兼容的接口。
