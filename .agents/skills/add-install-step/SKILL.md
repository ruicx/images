---
name: add-install-step
description: "Add a new shared installation step to the repository. Use when: adding a new shared install script, adding a new tool to dev images, adding a build step to Dockerfiles, creating a new _scripts entry, extracting repeated inline RUN commands into a reusable script."
argument-hint: "Describe the installation step to add, e.g. install tool X for dev images"
---

# Add a New Installation Step

## When to Use

- Installing a new tool or configuring a new environment in one or more Docker images
- Extracting repeated inline `RUN` commands into a reusable script
- Introducing new build-time assets (config files, templates, etc.)

## Repository Layout Reference

```
src/
  _scripts/   # Shared install scripts named by capability
  _assets/    # Build-time static assets (config files, etc.)
  <image>/
    image.yml
    Dockerfile
```

## Step 1 — Choose a Capability Name and Scope

Use a stable, descriptive capability name such as `cmake.sh`, `ros2.sh`, or
`dev-tools.sh`. Do not add sequence numbers: execution order belongs in each
Dockerfile, while consumption belongs in each image family's `image.yml`.

Determine the target scope:
- **Shared capability** → add one script and explicitly update every consuming
  Dockerfile and manifest
- **Specific image only** → update only that image family's Dockerfile and manifest
- **Internal base capability** → declare the consuming variant's explicit DAG edge
  in `dependencies`

## Step 2 — Write the Script

Create `src/_scripts/<capability>.sh` following these conventions:

```bash
#!/bin/bash
# One-line description: what this script does and which images use it.
# If the script must run as the target non-root user, state that here.
# List all GNU getopt options and their defaults.
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: capability.sh [--my-option <value>]

Options:
  --my-option <value>  Description (default: default_value)
  -h, --help           Show this help
EOF
}

MY_VAR="default_value"
if ! PARSED=$(getopt -o h -l help,my-option: -n "$(basename "$0")" -- "$@"); then
    usage >&2
    exit 64
fi
eval set -- "$PARSED"
while true; do
    case "$1" in
        --my-option)
            MY_VAR="$2"
            shift 2
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
    esac
done
if [ "$#" -ne 0 ]; then
    echo "capability.sh: unexpected positional arguments: $*" >&2
    usage >&2
    exit 64
fi
```

Rules:
- `set -euo pipefail` is mandatory
- After `apt-get install`, always clean up: `rm -rf /var/lib/apt/lists/*`
- Pass build-time values explicitly from Docker `ARG` to named script options; do
  not persist them through `ENV` unless the running container also needs them
- Reject unknown options, missing values, and positional arguments with exit 64
- Provide `-h` / `--help` without performing installation work
- Verify checksums for downloaded external binaries unless the consuming family's bilingual README
  records a user-approved exception with an exact version and HTTPS URL

## Step 3 — Handle Static Assets (if any)

If the script depends on config files or templates:

1. Place the files under `src/_assets/`
2. Copy only the declared asset into the image to keep cache invalidation scoped:
   ```dockerfile
   COPY src/_assets/my-config.yaml /tmp/assets/my-config.yaml
   ```
3. Pass the path to the script explicitly:
   ```bash
   /tmp/scripts/capability.sh --config /tmp/assets/my-config.yaml
   ```

## Step 4 — Update the Dockerfile(s)

### Where to call the script

- **Root-level scripts**: insert `RUN /tmp/scripts/<capability>.sh` before `USER ${USERNAME}`
- **Scripts that must run as the target user** (e.g. devshell, pre-commit): call after `USER ${USERNAME}`

### Standard Dockerfile structure

```dockerfile
COPY src/_scripts/system.sh /tmp/scripts/system.sh
COPY src/_assets/my-config.yaml /tmp/assets/my-config.yaml
RUN chmod +x /tmp/scripts/system.sh \
    && /tmp/scripts/system.sh --timezone "${TZ}"

# --- root-level scripts ---

ARG USERNAME=luciole
USER ${USERNAME}
WORKDIR /home/${USERNAME}

# --- user-level scripts (if any) ---
RUN /tmp/scripts/devshell.sh
RUN /tmp/scripts/precommit.sh

USER root
RUN rm -rf /tmp/scripts /tmp/assets   # clean up both in one RUN

USER ${USERNAME}
WORKDIR /home/${USERNAME}
```

> **Common mistake**: adding a shared input to the Dockerfile without declaring the
> exact path in `image.yml.inputs`. This prevents change impact analysis from
> rebuilding the correct family and downstream dependency closure.

## Step 5 — Update Documentation

Per the documentation sync rules in `AGENTS.md`:

| Changed file | Documentation to update |
|---|---|
| New `src/_scripts/*.sh` | Add it to every consumer's `image.yml.inputs`; update affected `README.md` / `README_zh.md` |
| `Dockerfile` | Update the corresponding image's `README.md` and `README_zh.md` |
| New file under `src/_assets/` | Update image docs that reference the asset's feature |

## Step 6 — Checklist

- [ ] Script has `#!/bin/bash` and `set -euo pipefail`
- [ ] Script has a stable capability name without a sequence number
- [ ] Parameterized scripts use GNU `getopt`, expose `--help`, and reject positional arguments
- [ ] All target Dockerfiles updated (base / dev / runtime as appropriate)
- [ ] Every script and asset copied by a Dockerfile is declared in `image.yml.inputs`
- [ ] Cleanup line `rm -rf /tmp/scripts /tmp/assets` covers all temp directories
- [ ] Documentation synced (`README.md`, `README_zh.md`, `AGENTS.md`)
- [ ] `python -m tools.images validate` passes
- [ ] New external downloads use exact versions and verified checksums, or document an approved
  exception in the consuming family's bilingual README
