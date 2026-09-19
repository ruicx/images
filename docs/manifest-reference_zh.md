# 镜像清单参考

`src/<family>/image.yml` 是镜像族的版本化发行契约。路径和 glob 模式均相对于仓库根目录，
未定义字段会被拒绝。

## 镜像族字段

| 字段 | 类型 | 契约 |
| --- | --- | --- |
| `schema_version` | 整数 | 必须为 `1`；未来不兼容格式需增加版本。 |
| `name` | 字符串 | 小写 kebab-case，并且必须等于 `<family>`。 |
| `description` | 字符串 | 非空、面向用户的镜像族简介。 |
| `dockerfile` | 路径 | 仓库内已存在的 Dockerfile。 |
| `context` | 路径 | 仓库内已存在的构建上下文。 |
| `platforms` | 列表 | 首期必须且只能是 `linux/amd64`。 |
| `inputs` | 列表 | 已存在的路径或 glob；变更时重建该族全部变体。 |
| `runtime.ssh.default` | 枚举 | `disabled`、`key-only` 或 `password`；变体可覆盖。 |
| `runtime.ssh.login_user` | 枚举 | `default` 跟随 `DEFAULT_USER`；`root` 显式选择 root；变体可覆盖。 |
| `publish` | 布尔值 | 是否允许从 `main` 发布选中的变体。 |
| `variants` | 列表 | 一个或多个变体定义。 |

## 变体字段

| 字段 | 类型 | 契约 |
| --- | --- | --- |
| `id` | 字符串 | 浮动标签名；小写分段可用 `.`、`_`、`-`，禁止 `latest`。 |
| `base.image` | 字符串 | 带明确版本标签的外部镜像；禁止 `latest` 和 `master`。 |
| `base.digest` | 字符串 | 必填的 `sha256:` digest，后接 64 位小写十六进制。 |
| `build_args` | 映射 | 传给对应 Dockerfile `ARG` 声明的任意非秘密标量值；疑似秘密的键会被拒绝。 |
| `mirror` | 枚举 | `upstream` 或显式选择的 `aliyun`。 |
| `runtime.ssh.default` | 枚举 | 可选，用于覆盖镜像族默认值；密码模式必须在镜像族文档中说明运行时秘密处理。 |
| `runtime.ssh.login_user` | 枚举 | 可选的 `default` 或 `root` 登录账号选择覆盖。 |
| `dependencies` | 列表 | 以 BuildKit 命名上下文暴露的内部目标。 |
| `tests` | 列表 | 一个或多个已存在的仓库相对冒烟测试脚本。 |

每个依赖包含 `family`、`variant` 和 `context`。同一消费变体中的 context 名不能重复，且
必须对应 Dockerfile 的命名上下文：

```yaml
dependencies:
  - context: internal_base
    family: base
    variant: ubuntu-24.04
```

```dockerfile
FROM internal_base AS development
```

Buildx Bake 会把 `internal_base` 解析为 `target:<generated-base-target>`，因此 PR 的内部依赖
不会读取 Registry 中的旧镜像。

`build_args` 是镜像专用构建选项的扩展点，不需要修改 Python 解析器。Bake 生成前，值会统一
转换为字符串。因此接收布尔选项的脚本必须自行归一化，例如 YAML 的 `true` 可能变为 `True`；
`${NAME}` 这类环境变量表达式不会被插值，而会保留为字面字符串。schema 仍禁止在
`build_args` 之外添加未知字段。

## 完整结构

```yaml
schema_version: 1
name: example
description: Example development image
dockerfile: src/example/Dockerfile
context: .
platforms: [linux/amd64]
inputs:
  - src/example/**
  - src/_scripts/example-tool.sh
runtime:
  ssh:
    default: disabled
    login_user: default
publish: true
variants:
  - id: ubuntu-24.04
    base:
      image: ubuntu:24.04
      digest: sha256:<64位小写十六进制字符>
    build_args:
      DEFAULT_USER: developer
      DEFAULT_UID: 1000
      DEFAULT_GID: 1000
      TOOL_VERSION: "1.2.3"
    mirror: upstream
    dependencies: []
    tests:
      - src/example/tests/smoke.sh
```

JSON Schema 负责结构校验；`images validate` 还会校验路径、目录与名称一致性、重复变体、
疑似秘密的构建参数、`DEFAULT_USER` 契约、依赖目标、重复 context、冒烟测试、DAG 环以及双语
文档。`DEFAULT_USER=root` 时必须省略 `DEFAULT_UID` 和 `DEFAULT_GID`；其他合法 Linux 用户名
必须同时提供这两个数值字段。
