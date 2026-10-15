# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
"""Repository discovery and bounded, repository-relative metadata reads."""
import json
from pathlib import Path, PurePosixPath


def find_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".workspace-graph.json").is_file():
            return candidate
    raise ValueError("No .workspace-graph.json found; this source is for inspection only")


def local_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError(f"Invalid repository path: {relative!r}")
    path = PurePosixPath(relative)
    if path.is_absolute() or any(part in {"..", ".git"} for part in path.parts):
        raise ValueError(f"Unsafe repository path: {relative!r}")
    result = (root / relative).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes repository: {relative}")
    return result


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read {path}: {error}") from error
