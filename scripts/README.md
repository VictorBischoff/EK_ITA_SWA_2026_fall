# Maintenance Scripts

This directory contains scripts to help maintain this forked repository.

## update-from-upstream.sh

Bash script to pull the latest changes from the upstream repository (ClausBove/EK_ITA_SWA_2026_fall).

### Usage

```bash
# Make executable (if not already)
chmod +x scripts/update-from-upstream.sh

# Run the script
./scripts/update-from-upstream.sh
```

### What it does

1. Checks if the `upstream` remote exists, adds it if not
2. Fetches the latest changes from upstream
3. Checks out the master branch
4. Merges changes from upstream/master into your local master
5. Provides instructions to push changes to your fork

### Manual Alternative

If you prefer to do it manually:

```bash
# Add upstream remote (only needed once)
git remote add upstream https://github.com/ClausBove/EK_ITA_SWA_2026_fall.git

# Fetch and merge
git fetch upstream
git checkout master
git merge upstream/master

# Push to your fork
git push origin master
```

### Updating the Upstream URL

If the upstream repository URL changes:

```bash
git remote set-url upstream https://github.com/ClausBove/EK_ITA_SWA_2026_fall.git
```

### Viewing Remotes

```bash
git remote -v
```
