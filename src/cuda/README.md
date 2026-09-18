# CUDA development image

This family builds parameterized Linux amd64 development images from digest-pinned NVIDIA CUDA
images. See `image.yml` for the supported CUDA/Ubuntu combinations.

The default user is `luciole`, the working directory is `/home/luciole`, the package mirror is
upstream, and SSH is disabled. To enable key-only SSH, build a variant with `SSH_MODE=key-only` and
mount a non-empty public-key file at `/home/luciole/.ssh/authorized_keys`.

