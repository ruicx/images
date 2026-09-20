# 开发镜像

[![PR 镜像验证](https://github.com/ruicx/images/actions/workflows/pull-request.yml/badge.svg)](https://github.com/ruicx/images/actions/workflows/pull-request.yml)
[![镜像发布](https://github.com/ruicx/images/actions/workflows/publish.yml/badge.svg)](https://github.com/ruicx/images/actions/workflows/publish.yml)

开箱即用的公开开发环境容器镜像。首个镜像族提供 CUDA 工具链、常用 C/C++ 与 Python
开发工具，以及可选的 SSH 服务。

本页帮助你选择并启动镜像。SSH、后台容器、自定义构建和安全说明请参阅
[CUDA 镜像使用指南](src/cuda/README_zh.md)。英文入口见 [README.md](README.md)。

## 使用镜像

你需要 Linux amd64 容器环境。使用 GPU 时，宿主机还需要兼容的 NVIDIA 驱动和 NVIDIA
Container Toolkit。

拉取 CUDA 12.8.2 镜像，把当前目录挂载到 `/work`，并进入 Bash：

```bash
docker pull ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
docker run --rm -it \
  --gpus all \
  -e SSH_MODE=disabled \
  -v "${PWD}:/work" \
  ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
```

进入容器后验证 GPU 和工具链：

```bash
nvidia-smi
nvcc --version
cmake --version
python3 --version
```

已发布的变体默认以 `root` 运行。在 Linux 宿主机上，容器写入绑定挂载目录的文件通常也会归
root 所有。如果需要保持宿主机侧的文件所有权，请使用非 root 的 `DEFAULT_USER` 构建自定义
变体。

## 选择变体

| CUDA / Ubuntu | 镜像 | 基础镜像策略 |
| --- | --- | --- |
| CUDA 12.6.3 / Ubuntu 24.04 | `ghcr.io/ruicx/cuda:12.6.3-devel-ubuntu24.04` | 固定 NVIDIA 基础镜像 digest |
| CUDA 12.8.2 / Ubuntu 24.04 | `ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04` | 跟随该 NVIDIA 明确版本标签的更新 |

请先按项目要求选择 CUDA 版本，再通过 NVIDIA 的
[CUDA 兼容性指南](https://docs.nvidia.com/deploy/cuda-compatibility/)确认宿主机驱动是否支持。
`nvidia-smi` 显示的 `CUDA Version` 是驱动能够支持的最高 CUDA 版本，不是镜像中已安装的
工具链版本。如果项目没有版本约束且驱动兼容，可以从 12.8.2 变体开始。

每次发布还会产生不可变的 `<variant>-<12位-git-sha>` 标签。需要可复现环境时，请使用该
标签或镜像 digest。上表中的短变体标签是便捷通道，成功发布后可能移动。本仓库不发布全局
`latest` 标签。
使用 `docker buildx imagetools inspect <image>` 可以查看已发布的 manifest digest，然后通过
`docker pull ghcr.io/ruicx/cuda@sha256:<digest>` 固定拉取。

## 镜像内容

CUDA 镜像族包含 CUDA 编译器、CMake 4.3.2、Ninja、GCC、clangd、GDB、Git LFS、Python
3、pip、虚拟环境支持、OpenCV 开发库、网络工具，以及 ripgrep、fd、bat 等命令行工具。
可选开发 shell 还提供 zsh、NvChad、使用当前 Node.js LTS 的 NVM、fzf、eza、Starship、
Sheldon、Zoxide、Witr 和 Atuin。

[CUDA 镜像使用指南](src/cuda/README_zh.md)还说明了完整默认值、已知的可复现性例外，以及
以下场景：

- 运行长期驻留的开发容器；
- 使用 SSH 公钥或运行时挂载的密码连接；
- 在构建期更改用户、工作目录、软件源或开发 shell。

## 设计特点

构建矩阵通过声明式清单管理，而不是硬编码在 CI 中。每个镜像族都有一个
`src/<family>/image.yml` 发行契约，用来声明变体、基础镜像明确标签及 digest 策略、构建参数、
内部依赖、运行策略、共享输入和冒烟测试。例如：

```yaml
variants:
  - id: 12.8.2-devel-ubuntu24.04
    base:
      image: nvidia/cuda:12.8.2-devel-ubuntu24.04
      digest: null
    build_args:
      DEFAULT_USER: root
      WORKSPACE_DIR: /work
    mirror: upstream
    runtime:
      ssh:
        mode: password
    dependencies: []
    tests:
      - src/cuda/tests/smoke.sh
```

- **清单驱动变体：** 一个参数化 Dockerfile 服务同一镜像族的所有变体；新增受支持组合通常只需
  修改 YAML，不需要改写 CI 工作流。
- **可复用能力：** 共享安装脚本各自负责一种能力及其参数校验，Dockerfile 只声明能力选择和
  执行顺序。相邻的 `COPY` 与 `RUN` 保留有效的 BuildKit 缓存边界。
- **依赖感知构建：** `images plan` 根据清单输入把变更映射到受影响镜像族，补齐所需上游并展开
  传递下游。内部依赖使用同一提交构建，而不是拉取 Registry 中的旧镜像。
- **显式可复现策略：** 每个外部基础镜像都使用明确标签，并且必须主动选择固定 digest，或声明
  `null` 来跟随该标签。发布时先生成不可变 revision 标签，再移动便捷的变体标签。
- **发布前校验：** Schema 和语义校验会拒绝无效清单、依赖环、疑似秘密的构建参数和缺失输入；
  选中的镜像还必须通过构建与冒烟测试才能发布。

完整设计和字段约束见[架构](docs/architecture_zh.md)与
[清单参考](docs/manifest-reference_zh.md)。

## 开发本仓库

源码位于 [ruicx/images](https://github.com/ruicx/images)。

在本地校验并构建所有变体：

```bash
git clone https://github.com/ruicx/images.git
cd images
python -m pip install -e ".[dev]"
images validate
images list
images plan --all --output build-plan.json
revision="$(git rev-parse HEAD)"
images bake --plan build-plan.json --owner ruicx --repository ruicx/images --revision "$revision" --mode load --output docker-bake.generated.json
images build-test --plan build-plan.json --bake docker-bake.generated.json --owner ruicx --revision "$revision"
```

新增或修改镜像前，请阅读[架构](docs/architecture_zh.md)、
[清单参考](docs/manifest-reference_zh.md)、[CLI 参考](docs/cli-reference_zh.md)、
[CI/CD 行为](docs/ci-cd_zh.md)、[开发准则](docs/development_zh.md)、
[发布指南](docs/release_zh.md)、[生命周期](docs/lifecycle_zh.md)和
[故障排查](docs/troubleshooting_zh.md)。
