# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-XX

### Added
- Initial release of GitHub Migrator
- Modular architecture with separate components:
  - `GitHubClient`: Unified GraphQL and REST API client
  - `ExcelHandler`: Excel file reading and writing
  - `FieldMapper`: Text to GitHub ID mapping
  - `IssueManager`: Issue creation and management
  - `RelationshipManager`: Issue relationship handling
  - `LabelManager`: Repository label management
  - `GitHubMigrator`: Main orchestrator
- Command-line interface (CLI) with multiple commands:
  - `extract`: Extract issues from GitHub projects
  - `map`: Map field values to GitHub IDs
  - `migrate`: Migrate issues to target repository
  - `relationships`: Migrate issue relationships
  - `labels`: Migrate repository labels
  - `full`: Complete migration workflow
- Configuration system with JSON config files
- Support for:
  - Issue extraction with all metadata
  - Field mapping (iterations, quarters, status, team, priority, etc.)
  - Issue creation with project fields
  - Parent/sub-issue relationships
  - Dependency relationships (blocked-by, blocking)
  - Label migration
  - Comment migration with authors
  - Assignee management
- Error handling and logging
- Dry-run mode for testing
- Batch processing support
- Comprehensive documentation and examples

### Features
- Extract issues from source GitHub projects
- Map human-readable values to GitHub IDs
- Create issues in target repository with all metadata
- Preserve issue relationships
- Migrate labels between repositories
- Handle errors gracefully with detailed reporting
- Support for large-scale migrations

[1.0.0]: https://github.com/yourusername/github-migrator/releases/tag/v1.0.0

