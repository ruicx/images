# Architecture

## Repository model

An image family is a directory under `src/` containing `image.yml`, one parameterized Dockerfile,
bilingual documentation, and smoke tests. The manifest is the source of truth; workflows do not
contain a hand-written image matrix.

This separation keeps release intent declarative: manifests describe variants and dependency
edges, Dockerfiles describe build order, shared scripts provide capability-level installation,
and the Python tooling turns those inputs into one validated execution graph. See the
[manifest reference](manifest-reference.md) for the complete contract.

`images plan` maps changed files to families through each manifest's `inputs`, expands transitive
dependents, and adds the ancestors needed to build the result. The generated Bake graph maps every
internal dependency to a `target:<name>` build context. A pull request therefore tests the base
image built from the same commit instead of a previously published GHCR image.

Disconnected dependency graphs become independent Bake component groups. CI attempts every group
before reporting the combined result, so a failure in one image family does not suppress useful
results from unrelated families. Exact change-impact rules are documented in
[CI/CD behavior](ci-cd.md).

## Tag lifecycle

The immutable tag is `<variant>-<short-sha>`. Before publishing, CI calculates the local manifest
digest and inspects GHCR. A missing tag is pushed, a matching tag is skipped, and a conflicting tag
fails the release. Only after all immutable tags exist does CI update the floating `<variant>` tags.

Consumers that need reproducibility must pin an immutable tag or digest. Floating variant tags are
convenience channels and can change after every successful merge.

## Trust boundaries

Pull requests have read-only repository access, do not log in to GHCR, and never push images or
caches. The main-branch publisher receives only `contents: read` and `packages: write`. Build
secrets must use BuildKit secret mounts; they must never be passed through `ARG`, `ENV`, or `COPY`.

SSH is an explicit runtime policy with `disabled`, `key-only`, and `password` modes. `key-only`
fails closed without mounted authorized keys. `password` may allow root login for a family that
selects it, but passwords must come from a runtime-mounted file and must never be stored in an
image layer, manifest, build argument, or environment value. The root account remains locked when
no runtime password file is supplied.
