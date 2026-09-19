# Repository instructions

- Treat `src/<family>/image.yml` as the source of truth for build variants and dependencies.
- Run `python -m tools.images validate` after changing manifests, shared inputs, or the schema.
- Shared install scripts use capability names, not sequence numbers. Add each consumer to the
  manifest `inputs` list and call the script explicitly from its Dockerfile.
- Give independently changeable capabilities adjacent `COPY + RUN` pairs. Do not group unrelated
  scripts in one `COPY`; order prerequisites first, then stable/expensive work before cheap or
  frequently changed work.
- Build-time script configuration uses named GNU `getopt` options. Every parameterized script
  provides `-h`/`--help` and returns 64 for invalid, missing, or positional arguments.
- Capability scripts own option validation and value-specific branches; Dockerfiles pass arguments
  and declare execution order instead of duplicating those conditions.
- External bases require exact tags and digests. Downloaded binaries require checksum verification
  unless the consuming family's bilingual README explicitly documents a user-approved exception.
- Rolling developer-shell tools may follow current upstream releases, branches, and installers only
  when the consuming family's bilingual README documents the user-approved reproducibility and
  supply-chain exception; do not extend this exception to runtime or application dependencies.
- Keep English and `_zh` documentation synchronized.
- Add English NumPy-style docstrings and parameter/return type hints to Python APIs. Comments in
  every language must explain intent in English.
- Never add a global `latest` tag, embedded password, or runtime mirror probe. Password/root SSH
  requires an explicit manifest mode, a runtime-mounted password file, and bilingual risk docs.
- Do not delete published immutable tags when retiring a variant.
