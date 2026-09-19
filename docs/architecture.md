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

## Image composition and cache boundaries

Shared scripts own capability behavior and validation; Dockerfiles own only capability selection,
argument wiring, and execution order. Build arguments are passed through named script options, so
value branches such as user selection, workspace ownership, and package-mirror selection stay in
the relevant script instead of being duplicated as Dockerfile shell expressions.

An independently changeable capability uses an adjacent `COPY` and `RUN`. Combining several
scripts in one `COPY` would make a change to any one of them invalidate every following capability,
even if the Dockerfile used separate `RUN` instructions. After dependency constraints are met,
stable or expensive capabilities go first and cheap or frequently changed capabilities go last.
This intentionally accepts a few small OCI layers in exchange for useful BuildKit cache boundaries,
clear build logs, and failures attributable to one capability. It is not a rule to split every shell
command: package installation and its apt-list cleanup remain in the same `RUN`.

Identity, SSH, and workspace setup are separate capabilities. User setup first reuses the existing
root account or creates the exact non-root name selected by `DEFAULT_USER`; SSH policy then targets
that resolved account; workspace setup finally creates `WORKSPACE_DIR` and assigns its ownership.
The workspace path is configurable, must be absolute, and cannot be `/` or contain `.`/`..` path
components. Keeping workspace layout out of user management allows either capability to be reused
without importing image-specific directory policy.

The container command and login shell are deliberately independent. An image may keep Bash as its
default command while a developer-shell capability changes the account's login shell to zsh for SSH
sessions. `docker exec` callers select the command they want explicitly; no wrapper guesses a shell
from the invocation environment.

Package installation uses the base image's upstream sources. The manifest `mirror` value becomes
`PACKAGE_MIRROR`, and a final mirror capability owns validation and persisted-source selection only
after all build-time installation is complete. `upstream` is a no-op; `aliyun` rewrites apt and pip
configuration. This improves GitHub-hosted build performance while still allowing a China-oriented
runtime image, and it avoids nondeterministic runtime network probing. `PACKAGE_MIRROR` may remain
visible in the final environment for introspection, but runtime startup never acts on it.

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
fails closed without mounted authorized keys. The `login_user` selector resolves to either the
image's `DEFAULT_USER` or root, and `AllowUsers` limits SSH to that account. In password mode,
`SSH_PASSWORD_FILE` may set the resolved account's password from a runtime-mounted file; passwords
must never be stored in an image layer, manifest, build argument, or environment value. The
account remains locked when no runtime password file is supplied.
