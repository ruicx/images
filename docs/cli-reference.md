# Shared v2 reference

The pinned component maintains the [shared contract](../vendor/image-kit/docs/cli-reference.md) and
[v2 migration guide](../vendor/image-kit/docs/migration-v2.md). Both image repositories use
the same schema, model and CLI. Initialize submodules and run `uv sync --locked --extra dev`.

YAML `name` is authoritative; directory names are independent. This consumer additionally
requires explicit `mirror`, `runtime.ssh.mode`, valid account fields, and bilingual root/family
READMEs plus CONTRIBUTING. Documents under `docs/` are English-only. Run `images validate` and
`python -m tools.check_repository`; consumer policy is not imposed on unrelated image-kit users.
