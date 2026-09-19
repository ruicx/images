# Development guide

## Adding an image family

1. Copy the `src/cuda` shape into `src/<family>` without copying its image-specific values.
2. Add a schema-valid `image.yml`; the manifest name must equal the directory name.
3. Pin external base images by exact tag and `sha256` digest.
4. Declare every shared script or asset in `inputs` and every internal base in `dependencies`.
5. Add bilingual family documentation and at least one smoke-test script per variant.
6. Run `images validate`, Ruff, mypy, pytest, ShellCheck, shfmt, and a local Bake build.

## Code rules

- Use English for code, identifiers, comments, and Conventional Commit messages.
- Shell scripts use capability names, `#!/bin/bash`, `set -euo pipefail`, quoted variables,
  architecture checks, deterministic temporary cleanup, and apt-list cleanup. Build-time
  configuration uses GNU `getopt` long options with `-h`/`--help`; environment variables are
  reserved for runtime container configuration.
- Python functions and methods declare parameter and return type hints. Public modules, classes,
  functions, methods, and non-trivial test helpers use English NumPy-style docstrings. Comments
  explain intent or constraints rather than restating code. Python must pass Ruff, mypy, and
  pytest. User-facing errors identify the family, variant, and field.
- Dockerfiles use BuildKit syntax, explicit non-interactive package installation, one cleanup layer,
  a non-root final user, and OCI labels supplied by Bake.
- Do not use `latest`, `master`, floating LTS installers, unversioned binary downloads, embedded
  passwords, or secrets in build arguments. A family may explicitly enable password/root SSH only
  when credentials are supplied from a runtime-mounted file and its bilingual README documents
  the risk, startup procedure, and safer modes.
- Downloaded binary archives normally require checksum verification. A user-approved exception
  must retain an exact version and HTTPS URL and be recorded in the family's bilingual README.
- Upstream Ubuntu and PyPI sources are the default. `aliyun` is an explicit build-time manifest
  choice and is never selected by runtime network probing.

## Documentation rules

English files are normative. Changes to a root guide or family README must update its `_zh`
counterpart in the same pull request. User-visible changes update the affected family README.
Removing a variant does not authorize deletion of published tags. `images validate` enforces the
required bilingual guide set. See the [lifecycle policy](lifecycle.md) for compatibility rules.
