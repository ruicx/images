# Image manifest reference

The shared schema and manifest contract is maintained in [image-kit](https://github.com/ruicx/image-kit/blob/main/docs/manifest-reference.md).
This repository installs the component from its pinned submodule; run `uv sync --extra dev`
after initializing or upgrading it. Existing `images` commands remain available, and
`python -m image_kit` is the module entry point.

Run `uv run python -m tools.check_repository` after `uv run images validate` to enforce
this repository's account contracts, explicit `mirror` and `runtime.ssh.mode` settings,
and bilingual documentation. The component does not require these policies from other users.

Registry and cache defaults, extra rebuild inputs, and shell validation inputs are declared
in `[tool.image-kit]` in the root `pyproject.toml`. GitHub Actions retains this repository's
permissions, native worker matrix, immutable release tags, and publication sequence.
