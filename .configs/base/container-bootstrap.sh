#!/bin/sh
# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
# Illustrative container lifecycle helper; not an approved environment setup.
set -eu
sudo python3 -m venv /opt/slyc-venv
sudo chown -R "$(id -u):$(id -g)" /opt/slyc-venv
/opt/slyc-venv/bin/python -m pip install --require-hashes -r slyc-requirements.lock
/opt/slyc-venv/bin/python - <<'INNER'
from pathlib import Path
root = Path.cwd()
launcher = Path('/opt/slyc-venv/bin/slyc')
launcher.write_text(f"#!/opt/slyc-venv/bin/python\nimport sys\nsys.path.insert(0, {str(root)!r})\nfrom slyc.cli import main\nraise SystemExit(main())\n")
launcher.chmod(0o755)
INNER
