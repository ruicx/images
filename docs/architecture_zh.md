# 架构

## 仓库模型

每个镜像族都是 `src/` 下的一个目录，包含 `image.yml`、一个参数化 Dockerfile、双语文档和
冒烟测试。清单是唯一事实来源，工作流中不手写镜像矩阵。

这种分层让发行意图保持声明式：清单描述变体和依赖边，Dockerfile 描述构建顺序，共享脚本
提供能力级安装，Python 工具把这些输入转换为一个经过校验的执行图。完整契约见
[清单参考](manifest-reference_zh.md)。

`images plan` 根据各清单的 `inputs` 把变更映射到镜像族，展开传递下游，并补齐构建所需的
上游。生成的 Bake 图把内部依赖映射为 `target:<name>` 构建上下文，因此 PR 验证使用同一提交
刚构建的基础镜像，而不是 GHCR 中的旧版本。

互不连接的依赖图会形成独立的 Bake 组件组。CI 会尝试全部组件后再汇总结果，因此一个镜像族
失败不会掩盖无关镜像族的有效结果。准确的变更影响规则见 [CI/CD 行为](ci-cd_zh.md)。

## 标签生命周期

不可变标签为 `<variant>-<short-sha>`。发布前，CI 计算本地产物 digest 并检查 GHCR：标签不
存在则推送，digest 相同则跳过，冲突则终止发布。所有不可变标签就绪后，CI 才更新浮动的
`<variant>` 标签。

要求可复现的使用者必须固定不可变标签或 digest。浮动变体标签仅为便利通道，每次成功合并后
都可能变化。

## 信任边界

PR 只有仓库只读权限，不登录 GHCR，也不推送镜像或缓存。主分支发布任务仅获得
`contents: read` 和 `packages: write`。构建秘密只能通过 BuildKit secret mount 使用，禁止经由
`ARG`、`ENV` 或 `COPY` 传递。

SSH 是显式运行策略，支持 `disabled`、`key-only` 和 `password`。`key-only` 在未挂载
authorized keys 时拒绝启动。选择 `password` 的镜像族可以允许 root 登录，但密码必须来自
运行时挂载文件，禁止写入镜像层、清单、构建参数或环境变量。未提供运行时密码文件时，root
账户保持锁定。
