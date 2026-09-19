# Development guide

## Adding an image family

1. Copy the `src/cuda` shape into `src/<family>` without copying its image-specific values.
2. Add a schema-valid `image.yml`; the manifest name must equal the directory name.
3. Give every external base an exact tag and a required `digest` key. Prefer a `sha256` pin;
   use explicit `null` only when intentionally tracking updates to that tag.
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
- Dockerfiles use pinned BuildKit syntax and explicit non-interactive installation. Give each
  independently changeable capability an adjacent `COPY + RUN`; do not copy unrelated scripts
  together because that collapses their cache boundaries. Order dependency prerequisites first,
  then prefer stable or expensive capabilities before cheap or frequently changed ones. Keep each
  package installation and its apt-list cleanup in the same `RUN`.
- Capability scripts own option validation and value-specific branching. Dockerfiles pass `ARG`
  values through named options and declare order; they do not duplicate conditions such as root
  handling, workspace ownership, or mirror selection.
- Images use a non-root final user by default and receive OCI labels from Bake. A family may
  explicitly choose a root final user only when its bilingual README documents the operational and
  credential risks.
- Every variant explicitly declares `runtime.ssh.mode`; SSH always targets its `DEFAULT_USER`.
  Keep the policy outside `build_args` so schema validation and security review remain explicit.
- Do not use `latest`, `master`, floating LTS installers, unversioned binary downloads, embedded
  passwords, or secrets in build arguments. A family may explicitly enable password/root SSH only
  when credentials are supplied from a runtime-mounted file and its bilingual README documents
  the risk, startup procedure, and safer modes.
- Downloaded binary archives normally require checksum verification. A user-approved exception
  must retain an exact version and HTTPS URL and be recorded in the family's bilingual README.
- A deliberately rolling developer-shell capability may follow current upstream releases,
  branches, and installers only when the family's bilingual README records the user-approved
  reproducibility and supply-chain exception. Keep this exception scoped to interactive tooling.
- Upstream Ubuntu and PyPI sources are the default during installation. The manifest `mirror`
  selection is finalized only after package installation: `upstream` preserves the base sources and
  `aliyun` rewrites persisted apt/pip configuration. It is never selected by runtime network probing.

## Documentation rules

English files are normative. Changes to a root guide or family README must update its `_zh`
counterpart in the same pull request. User-visible changes update the affected family README.
Removing a variant does not authorize deletion of published tags. `images validate` enforces the
required bilingual guide set. See the [lifecycle policy](lifecycle.md) for compatibility rules.
