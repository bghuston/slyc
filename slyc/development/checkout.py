# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
"""Resolve checkout intent without mutating Git or the working tree."""
import re
from ..workspace.projects import read_json, local_path
from .config import compose

MANDATORY_PATHS = ["slyc", ".configs", ".slices", "contracts", "deployments"]


def slice_definition(root, name):
    if not re.fullmatch(r"[a-z][a-z0-9-]*", name):
        raise ValueError("Slice names must contain lowercase letters, numbers and hyphens")
    definition = read_json(root / ".slices" / f"{name}.json")
    if not isinstance(definition, dict):
        raise ValueError(f"Slice must be a JSON object: {name}")
    if set(definition) != {"projects", "include", "configs"}:
        raise ValueError(f"Invalid slice fields: {name}")
    for key, values in definition.items():
        if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            raise ValueError(f"{name}.{key} must be a string array")
    if not definition["projects"] or not definition["configs"]:
        raise ValueError(f"Slice must select root projects and config fragments: {name}")
    for path in definition["include"]:
        local_path(root, path)
    return definition


def preview(root, graph, name):
    definition = slice_definition(root, name)
    projects = graph.closure(definition["projects"])
    paths = sorted(set(MANDATORY_PATHS + definition["include"] +
                       [graph.projects[project]["root"] for project in projects]))
    return {"slice": name, "mode": "PREVIEW_ONLY", "projects": projects, "paths": paths,
            "configuration": compose(root, definition["configs"]),
            "writes_performed": False}
