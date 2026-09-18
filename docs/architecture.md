# Architecture

## Repository model

An image family is a directory under `src/` containing `image.yml`, one parameterized Dockerfile,
bilingual documentation, and smoke tests. The manifest is the source of truth; workflows do not
contain a hand-written image matrix.

`images plan` maps changed files to families through each manifest's `inputs`, expands transitive
dependents, and adds the ancestors needed to build the result. The generated Bake graph maps every
internal dependency to a `target:<name>` build context. A pull request therefore tests the base
image built from the same commit instead of a previously published GHCR image.

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

SSH is an optional runtime capability. Images default to a locked non-root user and disabled SSH.
The only supported enabled mode is `key-only`; it rejects startup without mounted authorized keys.

