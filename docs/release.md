# Release guide

Pull requests validate and build the affected dependency closure without registry credentials.
Merges to `main` repeat validation, build and test locally, compare immutable tags, push missing
artifacts, and finally promote floating tags. A manual run can select all images, one family, or one
variant.

The precise change-selection, cache, permission, idempotency, concurrency, and failure-isolation
rules are defined in [CI/CD behavior](ci-cd.md). Operational recovery is covered by
[Troubleshooting](troubleshooting.md).

Required repository settings:

- Allow GitHub Actions to publish packages with `GITHUB_TOKEN`.
- Protect `main` and require the pull-request workflow.
- Keep workflow permissions read-only by default; the publish job declares `packages: write`.
- After first publication, set every intended package to Public and test anonymous pulls.

The first phase intentionally does not generate SBOMs, provenance attestations, or vulnerability
gates. These can be added without changing `image.yml` or the tag contract.
