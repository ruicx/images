# CUDA 开发镜像

本镜像族基于固定 digest 的 NVIDIA CUDA 镜像，为 Linux amd64 参数化构建开发环境。支持的
CUDA/Ubuntu 组合以 `image.yml` 为准。

默认用户为 `luciole`，工作目录为 `/home/luciole`，软件源使用上游，SSH 默认关闭。如需启用
纯公钥 SSH，请用 `SSH_MODE=key-only` 构建变体，并把非空公钥文件挂载到
`/home/luciole/.ssh/authorized_keys`。

