# Repository instructions

- Treat `src/<family>/image.yml` as the source of truth for build variants and dependencies.
- Run `python -m tools.images validate` after changing manifests, shared inputs, or the schema.
- Shared install scripts use capability names, not sequence numbers. Add each consumer to the
  manifest `inputs` list and call the script explicitly from its Dockerfile.
- External bases require exact tags and digests; downloaded binaries require checksum verification.
- Keep English and `_zh` documentation synchronized.
- Never add a global `latest` tag, embedded password, root SSH access, or a runtime mirror probe.
- Do not delete published immutable tags when retiring a variant.

