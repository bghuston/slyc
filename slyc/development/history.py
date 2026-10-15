# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
"""Compute relevant history paths; executing the git log wrapper is planned."""
from .checkout import slice_definition


def history_paths(root, graph, name):
    definition = slice_definition(root, name)
    return sorted(set(definition["include"] + [graph.projects[project]["root"]
                      for project in graph.closure(definition["projects"])]))
