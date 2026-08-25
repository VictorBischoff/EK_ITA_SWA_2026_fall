# Maintenance Scripts

This directory contains scripts to help maintain this forked repository.

## Automatic Updates

The upstream remote has been configured to point to:
```
https://github.com/Ek-Ita-Swa-Iti/EK_ITA_SWA_2026_fall.git
```

You can verify this with:
```bash
git remote -v
```

## Scripts

`auto_update.py` is the single source of truth for the fetch/merge logic —
`update-from-upstream.sh` and `server.py`'s `/api/update` endpoint both call
into it rather than each reimplementing git commands.

It **refuses to run if the working tree has local changes**, rather than
auto-stashing them: an unattended stash → merge → pop that later conflicts
leaves the repo in a broken, half-merged state discovered only when someone
next opens the file (this is exactly how `server.py` ended up with unresolved
conflict markers committed to it). Commit or stash your changes first.

Pushing to your fork is **opt-in** (`--push`), not automatic. An unattended
job that force-merges upstream and pushes with no review is the riskiest part
of this whole setup — think about whether you actually want that before
wiring it into cron.

### 1. auto_update.py (Recommended)

```bash
python scripts/auto_update.py          # fetch + merge only
python scripts/auto_update.py --push   # also push the merge to origin
```

**For Automatic Execution (macOS/Linux):**

If you do want unattended updates on a schedule, decide deliberately whether
to include `--push`. Fetch+merge only (no `--push`) is the safer default —
it updates your local checkout without publishing anything:
```bash
# Edit crontab
crontab -e

# Add this line (adjust the path to your repo)
0 * * * * cd /Users/victor/Dev/EK/3semester/systemarkitektur/repos/EK_ITA_SWA_2026_fall && /usr/bin/python3 scripts/auto_update.py >> /tmp/auto_update.log 2>&1
```

Or create a launchd plist for macOS to run daily:
```bash
# Create ~/.Library/LaunchAgents/com.auto.update.plist
cat > ~/.Library/LaunchAgents/com.auto.update.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.auto.update</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/victor/Dev/EK/3semester/systemarkitektur/repos/EK_ITA_SWA_2026_fall/scripts/auto_update.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>12</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/auto_update.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/auto_update_error.log</string>
</dict>
</plist>
EOF

# Load the agent
launchctl load ~/.Library/LaunchAgents/com.auto.update.plist
```

### 2. update-from-upstream.sh

Thin shell wrapper around `auto_update.py`, for people who prefer running a
`.sh` script. Same flags apply.

**Usage:**
```bash
chmod +x scripts/update-from-upstream.sh
./scripts/update-from-upstream.sh          # fetch + merge only
./scripts/update-from-upstream.sh --push   # also push
```

## Manual Update

If you prefer to do it manually:

```bash
# Fetch from upstream
git fetch upstream

# Checkout master and merge
git checkout master
git merge upstream/master

# Push to your fork
git push origin master
```

## Updating the Upstream URL

If the upstream repository URL changes:

```bash
git remote set-url upstream https://github.com/Ek-Ita-Swa-Iti/EK_ITA_SWA_2026_fall.git
```
