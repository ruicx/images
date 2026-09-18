# CI/CD behavior

## Change impact and graph construction

Changes to `.dockerignore`, `pyproject.toml`, `.github/workflows/**`, `schemas/**`, or
`tools/images/**` affect every variant. A change below `src/<family>/` or matching that family's
`inputs` affects every variant in the family. Documentation-only changes outside those inputs do
not build images.

The planner first expands transitive consumers: changing a base rebuilds every downstream target.
It then adds transitive ancestors required to build the selected outputs. Ancestors appear in the
plan with `publish: false` unless independently affected. The final order is topological.

Targets are partitioned into disconnected graph components. CI builds and tests all components,
records failures, and continues with unrelated components so one broken image graph does not hide
results from another.

## Workflow matrix

| Behavior | Pull request | Push to `main` | Manual publish |
| --- | --- | --- | --- |
| Selection | Changed closure | Changed closure; all on initial push | All, one family, or one variant |
| Permissions | `contents: read` | `contents: read`, `packages: write` | Same as main publish |
| Registry login | No | After local tests | After local tests |
| Image push | Never | Missing immutable tags only | Missing immutable tags only |
| Cache | Read family/variant scope | Read and write family/variant scope | Read and write family/variant scope |
| Floating tags | Never | Promoted after immutable tags succeed | Same as main publish |

Fork pull requests therefore remain read-only and receive no package credentials. An empty plan
skips Buildx setup and all image work while repository validation still runs.

## Publication transaction

The main workflow validates the repository, builds and smoke-tests locally, logs in with
`GITHUB_TOKEN`, performs an unpushed preflight build, and compares each local digest with GHCR.
A missing immutable tag remains in the publication plan, a matching digest is removed as an
idempotent retry, and a different digest fails. Missing immutable tags are pushed before any
floating tag is promoted.

The concurrency group `publish-images-main` serializes publishers and does not cancel an in-flight
release. Cache scope is `<family>-<variant>` to prevent unrelated variants from overwriting one
another. Third-party Actions are pinned to commit SHAs.

Generated plan, metadata, and Bake files are workflow-local artifacts. They contain no secrets.
