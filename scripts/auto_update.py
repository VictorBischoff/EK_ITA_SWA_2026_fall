#!/usr/bin/env python3
"""
Single source of truth for pulling changes from the upstream repository.

Used by:
- scripts/update-from-upstream.sh (thin CLI wrapper)
- server.py's /api/update endpoint (imports update_from_upstream() directly)

Usage:
    python scripts/auto_update.py            # fetch + merge only
    python scripts/auto_update.py --push      # also push to origin (opt-in)

To run unattended, add to crontab. Auto-pushing unattended is a deliberate
opt-in (--push) since it can push a bad merge to your fork with no review:
    0 * * * * cd /path/to/repo && /usr/bin/python3 scripts/auto_update.py >> /tmp/auto_update.log 2>&1
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).parent.parent
UPSTREAM_URL = "https://github.com/Ek-Ita-Swa-Iti/EK_ITA_SWA_2026_fall.git"


def run(cmd, check=True, repo_dir=REPO_DIR):
    """Run a git command (list of args) and return the CompletedProcess."""
    result = subprocess.run(
        cmd,
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result


def update_from_upstream(repo_dir=REPO_DIR, push=False):
    """
    Fetch and merge from the upstream remote (adding it if missing).

    Refuses to run if the working tree has local changes rather than
    auto-stashing them: an automated stash+merge+pop that later conflicts
    leaves the repo in a broken, half-merged state discovered only later
    (which is exactly how server.py ended up with unresolved conflict
    markers committed to it). Callers that want that tradeoff can stash
    manually first.

    Returns a dict: {"success": bool, "message": str, "pushed": bool}.
    """
    try:
        run(["git", "rev-parse", "--is-inside-work-tree"])
    except RuntimeError:
        return {"success": False, "message": "Not in a git repository.", "pushed": False}

    dirty = run(["git", "status", "--porcelain"]).stdout.strip()
    if dirty:
        return {
            "success": False,
            "message": "Working tree has local changes. Commit or stash them before updating.",
            "pushed": False,
        }

    remotes = run(["git", "remote"]).stdout.strip().splitlines()
    if "upstream" not in remotes:
        try:
            run(["git", "remote", "add", "upstream", UPSTREAM_URL])
        except RuntimeError as e:
            return {"success": False, "message": f"Failed to add upstream remote: {e}", "pushed": False}

    current_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()

    try:
        run(["git", "fetch", "upstream"])

        if current_branch != "master":
            run(["git", "checkout", "master"])

        ff_result = run(["git", "merge", "--ff-only", "upstream/master"], check=False)
        if ff_result.returncode != 0:
            run(["git", "merge", "upstream/master", "--no-edit"])

        pushed = False
        if push:
            run(["git", "push", "origin", "master"])
            pushed = True

        if current_branch != "master":
            run(["git", "checkout", current_branch])

        return {"success": True, "message": "Successfully updated from upstream.", "pushed": pushed}

    except RuntimeError as e:
        return {"success": False, "message": str(e), "pushed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--push", action="store_true", help="Also push the merged master to origin (opt-in)")
    args = parser.parse_args()

    print("=" * 60)
    print("Updating from upstream repository")
    print("=" * 60)

    result = update_from_upstream(push=args.push)

    print(result["message"])
    print("=" * 60)

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
