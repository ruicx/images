# 昇腾 PEFT 训练镜像

此 ARM64 镜像在[昇腾开发镜像](../ascend/README_zh.md)之上增加一组精简的 PEFT 训练包。
名为 `ascend_base` 的 Buildx 依赖会选取同一仓库版本构建的昇腾镜像。清单中必填的
`base.image` 字段记录父镜像所用的上游 TorchNPU 镜像；Dockerfile 的直接基础镜像是内部依赖。
英文说明见 [README.md](README.md)。

## 增加软件包

修改 `requirements.txt` 即可调整应用包集合。清单把该文件和
`src/_scripts/python/ascend-python-packages.sh` 登记为输入，修改后会重建此镜像。Dockerfile 分别复制
依赖清单和安装脚本，并在独立的缓存层安装。安装脚本使用父镜像中的
`/opt/image-python/base-constraints.txt` 上游包约束，安装后运行 `ascend-pip-check`。
若新包要求替换上游包，依赖解析会失败，而不会更改 TorchNPU 或 CANN。

应用包有意不固定版本。构建时，pip 在父镜像的上游包约束内解析兼容版本，包括与继承的
PyTorch 兼容的 TorchVision。父镜像的 PyTorch 和 TorchNPU 版本保持不变；若依赖无法同时
满足，构建会失败。包集合取自 `minifly` 的训练依赖。此镜像不安装 `minifly` 项目本身、
它指向 CUDA 的 uv 包源、模型权重或训练数据。先在项目侧调整 PyTorch 包源以适配昇腾，
再从项目源码安装。应用包和传递 Python 依赖都在构建时解析，重新构建可能选取不同版本。
若需复用特定训练环境，请使用已发布镜像的不可变标签。

## 验证与使用

ARM64 CI 冒烟测试无需 NPU 设备，只检查包元数据及现有的昇腾依赖诊断。测试会将实际安装的
PyTorch 和 TorchNPU 完整版本与父镜像的 `base-constraints.txt` 比较，允许父镜像升级，
但此镜像更改这些版本会导致测试失败。在目标服务器上，
先运行父镜像的 NPU 测试，再运行一次真实的 PEFT 前向、反向训练步骤及所选 VLA 训练脚本。
仅完成软件包安装不能证明 VLA 模型的算子能在昇腾上运行。

通过仓库的清单和 Bake 流程构建；`ascend-peft` 目标会包含它的 `ascend` 依赖。训练时使用
已发布镜像的不可变标签。Ascend Docker Runtime、设备选择、共享内存和 SSH 等容器启动参数
与[父镜像指南](../ascend/README_zh.md)一致。继承的默认用户为 root；按该指南限制可写的宿主机
挂载目录和 SSH 访问。
