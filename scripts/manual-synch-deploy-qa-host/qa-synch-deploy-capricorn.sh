#!/bin/bash
# Capricorn Deployment Script
# Syncs latest code from DevShare to QA Server location and restarts QA environment

set -e

echo ""
echo "🚀 Capricorn Deployment Script"
echo "==============================="
echo ""

SOURCE_BASE="/home/agamache/DevShare/cursor-projects"
DEST_DIR="/home/agamache/projects/unified_ui_DEV_PROD_GCP_2026"

# Step 1: Find the most recently updated unified_ui_DEV_PROD_GCP_2026* directory
echo "📂 Step 1: Finding latest source directory..."

if [ ! -d "$SOURCE_BASE" ]; then
    echo "❌ ERROR: Source directory not found: $SOURCE_BASE"
    exit 1
fi

# Find all directories matching the pattern and check which has most recent files
LATEST_DIR=""
LATEST_TIME=0

for dir in "$SOURCE_BASE"/unified_ui_DEV_PROD_GCP_2026*; do
    if [ -d "$dir" ]; then
        # Get the most recent modification time of any file in this directory
        RECENT_FILE=$(find "$dir" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1)
        if [ -n "$RECENT_FILE" ]; then
            FILE_TIME=$(echo "$RECENT_FILE" | awk '{print $1}' | cut -d. -f1)
            if [ "$FILE_TIME" -gt "$LATEST_TIME" ]; then
                LATEST_TIME=$FILE_TIME
                LATEST_DIR="$dir"
            fi
        fi
    fi
done

if [ -z "$LATEST_DIR" ]; then
    echo "❌ ERROR: No directories found matching pattern: unified_ui_DEV_PROD_GCP_2026*"
    exit 1
fi

echo "   ✅ Found latest: $(basename "$LATEST_DIR")"
echo "   📅 Last modified: $(date -d @$LATEST_TIME '+%Y-%m-%d %H:%M:%S')"
echo ""

# Step 2: Mirror the directory
echo "🔄 Step 2: Mirroring directory to QA Server location..."
echo "   Source: $LATEST_DIR"
echo "   Dest:   $DEST_DIR"
echo ""

# Create parent directory if it doesn't exist
mkdir -p "$(dirname "$DEST_DIR")"

# Use rsync to mirror (delete files in dest that don't exist in source)
rsync -av --delete \
    --exclude='.git/' \
    --exclude='node_modules/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    "$LATEST_DIR/" "$DEST_DIR/"

echo ""
echo "   ✅ Directory mirrored successfully"
echo ""

# Step 3: Navigate to destination and run nuke
echo "💀 Step 3: Nuking existing QA environment..."
cd "$DEST_DIR"

if [ ! -f "./capricorn/scripts/run-qa.sh" ]; then
    echo "❌ ERROR: run-qa.sh not found in $DEST_DIR/capricorn/scripts/"
    exit 1
fi

# Run nuke - this requires user confirmation
echo "NUKE" | ./capricorn/scripts/run-qa.sh nuke

echo ""
echo "   ✅ QA environment nuked"
echo ""

# Step 4: Start fresh QA environment
echo "🚀 Step 4: Starting fresh QA environment..."
./capricorn/scripts/run-qa.sh start

echo ""
echo "✅ Deployment complete!"
echo ""
echo "   QA URL: http://192.168.1.180:5001"
echo ""

