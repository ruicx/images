"""Unit tests for manifest validation, graph planning, and Bake rendering."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from tools.images.repository import ImageRepository, RepositoryError


def variant(identifier: str, dependencies: list[dict[str, str]] | None = None) -> dict[str, Any]:
    """Create a minimal schema-valid variant for repository tests.

    Parameters
    ----------
    identifier:
        Variant identifier.
    dependencies:
        Optional internal dependency records.

    Returns
    -------
    dict[str, Any]
        Mutable variant manifest data.
    """
    return {
        "id": identifier,
        "base": {
            "image": "ubuntu:24.04",
            "digest": "sha256:" + "a" * 64,
        },
        "build_args": {},
        "mirror": "upstream",
        "dependencies": dependencies or [],
        "tests": ["src/demo/tests/smoke.sh"],
    }


def manifest(name: str, variants: list[dict[str, Any]]) -> dict[str, Any]:
    """Create a minimal family manifest for repository tests.

    Parameters
    ----------
    name:
        Family and directory name.
    variants:
        Variant records to include.

    Returns
    -------
    dict[str, Any]
        Mutable family manifest data.
    """
    return {
        "schema_version": 1,
        "name": name,
        "description": f"{name} image",
        "dockerfile": f"src/{name}/Dockerfile",
        "context": ".",
        "platforms": ["linux/amd64"],
        "inputs": [f"src/{name}/Dockerfile"],
        "runtime": {"ssh": {"default": "disabled", "login_user": "default"}},
        "publish": True,
        "variants": variants,
    }


def write_family(root: Path, name: str, data: dict[str, Any]) -> None:
    """Write a temporary image family and its required files.

    Parameters
    ----------
    root:
        Temporary repository root.
    name:
        Family directory name.
    data:
        Manifest mapping to serialize.
    """
    directory = root / "src" / name
    (directory / "tests").mkdir(parents=True)
    (directory / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
    (directory / "tests" / "smoke.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    for item in data["variants"]:
        item["tests"] = [f"src/{name}/tests/smoke.sh"]
    (directory / "image.yml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    """Create a temporary repository root containing the production schema."""
    source_schema = Path(__file__).parents[3] / "schemas" / "image.schema.json"
    schema_directory = tmp_path / "schemas"
    schema_directory.mkdir()
    shutil.copyfile(source_schema, schema_directory / "image.schema.json")
    return tmp_path


def test_loads_valid_repository(repo_root: Path) -> None:
    """Load a repository whose manifest and files satisfy all contracts."""
    write_family(repo_root, "demo", manifest("demo", [variant("24.04")]))
    repository = ImageRepository(repo_root).load()
    assert list(repository.families) == ["demo"]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("id", "latest", "latest"),
        ("digest", "sha256:nope", "does not match"),
    ],
)
def test_schema_rejects_invalid_release_inputs(
    repo_root: Path, field: str, value: str, message: str
) -> None:
    """Reject release identifiers and digests that violate the JSON Schema."""
    item = variant("24.04")
    if field == "digest":
        item["base"][field] = value
    else:
        item[field] = value
    write_family(repo_root, "demo", manifest("demo", [item]))
    with pytest.raises(RepositoryError, match=message):
        ImageRepository(repo_root).load()


def test_requires_explicit_base_tag(repo_root: Path) -> None:
    """Reject an external base image without an explicit version tag."""
    item = variant("one")
    item["base"]["image"] = "ubuntu"
    write_family(repo_root, "demo", manifest("demo", [item]))
    with pytest.raises(RepositoryError, match="explicit version tag"):
        ImageRepository(repo_root).load()


def test_rejects_secret_like_build_arguments(repo_root: Path) -> None:
    """Reject build-argument keys that appear to contain secrets."""
    item = variant("one")
    item["build_args"] = {"API_TOKEN": "must-not-be-here"}
    write_family(repo_root, "demo", manifest("demo", [item]))
    with pytest.raises(RepositoryError, match="secret-like keys"):
        ImageRepository(repo_root).load()


def test_accepts_custom_default_user_and_renders_ssh_login_user(repo_root: Path) -> None:
    """Accept a named default user and pass the SSH account selector to Bake."""
    item = variant("one")
    item["build_args"] = {
        "DEFAULT_USER": "builder",
        "DEFAULT_UID": 1001,
        "DEFAULT_GID": 1001,
    }
    data = manifest("demo", [item])
    data["runtime"]["ssh"] = {"default": "password", "login_user": "default"}
    write_family(repo_root, "demo", data)
    repository = ImageRepository(repo_root).load()
    plan = repository.make_plan({("demo", "one")})
    bake = repository.render_bake(plan, "example", "1" * 40, "load")
    target = next(iter(bake["target"].values()))
    assert target["args"]["DEFAULT_USER"] == "builder"
    assert target["args"]["SSH_LOGIN_USER"] == "default"


@pytest.mark.parametrize(
    ("build_args", "message"),
    [
        (
            {"DEFAULT_USER": "root", "DEFAULT_UID": 1000},
            "must be omitted when DEFAULT_USER is root",
        ),
        (
            {"DEFAULT_USER": "Build User", "DEFAULT_UID": 1000, "DEFAULT_GID": 1000},
            "invalid Linux username",
        ),
        (
            {"DEFAULT_USER": "builder"},
            "are required for a non-root DEFAULT_USER",
        ),
    ],
)
def test_rejects_invalid_default_user_contract(
    repo_root: Path, build_args: dict[str, object], message: str
) -> None:
    """Reject inconsistent default-user build arguments."""
    item = variant("one")
    item["build_args"] = build_args
    write_family(repo_root, "demo", manifest("demo", [item]))
    with pytest.raises(RepositoryError, match=message):
        ImageRepository(repo_root).load()


def test_rejects_duplicate_variant(repo_root: Path) -> None:
    """Reject duplicate variant identifiers within one family."""
    write_family(repo_root, "demo", manifest("demo", [variant("one"), variant("one")]))
    with pytest.raises(RepositoryError, match="duplicate variant"):
        ImageRepository(repo_root).load()


def test_rejects_unknown_dependency(repo_root: Path) -> None:
    """Reject an internal dependency that does not identify a known target."""
    dependency = {"context": "base", "family": "missing", "variant": "one"}
    write_family(repo_root, "demo", manifest("demo", [variant("one", [dependency])]))
    with pytest.raises(RepositoryError, match="unknown target missing/one"):
        ImageRepository(repo_root).load()


def test_rejects_dependency_cycle(repo_root: Path) -> None:
    """Reject a dependency graph containing a cycle."""
    one_dep = {"context": "two", "family": "demo", "variant": "two"}
    two_dep = {"context": "one", "family": "demo", "variant": "one"}
    write_family(
        repo_root,
        "demo",
        manifest("demo", [variant("one", [one_dep]), variant("two", [two_dep])]),
    )
    with pytest.raises(RepositoryError, match="contains a cycle"):
        ImageRepository(repo_root).load()


def test_change_propagates_to_dependents_and_bake_uses_target_context(repo_root: Path) -> None:
    """Propagate base changes and connect consumers to same-build targets."""
    write_family(repo_root, "base", manifest("base", [variant("one")]))
    dependency = {"context": "internal_base", "family": "base", "variant": "one"}
    child = manifest("child", [variant("one", [dependency])])
    child["variants"][0]["tests"] = ["src/child/tests/smoke.sh"]
    write_family(repo_root, "child", child)
    repository = ImageRepository(repo_root).load()

    affected = repository.affected(["src/base/Dockerfile"])
    assert affected == {("base", "one"), ("child", "one")}
    plan = repository.make_plan(affected)
    bake = repository.render_bake(plan, "Example", "1" * 40, "load")
    child_target = repository.variants[("child", "one")].target_name
    base_target = repository.variants[("base", "one")].target_name
    assert bake["target"][child_target]["contexts"]["internal_base"] == f"target:{base_target}"


def test_tags_use_family_variant_and_short_revision(repo_root: Path) -> None:
    """Generate immutable and floating tags from the release contract."""
    write_family(repo_root, "demo", manifest("demo", [variant("24.04")]))
    repository = ImageRepository(repo_root).load()
    plan = repository.make_plan({("demo", "24.04")})
    bake = repository.render_bake(plan, "Example", "abcdef012345" + "0" * 28, "load")
    target = next(iter(bake["target"].values()))
    assert target["tags"] == [
        "ghcr.io/example/demo:24.04-abcdef012345",
        "ghcr.io/example/demo:24.04",
    ]


def test_independent_graph_branches_get_separate_bake_groups(repo_root: Path) -> None:
    """Place disconnected image graphs in independent Bake groups."""
    write_family(repo_root, "one", manifest("one", [variant("base")]))
    write_family(repo_root, "two", manifest("two", [variant("base")]))
    repository = ImageRepository(repo_root).load()
    plan = repository.make_plan(set(repository.variants))
    bake = repository.render_bake(plan, "example", "1" * 40, "load")
    component_groups = [name for name in bake["group"] if name.startswith("component-")]
    assert len(component_groups) == 2


def test_infrastructure_changes_affect_all_but_docs_do_not(repo_root: Path) -> None:
    """Apply global rebuild rules without rebuilding for unrelated docs."""
    write_family(repo_root, "demo", manifest("demo", [variant("one"), variant("two")]))
    repository = ImageRepository(repo_root).load()
    assert repository.affected(["tools/images/cli.py"]) == set(repository.variants)
    assert repository.affected([".dockerignore"]) == set(repository.variants)
    assert repository.affected(["docs/development.md"]) == set()
