"""Run the openbb-sugra tests against the OpenBB v5 source tree overlay."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

OPENBB_SOURCE_PATHS = (
    ("openbb_platform", "core"),
    ("openbb_platform", "providers", "congress_gov"),
    ("openbb_platform", "providers", "famafrench"),
    ("openbb_platform", "providers", "sec"),
)


def _existing_source_paths(openbb_path: Path) -> list[str]:
    """Return import paths for the OpenBB v5 source packages."""
    missing: list[Path] = []
    paths: list[str] = []
    for parts in OPENBB_SOURCE_PATHS:
        source_path = openbb_path.joinpath(*parts)
        if not source_path.exists():
            missing.append(source_path)
        paths.append(str(source_path))
    if missing:
        joined = "\n".join(str(path) for path in missing)
        raise SystemExit(f"OpenBB source path is incomplete:\n{joined}")
    return paths


def main() -> int:
    """Run pytest with OpenBB v5 packages ahead of installed OpenBB packages."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--openbb-path",
        required=True,
        type=Path,
        help="Path to an OpenBB repository checkout on the v5 branch.",
    )
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    overlay_paths = [str(project_root), *_existing_source_paths(args.openbb_path)]
    sys.path[:0] = overlay_paths

    pytest_args = args.pytest_args
    if pytest_args[:1] == ["--"]:
        pytest_args = pytest_args[1:]
    return pytest.main(pytest_args or ["-q"])


if __name__ == "__main__":
    raise SystemExit(main())
