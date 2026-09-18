# 架构

## 仓库模型

每个镜像族都是 `src/` 下的一个目录，包含 `image.yml`、一个参数化 Dockerfile、双语文档和
冒烟测试。清单是唯一事实来源，工作流中不手写镜像矩阵。

`images plan` 根据各清单的 `inputs` 把变更映射到镜像族，展开传递下游，并补齐构建所需的
上游。生成的 Bake 图把内部依赖映射为 `target:<name>` 构建上下文，因此 PR 验证使用同一提交
刚构建的基础镜像，而不是 GHCR 中的旧版本。

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

SSH 是可选运行能力。镜像默认使用锁定密码的非 root 用户并关闭 SSH；唯一允许的启用模式是
`key-only`，未挂载 authorized keys 时拒绝启动。

