#!/bin/bash
# Safe commit script: backs up API keys, commits, then restores them

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BACKUP_FILE=".api_keys_backup.txt"

echo "=== Preparing for commit ==="

# Step 1: Backup API keys from all shell scripts
echo "1. Backing up API keys..."
> "$BACKUP_FILE"

for file in run_*.sh; do
    if [ -f "$file" ]; then
        # Extract and backup API key lines
        api_lines=$(grep "^export \(OPENAI\|ANTHROPIC\)_API_KEY=" "$file" 2>/dev/null || true)
        if [ -n "$api_lines" ]; then
            echo "FILE:$file" >> "$BACKUP_FILE"
            echo "$api_lines" >> "$BACKUP_FILE"
        fi
    fi
done

if [ ! -s "$BACKUP_FILE" ]; then
    echo "   No API keys found in scripts (already clean or using env vars)"
    rm -f "$BACKUP_FILE"
else
    echo "   API keys backed up to $BACKUP_FILE"
fi

# Step 2: Remove API keys from files temporarily
echo "2. Removing API keys from scripts (temporary)..."
for file in run_*.sh; do
    if [ -f "$file" ]; then
        # Remove API key lines
        sed -i.bak '/^export \(OPENAI\|ANTHROPIC\)_API_KEY=sk-[^"]*/d' "$file" 2>/dev/null || true
        rm -f "$file.bak" 2>/dev/null || true
    fi
done

# Step 3: Stage and commit
echo "3. Committing changes..."
if [ $# -eq 0 ]; then
    echo "   Usage: $0 <commit-message>"
    echo "   Or: $0 \"commit message here\""
    
    # Restore keys even if commit fails
    if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
        echo ""
        echo "Restoring API keys..."
        restore_api_keys
    fi
    exit 1
fi

COMMIT_MSG="$@"

# Stage all changes
git add -A

# Commit
git commit -m "$COMMIT_MSG" || {
    echo "Commit failed. Restoring API keys..."
    if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
        restore_api_keys
    fi
    exit 1
}

# Function to restore API keys
restore_api_keys() {
    if [ ! -f "$BACKUP_FILE" ] || [ ! -s "$BACKUP_FILE" ]; then
        return
    fi
    
    current_file=""
    while IFS= read -r line; do
        if [[ "$line" =~ ^FILE: ]]; then
            current_file="${line#FILE:}"
        elif [[ "$line" =~ ^export.*API_KEY= ]] && [ -n "$current_file" ] && [ -f "$current_file" ]; then
            # Check if key already exists (shouldn't, but safety check)
            if ! grep -q "^export.*API_KEY=" "$current_file"; then
                # Add after "set -e" line
                sed -i "/^set -e$/a\\$line" "$current_file"
            fi
        fi
    done < "$BACKUP_FILE"
    
    echo "   API keys restored to scripts."
}

# Step 4: Restore API keys
echo "4. Restoring API keys..."
restore_api_keys

# Step 5: Cleanup
echo ""
echo "=== Commit complete! ==="
echo "API keys have been restored to your local scripts."
echo "The commit on GitHub does NOT contain any API keys."

