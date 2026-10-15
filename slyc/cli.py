# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
"""Small standard-library CLI. Mutating commands fail explicitly."""
import argparse
import json
import subprocess
import sys

from . import __version__
from .development.checkout import preview
from .workspace.graph import WorkspaceGraph
from .workspace.projects import find_root, read_json
from .workspace.affected import affected, changed_paths
from .deployment.graph import runtime_graph, affected_services
from .deployment.plan import plan, environment_state
from .deployment.verify import verify


def parser():
    cli = argparse.ArgumentParser(prog="slyc", description="Inspect development slices and runtime contracts (experimental POC)")
    cli.add_argument("--version", action="version", version=__version__)
    commands = cli.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="List committed slices with resolved development projects")
    status = commands.add_parser("status", help="Inspect local state, or preview a named slice")
    status.add_argument("--slice", help="Preview a slice and composed configuration without writing files")
    for name in ("open", "sync", "history", "add", "remove"):
        pending = commands.add_parser(name, help="Planned; exits 3 without modifying files")
        if name == "open":
            pending.add_argument("slice")
        if name in {"add", "remove"}:
            pending.add_argument("project")
        if name == "history":
            pending.add_argument("options", nargs=argparse.REMAINDER)
    graph = commands.add_parser("graph", help="Inspect the committed slyc-format development graph")
    actions = graph.add_subparsers(dest="action")
    actions.add_parser("check", help="Validate structure and references; not native mise parity")
    actions.add_parser("update", help="Planned native mise import; exits 3")
    deps = actions.add_parser("deps"); deps.add_argument("project")
    impact = actions.add_parser("affected"); impact.add_argument("--base", required=True)
    deploy = commands.add_parser("deploy", help="Read-only runtime metadata and requirements")
    operations = deploy.add_subparsers(dest="action", required=True)
    operations.add_parser("graph")
    ds = operations.add_parser("status"); ds.add_argument("--environment", choices=["staging", "production"], default="production")
    da = operations.add_parser("affected"); da.add_argument("service")
    for name in ("verify", "plan"):
        op = operations.add_parser(name)
        op.add_argument("service")
        op.add_argument("--environment", choices=["staging", "production"], default="production")
        if name == "plan":
            op.add_argument("--version", required=True, help="Explicit candidate service version")
    return cli


def execute(args, root):
    graph = WorkspaceGraph(root)
    if args.command in {"open", "sync", "history", "add", "remove"}:
        raise NotImplementedError(f"{args.command} is planned; no working-tree changes were made. This repository is untrusted inspection-only material; do not execute it.")
    if args.command == "list":
        return [{"name": file.stem, "projects": preview(root, graph, file.stem)["projects"]}
                for file in sorted((root / ".slices").glob("*.json"))], 0
    if args.command == "status":
        if args.slice:
            return preview(root, graph, args.slice), 0
        state = root / ".slice-state.json"
        return {"active_state": read_json(state) if state.exists() else None,
                "state_verified": False, "note": "No mutation commands implemented; state is informational"}, 0
    if args.command == "graph":
        if args.action == "update":
            raise NotImplementedError("Native mise graph capture and normalization are not available; this source is for inspection only")
        if args.action == "check":
            return graph.check(), 0
        if args.action == "deps":
            return {"project": args.project, "closure": graph.closure([args.project])}, 0
        if args.action == "affected":
            paths = changed_paths(root, args.base)
            return {"base": args.base, "changed_paths": paths, "projects": affected(graph, paths),
                    "scope": "committed changes from merge base to HEAD"}, 0
        return graph.document, 0
    if args.action == "graph":
        return runtime_graph(root), 0
    if args.action == "status":
        return environment_state(root, args.environment), 0
    if args.action == "affected":
        return {"services": affected_services(root, args.service), "meaning": "potential transitive consumer impact; not a deployment set"}, 0
    if args.action == "verify":
        verify(args.service, args.environment)
    result = plan(root, args.service, args.version, args.environment)
    return result, 4


def main(argv=None):
    cli = parser()
    args, unknown = cli.parse_known_args(argv)
    if unknown and args.command != "history":
        cli.error("unrecognized arguments: " + " ".join(unknown))
    try:
        result, code = execute(args, find_root())
        print(json.dumps(result, indent=2, sort_keys=True))
        return code
    except NotImplementedError as error:
        print(f"slyc: {error}", file=sys.stderr)
        return 3
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f"slyc: {error}", file=sys.stderr)
        return 2
