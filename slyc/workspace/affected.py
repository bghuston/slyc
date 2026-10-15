# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
"""Conservative development impact, using native Git for changed paths."""
import subprocess


def changed_paths(root, base):
    if base.startswith("-"):
        raise ValueError("Base revision must not begin with '-'")
    result = subprocess.run(["git", "diff", "--name-only", "-z", "--no-renames",
                             f"{base}...HEAD", "--"], cwd=root, check=True,
                            capture_output=True)
    return [path for path in result.stdout.decode().split("\0") if path]


def affected(graph, paths):
    global_inputs = {".workspace-graph.json", "mise.toml", "Cargo.toml", "Cargo.lock",
                     "package.json", "package-lock.json", "pyproject.toml", "uv.lock"}
    if any(path in global_inputs or path.startswith(("slyc/", ".configs/", ".slices/")) for path in paths):
        return sorted(graph.projects)
    selected = {name for name, project in graph.projects.items()
                if any(path == project["root"] or path.startswith(project["root"] + "/")
                       for path in paths)}
    while True:
        expanded = selected | {name for name, project in graph.projects.items()
                               if selected.intersection(project["dependencies"])}
        if expanded == selected:
            return sorted(selected)
        selected = expanded
