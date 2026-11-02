# Compatibility and lifecycle

The manifest schema version, CLI command names, plan schema, image names, variant identifiers, and
tag format are public compatibility surfaces. Compatible optional fields may be added to schema
version `2`; removing or changing a field's meaning requires a new schema version and a documented
migration period.

Changing a family name changes its GHCR package. Changing a variant identifier creates a new tag
channel. Treat both as remove-and-add operations: announce the replacement in both family READMEs,
keep the old identifier for an appropriate deprecation window when practical, and never repoint an
old channel to semantically unrelated software.

Removing a variant stops future builds only. Automation does not delete existing immutable tags.
Floating tags are mutable convenience channels; immutable build tags and digests remain the rollback
mechanism. To roll back a consumer, pin the previous immutable tag or digest. Moving a floating tag
backward is a deliberate maintainer operation outside the automatic workflow and must be recorded.

New CI releases use `<variant>-<short-sha>-<run-id>-<attempt>` instead of the legacy
`<variant>-<short-sha>` format. Existing immutable tags remain untouched. Local CLI calls without
`--build-id` use `<variant>-<sha12>-local` for load/test only; CI always supplies a build batch to support rolling rebuilds.

Shared scripts that are not referenced by any manifest `inputs` entry are pending migration. They
are retained but are not part of the supported phase-one build surface. A script becomes supported
only after a manifest consumes it, it follows the current argument and safety rules, and relevant
smoke tests cover the result.

Each family declares one or both native platforms, `linux/amd64` and `linux/arm64`; internal parents must cover their children. The repository does not
promise SBOM, provenance, or vulnerability-gate artifacts. Adding these features must preserve the manifest and tag contracts or introduce an
explicit versioned migration.
