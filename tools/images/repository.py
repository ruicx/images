"""Repository domain model and Buildx Bake graph generation."""

from __future__ import annotations

import fnmatch
import json
import re
import subprocess
from collections import defaultdict, deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
import yaml

TargetKey = tuple[str, str]
SHA_PATTERN = re.compile(r"^[0-9a-f]{12,40}$")
SENSITIVE_ARGUMENT_PATTERN = re.compile(r"(?:SECRET|PASSWORD|TOKEN|PRIVATE_KEY)", re.IGNORECASE)
USERNAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_-]*$")


class RepositoryError(RuntimeError):
    """Represent a user-actionable repository configuration error."""


@dataclass(frozen=True)
class Dependency:
    """Describe an internal image dependency exposed as a BuildKit context.

    Attributes
    ----------
    context:
        Dockerfile context name used by the dependent image.
    family:
        Name of the image family that provides the dependency.
    variant:
        Variant identifier in the provider family.
    """

    context: str
    family: str
    variant: str

    @property
    def key(self) -> TargetKey:
        """Return the repository key of the dependency target."""
        return (self.family, self.variant)


@dataclass(frozen=True)
class Variant:
    """Store the normalized build contract for one image variant.

    Attributes
    ----------
    family:
        Owning image family.
    identifier:
        Stable variant identifier and floating tag name.
    base_image:
        External base image including an explicit version tag.
    base_digest:
        Pinned digest for the external base image.
    build_args:
        Non-secret Docker build arguments declared by the manifest.
    mirror:
        Package mirror policy selected by the manifest.
    ssh_mode:
        Default runtime SSH policy.
    ssh_login_user:
        SSH account selector, either the image default user or root.
    dependencies:
        Internal image targets provided as named BuildKit contexts.
    tests:
        Repository-relative smoke-test scripts.
    """

    family: str
    identifier: str
    base_image: str
    base_digest: str
    build_args: Mapping[str, str]
    mirror: str
    ssh_mode: str
    ssh_login_user: str
    dependencies: tuple[Dependency, ...]
    tests: tuple[str, ...]

    @property
    def key(self) -> TargetKey:
        """Return the unique repository key for this variant."""
        return (self.family, self.identifier)

    @property
    def target_name(self) -> str:
        """Return the normalized Buildx Bake target name."""
        return sanitize_target(f"{self.family}--{self.identifier}")

    @property
    def base_reference(self) -> str:
        """Return the immutable external base image reference."""
        return f"{self.base_image}@{self.base_digest}"


@dataclass(frozen=True)
class Family:
    """Store a normalized image-family manifest.

    Attributes
    ----------
    name:
        Family name, which must match its directory name.
    directory:
        Absolute path to the family directory.
    description:
        Human-readable family description.
    dockerfile:
        Absolute path to the parameterized Dockerfile.
    context:
        Absolute Docker build context.
    platforms:
        Target platforms accepted by the current schema.
    inputs:
        Repository-relative glob patterns that trigger family rebuilds.
    publish:
        Whether selected variants may be published from the main branch.
    variants:
        Variants released by this family.
    """

    name: str
    directory: Path
    description: str
    dockerfile: Path
    context: Path
    platforms: tuple[str, ...]
    inputs: tuple[str, ...]
    publish: bool
    variants: tuple[Variant, ...]


def sanitize_target(value: str) -> str:
    """Convert an arbitrary identifier into a Bake-compatible target name.

    Parameters
    ----------
    value:
        Identifier to normalize.

    Returns
    -------
    str
        Identifier with unsupported characters replaced by hyphens.
    """
    return re.sub(r"[^a-zA-Z0-9_-]", "-", value)


class ImageRepository:
    """Load, validate, plan, and render a repository of image manifests.

    Parameters
    ----------
    root:
        Repository root containing ``schemas/`` and ``src/``.
    """

    def __init__(self, root: Path) -> None:
        """Initialize an unloaded repository model.

        Parameters
        ----------
        root:
            Repository root to inspect.
        """
        self.root = root.resolve()
        self.schema_path = self.root / "schemas" / "image.schema.json"
        self.families: dict[str, Family] = {}
        self.variants: dict[TargetKey, Variant] = {}

    def load(self) -> ImageRepository:
        """Load and validate every image manifest.

        Returns
        -------
        ImageRepository
            This repository instance populated with families and variants.

        Raises
        ------
        RepositoryError
            If the schema, a manifest, a path, or the dependency graph is invalid.
        """
        if not self.schema_path.is_file():
            raise RepositoryError(f"schema not found: {self.schema_path}")
        schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        manifests = sorted((self.root / "src").glob("*/image.yml"))
        if not manifests:
            raise RepositoryError("no image manifests found under src/<family>/image.yml")

        errors: list[str] = []
        raw_manifests: list[tuple[Path, dict[str, Any]]] = []
        for path in manifests:
            try:
                loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError as parse_error:
                errors.append(f"{path.relative_to(self.root)}: invalid YAML: {parse_error}")
                continue
            if not isinstance(loaded, dict):
                errors.append(f"{path.relative_to(self.root)}: root must be a mapping")
                continue
            for schema_error in sorted(
                validator.iter_errors(loaded), key=lambda item: list(item.path)
            ):
                field = ".".join(str(part) for part in schema_error.absolute_path) or "<root>"
                errors.append(f"{path.relative_to(self.root)}:{field}: {schema_error.message}")
            raw_manifests.append((path, loaded))

        if errors:
            raise RepositoryError("manifest validation failed:\n" + "\n".join(errors))

        for path, raw in raw_manifests:
            family = self._parse_family(path, raw)
            if family.name in self.families:
                raise RepositoryError(f"duplicate image family name: {family.name}")
            if family.name != path.parent.name:
                raise RepositoryError(
                    f"{path.relative_to(self.root)}: name '{family.name}' must match directory"
                )
            self.families[family.name] = family
            for variant in family.variants:
                if variant.key in self.variants:
                    raise RepositoryError(
                        f"{family.name}: duplicate variant id '{variant.identifier}'"
                    )
                self.variants[variant.key] = variant

        self._validate_paths_and_dependencies()
        self.topological_order()
        return self

    def _parse_family(self, path: Path, raw: dict[str, Any]) -> Family:
        """Normalize a schema-valid manifest into immutable data models.

        Parameters
        ----------
        path:
            Path to the family manifest.
        raw:
            Parsed manifest mapping.

        Returns
        -------
        Family
            Normalized family definition.
        """
        family_name = str(raw["name"])
        default_ssh = str(raw["runtime"]["ssh"]["default"])
        default_ssh_login_user = str(raw["runtime"]["ssh"]["login_user"])
        variants: list[Variant] = []
        for raw_variant in raw["variants"]:
            runtime = raw_variant.get("runtime", {})
            ssh_mode = str(runtime.get("ssh", {}).get("default", default_ssh))
            ssh_login_user = str(runtime.get("ssh", {}).get("login_user", default_ssh_login_user))
            dependencies = tuple(
                Dependency(
                    context=str(item["context"]),
                    family=str(item["family"]),
                    variant=str(item["variant"]),
                )
                for item in raw_variant["dependencies"]
            )
            variants.append(
                Variant(
                    family=family_name,
                    identifier=str(raw_variant["id"]),
                    base_image=str(raw_variant["base"]["image"]),
                    base_digest=str(raw_variant["base"]["digest"]),
                    build_args={
                        key: str(value) for key, value in raw_variant["build_args"].items()
                    },
                    mirror=str(raw_variant["mirror"]),
                    ssh_mode=ssh_mode,
                    ssh_login_user=ssh_login_user,
                    dependencies=dependencies,
                    tests=tuple(str(item) for item in raw_variant["tests"]),
                )
            )
        return Family(
            name=family_name,
            directory=path.parent,
            description=str(raw["description"]),
            dockerfile=self.root / str(raw["dockerfile"]),
            context=self.root / str(raw["context"]),
            platforms=tuple(str(item) for item in raw["platforms"]),
            inputs=tuple(str(item) for item in raw["inputs"]),
            publish=bool(raw["publish"]),
            variants=tuple(variants),
        )

    def _validate_paths_and_dependencies(self) -> None:
        """Validate repository paths, build arguments, tests, and dependency edges.

        Raises
        ------
        RepositoryError
            If any semantic constraint outside the JSON Schema is violated.
        """
        for family in self.families.values():
            for label, path in (("dockerfile", family.dockerfile), ("context", family.context)):
                if not path.exists():
                    raise RepositoryError(f"{family.name}.{label}: path does not exist: {path}")
                try:
                    path.resolve().relative_to(self.root)
                except ValueError as error:
                    raise RepositoryError(
                        f"{family.name}.{label}: path escapes repository: {path}"
                    ) from error
            for pattern in family.inputs:
                if not list(self.root.glob(pattern)):
                    raise RepositoryError(
                        f"{family.name}.inputs: pattern matches nothing: {pattern}"
                    )
            for variant in family.variants:
                image_name = variant.base_image.rsplit("/", maxsplit=1)[-1]
                if ":" not in image_name:
                    raise RepositoryError(
                        f"{family.name}.{variant.identifier}.base.image: "
                        "an explicit version tag is required"
                    )
                sensitive_args = sorted(
                    key for key in variant.build_args if SENSITIVE_ARGUMENT_PATTERN.search(key)
                )
                if sensitive_args:
                    raise RepositoryError(
                        f"{family.name}.{variant.identifier}.build_args: secret-like keys are "
                        f"forbidden: {', '.join(sensitive_args)}"
                    )
                default_user = variant.build_args.get("DEFAULT_USER")
                default_uid = variant.build_args.get("DEFAULT_UID")
                default_gid = variant.build_args.get("DEFAULT_GID")
                if default_user is not None:
                    if not USERNAME_PATTERN.fullmatch(default_user):
                        raise RepositoryError(
                            f"{family.name}.{variant.identifier}.build_args.DEFAULT_USER: "
                            f"invalid Linux username '{default_user}'"
                        )
                    if default_user == "root" and (
                        default_uid is not None or default_gid is not None
                    ):
                        raise RepositoryError(
                            f"{family.name}.{variant.identifier}.build_args: DEFAULT_UID and "
                            "DEFAULT_GID must be omitted when DEFAULT_USER is root"
                        )
                    if default_user != "root":
                        if default_uid is None or default_gid is None:
                            raise RepositoryError(
                                f"{family.name}.{variant.identifier}.build_args: DEFAULT_UID and "
                                "DEFAULT_GID are required for a non-root DEFAULT_USER"
                            )
                        if not default_uid.isdigit() or not default_gid.isdigit():
                            raise RepositoryError(
                                f"{family.name}.{variant.identifier}.build_args: DEFAULT_UID and "
                                "DEFAULT_GID must be non-negative integers"
                            )
                contexts: set[str] = set()
                for dependency in variant.dependencies:
                    if dependency.key not in self.variants:
                        raise RepositoryError(
                            f"{family.name}.{variant.identifier}.dependencies: unknown target "
                            f"{dependency.family}/{dependency.variant}"
                        )
                    if dependency.context in contexts:
                        raise RepositoryError(
                            f"{family.name}.{variant.identifier}.dependencies: duplicate context "
                            f"'{dependency.context}'"
                        )
                    contexts.add(dependency.context)
                for test in variant.tests:
                    test_path = self.root / test
                    if not test_path.is_file():
                        raise RepositoryError(
                            f"{family.name}.{variant.identifier}.tests: file not found: {test}"
                        )

    def validate_documentation(self) -> None:
        """Require every normative guide to have a non-empty Chinese counterpart.

        Raises
        ------
        RepositoryError
            If a required documentation file is missing or empty.
        """
        pairs = [
            (self.root / "README.md", self.root / "README_zh.md"),
            (self.root / "docs" / "architecture.md", self.root / "docs" / "architecture_zh.md"),
            (self.root / "docs" / "ci-cd.md", self.root / "docs" / "ci-cd_zh.md"),
            (self.root / "docs" / "cli-reference.md", self.root / "docs" / "cli-reference_zh.md"),
            (self.root / "docs" / "development.md", self.root / "docs" / "development_zh.md"),
            (self.root / "docs" / "lifecycle.md", self.root / "docs" / "lifecycle_zh.md"),
            (
                self.root / "docs" / "manifest-reference.md",
                self.root / "docs" / "manifest-reference_zh.md",
            ),
            (self.root / "docs" / "release.md", self.root / "docs" / "release_zh.md"),
            (
                self.root / "docs" / "troubleshooting.md",
                self.root / "docs" / "troubleshooting_zh.md",
            ),
            (self.root / "CONTRIBUTING.md", self.root / "CONTRIBUTING_zh.md"),
        ]
        pairs.extend(
            (family.directory / "README.md", family.directory / "README_zh.md")
            for family in self.families.values()
        )
        for english, chinese in pairs:
            for path in (english, chinese):
                if not path.is_file() or not path.read_text(encoding="utf-8").strip():
                    raise RepositoryError(
                        "missing or empty bilingual documentation file: "
                        f"{path.relative_to(self.root)}"
                    )

    def shell_files(self) -> list[Path]:
        """Return ShellCheck inputs used by manifests and repository tooling.

        Returns
        -------
        list[pathlib.Path]
            Sorted, de-duplicated absolute paths to shell scripts.
        """
        paths: set[Path] = set()
        paths.update(self.root.glob("tools/**/*.sh"))
        for family in self.families.values():
            for pattern in family.inputs:
                paths.update(path for path in self.root.glob(pattern) if path.suffix == ".sh")
            for variant in family.variants:
                paths.update(
                    self.root / test for test in variant.tests if Path(test).suffix == ".sh"
                )
        return sorted(paths)

    def topological_order(self, subset: Iterable[TargetKey] | None = None) -> list[TargetKey]:
        """Order image variants so every dependency precedes its consumers.

        Parameters
        ----------
        subset:
            Optional target subset. Dependencies outside the subset are ignored.

        Returns
        -------
        list[TargetKey]
            Deterministic topological ordering.

        Raises
        ------
        RepositoryError
            If the selected graph contains a dependency cycle.
        """
        selected = set(subset if subset is not None else self.variants)
        indegree = {key: 0 for key in selected}
        children: dict[TargetKey, list[TargetKey]] = defaultdict(list)
        for key in selected:
            for dependency in self.variants[key].dependencies:
                if dependency.key in selected:
                    indegree[key] += 1
                    children[dependency.key].append(key)
        ready = deque(sorted(key for key, degree in indegree.items() if degree == 0))
        result: list[TargetKey] = []
        while ready:
            key = ready.popleft()
            result.append(key)
            for child in sorted(children[key]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
        if len(result) != len(selected):
            cyclic = sorted(key for key, degree in indegree.items() if degree > 0)
            formatted = ", ".join(f"{family}/{variant}" for family, variant in cyclic)
            raise RepositoryError(f"image dependency graph contains a cycle: {formatted}")
        return result

    def component_groups(self, subset: Iterable[TargetKey]) -> list[set[TargetKey]]:
        """Partition targets into independent undirected graph components.

        Parameters
        ----------
        subset:
            Targets to partition.

        Returns
        -------
        list[set[TargetKey]]
            Components that can be built and tested independently.
        """
        selected = set(subset)
        adjacency: dict[TargetKey, set[TargetKey]] = {key: set() for key in selected}
        for key in selected:
            for dependency in self.variants[key].dependencies:
                if dependency.key in selected:
                    adjacency[key].add(dependency.key)
                    adjacency[dependency.key].add(key)

        groups: list[set[TargetKey]] = []
        remaining = set(selected)
        while remaining:
            seed = min(remaining)
            group = {seed}
            queue = deque([seed])
            remaining.remove(seed)
            while queue:
                for neighbour in sorted(adjacency[queue.popleft()]):
                    if neighbour in remaining:
                        remaining.remove(neighbour)
                        group.add(neighbour)
                        queue.append(neighbour)
            groups.append(group)
        return groups

    def changed_files(self, base: str, head: str) -> list[str]:
        """List files changed between two Git revisions using merge-base semantics.

        Parameters
        ----------
        base:
            Base Git revision.
        head:
            Head Git revision.

        Returns
        -------
        list[str]
            Repository-relative paths using forward slashes.

        Raises
        ------
        RepositoryError
            If Git cannot calculate the diff.
        """
        command = ["git", "diff", "--name-only", f"{base}...{head}"]
        result = subprocess.run(
            command,
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RepositoryError(f"git diff failed: {result.stderr.strip()}")
        return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line]

    def affected(self, changed_files: Sequence[str]) -> set[TargetKey]:
        """Calculate directly changed variants and all transitive consumers.

        Parameters
        ----------
        changed_files:
            Repository-relative changed paths.

        Returns
        -------
        set[TargetKey]
            Publish targets affected by the changes.
        """
        infrastructure_prefixes = (
            ".github/workflows/",
            "schemas/",
            "tools/images/",
        )
        infrastructure_files = {".dockerignore", "pyproject.toml"}
        direct: set[TargetKey]
        if any(
            path in infrastructure_files or path.startswith(infrastructure_prefixes)
            for path in changed_files
        ):
            direct = set(self.variants)
        else:
            direct = set()
            for family in self.families.values():
                family_prefix = f"src/{family.name}/"
                if any(path.startswith(family_prefix) for path in changed_files) or any(
                    fnmatch.fnmatch(path, pattern)
                    for pattern in family.inputs
                    for path in changed_files
                ):
                    direct.update(variant.key for variant in family.variants)

        # Reverse edges let a changed base propagate to every transitive consumer.
        reverse: dict[TargetKey, set[TargetKey]] = defaultdict(set)
        for key, variant in self.variants.items():
            for dependency in variant.dependencies:
                reverse[dependency.key].add(key)
        affected = set(direct)
        queue = deque(direct)
        while queue:
            for child in reverse[queue.popleft()]:
                if child not in affected:
                    affected.add(child)
                    queue.append(child)
        return affected

    def build_closure(self, publish_targets: Iterable[TargetKey]) -> set[TargetKey]:
        """Add every transitive build dependency required by publish targets.

        Parameters
        ----------
        publish_targets:
            Variants selected for testing or publication.

        Returns
        -------
        set[TargetKey]
            Selected targets plus their transitive ancestors.
        """
        # Publication selection expands upward so internal bases are built from this commit.
        closure = set(publish_targets)
        queue = deque(closure)
        while queue:
            for dependency in self.variants[queue.popleft()].dependencies:
                if dependency.key not in closure:
                    closure.add(dependency.key)
                    queue.append(dependency.key)
        return closure

    def make_plan(
        self,
        publish_targets: Iterable[TargetKey],
        changed_files: Sequence[str] = (),
    ) -> dict[str, Any]:
        """Create the stable JSON plan consumed by CI and Bake rendering.

        Parameters
        ----------
        publish_targets:
            Variants affected by a change or selected manually.
        changed_files:
            Optional changed paths retained for diagnostics.

        Returns
        -------
        dict[str, Any]
            Versioned plan containing topologically ordered build targets.
        """
        publish_set = set(publish_targets)
        build_set = self.build_closure(publish_set)
        targets: list[dict[str, Any]] = []
        for key in self.topological_order(build_set):
            variant = self.variants[key]
            family = self.families[variant.family]
            targets.append(
                {
                    "family": variant.family,
                    "variant": variant.identifier,
                    "target": variant.target_name,
                    "publish": key in publish_set and family.publish,
                }
            )
        return {"schema_version": 1, "changed_files": list(changed_files), "targets": targets}

    def render_bake(
        self,
        plan: Mapping[str, Any],
        owner: str,
        revision: str,
        mode: str,
        source_repository: str | None = None,
    ) -> dict[str, Any]:
        """Render a Docker Buildx Bake definition for a build plan.

        Parameters
        ----------
        plan:
            Plan produced by :meth:`make_plan`.
        owner:
            GHCR namespace owner.
        revision:
            Full Git revision used for labels and immutable tags.
        mode:
            One of ``load``, ``preflight``, or ``publish``.
        source_repository:
            Optional ``owner/repository`` value for the OCI source label.

        Returns
        -------
        dict[str, Any]
            JSON-serializable Bake groups and targets.

        Raises
        ------
        RepositoryError
            If the revision or requested mode is invalid.
        """
        normalized_owner = owner.lower()
        short_revision = revision[:12].lower()
        if not SHA_PATTERN.fullmatch(short_revision):
            raise RepositoryError(
                "revision must contain at least 12 lowercase hexadecimal characters"
            )
        planned = {(item["family"], item["variant"]): item for item in plan["targets"]}
        targets: dict[str, Any] = {}
        default_targets: list[str] = []
        for key in self.topological_order(planned):
            variant = self.variants[key]
            family = self.families[variant.family]
            planned_item = planned[key]
            immutable_tag = (
                f"ghcr.io/{normalized_owner}/{variant.family}:{variant.identifier}-{short_revision}"
            )
            floating_tag = f"ghcr.io/{normalized_owner}/{variant.family}:{variant.identifier}"
            build_args = dict(variant.build_args)
            build_args.update(
                {
                    "BASE_IMAGE": variant.base_reference,
                    "IMAGE_REVISION": revision,
                    "IMAGE_VERSION": f"{variant.identifier}-{short_revision}",
                    "PACKAGE_MIRROR": variant.mirror,
                    "SSH_MODE": variant.ssh_mode,
                    "SSH_LOGIN_USER": variant.ssh_login_user,
                }
            )
            target: dict[str, Any] = {
                "context": str(family.context.relative_to(self.root)).replace("\\", "/"),
                "dockerfile": str(family.dockerfile.relative_to(self.root)).replace("\\", "/"),
                "platforms": list(family.platforms),
                "args": build_args,
                "contexts": {
                    dependency.context: f"target:{self.variants[dependency.key].target_name}"
                    for dependency in variant.dependencies
                },
                "labels": {
                    "org.opencontainers.image.source": (
                        f"https://github.com/{source_repository}"
                        if source_repository
                        else f"https://github.com/{normalized_owner}"
                    ),
                    "org.opencontainers.image.revision": revision,
                    "org.opencontainers.image.version": f"{variant.identifier}-{short_revision}",
                    "org.opencontainers.image.title": variant.family,
                },
                "cache-from": [f"type=gha,scope={variant.family}-{variant.identifier}"],
                "tags": [immutable_tag],
            }
            if mode == "load":
                target["output"] = ["type=docker"]
                target["tags"].append(floating_tag)
            elif mode == "preflight":
                target["output"] = ["type=image,push=false"]
            elif mode == "publish":
                if planned_item["publish"]:
                    target["output"] = ["type=registry"]
                    target["cache-to"] = [
                        f"type=gha,mode=max,scope={variant.family}-{variant.identifier}"
                    ]
            else:
                raise RepositoryError(f"unsupported bake mode: {mode}")
            targets[variant.target_name] = target
            if mode != "publish" or planned_item["publish"]:
                default_targets.append(variant.target_name)
        groups: dict[str, Any] = {"default": {"targets": default_targets}}
        default_keys = {
            key for key, item in planned.items() if mode != "publish" or bool(item["publish"])
        }
        for index, component in enumerate(self.component_groups(default_keys)):
            groups[f"component-{index}"] = {
                "targets": [
                    self.variants[key].target_name for key in self.topological_order(component)
                ]
            }
        return {"group": groups, "target": targets}

    def select(self, family: str | None, variant: str | None) -> set[TargetKey]:
        """Resolve a manual all, family, or variant selection.

        Parameters
        ----------
        family:
            Optional family name.
        variant:
            Optional variant identifier, valid only with ``family``.

        Returns
        -------
        set[TargetKey]
            Selected publish targets.

        Raises
        ------
        RepositoryError
            If the selection is incomplete or names an unknown target.
        """
        if variant and not family:
            raise RepositoryError("--variant requires --family")
        if family:
            if family not in self.families:
                raise RepositoryError(f"unknown image family: {family}")
            if variant:
                key = (family, variant)
                if key not in self.variants:
                    raise RepositoryError(f"unknown image variant: {family}/{variant}")
                return {key}
            return {item.key for item in self.families[family].variants}
        return set(self.variants)


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk.

    Parameters
    ----------
    path:
        JSON file to read.

    Returns
    -------
    dict[str, Any]
        Parsed JSON object.

    Raises
    ------
    RepositoryError
        If the JSON root is not an object.
    """
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise RepositoryError(f"JSON root must be an object: {path}")
    return loaded


def write_json(data: Mapping[str, Any], output: Path | None) -> None:
    """Write deterministic JSON to a file or standard output.

    Parameters
    ----------
    data:
        Mapping to serialize.
    output:
        Destination path, or ``None`` to print to standard output.
    """
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if output:
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
