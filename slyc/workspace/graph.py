# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
"""Read the explicit slyc graph; never impersonate mise's native format."""
from .projects import local_path, read_json


class WorkspaceGraph:
    def __init__(self, root):
        self.root = root
        self.document = read_json(root / ".workspace-graph.json")
        if not isinstance(self.document, dict):
            raise ValueError("Workspace graph must be a JSON object")
        if self.document.get("schema_version") != 1 or self.document.get("format") != "slyc.workspace":
            raise ValueError("Unsupported workspace graph format")
        self.projects = self.document["projects"]
        if not isinstance(self.projects, dict) or not self.projects:
            raise ValueError("Graph must contain projects")
        seen_roots = set()
        for name, project in self.projects.items():
            if not isinstance(project, dict) or not isinstance(project.get("dependencies"), list):
                raise ValueError(f"Invalid project structure: {name}")
            if not all(isinstance(item, str) for item in project["dependencies"]):
                raise ValueError(f"Dependencies must be project ID strings: {name}")
            path = project["root"]
            local_path(root, path)
            if path in seen_roots:
                raise ValueError(f"Duplicate project root: {path}")
            seen_roots.add(path)
            for dependency in project["dependencies"]:
                if dependency not in self.projects:
                    raise ValueError(f"{name} references unknown project {dependency}")
        self.closure(list(self.projects))

    def closure(self, projects):
        visited, visiting = set(), set()

        def visit(name):
            if name not in self.projects:
                raise ValueError(f"Unknown project: {name}")
            if name in visiting:
                raise ValueError(f"Dependency cycle at {name}")
            if name in visited:
                return
            visiting.add(name)
            for dependency in self.projects[name]["dependencies"]:
                visit(dependency)
            visiting.remove(name)
            visited.add(name)

        for project in projects:
            visit(project)
        return sorted(visited)

    def check(self):
        # Works in sparse checkouts; manifest parity is a separate full-checkout check.
        return {"status": "VALID", "projects": len(self.projects),
                "provenance": self.document["provenance"],
                "native_mise_parity": "NOT_CHECKED"}
