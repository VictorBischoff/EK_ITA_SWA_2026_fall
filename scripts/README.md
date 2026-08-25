# Maintenance Scripts

This directory contains scripts to help maintain this forked repository.

## Automatic Updates

The upstream remote has been configured to point to:
```
https://github.com/ClausBove/EK_ITA_SWA_2026_fall.git
```

You can verify this with:
```bash
git remote -v
```

## Scripts

### 1. auto_update.py (Recommended)

Python script for fully automatic updates. Handles all edge cases:
- Adds upstream remote if missing
- Stashes local changes automatically
- Attempts fast-forward merge, falls back to regular merge
- Pushes to your fork automatically
- Returns to your original branch
- Reapplies stashed changes

**Usage:**
```bash
python scripts/auto_update.py
```

**For Automatic Execution (macOS/Linux):**

Add to crontab to run hourly:
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

Bash script alternative for manual updates.

**Usage:**
```bash
chmod +x scripts/update-from-upstream.sh
./scripts/update-from-upstream.sh
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
git remote set-url upstream https://github.com/ClausBove/EK_ITA_SWA_2026_fall.git
```
