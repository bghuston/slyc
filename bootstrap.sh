#!/bin/sh
# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
set -eu
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: sh bootstrap.sh <repository-url> [new-destination]" >&2
  exit 2
fi
command -v git >/dev/null 2>&1 || { echo "Git is required" >&2; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3.11+ is required" >&2; exit 2; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else "Python 3.11+ is required")'
repo_url=$1
destination=${2:-slyc-workspace}
case "$repo_url" in -*) echo "Repository URL cannot start with '-'" >&2; exit 2 ;; esac
case "$destination" in -*) echo "Destination cannot start with '-'" >&2; exit 2 ;; esac
if [ -e "$destination" ]; then
  echo "Destination already exists: $destination (choose a new directory)" >&2
  exit 2
fi
git clone --filter=blob:none --sparse -- "$repo_url" "$destination"
cd "$destination"
git sparse-checkout set slyc .configs .slices contracts deployments
python3 -m slyc.bootstrap
