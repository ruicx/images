# CUDA 开发镜像

本镜像族基于固定 digest 的 NVIDIA CUDA 镜像，为 Linux amd64 参数化构建开发环境。支持的
CUDA/Ubuntu 组合以 `image.yml` 为准。镜像包含 CUDA 编译器、固定版本的 CMake
4.3.2、Ninja、GCC、clangd、GDB、Git LFS、Python 3、pip、虚拟环境支持、OpenCV 开发库、
支持 CUDA 的预编译 llama.cpp、常用网络工具，以及 ripgrep、fd、bat 等现代命令行工具。

llama.cpp 使用官方 GitHub `b11046` Ubuntu x64 CUDA 12.8 release 资产：
`https://github.com/ggml-org/llama.cpp/releases/download/b11046/llama-b11046-bin-ubuntu-cuda-12.8-x64.tar.gz`。
本镜像族对这个精确版本和 HTTPS URL 采用用户批准的 checksum 例外，因此接受同名 release
资产被替换的供应链风险。压缩包解压到 `/opt/llama.cpp`，其中的 `llama-*` 可执行文件链接到
`/usr/local/bin`，无需修改 `PATH`。本镜像族已经提供 CUDA 12 运行库，因此有意不安装上游
单独发布的 CUDA runtime 压缩包。升级时必须同时更新 `LLAMA_CPP_VERSION` 和
`LLAMA_CPP_CUDA_VERSION`。llama.cpp 层位于开发 shell 层之后，因此修改 llama.cpp 版本不会
让更昂贵的 shell 配置层失效；最终镜像源选择位于其后，因为 shell 配置过程中仍会安装软件包。

开发 shell 默认通过 `DEVSHELL: true` 启用，安装 zsh、Oh My Zsh、NvChad、使用当前 Node.js
LTS 的 NVM、fzf、eza、Starship、Sheldon、Zoxide、Witr 和 Atuin。容器命令仍默认为 Bash；
SSH 会话使用账号配置的 zsh 登录 shell，`docker exec` 调用者可显式选择 `bash` 或 `zsh`。
设置 `DEVSHELL: false` 会跳过开发 shell 安装。

该开发 shell 能力按用户要求持续跟随上游当前 release、分支和安装器，不固定每个组件版本。
这是对仓库常规可复现构建与 checksum 规则的明确滚动更新例外。因此，在不同时间重建同一 Git
提交可能得到不同的开发 shell 内容，也可能因上游产物变化而失败。

CMake 从精确版本的 HTTPS release 地址下载；本镜像族明确不校验该压缩包的 checksum。

默认交互用户为 `root`，不创建额外登录账号，软件源使用上游；`WORKSPACE_DIR` 用来选择创建
的工作目录（默认为 `/work`）。工作目录必须是 `/` 以外的绝对路径，其所有者为
`DEFAULT_USER`。该镜像族默认启用密码 SSH 和 root 登录，但在运行时提供密码前 root 账户
保持锁定；镜像中不保存任何密码。

`PACKAGE_MIRROR` 支持 `upstream` 和 `aliyun`。最终镜像源能力在 `upstream` 模式下保持基础
镜像的软件源不变；在 `aliyun` 模式下，仅在所有构建期软件安装完成后切换最终保留的 apt 和
pip 配置。

以 root 运行容器并开放密码 SSH，意味着容器进程和成功登录的 SSH 会话拥有容器内的完整
控制权。请使用独立的强密码，在宿主机或网络边界限制 SSH 端口，并尽可能改用
`SSH_MODE=key-only` 或 `SSH_MODE=disabled`。

创建本地密码文件并以只读方式挂载，即可启动接受 root SSH 的容器：

```bash
printf '%s' 'replace-with-a-private-password' >ssh-password
chmod 600 ssh-password
docker run --rm -d \
  --name cuda-dev \
  --gpus all \
  -p 2222:22 \
  -e SSH_PASSWORD_FILE=/run/secrets/ssh-password \
  -v "${PWD}/ssh-password:/run/secrets/ssh-password:ro" \
  ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04 \
  sleep infinity
ssh -p 2222 root@localhost
```

不再需要时请删除本地密码文件。设置 `SSH_MODE=disabled` 可以关闭 SSH；如需使用更安全的
纯公钥模式，请设置 `SSH_MODE=key-only`，并把非空公钥文件挂载到
`/root/.ssh/authorized_keys`。

`DEFAULT_USER=root` 会让用户配置能力复用已有的 root 账号，不创建用户或修改其 UID；此模式
不会应用 `DEFAULT_UID` 和 `DEFAULT_GID`。设置为其他合法 Linux 用户名时，会使用
`DEFAULT_UID` 和 `DEFAULT_GID` 创建该账号，将其设为 Docker 最终用户，并授予免密 sudo。
例如：

```yaml
build_args:
  DEFAULT_USER: developer
  DEFAULT_UID: 1000
  DEFAULT_GID: 1000
  WORKSPACE_DIR: /workspace
runtime:
  ssh:
    mode: password
```

每个变体都必须声明 `runtime.ssh.mode`。SSH 始终使用 `DEFAULT_USER`，不再提供独立登录账号
选择器。密码模式下，`SSH_PASSWORD_FILE` 会在容器启动时为该账号设置密码；纯公钥模式下，
应把 `authorized_keys` 挂载到该账号的 home 目录。
