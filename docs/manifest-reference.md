# Image manifest reference

`src/<family>/image.yml` is the versioned release contract for an image family. Paths and glob
patterns are relative to the repository root. Unknown fields are rejected.

## Family fields

| Field | Type | Contract |
| --- | --- | --- |
| `schema_version` | integer | Must be `1`. A future incompatible format increments this value. |
| `name` | string | Lowercase kebab-case and identical to `<family>`. |
| `description` | string | Non-empty, user-facing family summary. |
| `dockerfile` | path | Existing Dockerfile inside the repository. |
| `context` | path | Existing build context inside the repository. |
| `platforms` | list | Phase one accepts exactly `linux/amd64`. |
| `inputs` | list | Existing path/glob patterns whose changes rebuild every family variant. |
| `runtime.ssh.default` | enum | `disabled`, `key-only`, or `password`; variants may override it. |
| `runtime.ssh.login_user` | enum | `default` follows `DEFAULT_USER`; `root` explicitly selects root. Variants may override it. |
| `publish` | boolean | Allows selected variants to be published from `main`. |
| `variants` | list | One or more variant definitions. |

## Variant fields

| Field | Type | Contract |
| --- | --- | --- |
| `id` | string | Floating tag name; lowercase segments separated by `.`, `_`, or `-`; never `latest`. |
| `base.image` | string | External image with an explicit version tag; `latest` and `master` are forbidden. |
| `base.digest` | string | Required `sha256:` digest with 64 lowercase hexadecimal characters. |
| `build_args` | mapping | Non-secret values passed to the Dockerfile. Secret-like keys are rejected. |
| `mirror` | enum | `upstream` or explicitly selected `aliyun`. |
| `runtime.ssh.default` | enum | Optional variant override of the family default. Password mode requires runtime secret handling documented by the family. |
| `runtime.ssh.login_user` | enum | Optional `default` or `root` override of the family login account selector. |
| `dependencies` | list | Internal targets exposed as named BuildKit contexts. |
| `tests` | list | One or more existing repository-relative smoke-test scripts. |

Each dependency contains `family`, `variant`, and `context`. The context name must be unique inside
the consumer variant and must match a Dockerfile named context:

```yaml
dependencies:
  - context: internal_base
    family: base
    variant: ubuntu-24.04
```

```dockerfile
FROM internal_base AS development
```

Buildx Bake resolves `internal_base` to `target:<generated-base-target>`, so a pull request never
uses an older registry copy for an internal dependency.

## Complete shape

```yaml
schema_version: 1
name: example
description: Example development image
dockerfile: src/example/Dockerfile
context: .
platforms: [linux/amd64]
inputs:
  - src/example/**
  - src/_scripts/example-tool.sh
runtime:
  ssh:
    default: disabled
    login_user: default
publish: true
variants:
  - id: ubuntu-24.04
    base:
      image: ubuntu:24.04
      digest: sha256:<64-lowercase-hex-characters>
    build_args:
      DEFAULT_USER: developer
      DEFAULT_UID: 1000
      DEFAULT_GID: 1000
      TOOL_VERSION: "1.2.3"
    mirror: upstream
    dependencies: []
    tests:
      - src/example/tests/smoke.sh
```

The JSON Schema performs structural validation. `images validate` additionally checks paths,
directory/name equality, duplicate variants, secret-like build arguments, the `DEFAULT_USER`
contract, dependency targets, duplicate context names, smoke tests, graph cycles, and bilingual
documentation. `DEFAULT_USER=root` must omit `DEFAULT_UID` and `DEFAULT_GID`; any other valid Linux
username requires both numeric fields.
