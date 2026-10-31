# 昇腾 910B 开发镜像

面向鲲鹏 CPU 与昇腾 910B NPU 的 ARM64 开发环境，基础镜像为
`ascendai/torch-npu:2.14.0-cann9.2.0-910b-ubuntu22.04-py3.12`。清单固定上游多架构索引的
digest，本镜像族只构建 `linux/arm64`。英文说明见 [README.md](README.md)。

## 内容与默认值

基础镜像提供 Ubuntu 22.04、CANN 9.2.0 Toolkit/910B 算子包/NNAL、PyTorch 2.14.0、
TorchNPU 2.14.0 和 Python 3.12.15。CPU 版 PyTorch 通过 TorchNPU 使用 NPU。我们保留上游
解释器、头文件、pip 和已安装 Python 包的版本。apt 依赖也可能引入发行版 Python，
`/usr/bin/python3` 继续由 Ubuntu 管理；用户使用的 `python` 和 `python3` 选择上游解释器。

新增工具与 CUDA 镜像族保持相近：CMake 4.3.2、Ninja、GCC、clangd、GDB、Git LFS、OpenCV
开发库、网络工具、ripgrep、fd、bat、Python 开发包、uv，以及 zsh/Oh My Zsh/NvChad/Node.js
开发 shell。两个镜像族共用 `src/_scripts/pip-packages.sh` 中不指定版本的包列表，uv 也通过
pip 安装。昇腾传入 `--preserve-existing --profile ascend`，通过构建期约束保留固定
基础镜像中已有包的版本；发生依赖冲突时构建失败，不替换上游软件栈。有效约束保留在
`/opt/image-python/base-constraints.txt`，可供检查。

昇腾 profile 还会补装上游工具缺失的依赖：`plotly`、Python `ninja` 发行包、`colorlog`、
`msguard`，以及 gRPC/HTTP OpenTelemetry OTLP exporter（>=1.33.1,<2.0.0）。仅安装 apt 的
`ninja-build` 可执行文件不能满足 Python 包元数据的依赖要求。
构建和冒烟测试统一运行 `ascend-pip-check`。经用户批准，该检查器仅对固定基础镜像中的
`mindstudio-kl 26.2.0` 要求 `numpy<=1.26.4`、但已安装 `numpy 2.5.4` 这一条冲突输出警告
并放行，两个上游包均保留原版本。其他依赖错误、版本变化及 pip 执行错误仍会导致失败。
这一例外不代表已验证 msKL 与 NumPy 2.5.4 兼容；本镜像测试不覆盖 msKL 算子调用与自动调优。
使用 msKL 前应先解决该兼容性问题。

| 配置 | 清单默认值 |
| --- | --- |
| 平台 | `linux/arm64` |
| 默认用户 | `luciole`（UID/GID 为 `1000`，免密 sudo） |
| 工作目录 | `/work` |
| 开发 shell | 启用；容器默认命令为 Bash，登录 shell 为 zsh |
| 时区 | `Asia/Shanghai` |
| 软件源 | `upstream`（保留基础镜像的上游配置） |
| SSH 模式 | `password`；提供密码文件前账号保持锁定 |

入口包装脚本保留上游 CANN、毕昇与 NNAL 初始化，然后应用共享 SSH 策略。Bash 登录会话和
zsh 会话恢复上游开发环境，包括 Python 路径。普通 `docker exec` 命令继承基础镜像的环境。
设备可见性和昇腾运行时选项在启动容器时设置，不固化进镜像。

## 宿主机要求与交互使用

使用 ARM64 Linux 宿主机，并安装兼容的昇腾 910B 固件与驱动。运行工作负载前，对照
[CANN 配套信息](https://www.hiascend.com/developer/download/compatibility)核对实际宿主机版本。
本镜像不安装或升级宿主机驱动与固件。

安装 Ascend Docker Runtime 并注册为 `ascend` 后，开放一个 NPU 并关闭 SSH：

```bash
IMAGE=ghcr.io/ruicx/ascend:2.14.0-cann9.2.0-910b-ubuntu22.04-py3.12
docker run --rm -it \
  --runtime=ascend \
  -e ASCEND_VISIBLE_DEVICES=0 \
  -e SSH_MODE=disabled \
  --shm-size=8g \
  -v "${PWD}:/work" \
  "$IMAGE"
```

根据工作负载调整共享内存。使用多张卡时，指定 `ASCEND_VISIBLE_DEVICES=0,1` 等明确列表；
卡数和拓扑属于服务器配置。非 root 用户需要按已安装的运行时和驱动配置设备访问组，或添加
匹配的补充 GID。不要把设备节点设为所有用户可写。

没有 Ascend Docker Runtime 时，单卡手动挂载示例如下：

```bash
docker run --rm -it \
  --device /dev/davinci0 \
  --device /dev/davinci_manager \
  --device /dev/devmm_svm \
  --device /dev/hisi_hdc \
  -v /usr/local/dcmi:/usr/local/dcmi:ro \
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi:ro \
  -v /usr/local/Ascend/driver:/usr/local/Ascend/driver:ro \
  -v /etc/ascend_install.info:/etc/ascend_install.info:ro \
  -e SSH_MODE=disabled \
  --shm-size=8g \
  -v "${PWD}:/work" \
  "$IMAGE"
```

先核对宿主机路径，再按实际驱动布局和设备权限调整。只挂载驱动，不要覆盖整个宿主机
`/usr/local/Ascend`，以免隐藏容器内 CANN。另见
[上游镜像指南](https://hub.docker.com/r/ascendai/torch-npu)。

进入容器后检查 `npu-smi info`、`python3 --version` 和 `cmake --version`。在本仓库运行硬件
测试时，将脚本重定向到具有相同设备或运行时参数的容器，例如：

```bash
docker run --rm -i --runtime=ascend \
  -e ASCEND_VISIBLE_DEVICES=0 -e SSH_MODE=disabled \
  "$IMAGE" bash -s < src/ascend/tests/npu.sh
```

该测试检查设备可见性，并把小规模矩阵乘法与 CPU 结果比较。多卡 HCCL 通信和应用性能仍需在
服务器上按实际工作负载验证。

## 常驻容器与 SSH

把交互参数换为 `-d --name ascend-dev` 并在命令末尾添加 `sleep infinity`，即可后台运行，
随后使用 `docker exec -it ascend-dev zsh`。绑定挂载的文件以 UID/GID 1000 写入；必要时在
自定义清单中匹配宿主机用户。只需读取的项目输入可使用 `:ro`。以 `--rm` 启动的容器停止后
会被删除。

使用公钥认证时，在相同 NPU 参数之外添加：

```bash
-e SSH_MODE=key-only \
-p 127.0.0.1:2222:22 \
-v "${HOME}/.ssh/id_ed25519.pub:/home/luciole/.ssh/authorized_keys:ro"
```

以 `sleep infinity` 启动，并使用 `ssh -p 2222 luciole@localhost` 连接。公钥缺失或为空时
启动失败。密码认证先在项目外创建密码文件，再于运行时挂载：

```bash
read -rsp 'SSH password: ' ASCEND_DEV_PASSWORD && printf '\n'
printf '%s' "${ASCEND_DEV_PASSWORD}" > "${HOME}/.ascend-dev-ssh-password"
unset ASCEND_DEV_PASSWORD
chmod 600 "${HOME}/.ascend-dev-ssh-password"
```

添加 `-e SSH_MODE=password -e SSH_PASSWORD_FILE=/run/secrets/ssh-password` 和
`-v "${HOME}/.ascend-dev-ssh-password:/run/secrets/ssh-password:ro"`，把端口发布到可信接口，
以 `luciole` 连接。不再需要时删除密码文件；密码不会构建进镜像。免密 sudo 赋予该账号完整的
容器控制权，密码 SSH 会将此控制权开放给持有凭据的人。优先选择公钥认证或关闭 SSH。启用
root 需要自定义清单，同样存在容器控制权与绑定挂载风险；选择 root 时省略 UID/GID。

## 构建与可复现性

`image.yml` 是事实来源。在原生 ARM64 Docker 构建机上按照
[仓库开发指南](../../docs/development_zh.md)操作，并选择：

```bash
python -m tools.images plan --family ascend --platform linux/arm64 --output build-plan.json
```

普通 CI 在原生 ARM64 runner 上构建并运行 `tests/smoke.sh`，不要求 NPU 硬件。测试覆盖工具、
Python 元数据和 venv、shell 环境及 SSH 策略；不导入 TorchNPU，也不声称已验证硬件兼容。
请在目标服务器单独运行 `tests/npu.sh`。

基础镜像已固定，ARM64 CMake 压缩包按清单中的 SHA-256 校验。按用户要求，新增 Python 包
采用共享包列表，不指定版本，同时用约束保留上游软件栈的已安装版本。这项经用户批准的滚动
Python 包策略意味着重建时新增包和传递依赖可能变化，apt 包也未锁定。为保持 CUDA 开发体验，
本镜像复用其
经用户批准的滚动交互式开发 shell 例外：当前上游 release、分支、安装器和插件可不固定版本或
checksum。此例外仅适用于开发 shell 工具，不适用于 CANN、PyTorch、TorchNPU 或应用依赖。
因此，重建同一提交不保证得到逐字节相同的内容。设置 `DEVSHELL: false` 可跳过交互式 shell
安装。发布的不可变 revision 标签和 digest 标识实际构建产物；不发布全局 `latest` 标签。
