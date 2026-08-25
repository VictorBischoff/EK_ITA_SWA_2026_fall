#!/usr/bin/env python3
"""
Automatically pull and merge changes from upstream repository.

This script:
1. Adds upstream remote if not present
2. Fetches from upstream
3. Merges changes into master
4. Pushes to origin

Usage:
    python scripts/auto_update.py

To run automatically, add to crontab:
    0 * * * * cd /path/to/repo && /usr/bin/python3 scripts/auto_update.py >> /tmp/auto_update.log 2>&1
"""

import subprocess
import sys
import os
from pathlib import Path

REPO_DIR = Path(__file__).parent.parent
UPSTREAM_URL = "https://github.com/Ek-Ita-Swa-Iti/EK_ITA_SWA_2026_fall.git"


def run(cmd, check=True, capture_output=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=REPO_DIR,
        check=check,
        capture_output=capture_output,
        text=True
    )
    if capture_output:
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
    return result


def main():
    print("=" * 60)
    print("Auto-updating from upstream repository")
    print("=" * 60)
    
    # Check if we're in a git repo
    try:
        run("git status")
    except subprocess.CalledProcessError:
        print("Error: Not in a git repository")
        sys.exit(1)
    
    # Get current branch
    current_branch = run("git rev-parse --abbrev-ref HEAD", capture_output=True).stdout.strip()
    print(f"Current branch: {current_branch}")
    
    # Check if upstream remote exists
    remotes = run("git remote", capture_output=True).stdout.strip().split('\n')
    if 'upstream' not in remotes:
        print("Adding upstream remote...")
        run(f"git remote add upstream {UPSTREAM_URL}")
    
    # Stash local changes if any
    status = run("git status --porcelain", capture_output=True).stdout.strip()
    stashed = False
    if status:
        print("Stashing local changes...")
        run("git stash push -m 'Auto-stash before upstream update'")
        stashed = True
    
    # Fetch from upstream
    print("Fetching from upstream...")
    run("git fetch upstream")
    
    # Checkout master
    print("Checking out master...")
    run("git checkout master")
    
    # Try fast-forward merge first
    print("Attempting fast-forward merge...")
    result = run("git merge --ff-only upstream/master", check=False, capture_output=True)
    
    if result.returncode != 0:
        print("Fast-forward failed, trying regular merge...")
        run("git merge upstream/master --no-edit -m 'Auto-merge upstream changes'")
    
    # Push to origin
    print("Pushing to origin...")
    run("git push origin master")
    
    # Return to original branch
    if current_branch != "master":
        print(f"Returning to {current_branch}...")
        run(f"git checkout {current_branch}")
    
    # Reapply stashed changes
    if stashed:
        print("Reapplying stashed changes...")
        run("git stash pop")
    
    print("=" * 60)
    print("Auto-update complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
