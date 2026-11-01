# 🛠️ Images: 现代 GPU 与 NPU 模块化开发镜像

[![PR 镜像验证](https://github.com/ruicx/images/actions/workflows/pull-request.yml/badge.svg)](https://github.com/ruicx/images/actions/workflows/pull-request.yml)
[![镜像发布](https://github.com/ruicx/images/actions/workflows/publish.yml/badge.svg)](https://github.com/ruicx/images/actions/workflows/publish.yml)


---

## 背景与设计初衷

在多台物理工作站或云端实例上搭建稳定、高效的 GPU 与 NPU 开发环境，往往伴随着琐碎的重复劳动：

- **环境配置繁琐耗时**：每次初始化开发环境都需要反复核验显卡驱动与运行时兼容性，逐一安装 CMake、Ninja、GCC 等基础编译套件，配置 Python 虚拟环境，并耗费大量时间重新调优 Shell、编辑器及现代命令行工具。
- **官方基础镜像过于精简**：上游官方镜像通常仅包含最低运行依赖，缺乏日常开发、性能剖析与故障排查所需的调试工具。
- **散装 Dockerfile 维护成本高**：零散维护的 Dockerfile 极易随着时间推移变得臃肿杂乱，不仅难以收敛依赖，且缺乏有效的构建缓存优化与可复现性保证。

**本项目旨在消除这些重复配置开销。** 仓库提供了一组经过系统验证、持续维护且公开可用的现代开发容器镜像：涵盖 NVIDIA CUDA（基于 Ubuntu 24.04 的 12.6 与 12.8 变体）以及华为昇腾（面向鲲鹏 ARM64 + 910B，集成 CANN 9.2.0 与 TorchNPU 2.14.0）。镜像深度整合了底层编译调试工具与现代终端生产力套件，并依托基于声明式清单的容器构建与管理工具进行全生命周期维护。

> 📖 **各镜像族详细指南**：
> - 关于 SSH 远程开发、后台常驻服务、非 root 用户及运行时密钥挂载，详见 [CUDA 镜像指南](src/cuda/README_zh.md)。
> - 关于鲲鹏 + 昇腾 910B 设备挂载、驱动映射与 NPU 验证，详见 [昇腾镜像指南](src/ascend/README_zh.md)。
> - 关于昇腾 PEFT 软件包层，详见 [昇腾 PEFT 指南](src/ascend-peft/README_zh.md)。
> - English documentation is available at [README.md](README.md)。

---

## 🚀 快速上手

### 前置要求

- 与目标架构匹配的 Linux 容器运行环境：CUDA 使用 `linux/amd64`，昇腾使用 `linux/arm64`。
- **NVIDIA GPU**：宿主机安装兼容的 NVIDIA 驱动以及 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)。
- **华为昇腾 NPU**：宿主机安装昇腾驱动、固件以及 [Ascend Docker Runtime](https://www.hiascend.com/document/detail/zh/mindx-dl/latest/clusterscheduling/dlug/dlug_installation_0007.html)（或采用手动设备挂载模式）。

### 交互式运行容器

**NVIDIA CUDA (amd64)**：
将当前工作目录挂载至容器内部 `/work` 并启动交互式终端：

```bash
docker pull ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
docker run --rm -it \
  --gpus all \
  -e SSH_MODE=disabled \
  -v "${PWD}:/work" \
  ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
```

**华为昇腾 910B (arm64)**：
在使用 Ascend Docker Runtime 时，指定 NPU 设备并启动：

```bash
docker pull ghcr.io/ruicx/ascend:2.14.0-cann9.2.0-910b-ubuntu22.04-py3.12
docker run --rm -it \
  --runtime=ascend \
  -e ASCEND_VISIBLE_DEVICES=0 \
  -e SSH_MODE=disabled \
  --shm-size=8g \
  -v "${PWD}:/work" \
  ghcr.io/ruicx/ascend:2.14.0-cann9.2.0-910b-ubuntu22.04-py3.12
```
*（若宿主机未安装 Ascend Docker Runtime，可参考 [昇腾镜像指南](src/ascend/README_zh.md#宿主机要求与交互式使用) 进行手动设备节点与驱动目录映射。）*

### 验证环境与工具链

进入容器后，可执行基础命令验证硬件访问与工具链版本：

```bash
# CUDA 环境验证
nvidia-smi
nvcc --version
cmake --version
python3 --version

# 昇腾环境验证
npu-smi info
cmake --version
python3 --version
```

> [!TIP]
> **💡 贴士 1：文件权限与默认用户归属**
> CUDA 变体默认以普通用户 `luciole`（UID/GID `1000`）运行，并具备免密 `sudo` 权限；昇腾镜像默认使用 root。在 Linux 宿主机中，容器向挂载目录写入的文件使用该 UID/GID。若需与宿主机当前非 root 用户的专属 UID/GID 保持一致，可通过构建期参数 `DEFAULT_USER`、`DEFAULT_UID` 和 `DEFAULT_GID` 构建专属变体（详见 [CUDA 指南：构建期自定义](src/cuda/README_zh.md#构建期自定义)）。

> [!TIP]
> **💡 贴士 2：宿主机驱动支持上限 vs 容器工具链版本**
> `nvidia-smi` 顶部显示的 `CUDA Version` 代表宿主机当前驱动所能支持的**最高 CUDA 版本上限**，而非容器内部已安装的具体编译器版本。容器内实际生效的编译器版本请以 `nvcc --version` 输出为准。

---

## 📦 变体选型与镜像策略

| 平台与硬件环境 | 镜像标签 | 基础镜像策略 | 推荐适用场景 |
| :--- | :--- | :--- | :--- |
| **CUDA 12.8.2**<br>`linux/amd64` (Ubuntu 24.04) | `ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04` | 跟踪官方明确版本标签 | **NVIDIA GPU 推荐默认起点**。兼顾版本稳定性与官方安全更新。 |
| **CUDA 12.6.3**<br>`linux/amd64` (Ubuntu 24.04) | `ghcr.io/ruicx/cuda:12.6.3-devel-ubuntu24.04` | 跟踪明确的 NVIDIA 基础镜像标签 | 使用 CUDA 12.6.3，并接收上游在同一基础镜像标签下发布的修复。 |
| **Ascend 910B**<br>`linux/arm64` (Ubuntu 22.04) | `ghcr.io/ruicx/ascend:2.14.0-cann9.2.0-910b-ubuntu22.04-py3.12` | 跟踪明确的上游基础镜像标签 | 鲲鹏 ARM64 + 昇腾 910B 环境（集成 CANN 9.2.0、PyTorch 2.14.0 与 TorchNPU 2.14.0）。 |
| **Ascend PEFT**<br>`linux/arm64` (Ubuntu 22.04) | `ghcr.io/ruicx/ascend-peft:2.14.0-cann9.2.0-peft-910b-ubuntu22.04-py3.12` | 从同一构建图中的昇腾镜像构建 | 在昇腾 910B 开发镜像上叠加 PEFT 训练软件包。 |

### 选型说明与标签策略

1. **驱动兼容性确认**：根据具体工程需求选定 CUDA 或 CANN 版本，并对照官方文档确保宿主机驱动满足最低要求（NVIDIA 环境请参阅 [CUDA 兼容性指南](https://docs.nvidia.com/deploy/cuda-compatibility/)）。在宿主机驱动满足条件且无历史基线约束时，推荐选用 `12.8.2` 变体。
2. **便捷标签与不可变锁定**：
   - 上述表格中的短标签（如 `12.8.2-devel-ubuntu24.04`）为**便捷通道**，成功发布新构建后会自动向前滚动更新。
   - 需要复用已发布环境时，锁定不可变的 `<variant>-<12位-git-sha>-<run-id>-<attempt>` 发布标签，或通过 `docker buildx imagetools inspect <image>` 查询 manifest digest 并采用 `ghcr.io/ruicx/cuda@sha256:<digest>` 引用。相同源码重建可能生成更新的环境，历史镜像保留供回滚。
   - 📌 *注：本仓库遵循明确的版本追踪规范，不发布语义模糊的全局 `latest` 标签。*

---

## 🧰 预置工具链矩阵

镜像预置了现代系统开发与高频调试所需的完整工具链，避免手动安装的等待与版本冲突：

- ⚡ **核心编译与调试**：CUDA 编译器 (`nvcc`) 或昇腾 CANN 开发套件、GCC、CMake 4.3.2、Ninja、`clangd` 语言服务器、GDB 调试器、Git LFS。
- 🐍 **现代 Python 环境**：Python 3、pip 及内置虚拟环境（venv）支持，包含常用科学计算与深度学习基础依赖。
- 🖼️ **开发库与网络工具**：OpenCV 开发依赖、curl、wget 及基础网络诊断工具。
- 🔍 **高效现代 CLI 实用工具**：`ripgrep`（极速全文检索）、`fd`（人性化文件查找）、`bat`（语法高亮查看器）。
- ✨ **现代终端开发环境（可选）**：配置完备的 zsh、Oh My Zsh、Starship 跨平台提示符、NvChad（Neovim 预配置发行版），以及 fzf、eza、zoxide、sheldon、witr 与基于 NVM 的 Node.js LTS。

关于后台常驻服务、SSH 公钥登录及运行时机密密码挂载等高级配置，请参阅 [CUDA 镜像指南](src/cuda/README_zh.md) 与 [昇腾镜像指南](src/ascend/README_zh.md)。

---

## 🏗️ 构建机制与架构设计

除了开箱即用的预构建镜像，本项目还采用声明式清单与模块化工具链组织各个镜像族的构建与测试流程：

```yaml
# src/cuda/image.yml 变体定义示例
variants:
  - id: 12.8.2-devel-ubuntu24.04
    base:
      image: nvidia/cuda:12.8.2-devel-ubuntu24.04
      digest: null
    build_args:
      DEFAULT_USER: luciole
      DEFAULT_UID: 1000
      DEFAULT_GID: 1000
      WORKSPACE_DIR: /work
    mirror: upstream
    runtime:
      ssh:
        mode: password
    dependencies: []
    tests:
      - src/cuda/tests/smoke.sh
```

- 📄 **清单驱动变体（Manifest-driven）**：单个参数化 Dockerfile 支撑整个镜像族。新增环境变体或组合只需在 `image.yml` 中声明，无需改写 CI 工作流代码。
- 🧩 **积木式能力复用（Reusable Capabilities）**：将工具安装解耦为独立的职责脚本（如 `cmake.sh`、`python-install.sh`、`devshell.sh`），各脚本内建严格的参数校验；相邻的 `COPY` 与 `RUN` 保证最佳的 BuildKit 缓存边界。
- 🧭 **依赖感知与增量构建（Dependency-aware）**：`images plan` 根据变更输入自动分析受影响的镜像族与传递依赖，避免不必要的全量重构；内部镜像依赖始终基于同一次提交构建。
- 🔒 **透明的可复现策略**：开发镜像跟踪明确的上游基础镜像标签，每次构建检查更新；发布时先保留每个构建批次的不可变标签，再更新便捷标签。
- 🛡️ **发布前多重校验**：Schema 与语义检查自动拦截环形依赖、未声明的构建参数或遗漏的依赖；所有镜像在推送到 Registry 前，均需通过真实构建与冒烟测试验证。

详细架构设计与配置契约请参阅[架构设计](docs/architecture.md)与[清单参考手册](docs/manifest-reference.md)。

---

## 💻 本地开发与编排构建

本仓库基于 [uv](https://github.com/astral-sh/uv) 管理 Python 开发与构建工具链。在本地构建定制镜像或参与仓库开发的步骤如下：

```bash
git clone --recurse-submodules https://github.com/ruicx/images.git
cd images

# 在已有工作副本中初始化公共能力组件
git submodule update --init --recursive

# 使用 uv 安装依赖并同步开发环境
uv sync --extra dev

# 1. 校验清单合法性与格式规范
uv run images validate
uv run python -m tools.check_repository

# 2. 查看受支持变体并生成构建计划
uv run images list
uv run images plan --all --output build-plan.json

# 3. 生成 Bake 定义并在本地执行构建与冒烟测试
revision="$(git rev-parse HEAD)"
uv run images bake --plan build-plan.json --owner ruicx --repository ruicx/images --revision "$revision" --mode load --output docker-bake.generated.json
uv run images build-test --plan build-plan.json --bake docker-bake.generated.json --owner ruicx --revision "$revision"
```

---

共享安装脚本和资源来自公开的 [image-kit](https://github.com/ruicx/image-kit) 子模块，位于
`vendor/image-kit`，并固定到具体提交。组件还提供 Python 构建工具、包内 schema 和工具测试。
Dockerfile、清单、镜像测试、账号/文档策略和发布流程仍由本仓库维护。升级组件引用会重建全部镜像变体，操作方式见[开发准则](docs/development.md)。

## 📚 进阶文档与开发指引

系统设计、开发规范与运维指南：

- 📐 **架构与规范**：[架构设计](docs/architecture.md) · [清单参考手册](docs/manifest-reference.md) · [CLI 使用手册](docs/cli-reference.md)
- ⚙️ **工程与发布**：[CI/CD 机制](docs/ci-cd.md) · [开发规范指南](docs/development.md) · [发布流程说明](docs/release.md)
- 🔄 **生命周期与排错**：[版本生命周期](docs/lifecycle.md) · [常见故障排查](docs/troubleshooting.md)

> 🤖 **面向 AI 编程助手（AI Agents）与自动化工作流**：
> 本仓库严谨的工程契约、Dockerfile 分层缓存规范、参数解析标准与 Git 提交要求均详见 [AGENTS.md](AGENTS.md)。所有参与仓库代码生成的 AI Agent 均须严格遵循该规范。
