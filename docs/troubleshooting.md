# Troubleshooting

## Reproduce validation locally

```bash
python -m pip install -e ".[dev]"
python -m ruff check tools
python -m ruff format --check tools
python -m mypy tools/images
python -m pytest
python -m tools.images validate
bash tools/shell-tests/install-arguments.sh
```

Use `images plan --all --output build-plan.json` and the quick-start Bake commands from the root
README to reproduce image builds. Generated JSON files are disposable.

## Common failures

- **A manifest path matches nothing:** fix the path or add the missing file. `inputs` must describe
  real build inputs so change detection cannot silently miss them.
- **An unknown dependency or graph cycle is reported:** verify `family` and `variant`, then remove
  the edge that makes a target depend on itself transitively.
- **A named context cannot be resolved:** make `dependencies[].context` exactly match the
  Dockerfile `FROM <context>` name.
- **A fork PR cannot push or write cache:** this is expected. PRs build locally with read-only
  permissions; only trusted main/manual workflows write Registry images and caches.
- **GHCR returns permission denied:** confirm Actions package access, the repository/package link,
  and `packages: write` on the publish job. Do not replace `GITHUB_TOKEN` with a long-lived token.
- **An immutable tag conflict is reported:** do not overwrite it. Investigate why the same Git SHA
  produced a different manifest digest, then publish from a corrected commit.
- **An immutable tag is skipped:** its remote digest matches the preflight result; this is a safe
  idempotent retry.
- **Anonymous pull fails after publication:** new GHCR packages may be private. Set the package to
  Public and retry after `docker logout ghcr.io`.
- **One graph fails but others continue:** this is intentional failure isolation. The command exits
  nonzero after all independent components have been attempted.
- **SSH exits with an error:** `key-only` requires a mounted non-empty `authorized_keys`; SSH is
  disabled by default and password/root login are unsupported.

For rollback, change the consumer to a previously known immutable SHA tag or digest. Never delete
or overwrite the bad immutable tag; retain it for auditability and diagnose the originating build.
