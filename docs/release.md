# Release guide

Pull requests validate and build the affected dependency closure without registry credentials.
Merges to `main` repeat validation, build and test locally, compare immutable tags, push missing
artifacts, and finally promote floating tags. A manual run can select all images, one family, or one
variant.

CI identifies each release as `<variant>-<short-sha>-<run-id>-<attempt>`. To refresh an existing
commit from updated upstream base tags, start a manual publish or rerun the workflow: the new run
or attempt gets a separate immutable tag. No scheduled rebuild is configured. Historical images
and legacy `<variant>-<short-sha>` tags are retained; pin one of those artifacts or its digest to
restore an old environment. Actions logs alone do not preserve an image.

The precise change-selection, cache, permission, idempotency, concurrency, and failure-isolation
rules are defined in [CI/CD behavior](ci-cd.md). Operational recovery is covered by
[Troubleshooting](troubleshooting.md).

Required repository settings:

- Allow GitHub Actions to publish packages with `GITHUB_TOKEN`.
- Protect `main` and require the pull-request workflow.
- Keep workflow permissions read-only by default; the publish job declares `packages: write`.
- After first publication, set every intended package to Public and test anonymous pulls.

GitHub manages source-repository and container-package visibility separately, so a package created
from a public repository may still be private. After the first successful publication of each
package, an owner must open its package settings, change the visibility to **Public**, and verify
that the image can be pulled without registry credentials. For example:

```bash
docker logout ghcr.io
docker pull ghcr.io/ruicx/cuda:12.8.2-devel-ubuntu24.04
```

Automation never deletes immutable tags. Removing a variant from `image.yml` stops future builds
but does not delete tags that have already been published.

The first phase intentionally does not generate SBOMs, provenance attestations, or vulnerability
gates. These can be added without changing `image.yml` or the tag contract.
