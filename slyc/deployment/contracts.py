# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
"""Read explicit version bindings; contract revisions are not service versions."""
import hashlib
from ..workspace.projects import read_json, local_path


def catalog(root):
    data = read_json(root / "contracts/catalog.json")
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported contract catalog")
    for service, versions in data["services"].items():
        for version, bindings in versions.items():
            for provider, relative in bindings.items():
                pact = read_json(local_path(root, relative))
                if pact["consumer"]["name"] != service or pact["provider"]["name"] != provider:
                    raise ValueError(f"Contract identity mismatch for {service} {version}")
    return data


def contract_digest(root, relative):
    return hashlib.sha256(local_path(root, relative).read_bytes()).hexdigest()
