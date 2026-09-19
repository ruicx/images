# CLI reference

Run commands as `images ...` after installation or as `python -m tools.images ...`. The global
`--root` option selects a repository root and defaults to the current directory. Successful
commands return `0`; repository, Docker, or subprocess failures return `2` with an actionable
message on standard error.

| Command | Purpose | Important options/output |
| --- | --- | --- |
| `validate` | Validate manifests, paths, DAG, and bilingual docs. | No output file. |
| `list` | List families, variants, base-resolution modes, and direct dependencies. | Human-readable stdout; base mode is `pinned` or `tag-tracking`. |
| `files --kind shell` | List ShellCheck/shfmt inputs. | Repository-relative paths. |
| `plan` | Calculate publish targets and required ancestors. | Use `--base/--head`, `--all`, or `--family [--variant]`; optional `--output`. |
| `bake` | Render a JSON Bake definition from a plan. | Requires owner, revision, mode, and plan. Modes: `load`, `preflight`, `publish`. |
| `test` | Run declared smoke tests against locally loaded images. | Requires plan, owner, and revision. |
| `build-test` | Build and test every independent graph component. | Requires plan and generated Bake file; reports all failed components. |
| `guard-tags` | Compare local metadata with immutable GHCR tags. | Writes a filtered publication plan; conflicts fail. |
| `promote` | Move each floating variant tag to its immutable release. | Runs only after immutable publication succeeds. |

`plan` emits schema version `1`, changed paths, and topologically ordered targets. A target's
`publish` flag distinguishes affected outputs from ancestors that are built only to satisfy the
DAG. Generated plan and Bake files are ephemeral CI artifacts and must not be edited by hand.

`bake --mode load` loads images into the local Docker daemon and includes floating tags for smoke
tests. `preflight` builds without pushing and produces digest metadata. `publish` pushes only
targets whose plan record still has `publish: true` and writes the scoped main-branch cache.

Use `images <command> --help` as the authoritative option list. The command names, plan schema,
and exit-status meanings are compatibility-sensitive interfaces.
