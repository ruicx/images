# CUDA development image

This family builds parameterized Linux amd64 development images from digest-pinned NVIDIA CUDA
images. See `image.yml` for the supported CUDA/Ubuntu combinations. The image includes the CUDA
compiler, a version-pinned CMake 4.3.2 installation, Ninja, GCC, clangd, GDB, Git LFS, Python 3,
pip, virtual-environment support, OpenCV development libraries, common network tools, and modern
command-line utilities such as ripgrep, fd, and bat.

CMake is downloaded from its exact HTTPS release URL. This family intentionally does not verify a
checksum for that archive.

The default interactive user is `luciole`, the writable working directory is `/work`, and the
package mirror is upstream. Password SSH and root login are enabled for this family, but the root
account remains locked until a password is supplied at runtime. No password is stored in the image.

Create a local password file and mount it read-only to start a container that accepts root SSH:

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

Delete the local password file when it is no longer needed. To disable SSH, set
`SSH_MODE=disabled`. To use the safer key-only mode, set `SSH_MODE=key-only` and mount a non-empty
public-key file at `/home/luciole/.ssh/authorized_keys`.
