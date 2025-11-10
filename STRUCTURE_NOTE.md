# File Structure Note

## Current Organization

All GitHub-related files have been moved into the `github_migrator/` folder for better organization.

## Files That Should Be at Repository Root

For GitHub to properly recognize and use certain files, they **MUST** be at the repository root:

### Required at Root:
1. **`.github/`** - GitHub Actions, issue templates, workflows
   - Location: `.github/` (not inside github_migrator/)
   - Why: GitHub looks for this folder at the root

2. **`README.md`** - Main project documentation
   - Location: Root of repository
   - Why: GitHub displays this on the repository homepage

3. **`LICENSE`** - Project license
   - Location: Root (or github_migrator/ is fine too)
   - Why: GitHub recognizes it at root, but works in subfolder too

4. **`setup.py`** - Python package setup
   - Location: Root
   - Why: Standard Python package structure

5. **`requirements.txt`** - Dependencies
   - Location: Root
   - Why: Standard Python project structure

6. **`.gitignore`** - Git ignore rules
   - Location: Root
   - Why: Git looks for this at repository root

## Recommended Action

When setting up the GitHub repository:

1. **Copy `.github/` to root** (if it's only in github_migrator/)
2. **Keep `README.md` at root** (main project README)
3. **Keep `setup.py` at root**
4. **Keep `requirements.txt` at root**
5. **Keep `.gitignore` at root**

Other files (CHANGELOG.md, CONTRIBUTING.md, etc.) can stay in github_migrator/ or be moved to root - both work fine.

## Quick Fix Script

If you need to move files back to root:

```bash
# Copy .github to root (if needed)
cp -r github_migrator/.github .  # Linux/Mac
xcopy /E /I github_migrator\.github .github  # Windows

# Copy LICENSE to root (optional)
cp github_migrator/LICENSE .  # Linux/Mac
copy github_migrator\LICENSE .  # Windows
```

## Current Status

✅ All files are organized in `github_migrator/` folder
⚠️ Remember to copy `.github/` to root before pushing to GitHub
⚠️ Keep `README.md`, `setup.py`, `requirements.txt` at root

