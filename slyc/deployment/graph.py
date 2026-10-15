# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
"""Consumer-to-provider runtime graph from committed Pact identities."""
from .contracts import catalog


def runtime_graph(root):
    data = catalog(root)
    edges = {(consumer, provider) for consumer, versions in data["services"].items()
             for bindings in versions.values() for provider in bindings}
    return {"direction": "consumer-to-provider", "edges": [
        {"consumer": consumer, "provider": provider} for consumer, provider in sorted(edges)]}


def affected_services(root, service):
    data = catalog(root)
    if service not in data["services"]:
        raise ValueError(f"Unknown service: {service}")
    edges = runtime_graph(root)["edges"]
    impacted = {service}
    while True:
        expanded = impacted | {edge["consumer"] for edge in edges if edge["provider"] in impacted}
        if expanded == impacted:
            return sorted(impacted)
        impacted = expanded
