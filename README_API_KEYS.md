# API Keys Management

> **Note:** This guide covers how to manage API keys locally while keeping them out of Git commits.

## Quick Start

**Just add your API keys to the scripts and use `safe_commit.sh` for commits!**

1. **Add your keys** to any script (they stay there permanently):
   ```bash
   # In run_gpt_*.sh files:
   export OPENAI_API_KEY=sk-your-actual-key-here
   
   # In run_claude_*.sh files:
   export ANTHROPIC_API_KEY=sk-your-actual-key-here
   ```

2. **Use safe commit** for all commits:
   ```bash
   ./safe_commit.sh "Your commit message"
   ```

That's it! Your keys are always in your local files but never committed to Git.

## What Happens

When you run `./safe_commit.sh`:

1. ✅ **Backup** - Your API keys are saved to `.api_keys_backup.txt` (gitignored)
2. ✅ **Remove** - Keys are temporarily removed from scripts
3. ✅ **Commit** - Clean commit (no keys) is made to Git
4. ✅ **Restore** - Keys are automatically put back in your local files

## Manual Method

If you prefer to use git directly:

1. Enable hooks:
   ```bash
   git config core.hooksPath .githooks
   ```

2. Commit normally:
   ```bash
   git add .
   git commit -m "Your message"
   ```

The hooks will handle backup/restore automatically.

## Important Notes

- **Your local scripts always have keys** - They're never permanently removed
- **Git commits never have keys** - They're removed before commit, restored after
- **No need to export every time** - Keys in scripts work directly
- **Backup file is gitignored** - `.api_keys_backup.txt` stays local only

## Troubleshooting

If keys don't restore:
```bash
# Check backup file
cat .api_keys_backup.txt

# Manually restore (if needed)
# Just uncomment/add the export lines back to your scripts
```

If commit fails:
- Keys are automatically restored before the script exits
- Your files are safe

