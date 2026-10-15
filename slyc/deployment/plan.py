# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
"""Read-only compatibility requirements; authorization is deliberately unavailable."""
from .contracts import catalog, contract_digest
from ..workspace.projects import read_json


def environment_state(root, environment):
    if environment not in {"staging", "production"}:
        raise ValueError("Environment must be staging or production")
    data = read_json(root / "deployments/environments" / f"{environment}.json")
    known = catalog(root)["services"]
    if set(data["services"]) != set(known):
        raise ValueError("Environment must bind exactly the catalog services")
    for service, version in data["services"].items():
        if version not in known[service]:
            raise ValueError(f"Unknown deployed version: {service} {version}")
    return data


def plan(root, service, version, environment):
    services = catalog(root)["services"]
    if service not in services or version not in services[service]:
        raise ValueError(f"Unknown candidate service/version: {service} {version}")
    current = environment_state(root, environment)["services"]
    target = {**current, service: version}
    requirements = []
    for consumer, consumer_version in sorted(target.items()):
        for provider, contract in sorted(services[consumer][consumer_version].items()):
            if service not in {consumer, provider}:
                continue
            requirements.append({"consumer": consumer, "consumer_version": consumer_version,
                                 "provider": provider, "provider_version": target[provider],
                                 "contract": contract, "contract_sha256": contract_digest(root, contract),
                                 "status": "UNKNOWN", "reason": "No trusted Pact evidence importer exists"})
    return {"status": "UNKNOWN", "decision": "BLOCKED", "environment": environment,
            "state_source": "static demonstration fixture", "candidate": {service: version},
            "requirements": requirements, "deployment_permitted": False,
            "scope": "candidate-adjacent edges only; baseline environment is not certified",
            "note": "Requirements preview only. No verifier or deployment executor was run."}
