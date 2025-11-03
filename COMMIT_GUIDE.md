# How to Commit Your Changes

## Quick Start

Use the safe commit script - it handles API key removal automatically:

```bash
./safe_commit.sh "Your commit message here"
```

For example:
```bash
./safe_commit.sh "Add evaluation scripts and core functionality"
./safe_commit.sh "Update README with setup instructions"
./safe_commit.sh "Clean up temporary files"
```

## What Happens Automatically

1. ✅ **Backup** - Your API keys are saved to `.api_keys_backup.txt` (gitignored)
2. ✅ **Remove** - Keys are temporarily removed from all shell scripts
3. ✅ **Commit** - Clean commit is made (no API keys in Git)
4. ✅ **Restore** - Keys are automatically put back in your local files

**Your local files always keep working with keys!**

## Step-by-Step Process

### 1. Check What Will Be Committed

```bash
git status
```

### 2. Stage Your Changes (Optional)

If you want to be selective:
```bash
git add src/
git add run_*.sh
git add README.md
# etc.
```

Or stage everything:
```bash
git add -A
```

### 3. Commit Using Safe Script

```bash
./safe_commit.sh "Your descriptive commit message"
```

The script will automatically:
- Stage all changes if you haven't already
- Remove API keys
- Commit
- Restore API keys

## Alternative: Manual Git Commands

If you prefer using git directly:

### Enable Git Hooks

First, enable the hooks:
```bash
git config core.hooksPath .githooks
```

### Then Commit Normally

```bash
git add .
git commit -m "Your commit message"
```

The hooks will automatically handle API key backup/restore.

## First-Time Setup (If Needed)

If this is a new repository:

```bash
cd /home/js3673/UserSimu/clarifying_questions

# Initialize git (if not already done)
git init

# Enable hooks
git config core.hooksPath .githooks

# Make sure hooks are executable
chmod +x .githooks/pre-commit .githooks/post-commit

# Add remote (if pushing to GitHub)
git remote add origin https://github.com/yourusername/your-repo.git
```

## Verify API Keys Are Removed

After committing, verify your keys aren't in Git:

```bash
# Check the last commit
git show HEAD:run_gpt_evaluation.sh | grep API_KEY

# Should show only comments, not actual keys
```

## Push to GitHub

Once you're ready:

```bash
git push origin main
# or
git push origin master
```

## Important Notes

- **Always use `safe_commit.sh`** - It ensures keys are never committed
- **Your local files keep working** - Keys are restored after commit
- **Never manually commit files with API keys** - Let the script handle it
- **Backup file is gitignored** - `.api_keys_backup.txt` stays local only

## Troubleshooting

If commit fails:
- Keys are automatically restored before the script exits
- Check git status to see what went wrong
- Try committing again with `safe_commit.sh`

If keys don't restore:
- Check `.api_keys_backup.txt` file
- Manually uncomment/add your API key lines back to scripts

