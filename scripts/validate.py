#!/usr/bin/env python3
# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
"""Validate repository artifacts; no behavioral tests or third-party dependencies."""
import argparse
import ast
import json
from pathlib import Path
import re
import sys
import tomllib
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from slyc.development.checkout import preview, MANDATORY_PATHS
from slyc.deployment.contracts import catalog
from slyc.deployment.plan import environment_state
from slyc.workspace.graph import WorkspaceGraph
from slyc.workspace.projects import read_json, local_path


def manifest_parity(graph):
    """Compare the bounded demo's explicit local declarations, not native discovery."""
    manifests = {}
    for identity, project in graph.projects.items():
        root = local_path(ROOT, project["root"])
        provider, name = identity.split(":", 1)
        filename = {"node": "package.json", "uv": "pyproject.toml", "cargo": "Cargo.toml"}[provider]
        source = root / filename
        data = read_json(source) if provider == "node" else tomllib.loads(source.read_text())
        declared_name = data["name"] if provider == "node" else data["project" if provider == "uv" else "package"]["name"]
        if declared_name != name:
            raise ValueError(f"Project identity differs from manifest: {identity}")
        manifests[identity] = data
    for identity, data in manifests.items():
        provider = identity.split(":", 1)[0]
        if provider == "uv":
            declared = {entry.split("=", 1)[0].split(">", 1)[0].split("<", 1)[0].strip()
                        for entry in data["project"].get("dependencies", [])}
        else:
            declared = set(data.get("dependencies", {}))
        local_edges = sorted(candidate for candidate in manifests
                             if candidate.startswith(provider + ":") and candidate.split(":", 1)[1] in declared)
        if local_edges != sorted(graph.projects[identity]["dependencies"]):
            raise ValueError(f"Local dependency declarations differ from snapshot: {identity}")
        for dependency in local_edges:
            dep_name = dependency.split(":", 1)[1]
            if provider == "uv":
                source = data.get("tool", {}).get("uv", {}).get("sources", {}).get(dep_name, {})
                if source.get("workspace") is not True:
                    raise ValueError(f"Missing workspace source for {identity} -> {dependency}")
            if provider == "cargo":
                source = data["dependencies"][dep_name].get("path")
                if source is None or (ROOT / graph.projects[identity]["root"] / source).resolve() != (ROOT / graph.projects[dependency]["root"]).resolve():
                    raise ValueError(f"Local Cargo path differs from snapshot: {identity}")
    # Ensure the three root workspace definitions still cover the snapshot's roots.
    node = read_json(ROOT / "package.json")["workspaces"]
    uv = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["uv"]["workspace"]["members"]
    cargo = tomllib.loads((ROOT / "Cargo.toml").read_text())["workspace"]["members"]
    for provider, patterns, manifest_name in [("node", node, "package.json"), ("uv", uv, "pyproject.toml"), ("cargo", cargo, "Cargo.toml")]:
        discovered = {path.relative_to(ROOT).as_posix() for pattern in patterns for path in ROOT.glob(pattern) if (path / manifest_name).is_file()}
        committed = {project["root"] for name, project in graph.projects.items() if name.startswith(provider + ":")}
        if discovered != committed:
            raise ValueError(f"Root {provider} workspace membership differs from snapshot")


def document_links():
    count = 0
    for source in sorted(ROOT.rglob("*.md")):
        for target in re.findall(r"\]\(([^)]+)\)", source.read_text()):
            target = target.strip().split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = (source.parent / unquote(target)).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.exists():
                raise ValueError(f"Broken local link in {source.relative_to(ROOT)}: {target}")
            count += 1
    return count


def validate(graph_only=False):
    graph = WorkspaceGraph(ROOT)
    manifest_parity(graph)
    if graph_only:
        return {"status": "VALID", "projects": len(graph.projects),
                "check": "full-checkout manifest declarations vs hand-authored slyc graph",
                "native_mise_parity": "NOT_CHECKED"}
    counts = {"json": 0, "toml": 0, "python_sources": 0}
    # Exclude the existing host devcontainer (JSONC) and generated/dependency folders.
    roots = ["slyc", "apps", "services", "packages", ".slices", ".configs", "contracts", "deployments", "scripts"]
    files = [path for name in roots for path in (ROOT / name).rglob("*") if path.is_file()
             and not set(path.relative_to(ROOT).parts).intersection({"node_modules", "target", "dist", "__pycache__"})]
    files += list(ROOT.glob("*.toml")) + [ROOT / "package.json", ROOT / ".workspace-graph.json"]
    for path in sorted(set(files)):
        if path.suffix == ".json":
            json.loads(path.read_text()); counts["json"] += 1
        if path.suffix == ".toml":
            tomllib.loads(path.read_text()); counts["toml"] += 1
        if path.suffix == ".py":
            ast.parse(path.read_text(), filename=str(path), feature_version=(3, 11)); counts["python_sources"] += 1
    slices = sorted((ROOT / ".slices").glob("*.json"))
    for definition in slices:
        resolved = preview(ROOT, graph, definition.stem)
        for path in resolved["paths"]:
            if not local_path(ROOT, path).is_dir():
                raise ValueError(f"Slice {definition.stem} includes absent directory: {path}")
    bindings = catalog(ROOT)
    for project in graph.projects.values():
        if project.get("service") and project["service"] not in bindings["services"]:
            raise ValueError(f"Unbound service: {project['service']}")
    for environment in ("production", "staging"):
        environment_state(ROOT, environment)
    pacts = list((ROOT / "contracts/pact").rglob("*.json"))
    for source in pacts:
        document = read_json(source)
        if document["metadata"]["pactSpecification"]["version"] != "4.0":
            raise ValueError(f"Unexpected specification declaration: {source}")
        for interaction in document["interactions"]:
            if interaction["type"] != "Synchronous/HTTP" or not interaction["request"]["path"].startswith("/"):
                raise ValueError(f"Invalid HTTP fixture: {source}")
            if interaction["request"]["method"] not in {"GET", "POST"} or not 100 <= interaction["response"]["status"] < 600:
                raise ValueError(f"Invalid HTTP request/status: {source}")
    for path in MANDATORY_PATHS:
        if not (ROOT / path).is_dir():
            raise ValueError(f"Missing mandatory directory: {path}")
    for source in (ROOT / "deployments/scenarios").glob("*.json"):
        scenario = read_json(source)
        for service, version in scenario["candidate"].items():
            if version not in bindings["services"][service]:
                raise ValueError(f"Unknown scenario candidate: {service} {version}")
    return {"status": "VALID", "checks": counts, "slices": len(slices), "pact_design_fixtures": len(pacts),
            "local_document_links": document_links(), "native_mise_parity": "NOT_CHECKED",
            "pact_verification": "NOT_RUN", "application_builds": "NOT_RUN",
            "behavioral_tests": "NOT_WRITTEN_OR_RUN"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph-only", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.graph_only), indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, TypeError, SyntaxError) as error:
        print(f"validation failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
