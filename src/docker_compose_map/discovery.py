from __future__ import annotations

import glob
import os
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

COMPOSE_FILE_NAMES = frozenset(
    {
        "compose.yaml",
        "compose.yml",
        "docker-compose.yaml",
        "docker-compose.yml",
    }
)
Candidate = tuple[Path, Path]


class ComposeSelection(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)

    root: Path
    files: tuple[Path, ...] = Field(min_length=1)


def select_compose_files(inputs: Sequence[str]) -> ComposeSelection:
    by_file: dict[Path, Path] = {}
    for raw_input in inputs:
        for path, root_hint in _expand_input(raw_input):
            by_file.setdefault(path, root_hint)

    if not by_file:
        raise FileNotFoundError("no compose files matched the given inputs")

    files = tuple(sorted(by_file))
    root = _common_path(tuple(by_file[path] for path in files))
    return ComposeSelection(root=root, files=files)


def _expand_input(raw_input: str) -> tuple[Candidate, ...]:
    if glob.has_magic(raw_input):
        matches = tuple(Path(match).resolve() for match in glob.glob(raw_input, recursive=True))
        if not matches:
            raise FileNotFoundError(f"{raw_input!r} matched no files")
        return tuple(
            candidate for match in matches for candidate in _expand_path(match, explicit_file=True)
        )

    path = Path(raw_input).resolve()
    if not path.exists():
        raise FileNotFoundError(f"{raw_input!r} does not exist")
    return _expand_path(path, explicit_file=False)


def _expand_path(path: Path, *, explicit_file: bool) -> tuple[Candidate, ...]:
    if path.is_dir():
        return tuple((compose_file, path) for compose_file in _discover_directory(path))
    if path.is_file():
        if explicit_file or path.name in COMPOSE_FILE_NAMES:
            return ((path, path.parent),)
        raise ValueError(f"{path} is not a known compose filename")
    raise FileNotFoundError(f"{path} is neither a file nor a directory")


def _discover_directory(root: Path) -> tuple[Path, ...]:
    found = sorted(
        (path for path in root.rglob("*") if path.name in COMPOSE_FILE_NAMES),
        key=lambda path: (len(path.relative_to(root).parts), path.as_posix()),
    )
    by_top: dict[str, Path] = {}
    for path in found:
        rel_path = path.relative_to(root).as_posix()
        top = rel_path.split("/", 1)[0] if "/" in rel_path else "."
        by_top.setdefault(top, path.resolve())
    return tuple(by_top[key] for key in sorted(by_top))


def _common_path(paths: Sequence[Path]) -> Path:
    return Path(os.path.commonpath(tuple(str(path) for path in paths))).resolve()
