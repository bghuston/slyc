# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
"""Pure JSON composition. Preview only; no root files are written."""
from copy import deepcopy
from ..workspace.projects import read_json, local_path


def merge(left, right, key=""):
    if isinstance(left, dict) and isinstance(right, dict):
        result = deepcopy(left)
        for name, value in right.items():
            result[name] = merge(result[name], value, name) if name in result else deepcopy(value)
        return result
    if isinstance(left, list) and isinstance(right, list):
        if key in {"args", "command", "entrypoint"}:
            return deepcopy(right)
        identity = {"tasks": "label", "configurations": "name", "mounts": "target"}.get(key)
        result = deepcopy(left)
        for item in right:
            if identity:
                if not isinstance(item, dict) or identity not in item:
                    raise ValueError(f"{key} entries must be objects with {identity}")
                old = next((entry for entry in result if entry.get(identity) == item[identity]), None)
                if old is not None and old != item:
                    raise ValueError(f"Conflicting {key} identity: {item[identity]}")
            if item not in result:
                result.append(deepcopy(item))
        return result
    if type(left) is not type(right):
        raise ValueError(f"Conflicting value types at {key}")
    return deepcopy(right)


def validate_fragment(value, key=""):
    """Reject ambiguous identity arrays even within the first fragment."""
    if isinstance(value, dict):
        for name, child in value.items():
            validate_fragment(child, name)
    elif isinstance(value, list):
        identity = {"tasks": "label", "configurations": "name", "mounts": "target"}.get(key)
        seen = {}
        for item in value:
            if identity:
                if not isinstance(item, dict) or not isinstance(item.get(identity), str):
                    raise ValueError(f"{key} entries must be objects with string {identity}")
                label = item[identity]
                if label in seen and seen[label] != item:
                    raise ValueError(f"Conflicting {key} identity: {label}")
                seen[label] = item
            validate_fragment(item)


def compose(root, fragments):
    output = {}
    for name in fragments:
        if not name or "/" in name or name.startswith("."):
            raise ValueError(f"Invalid fragment name: {name}")
        directory = local_path(root, f".configs/{name}")
        if not directory.is_dir():
            raise ValueError(f"Missing config fragment: {name}")
        for source in sorted(directory.rglob("*.json")):
            local_path(root, source.relative_to(root).as_posix())
            target = source.relative_to(directory).as_posix()
            value = read_json(source)
            if not isinstance(value, dict):
                raise ValueError(f"Configuration document must be an object: {source}")
            validate_fragment(value)
            output[target] = merge(output[target], value) if target in output else value
    return dict(sorted(output.items()))
