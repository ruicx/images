# Agent Instructions & Repository Invariants

This document defines operational rules, architectural contracts, and safety constraints for AI coding agents and automated workflows modifying this repository.

Agents must prioritize correctness, reproducibility, and cache efficiency over ad-hoc solutions. When modifying files or adding capabilities, adhere strictly to the following requirements.

---

## 1. Source of Truth & Manifest Contracts

- **Declarative Source of Truth**: `src/<family>/image.yml` is the sole authority for image variants, build arguments, platforms, and dependency relationships. Never hardcode variant lists or bypass manifest definitions.
- **Mandatory Pre-flight Validation**: Always run manifest validation after modifying any manifest, shared input, or schema:
  ```bash
  uv run images validate
  uv run python -m tools.check_repository
  # or: python -m image_kit validate
  ```
- **Graph Integrity**: Build dependency graphs must remain strictly acyclic. Cross-platform internal dependencies and undeclared dependencies are strictly forbidden.

---

## 2. Capability Scripts & Dockerfile Architecture

- **Shared Component**: `vendor/image-kit` is the commit-pinned public submodule from
  `https://github.com/ruicx/image-kit.git`. Initialize it with
  `git submodule update --init --recursive` before validation or builds. Shared scripts, assets,
  shell contract tests, the installable Python tooling, its bundled schema, and tool tests belong
  there; manifests, Dockerfiles, image smoke tests, account/documentation checks, and release policies
  remain in this repository. Run `uv sync --extra dev` after component upgrades. Publish component commits before
  recording their pins here. Component pin or `.gitmodules` changes rebuild every variant.

- **Capability Naming (No Sequence Numbers)**: Shared installation scripts in `vendor/image-kit/scripts/` must be named after their functional capability (e.g., `cmake.sh`, `dev-tools.sh`, `ssh.sh`). Never use sequence numbers (such as `01-system.sh`).
- **Explicit Manifest & Dockerfile Registration**: Every script consumed by an image family must be:
  1. Declared in the `inputs` list of `src/<family>/image.yml`.
  2. Explicitly copied and executed in `src/<family>/Dockerfile`.
- **Optimal BuildKit Layer Caching**: Independently changeable capabilities must use adjacent `COPY + RUN` pairs:
  ```dockerfile
  COPY vendor/image-kit/scripts/dev/cmake.sh /tmp/scripts/cmake.sh
  RUN /tmp/scripts/cmake.sh --version "${CMAKE_VERSION}" --sha256 "${CMAKE_SHA256}"
  ```
  - Never bundle unrelated scripts into a single `COPY` instruction.
  - Order prerequisites first, followed by stable and expensive build steps, placing lightweight or frequently modified steps near the end.
- **GNU getopt Argument Parsing**: Build-time scripts accepting parameters must use named GNU `getopt` options. Every parameterized script must:
  - Implement `-h` / `--help` displaying usage and default values.
  - Exit with code `64` (`EX_USAGE`) upon encountering invalid, missing, or unrecognized positional arguments.
- **Separation of Concerns**: Capability scripts own argument validation, dependency installation, and value-specific branching. Dockerfiles must only declare layer execution order and pass arguments; never duplicate conditional branching inside Dockerfiles.

---

## 3. Base Images & Supply Chain Integrity

- **Exact Base Image Tags**: External base images must specify an explicit, exact tag (e.g., `nvidia/cuda:12.8.2-devel-ubuntu24.04`). Dynamic or moving tags are prohibited.
- **Digest Key Requirement**: The `digest` field in `image.yml` is required for every variant:
  - Specify a full `sha256:<hex>` digest to lock an immutable, byte-for-byte reproducible base.
  - Specify explicit `null` only when intentionally tracking upstream updates for that exact tag.
- **Cryptographic Checksums**: All downloaded third-party binaries, archives, and installers must verify cryptographic checksums (SHA256) prior to extraction or installation, unless an explicit exception is documented in the consuming family's bilingual README with user approval.
- **Rolling Developer-Shell Exception**: Developer-shell tools (e.g., Oh My Zsh plugins, Neovim distributions) may follow upstream rolling releases only when explicitly approved and documented in the family's bilingual README. This exception must never be extended to runtime, compiler, or application dependencies.

---

## 4. Security & Safety Invariants

- **No Global `latest` Tag**: Never define, publish, or generate a global `latest` tag under any circumstances.
- **Zero Embedded Secrets**: Never hardcode or embed passwords, private keys, API tokens, or secrets in Dockerfiles, scripts, or assets.
- **SSH Security Constraints**: Root or password-based SSH access requires:
  1. An explicit runtime manifest mode (`runtime.ssh.mode`).
  2. A runtime-mounted secret password file.
  3. Prominent bilingual documentation warning of associated security risks.
- **No Runtime Mirror Probes**: Never introduce dynamic network probing or mirror discovery into runtime entrypoints or installation scripts.
- **Immutable Tag Retention**: When deprecating or retiring an image variant, never delete previously published immutable tags from the container registry.

---

## 5. Code Style & Documentation Standards

- **Documentation Language**: Keep English and Chinese README files (`README.md` and `README_zh.md`, including family READMEs) synchronized in structure and technical accuracy. Write documents under `docs/` in English.
- **Python API Conventions**:
  - Provide English NumPy-style docstrings for all functions, methods, and classes.
  - Include strict type hints for all parameters and return values.
- **English Code Comments**: Comments across all languages (Bash, Dockerfile, Python, YAML) must explain intent in clear English.

---

## 6. Git Workflow & Commit Guidelines

- **Commit Message Format**: Format commit subjects strictly as `<Type>: <summary>`.
  - The `<Type>` prefix must be chosen from: `Feat`, `BugFix`, `Refactor`, or `Doc`.
  - Separate the subject from the body with a blank line.
  - Detail changes in a numbered list:
  ```text
  BugFix: Fix Ascend zsh configuration order

  1. Configure the Ascend shell environment after zsh installation to avoid dpkg prompts.
  2. Preserve package defaults and verify clean shell startup.
  ```
- **Pre-commit Verification**: Before concluding any task, verify that manifests pass schema validation and all relevant tests pass:
  ```bash
  uv run images validate
  uv run python -m tools.check_repository
  uv run ruff check .
  ```
