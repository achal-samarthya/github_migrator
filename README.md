# GitHub Migrator Package

This is the main Python package for the GitHub Project Migrator.

## Package Structure

```
github_migrator/
├── __init__.py              # Package initialization
├── config.py                # Configuration management
├── github_client.py         # Unified GitHub API client
├── excel_handler.py         # Excel file operations
├── field_mapper.py          # Field value mapping
├── issue_manager.py         # Issue management
├── relationship_manager.py  # Relationship handling
├── label_manager.py         # Label management
├── migrator.py              # Main orchestrator
├── cli.py                   # Command-line interface
│
├── .github/                 # GitHub Actions and templates (copied from root)
├── LICENSE                  # MIT License
├── CHANGELOG.md             # Version history
├── CONTRIBUTING.md          # Contribution guidelines
├── CODE_OF_CONDUCT.md       # Code of conduct
├── GITHUB_SETUP.md          # GitHub setup guide
├── PROJECT_SUMMARY.md       # Project overview
├── config.example.json      # Example configuration
├── example_usage.py          # Usage examples
└── MANIFEST.in              # Package manifest
```

## Important Note

**For GitHub to work properly, some files MUST remain at the repository root:**

- `.github/` folder - GitHub Actions and templates (should be at root)
- `README.md` - Main project README (should be at root)
- `setup.py` - Package setup (should be at root)
- `requirements.txt` - Dependencies (should be at root)
- `.gitignore` - Git ignore rules (should be at root)

These files are kept in this folder for organization, but when pushing to GitHub, you should:

1. **Keep `.github/` at root** - Copy it back to root if needed
2. **Keep `README.md` at root** - This is the main project README
3. **Keep `setup.py` and `requirements.txt` at root** - Required for package installation

## Usage

See the main [README.md](../README.md) in the repository root for usage instructions.

## Installation

```bash
pip install -e .
```

## Development

```bash
# Install in development mode
pip install -e .

# Run CLI
python -m github_migrator.cli --help
```

