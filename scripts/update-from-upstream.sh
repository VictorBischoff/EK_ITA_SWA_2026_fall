#!/bin/bash
# Thin wrapper around scripts/auto_update.py, which is the single source of
# truth for the fetch/merge/push logic. Kept for people who prefer running a
# shell script; pass --push to also push the merge to origin (opt-in).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

exec python3 "$REPO_DIR/scripts/auto_update.py" "$@"
