"""Verify the consumer policies kept outside the reusable build tool."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from image_kit.repository import ImageRepository, RepositoryError

from tools.check_repository import validate_documentation, validate_repository, validate_user


@pytest.mark.parametrize(
    ("build_args", "message"),
    [
        ({"DEFAULT_USER": "root", "DEFAULT_UID": "1000"}, "must be omitted"),
        (
            {"DEFAULT_USER": "Build User", "DEFAULT_UID": "1000", "DEFAULT_GID": "1000"},
            "invalid Linux username",
        ),
        ({"DEFAULT_USER": "builder"}, "are required"),
        (
            {
                "DEFAULT_USER": "builder",
                "DEFAULT_UID": "1001",
                "DEFAULT_GID": "1001",
                "DEFAULT_GROUPS": "video,,render",
            },
            "must be comma-separated",
        ),
        ({"DEFAULT_USER": "root", "DEFAULT_GROUPS": "video"}, "cannot be set"),
    ],
)
def test_account_contract(build_args: dict[str, str], message: str) -> None:
    """Keep account checks enforced by the consumer after extracting the engine.

    Parameters
    ----------
    build_args:
        Invalid account argument combination.
    message:
        Expected policy diagnostic.
    """
    repository = ImageRepository(Path(__file__).parents[1]).load()
    variant = replace(next(iter(repository.variants.values())), build_args=build_args)
    with pytest.raises(RepositoryError, match=message):
        validate_user(variant.family, variant)


@pytest.mark.parametrize("field", ["ssh_mode", "mirror"])
def test_runtime_configuration_remains_required_here(field: str) -> None:
    """Require local runtime policy even though the generic schema permits omission.

    Parameters
    ----------
    field:
        Optional engine field that this repository requires explicitly.
    """
    repository = ImageRepository(Path(__file__).parents[1]).load()
    family = next(iter(repository.families.values()))
    changed = replace(family.variants[0], **{field: None})
    repository.families[family.name] = replace(family, variants=(changed,))
    with pytest.raises(RepositoryError, match="required"):
        validate_repository(repository)


def test_missing_bilingual_documentation_is_rejected(tmp_path: Path) -> None:
    """Reject missing translated guides in the consumer repository.

    Parameters
    ----------
    tmp_path:
        Isolated repository with an incomplete guide pair.
    """
    (tmp_path / "README.md").write_text("# Example\n", encoding="utf-8")
    with pytest.raises(RepositoryError, match="README_zh.md"):
        validate_documentation(ImageRepository(tmp_path))


def test_checkout_satisfies_repository_policies() -> None:
    """Accept all real family accounts, runtime declarations, and guide pairs."""
    validate_repository(ImageRepository(Path(__file__).parents[1]).load())
