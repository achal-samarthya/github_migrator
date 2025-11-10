# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

Please report (suspected) security vulnerabilities to **[security@example.com](mailto:security@example.com)**. You will receive a response within 48 hours. If the issue is confirmed, we will release a patch as soon as possible depending on complexity but historically within a few days.

## Security Best Practices

When using this tool:

1. **Never commit your GitHub token** to version control
2. **Use environment variables** or secure secret management for tokens
3. **Use fine-grained tokens** with minimal required permissions
4. **Review token permissions** regularly
5. **Rotate tokens** periodically
6. **Use dry-run mode** to test before actual migration
7. **Backup data** before running migrations

## Token Permissions

The tool requires the following GitHub token permissions:

- `repo` - Full control of private repositories
- `read:org` - Read org and team membership
- `read:project` - Read project data
- `write:project` - Write project data

Use the minimum permissions necessary for your use case.

## Disclosure Policy

- We will acknowledge receipt of your vulnerability report within 48 hours
- We will provide a detailed response within 7 days
- We will keep you informed of the progress toward resolving the vulnerability
- We will notify you when the vulnerability has been resolved

Thank you for helping keep GitHub Migrator and our users safe!

