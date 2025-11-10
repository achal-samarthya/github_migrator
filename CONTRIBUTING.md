# Contributing to GitHub Migrator

Thank you for your interest in contributing to GitHub Migrator! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Report issues or concerns to maintainers

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/yourusername/github-migrator/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (Python version, OS, etc.)
   - Error messages or logs

### Suggesting Features

1. Check existing issues and discussions
2. Create a new issue with:
   - Clear description of the feature
   - Use case and benefits
   - Possible implementation approach (if you have ideas)

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/github-migrator.git
   cd github-migrator
   ```

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Make your changes**
   - Follow the code style (see below)
   - Add tests if applicable
   - Update documentation
   - Update CHANGELOG.md

5. **Test your changes**
   ```bash
   # Run tests if available
   pytest
   
   # Test your specific feature
   python -m github_migrator.cli --help
   ```

6. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```
   
   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `refactor:` for code refactoring
   - `test:` for tests
   - `chore:` for maintenance

7. **Push and create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   
   Then create a Pull Request on GitHub with:
   - Clear title and description
   - Reference related issues
   - Screenshots or examples if applicable

## Code Style

- Follow PEP 8 style guide
- Use type hints where possible
- Write docstrings for all public functions/classes
- Keep functions focused and small
- Use meaningful variable and function names

### Example

```python
def create_issue(
    self,
    repo_id: str,
    title: str,
    body: str = ""
) -> IssueResult:
    """
    Create a new issue.
    
    Args:
        repo_id: Repository node ID
        title: Issue title
        body: Issue body/description
    
    Returns:
        IssueResult with issue details
    """
    # Implementation
```

## Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for good test coverage
- Test edge cases and error conditions

## Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Update CHANGELOG.md with your changes
- Include examples in documentation

## Review Process

1. All PRs require review from maintainers
2. Address feedback and suggestions
3. Ensure CI checks pass
4. Maintainers will merge when ready

## Questions?

Feel free to:
- Open an issue for questions
- Start a discussion
- Contact maintainers

Thank you for contributing! 🎉

