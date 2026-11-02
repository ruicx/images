"""Enforce ruicx/images account, runtime, and bilingual documentation policies."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from image_kit.repository import ImageRepository, RepositoryError, Variant

USERNAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_-]*$")


def validate_user(family_name: str, variant: Variant) -> None:
    """Validate the account contract used by this repository's shared scripts.

    Parameters
    ----------
    family_name:
        Family owning the variant.
    variant:
        Parsed variant whose account arguments should be checked.

    Raises
    ------
    RepositoryError
        If account arguments are inconsistent or invalid.
    """
    default_user = variant.build_args.get("DEFAULT_USER")
    default_uid = variant.build_args.get("DEFAULT_UID")
    default_gid = variant.build_args.get("DEFAULT_GID")
    default_groups = variant.build_args.get("DEFAULT_GROUPS", "")
    if default_groups and any(
        not USERNAME_PATTERN.fullmatch(group) for group in default_groups.split(",")
    ):
        raise RepositoryError(
            f"{family_name}.{variant.identifier}.build_args.DEFAULT_GROUPS: "
            "must be comma-separated Linux group names"
        )
    if default_user is not None:
        if not USERNAME_PATTERN.fullmatch(default_user):
            raise RepositoryError(
                f"{family_name}.{variant.identifier}.build_args.DEFAULT_USER: "
                f"invalid Linux username '{default_user}'"
            )
        if default_user == "root" and (default_uid is not None or default_gid is not None):
            raise RepositoryError(
                f"{family_name}.{variant.identifier}.build_args: DEFAULT_UID and "
                "DEFAULT_GID must be omitted when DEFAULT_USER is root"
            )
        if default_user == "root" and default_groups:
            raise RepositoryError(
                f"{family_name}.{variant.identifier}.build_args.DEFAULT_GROUPS: "
                "cannot be set when DEFAULT_USER is root"
            )
        if default_user != "root":
            if default_uid is None or default_gid is None:
                raise RepositoryError(
                    f"{family_name}.{variant.identifier}.build_args: DEFAULT_UID and "
                    "DEFAULT_GID are required for a non-root DEFAULT_USER"
                )
            if not default_uid.isdigit() or not default_gid.isdigit():
                raise RepositoryError(
                    f"{family_name}.{variant.identifier}.build_args: DEFAULT_UID and "
                    "DEFAULT_GID must be non-negative integers"
                )


def validate_documentation(repository: ImageRepository) -> None:
    """Require bilingual READMEs and CONTRIBUTING while keeping docs English-only.

    Parameters
    ----------
    repository:
        Loaded consumer repository whose guide pairs should be checked.

    Raises
    ------
    RepositoryError
        If a required documentation file is missing or empty.
    """
    if translations := sorted((repository.root / "docs").glob("*_zh.md")):
        raise RepositoryError(f"docs must be English-only: {translations}")
    pairs = [
        (repository.root / "README.md", repository.root / "README_zh.md"),
        (repository.root / "CONTRIBUTING.md", repository.root / "CONTRIBUTING_zh.md"),
    ]
    pairs.extend(
        (family.directory / "README.md", family.directory / "README_zh.md")
        for family in repository.families.values()
    )
    for english, chinese in pairs:
        for path in (english, chinese):
            if not path.is_file() or not path.read_text(encoding="utf-8").strip():
                raise RepositoryError(
                    "missing or empty bilingual documentation file: "
                    f"{path.relative_to(repository.root)}"
                )


def validate_repository(repository: ImageRepository) -> None:
    """Check repository policies after generic manifest validation.

    Parameters
    ----------
    repository:
        Loaded image repository to inspect.

    Raises
    ------
    RepositoryError
        If account, runtime, mirror, or documentation policy is violated.
    """
    for family in repository.families.values():
        for variant in family.variants:
            if variant.mirror is None:
                raise RepositoryError(f"{family.name}.{variant.identifier}: mirror is required")
            if variant.ssh_mode is None:
                raise RepositoryError(
                    f"{family.name}.{variant.identifier}: runtime.ssh.mode is required"
                )
            validate_user(family.name, variant)
    validate_documentation(repository)


def main() -> int:
    """Validate the consumer checkout without imposing its policies on image-kit.

    Returns
    -------
    int
        Zero when all repository policies pass, otherwise two.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        validate_repository(ImageRepository(args.root).load())
    except RepositoryError as error:
        parser.exit(2, f"repository policy: {error}\n")
    print("repository policies validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
