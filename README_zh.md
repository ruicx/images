# 🛠️ Images: 开发镜像合集

[![PR 镜像验证](https://github.com/ruicx/images/actions/workflows/pull-request.yml/badge.svg)](https://github.com/ruicx/images/actions/workflows/pull-request.yml)
[![镜像发布](https://github.com/ruicx/images/actions/workflows/publish.yml/badge.svg)](https://github.com/ruicx/images/actions/workflows/publish.yml)

> **专注开发，告别繁复配置**。专为现代系统编程设计的模块化开发容器镜像和管理工具。

---

## 背景与设计初衷

在多台物理机或云端实例上搭建稳定、高效的 GPU 开发环境往往伴随着琐碎的重复劳动：

- **环境配置繁琐**：每次初始化开发机都需要反复核验显卡驱动与 CUDA 运行时兼容性，逐一安装 CMake、Ninja、GCC 以及配置 Python 虚拟环境，并耗费大量时间重新调优 zsh、Neovim 及现代命令行工具；
- **官方镜像过于精简**：上游官方基础镜像通常仅提供最小运行库，缺乏基础开发排错工具；
- **定制 Dockerfile 维护成本高**：零散维护的 Dockerfile 极易随着时间推移变得臃肿杂乱，缺乏明确的依赖收敛与可复现构建保证。

**本项目旨在消除这些重复配置开销**。仓库提供了一组经过系统验证、持续维护且公开可用的现代开发容器镜像。首发镜像族聚焦 CUDA（提供 12.6 与 12.8 变体），深度整合底层编译调试与现代终端生产力工具；同时提供了一套基于声明式清单的容器构建与管理工具。

> 📖 **更多指引**：
> - 关于 SSH 远程开发、后台常驻容器及自定义用户配置，详见 [CUDA 镜像使用指南](src/cuda/README_zh.md)。
> - English documentation is available at [README.md](README.md)。

---

## 🚀 极速上手

### 前置要求

- Linux amd64 容器运行环境；
- 启用 GPU 支持需在宿主机安装兼容的 NVIDIA 显卡驱动以及 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)。

### 快速启动

以 CUDA 12.8.2 镜像为例，将当前工作目录挂载至容器内部 `/work`，并以交互模式启动：

```bash
docker pull ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
docker run --rm -it \
  --gpus all \
  -e SSH_MODE=disabled \
  -v "${PWD}:/work" \
  ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
```

启动后可运行基础命令检查 GPU 挂载与工具链版本：

```bash
nvidia-smi
nvcc --version
cmake --version
python3 --version
```

> [!TIP]
> **💡 贴士 1：文件权限与用户归属**
> 已发布的公开镜像默认以 `root` 身份运行。在 Linux 宿主机中，容器向挂载目录写入的文件在宿主机端亦归属 root。若需在宿主机侧保持非 root 用户的专属所有权，可基于构建期参数 `DEFAULT_USER` 构建定制变体（详见 [CUDA 镜像使用指南：构建期自定义](src/cuda/README_zh.md#构建期自定义)）。

> [!TIP]
> **💡 贴士 2：宿主机驱动支持上限 vs 容器工具链版本**
> `nvidia-smi` 顶部显示的 `CUDA Version` 代表宿主机当前驱动所能支持的**最高 CUDA 版本上限**，而非容器内部已安装的具体编译器版本。容器内实际生效的编译器版本请以 `nvcc --version` 输出为准。

---

## 📦 变体选型与镜像策略

| CUDA / Ubuntu 版本 | 镜像地址 | 基础镜像解析策略 | 推荐适用场景 |
| :--- | :--- | :--- | :--- |
| **CUDA 12.6.3** / Ubuntu 24.04 | `ghcr.io/ruicx/cuda:12.6.3-devel-ubuntu24.04` | 锁定 NVIDIA 基础镜像 digest | 追求严格可复现性、不希望任何上游更新带来构建漂移的项目 |
| **CUDA 12.8.2** / Ubuntu 24.04 | `ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04` | 跟踪官方明确版本标签更新 | **推荐默认起点**。兼顾版本稳定性与官方安全维护 |

### 选型说明与标签机制

1. **驱动兼容性确认**：根据具体工程需求选定 CUDA 版本，并对照 NVIDIA 官方 [CUDA 兼容性指南](https://docs.nvidia.com/deploy/cuda-compatibility/) 确保宿主机驱动满足最低要求。在宿主机驱动兼容且无遗留环境约束时，推荐选用 `12.8.2` 变体。
2. **便捷标签与不可变锁定**：
   - 上述列表中的短标签（如 `12.8.2-devel-ubuntu24.04`）为**便捷通道**，成功发布新构建后会向前滚动。
   - 在生产环境、长期固定基线或严格可复现的 CI 流水线中，建议锁定带有提交特征的不可变 `<variant>-<12位-git-sha>` 标签，或通过 `docker buildx imagetools inspect <image>` 查询 manifest digest 并采用 `ghcr.io/ruicx/cuda@sha256:<digest>` 进行明确引用。
   - 📌 *注：本仓库遵循明确的版本追踪规范，不发布语义模糊的全局 `latest` 标签。*

---

## 🧰 预置工具链矩阵

镜像预置了现代系统开发与高频调试所需的完整工具链，避免手动安装的等待与版本冲突：

- ⚡ **核心编译与调试**：CUDA 编译器 (`nvcc`)、GCC、CMake 4.3.2、Ninja、`clangd` 语言服务器、GDB 调试器、Git LFS。
- 🐍 **现代 Python 环境**：Python 3、pip 及内置虚拟环境（venv）支持。
- 🖼️ **开发库与网络工具**：OpenCV 开发依赖及基础网络诊断工具。
- 🔍 **高效现代 CLI 实用工具**：`ripgrep`（极速全文检索）、`fd`（人性化文件查找）、`bat`（语法高亮查看器）。
- ✨ **现代终端开发环境（可选）**：配置完备的 zsh、Oh My Zsh、NvChad（Neovim 预配置发行版）、Starship 跨平台提示符，以及 fzf、eza、zoxide、sheldon、witr 与基于 NVM 的 Node.js LTS。

关于后台守护容器运行、SSH 公钥登录及运行时机密密码挂载等高级配置，请参阅 [CUDA 镜像使用指南](src/cuda/README_zh.md)。

---

## 🏗️ 构建机制与设计特点

除了直接使用预构建镜像，本仓库还通过声明式清单来组织各个镜像族的构建与测试流程：

```yaml
# src/cuda/image.yml 变体定义示例
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

- 📄 **清单驱动变体（Manifest-driven）**：单个参数化 Dockerfile 支撑整个镜像族。新增环境变体或组合只需在 `image.yml` 中声明，无需改写 CI 工作流逻辑。
- 🧩 **积木式能力复用（Reusable Capabilities）**：将工具安装解耦为独立的职责脚本（如 cmake、python、devshell），各脚本内建严格的参数校验；相邻的 `COPY` 与 `RUN` 保留有效的 BuildKit 缓存边界。
- 🧭 **依赖感知与增量构建（Dependency-aware）**：`images plan` 根据变更输入自动分析受影响的镜像族与传递依赖，避免全量重构；内部镜像依赖始终基于同一次提交构建。
- 🔒 **透明的可复现策略**：外部基础镜像必须显式指定标签，并主动决定是绑定 digest 还是跟随上游；发布时优先固化不可变 revision 标签。
- 🛡️ **发布前多重校验**：Schema 与语义检查自动拦截环形依赖、未声明的构建参数或遗漏的依赖；所有镜像在推送到 Registry 前，均需通过真实构建与冒烟测试验证。

详细设计与契约约束请参阅[架构设计](docs/architecture_zh.md)与[清单参考手册](docs/manifest-reference_zh.md)。

---

## 💻 本地开发与编排构建

本仓库基于 [uv](https://github.com/astral-sh/uv) 管理 Python 开发环境。在本地构建定制镜像或参与仓库维护的步骤如下：

```bash
git clone https://github.com/ruicx/images.git
cd images

# 使用 uv 安装依赖并同步开发环境
uv sync --extra dev

# 1. 校验清单合法性与格式规范
uv run images validate

# 2. 查看受支持变体并生成构建计划
uv run images list
uv run images plan --all --output build-plan.json

# 3. 生成 Bake 定义并在本地执行构建与冒烟测试
revision="$(git rev-parse HEAD)"
uv run images bake --plan build-plan.json --owner ruicx --repository ruicx/images --revision "$revision" --mode load --output docker-bake.generated.json
uv run images build-test --plan build-plan.json --bake docker-bake.generated.json --owner ruicx --revision "$revision"
```

进阶开发与架构文档：

- 📐 [架构设计](docs/architecture_zh.md) · [清单参考手册](docs/manifest-reference_zh.md) · [CLI 使用手册](docs/cli-reference_zh.md)
- ⚙️ [CI/CD 机制](docs/ci-cd_zh.md) · [开发规范指南](docs/development_zh.md) · [发布流程说明](docs/release_zh.md)
- 🔄 [版本生命周期](docs/lifecycle_zh.md) · [常见故障排查](docs/troubleshooting_zh.md)
