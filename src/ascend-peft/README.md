# Ascend PEFT training image

This ARM64 image extends the [Ascend development image](../ascend/README.md) with a small PEFT
training package set. The Buildx dependency named `ascend_base` selects the Ascend image built from
the same repository revision. The required `base.image` manifest field records that parent's
upstream TorchNPU image; the Dockerfile uses the internal dependency as its direct base. See the
[Chinese guide](README_zh.md).

## Adding packages

Edit `requirements.txt` to change the application package set. The manifest registers that file and
`src/_scripts/python/ascend-python-packages.sh` as inputs, so changes rebuild this image. The Dockerfile
copies the requirements separately from the installer and runs installation in its own cached
layer. The installer uses the parent image's vendor constraints at
`/opt/image-python/base-constraints.txt` and runs `ascend-pip-check` after installation. A package
that requires replacing a vendor package fails resolution instead of changing TorchNPU or CANN.

Application packages are intentionally unpinned. At build time, pip resolves compatible versions
within the parent's vendor constraints, including a TorchVision version compatible with the
inherited PyTorch. The parent's PyTorch and TorchNPU versions stay fixed; an unsatisfiable dependency
set fails the build. The package set comes from `minifly`'s training dependencies. This image does
not install `minifly` itself, its CUDA-specific uv package source, model weights, or training data.
Install the project from its own source only after adapting its PyTorch package source for Ascend.
Application and transitive Python dependencies are resolved at build time, so rebuilding can select
different versions. Use an immutable published image tag to reuse a specific training environment.

## Verification and use

The ARM64 CI smoke test checks package metadata and the existing Ascend dependency diagnostics
without NPU devices. It compares the full installed PyTorch and TorchNPU versions with the parent's
`base-constraints.txt`, so parent upgrades are accepted while changes made by this image fail the test.
On the target server, first run the parent's NPU test, then run a real PEFT
forward/backward training step and the selected VLA training script. Package installation alone
does not establish that the VLA model's operators work on Ascend.

Build with the repository's manifest and Bake workflow; the `ascend-peft` target pulls in its
`ascend` dependency. Use an immutable published image tag for training. Container start options,
including Ascend Docker Runtime, device selection, shared memory, and SSH, are the same as in the
[parent guide](../ascend/README.md). The inherited default user is root; restrict writable host
mounts and SSH access as described there.
