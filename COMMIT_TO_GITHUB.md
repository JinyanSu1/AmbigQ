# Committing to GitHub: git@github.com:JinyanSu1/AmbigQ.git

## Quick Commit

**Use the safe commit script:**

```bash
cd /home/js3673/UserSimu/clarifying_questions
./safe_commit.sh "Your commit message here"
```

Then push:
```bash
git push origin main
```

## What Will Be Committed

### Important New Files:
- `.gitignore` - Excludes data, results, API keys
- `.gitattributes` - Git configuration
- `.githooks/` - Pre/post-commit hooks for API key management
- `safe_commit.sh` - Safe commit script
- `extract_*.py` - Utility scripts for generating tables
- `README_API_KEYS.md`, `GITHUB_SETUP.md` - Documentation
- `add_local_api_keys.sh` - Helper script

### Core Source Code:
- `src/` - All evaluation scripts
- `run_*.sh` - Experiment scripts (without API keys)
- `requirements.txt` - Dependencies

### Modified Files:
- `README.md` - Updated documentation
- `src/utils.py` - Updated utilities

### Deleted Files (cleanup):
- Old data files
- Unused source files

## Step-by-Step

### 1. Review Changes
```bash
git status
```

### 2. Commit (Safe - handles API keys automatically)
```bash
./safe_commit.sh "Initial commit: Add evaluation framework and scripts"
```

### 3. Verify No API Keys in Commit
```bash
git show HEAD:run_gpt_evaluation.sh | grep "export.*API_KEY=sk-"
# Should show nothing (or only commented lines)
```

### 4. Push to GitHub
```bash
git push origin main
```

## Remote Repository

Current remote: `git@github.com:JinyanSu1/AmbigQ.git`

To verify:
```bash
git remote -v
```

## Troubleshooting

### If push fails:
```bash
# Check if you need to set upstream
git push -u origin main
```

### If authentication fails:
Make sure your SSH key is set up:
```bash
ssh -T git@github.com
```

### If branch mismatch:
```bash
# Check current branch
git branch

# Switch if needed
git checkout main
# or
git checkout -b main
```

