# Compatibility and lifecycle

The manifest schema version, CLI command names, plan schema, image names, variant identifiers, and
tag format are public compatibility surfaces. Compatible optional fields may be added to schema
version `1`; removing or changing a field's meaning requires a new schema version and a documented
migration period.

Changing a family name changes its GHCR package. Changing a variant identifier creates a new tag
channel. Treat both as remove-and-add operations: announce the replacement in both family READMEs,
keep the old identifier for an appropriate deprecation window when practical, and never repoint an
old channel to semantically unrelated software.

Removing a variant stops future builds only. Automation does not delete existing immutable tags.
Floating tags are mutable convenience channels; immutable SHA tags and digests remain the rollback
mechanism. To roll back a consumer, pin the previous immutable tag or digest. Moving a floating tag
backward is a deliberate maintainer operation outside the automatic workflow and must be recorded.

Shared scripts that are not referenced by any manifest `inputs` entry are pending migration. They
are retained but are not part of the supported phase-one build surface. A script becomes supported
only after a manifest consumes it, it follows the current argument and safety rules, and relevant
smoke tests cover the result.

Phase one supports only `linux/amd64` and does not promise SBOM, provenance, or vulnerability-gate
artifacts. Adding these features must preserve the manifest and tag contracts or introduce an
explicit versioned migration.
