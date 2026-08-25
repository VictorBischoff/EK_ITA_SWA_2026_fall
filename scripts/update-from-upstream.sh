#!/bin/bash
# Script to pull latest changes from the upstream repository
# This script assumes the upstream is ClausBove/EK_ITA_SWA_2026_fall

set -e

echo "=========================================="
echo " Updating from Upstream Repository"
echo "=========================================="
echo ""

# Check if upstream remote exists, if not add it
if git remote | grep -q "^upstream$"; then
    echo "Upstream remote already exists."
else
    echo "Adding upstream remote..."
    git remote add upstream https://github.com/ClausBove/EK_ITA_SWA_2026_fall.git
    echo "Upstream remote added: upstream"
fi

echo ""
echo "Fetching from upstream..."
git fetch upstream

echo ""
echo "Checking out master branch..."
git checkout master

echo ""
echo "Merging changes from upstream/master..."
git merge upstream/master --no-ff -m "Merge upstream changes from ClausBove/EK_ITA_SWA_2026_fall"

echo ""
echo "=========================================="
echo " Update Complete!"
echo "=========================================="
echo ""
echo "To push these changes to your fork:"
echo "  git push origin master"
echo ""
