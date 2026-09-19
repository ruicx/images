# CUDA 开发镜像

本镜像族基于固定 digest 的 NVIDIA CUDA 镜像，为 Linux amd64 参数化构建开发环境。支持的
CUDA/Ubuntu 组合以 `image.yml` 为准。镜像包含 CUDA 编译器、固定版本的 CMake
4.3.2、Ninja、GCC、clangd、GDB、Git LFS、Python 3、pip、虚拟环境支持、OpenCV 开发库、
常用网络工具，以及 ripgrep、fd、bat 等现代命令行工具。

CMake 从精确版本的 HTTPS release 地址下载；本镜像族明确不校验该压缩包的 checksum。

默认交互用户为 `luciole`，可写工作目录为 `/work`，软件源使用上游。该镜像族默认启用密码
SSH 和 root 登录，但在运行时提供密码前 root 账户保持锁定；镜像中不保存任何密码。

创建本地密码文件并以只读方式挂载，即可启动接受 root SSH 的容器：

```bash
printf '%s' 'replace-with-a-private-password' >root-password
chmod 600 root-password
docker run --rm -d \
  --name cuda-dev \
  --gpus all \
  -p 2222:22 \
  -e ROOT_PASSWORD_FILE=/run/secrets/root-password \
  -v "${PWD}/root-password:/run/secrets/root-password:ro" \
  ghcr.io/ruicx/cuda:12.8.1-devel-ubuntu24.04 \
  sleep infinity
ssh -p 2222 root@localhost
```

不再需要时请删除本地密码文件。设置 `SSH_MODE=disabled` 可以关闭 SSH；如需使用更安全的
纯公钥模式，请设置 `SSH_MODE=key-only`，并把非空公钥文件挂载到
`/home/luciole/.ssh/authorized_keys`。
