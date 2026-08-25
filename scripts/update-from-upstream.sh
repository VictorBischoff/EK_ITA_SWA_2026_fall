#!/bin/bash
# Automatically pull latest changes from the upstream repository
# This script fetches from ClausBove/EK_ITA_SWA_2026_fall and merges into master

set -e

# Ensure we're in the correct directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
cd "$REPO_DIR"

# Ensure upstream remote exists
if ! git remote | grep -q "^upstream$"; then
    git remote add upstream https://github.com/Ek-Ita-Swa-Iti/EK_ITA_SWA_2026_fall.git
fi

# Stash any local changes
if ! git diff --quiet; then
    git stash push -m "Auto-stash before upstream update"
    STASHED=1
else
    STASHED=0
fi

# Fetch from upstream
echo "Fetching from upstream..."
git fetch upstream 2>&1

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Checkout master
git checkout master 2>&1

# Fast-forward merge from upstream
echo "Updating from upstream/master..."
git merge --ff-only upstream/master 2>&1 || {
    # If fast-forward fails, try regular merge
    git merge upstream/master --no-edit -m "Auto-merge upstream changes" 2>&1
}

# Return to original branch if not master
if [ "$CURRENT_BRANCH" != "master" ]; then
    git checkout "$CURRENT_BRANCH" 2>&1
fi

# Reapply stashed changes if any
if [ "$STASHED" -eq 1 ]; then
    git stash pop 2>&1
fi

# Push to origin if on master
git checkout master 2>&1
git push origin master 2>&1

echo "Upstream update complete."
