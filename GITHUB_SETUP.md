# GitHub Setup Guide

This repository is configured to keep API keys locally for your convenience while automatically removing them when pushing to GitHub.

## How It Works

1. **Locally**: Add your API keys directly to the shell scripts - they stay there for easy development
2. **On Commit**: API keys are automatically backed up, removed, committed, then restored
3. **On GitHub**: Commits contain NO API keys - only your local files have them

## Setup for Local Development

### Option 1: Add Keys to Scripts Directly

Edit any shell script and uncomment/add your API key:

```bash
# In run_gpt_*.sh, run_judge_*.sh files:
export OPENAI_API_KEY=sk-your-actual-key-here

# In run_claude_*.sh files:
export ANTHROPIC_API_KEY=sk-your-actual-key-here
```

These keys will work locally but will be automatically removed when you commit.

### Option 2: Use the Helper Script

Run the interactive helper:
```bash
./add_local_api_keys.sh
```

It will prompt you for your keys and add them to all relevant scripts.

### Option 3: Use Environment Variables

Set them in your shell before running scripts:
```bash
export OPENAI_API_KEY=sk-your-key
export ANTHROPIC_API_KEY=sk-your-key
```

## Using Safe Commit (Recommended)

**Use the safe commit script** - it handles everything automatically:

```bash
./safe_commit.sh "Your commit message here"
```

This script will:
1. Backup your API keys
2. Remove them from files temporarily
3. Commit your changes
4. Restore your API keys automatically

**Your local files always keep working with keys!**

## Alternative: Using Git Hooks

If you prefer using git hooks directly:

```bash
git config core.hooksPath .githooks
```

Then commit normally:
```bash
git add .
git commit -m "Your message"
```

The hooks will automatically:
- Backup keys before commit
- Remove keys during commit
- Restore keys after commit

## Testing

1. Add your API key to a script locally
2. Try to commit:
   ```bash
   git add run_gpt_evaluation.sh
   git commit -m "Test commit"
   ```
3. Check the committed file - your API key should be gone:
   ```bash
   git show HEAD:run_gpt_evaluation.sh | grep API_KEY
   ```

## Important Notes

- **Never commit API keys manually** - Always let the pre-commit hook handle it
- The hook removes lines matching `export *_API_KEY=sk-*` pattern
- Placeholder comments (starting with `#`) are preserved
- Your local files remain unchanged (only the commit has keys removed)

## If Pre-commit Hook Doesn't Work

If for some reason the hook doesn't run, you can manually clean scripts before committing:

```bash
# Remove API keys from all scripts
for file in run_*.sh; do
    sed -i '/^export \(OPENAI\|ANTHROPIC\)_API_KEY=sk-[^"]*/d' "$file"
done
```

Then commit normally.

