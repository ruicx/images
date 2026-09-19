# CUDA 开发镜像

本镜像族基于固定 digest 的 NVIDIA CUDA 镜像，为 Linux amd64 参数化构建开发环境。支持的
CUDA/Ubuntu 组合以 `image.yml` 为准。镜像包含 CUDA 编译器、固定版本的 CMake
4.3.2、Ninja、GCC、clangd、GDB、Git LFS、Python 3、pip、虚拟环境支持、OpenCV 开发库、
常用网络工具，以及 ripgrep、fd、bat 等现代命令行工具。

开发 shell 默认通过 `DEVSHELL: true` 启用，安装 zsh、Oh My Zsh、NvChad、使用当前 Node.js
LTS 的 NVM、fzf、eza、Starship、Sheldon、Zoxide、Witr 和 Atuin。容器命令仍默认为 Bash；
SSH 会话使用账号配置的 zsh 登录 shell，`docker exec` 调用者可显式选择 `bash` 或 `zsh`。
设置 `DEVSHELL: false` 会跳过开发 shell 安装。

该开发 shell 能力按用户要求持续跟随上游当前 release、分支和安装器，不固定每个组件版本。
这是对仓库常规可复现构建与 checksum 规则的明确滚动更新例外。因此，在不同时间重建同一 Git
提交可能得到不同的开发 shell 内容，也可能因上游产物变化而失败。

CMake 从精确版本的 HTTPS release 地址下载；本镜像族明确不校验该压缩包的 checksum。

默认交互用户为 `root`，不创建额外登录账号，工作目录为 `/work`，软件源使用上游。该镜像族
默认启用密码 SSH 和 root 登录，但在运行时提供密码前 root 账户保持锁定；镜像中不保存任何
密码。

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
  ghcr.io/ruicx/cuda:12.8.1-devel-ubuntu24.04 \
  sleep infinity
ssh -p 2222 root@localhost
```

不再需要时请删除本地密码文件。设置 `SSH_MODE=disabled` 可以关闭 SSH；如需使用更安全的
纯公钥模式，请设置 `SSH_MODE=key-only`，并把非空公钥文件挂载到
`/root/.ssh/authorized_keys`。

`DEFAULT_USER=root` 会选择已有的 root 账号，不创建其他用户。设置为其他合法 Linux 用户名
时，会使用 `DEFAULT_UID` 和 `DEFAULT_GID` 创建该账号，将其设为 Docker 最终用户，并授予
免密 sudo。例如：

```yaml
build_args:
  DEFAULT_USER: developer
  DEFAULT_UID: 1000
  DEFAULT_GID: 1000
runtime:
  ssh:
    default: password
    login_user: default
```

`runtime.ssh.login_user` 可设为 `default` 或 `root`。`default` 跟随 `DEFAULT_USER`，`root`
显式选择 root。密码模式下，`SSH_PASSWORD_FILE` 会在容器启动时为解析后的登录账号设置密码；
纯公钥模式下，应把 `authorized_keys` 挂载到该账号的 home 目录。
