# Repository instructions

- Treat `src/<family>/image.yml` as the source of truth for build variants and dependencies.
- Run `python -m tools.images validate` after changing manifests, shared inputs, or the schema.
- Shared install scripts use capability names, not sequence numbers. Add each consumer to the
  manifest `inputs` list and call the script explicitly from its Dockerfile.
- Build-time script configuration uses named GNU `getopt` options. Every parameterized script
  provides `-h`/`--help` and returns 64 for invalid, missing, or positional arguments.
- External bases require exact tags and digests; downloaded binaries require checksum verification.
- Keep English and `_zh` documentation synchronized.
- Add English NumPy-style docstrings and parameter/return type hints to Python APIs. Comments in
  every language must explain intent in English.
- Never add a global `latest` tag, embedded password, root SSH access, or a runtime mirror probe.
- Do not delete published immutable tags when retiring a variant.
