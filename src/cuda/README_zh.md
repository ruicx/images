# CUDA 开发镜像

基于 NVIDIA CUDA `devel` 镜像构建的开箱即用 Linux amd64 开发环境。已发布的变体包含 CUDA
编译器、常用 C/C++ 与 Python 工具、配置好的开发 shell，以及可选的 SSH 访问。英文版本见
[README.md](README.md)。

## 使用要求

要在容器中使用 GPU，宿主机需要：

- 兼容的 NVIDIA GPU 和驱动；
- 已配置 NVIDIA Container Toolkit 的 Docker；
- amd64 容器环境。

镜像可以不带 `--gpus all` 启动，但 GPU 命令和 CUDA 工作负载将无法访问宿主机 GPU。

## 启动交互式开发环境

拉取镜像，把当前项目挂载到 `/work`，关闭不需要的 SSH 服务，然后进入默认 Bash：

```bash
docker pull ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
docker run --rm -it \
  --gpus all \
  -e SSH_MODE=disabled \
  -v "${PWD}:/work" \
  ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
```

进入容器后验证环境：

```bash
nvidia-smi
nvcc --version
cmake --version
python3 --version
```

已发布的变体默认以 `root` 运行。在 Linux 宿主机上，容器写入绑定挂载目录的文件通常也会归
root 所有。如果需要让容器用户匹配宿主机用户，请参阅[构建期自定义](#构建期自定义)。可写的
绑定挂载也允许容器进程修改或删除其暴露的宿主机文件。请先提交或备份重要工作；容器只需读取
时，请在挂载参数末尾添加 `:ro`。

## 运行长期驻留的开发容器

在后台启动容器，需要时进入配置好的 zsh 开发 shell：

```bash
docker run --rm -d \
  --name cuda-dev \
  --gpus all \
  -e SSH_MODE=disabled \
  -v "${PWD}:/work" \
  ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04 \
  sleep infinity

docker exec -it cuda-dev zsh
docker stop cuda-dev
```

该示例长期运行但不保留容器：由于使用了 `--rm`，停止容器就会将其删除。只有 `/work` 等绑定
挂载中的数据会保留。如果必须保留停止后的容器，可以移除 `--rm`；但更推荐通过已声明的输入
重新构建，而不是在容器内累积未记录的修改。

镜像的默认容器命令仍为 Bash。SSH 登录会话使用账号配置的 zsh 登录 shell；`docker exec`
调用者则显式选择 `bash`、`zsh` 或其他命令。

## 通过 SSH 连接

入口脚本根据运行时 `SSH_MODE` 启动 SSH。请把发布端口绑定到可信的宿主机接口，并优先使用
纯公钥认证。SSH 始终登录镜像的 `DEFAULT_USER`，已发布变体中的该用户为 `root`。

### 纯公钥认证

把非空公钥文件挂载为 `authorized_keys`：

```bash
docker run --rm -d \
  --name cuda-dev \
  --gpus all \
  -e SSH_MODE=key-only \
  -p 127.0.0.1:2222:22 \
  -v "${HOME}/.ssh/id_ed25519.pub:/root/.ssh/authorized_keys:ro" \
  -v "${PWD}:/work" \
  ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04 \
  sleep infinity

ssh -p 2222 root@localhost
```

必要时请替换公钥路径。挂载的 `authorized_keys` 不存在或为空时，容器会以错误退出，不会降级
为其他认证方式。对于自定义的非 root 镜像，请把公钥挂载到该用户的
`~/.ssh/authorized_keys`，并使用该用户名而不是 `root` 连接。

### 密码认证

密码模式只通过运行时挂载的文件接收密码，镜像中不保存密码：

```bash
read -rsp 'SSH password: ' CUDA_DEV_SSH_PASSWORD && printf '\n'
printf '%s' "${CUDA_DEV_SSH_PASSWORD}" >"${HOME}/.cuda-dev-ssh-password"
unset CUDA_DEV_SSH_PASSWORD
chmod 600 "${HOME}/.cuda-dev-ssh-password"

docker run --rm -d \
  --name cuda-dev \
  --gpus all \
  -e SSH_MODE=password \
  -e SSH_PASSWORD_FILE=/run/secrets/ssh-password \
  -p 127.0.0.1:2222:22 \
  -v "${HOME}/.cuda-dev-ssh-password:/run/secrets/ssh-password:ro" \
  -v "${PWD}:/work" \
  ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04 \
  sleep infinity

ssh -p 2222 root@localhost
```

不再需要时请删除 `${HOME}/.cuda-dev-ssh-password`。隐藏输入可避免密码出现在终端输出和 shell
历史中，把密码文件放在项目之外则可降低误提交风险。密码模式在未设置 `SSH_PASSWORD_FILE`
时仍会启动 sshd，但默认 root 账号保持锁定，无法使用密码认证。不需要 SSH 时请设置
`SSH_MODE=disabled`。

以 root 运行容器并开放密码 SSH，意味着容器进程和成功登录的 SSH 会话拥有容器内的完整
控制权。请使用独立的强密码，在宿主机或网络边界限制发布端口，并尽可能使用纯公钥模式或关闭
SSH。

## 内置工具与默认值

镜像包含 CUDA、CMake 4.3.2、Ninja、GCC、clangd、GDB、Git LFS、Python 3、pip、虚拟
环境支持、OpenCV 开发库、常用网络工具，以及 ripgrep、fd 和 bat。

部分通过 apt 安装的命令行工具可能依赖发行版提供的 Python 模块。独立的 Python 安装步骤会
在这些工具之后运行，复用发行版默认的 `python3`，补齐匹配的开发头文件和虚拟环境支持，并为
该解释器引导安装 pip。

开发 shell 还包含 zsh、Oh My Zsh、NvChad、使用当前 Node.js LTS 的 NVM、fzf、eza、
Starship、Sheldon、Zoxide 和 Witr。

| 配置 | 已发布变体的值 | 可更改时机 |
| --- | --- | --- |
| `DEFAULT_USER` | `root` | 构建期 |
| `DEFAULT_UID` | `1000`（root 模式不使用） | 构建期 |
| `DEFAULT_GID` | `1000`（root 模式不使用） | 构建期 |
| `WORKSPACE_DIR` | `/work` | 构建期 |
| `DEVSHELL` | `true` | 构建期 |
| `TZ` | `Asia/Shanghai` | 构建期 |
| `PACKAGE_MIRROR` | `upstream` | 构建期 |
| `SSH_MODE` | `password` | 构建期默认值或运行时覆盖 |
| `SSH_PASSWORD_FILE` | 未设置 | 仅运行时 |

`PACKAGE_MIRROR` 支持 `upstream` 和 `aliyun`。`upstream` 保持基础镜像的软件源不变；
`aliyun` 在所有构建期安装完成后切换最终保留的 apt 和 pip 配置。在已构建容器中修改同名
环境变量不会重写这些文件。

## 构建期自定义

`src/cuda/image.yml` 是已发布变体的事实来源。例如，自定义清单变体可以使用非特权用户和不同
的工作目录：

```yaml
build_args:
  DEFAULT_USER: developer
  DEFAULT_UID: 1000
  DEFAULT_GID: 1000
  WORKSPACE_DIR: /workspace
  DEVSHELL: true
mirror: upstream
runtime:
  ssh:
    mode: key-only
```

`DEFAULT_USER=root` 会复用已有的 root 账号，因此不会应用 `DEFAULT_UID` 和 `DEFAULT_GID`。
其他合法 Linux 用户名会创建对应账号，使用声明的 UID 和 GID，将其设为 Docker 最终用户，
并授予免密 sudo。工作目录必须是 `/` 以外的绝对路径，其所有者为 `DEFAULT_USER`。

每个变体都必须把 `runtime.ssh.mode` 显式声明为 `disabled`、`key-only` 或 `password`。规划器
会把清单策略转换为镜像的 `SSH_MODE` 构建参数：清单中的值决定镜像内置默认值，
`docker run -e SSH_MODE=...` 只改变本次启动的容器行为。

请把完整的自定义变体添加到 `src/cuda/image.yml` 的 `variants` 下，然后按照
[仓库构建流程](../../README_zh.md#开发本仓库)操作，并把 `plan --all` 替换为：

```bash
images plan --family cuda --variant <variant-id> --output build-plan.json
```

使用 `load` 模式时，生成的本地镜像除不可变 revision 标签外，还会获得浮动标签
`ghcr.io/ruicx/cuda:<variant-id>`。

## 可复现性与能力边界

支持的 CUDA/Ubuntu 组合及基础镜像解析策略在 `src/cuda/image.yml` 中声明。12.6.3 变体通过
digest 固定 NVIDIA 基础镜像；12.8.2 变体使用明确标签和空 digest，因此会跟随该标签的更新。
需要可重复环境时，请使用不可变镜像标签或 digest。

固定已发布镜像的 digest 可以让后续拉取结果保持一致，但不能保证重新从源码构建时逐字节一致。
使用 `docker buildx imagetools inspect <image>` 查看 digest，然后按
`ghcr.io/ruicx/cuda@sha256:<digest>` 拉取。

开发 shell 能力按用户要求持续跟随上游当前 release、分支和安装器。这是对仓库常规可复现
构建与 checksum 规则的明确例外。因此，在不同时间重建同一 Git 提交可能得到不同的开发 shell
内容，也可能因上游产物变化而失败。设置 `DEVSHELL: false` 会跳过该能力。

Python 包管理能力也按用户要求持续跟随上游内容。它从当前的
`https://bootstrap.pypa.io/get-pip.py` 引导安装 pip，安装
`src/_scripts/pip-packages.sh` 中未固定版本的包，并通过当前的
`https://astral.sh/uv/install.sh` 安装 uv。这些输入有意不固定版本或 checksum，因此在不同
时间重建同一 Git 提交可能选择更新的 Python 包管理工具和库。GitHub/GHCR 构建历史中保留的
不可变镜像标签和 digest 是这些输入的回滚与审计边界。

CMake 从精确版本的 HTTPS release 地址下载；本镜像族明确不校验该压缩包的 checksum。如果
你的威胁模型无法接受这一例外，请独立审计生成的镜像，或在构建前把该安装步骤改为校验
checksum 的来源；仅重新构建本仓库并不能消除该风险。

CUDA 镜像有意不内置 llama.cpp。需要它的应用应运行官方 llama.cpp 镜像作为独立服务，并在
下游项目中定义编排。共享的 `llama-cpp.sh` 脚本是未被引用的待迁移能力，不属于本镜像族承诺
支持的内容。
