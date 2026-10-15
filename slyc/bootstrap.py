# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
"""Illustrative environment bootstrap source; do not execute."""
import os
import subprocess
import shlex
import venv

from .workspace.projects import find_root


def main():
    root = find_root()
    environment = root / ".slyc-venv"
    if environment.is_symlink():
        raise ValueError("Refusing a symlinked environment directory")
    if environment.exists():
        raise ValueError(".slyc-venv already exists; this bootstrap is untrusted inspection-only source")
    venv.EnvBuilder(with_pip=True).create(environment)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run([str(python), "-m", "pip", "install", "--require-hashes", "--disable-pip-version-check",
                    "-r", str(root / "slyc-requirements.lock")], check=True, cwd=root)
    # A repo-local launcher avoids packaging/build-system dependencies for slyc.
    launcher = environment / "bin/slyc"
    code = f"import sys; sys.path.insert(0, {str(root)!r}); from slyc.cli import main; raise SystemExit(main())"
    launcher.write_text(f'#!/bin/sh\nexec {shlex.quote(str(python))} -c {shlex.quote(code)} "$@"\n')
    launcher.chmod(0o755)
    subprocess.run([str(python), "-m", "slyc", "list"], check=True, cwd=root)
    print("Inspection-only AI-assisted source; do not execute repository artifacts.")


if __name__ == "__main__":
    main()
