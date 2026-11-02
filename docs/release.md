# Release guide

Main and manual builds use the common native digest workflow. PRs validate/build/test without
GHCR credentials or pushes. Selected targets and required ancestors build on native amd64 and
arm64 workers derived from the plan; no QEMU is used. Every worker must pass before public tags
advance. Ancestors remain unpublished unless explicitly selected.

Build tags use `<variant>-<sha12>-<run-id>-<attempt>`. Rebuilding a source revision uses a new
run or attempt. Only main advances floating `<variant>` channels. Existing build tags cannot
be overwritten with different index contents; conflicts and registry lookup errors fail.
No global latest/main/bare-SHA or unprefixed version tags are generated. Historical artifacts
are never deleted by automation. Pin the final index digest for a fixed environment.

Merge validates all native artifacts and saves `publication.json` as `publication-<attempt>`
for 90 days. Use the separate Release verified images workflow with the successful main run ID,
attempt and version such as `v1.2.0`. It checks the source run/workflow and receipt and creates
`<variant>-v1.2.0` from existing registry digests without rebuilding or creating Git tags.
Keep a downloaded receipt for promotions after Actions artifact retention expires. The same
operation is available through `images release`; see the shared
[CLI contract](../vendor/image-kit/docs/cli-reference.md).

Default workflow permissions are read-only. Publishing jobs explicitly receive packages:write;
release additionally receives actions:read. Native workers clean unused hosted SDKs/images,
limit BuildKit parallelism to one, and report disk usage even after failure. Tag updates across
multiple images are sequential, not transactional.

After first publication, verify intended package visibility and anonymous pulls. Registry
package visibility and source repository visibility are managed separately. Do not delete
historical immutable tags when removing a variant from a manifest.
