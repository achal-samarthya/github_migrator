"""
Example usage of the GitHub Migrator.

Author: Achal Samarthya

This script demonstrates how to use the GitHub Migrator programmatically.
It provides example code snippets showing how to:
- Load configuration and initialize the migrator
- Extract issues from a source project
- Map field values to GitHub IDs
- Migrate issues to a target repository
- Migrate issue relationships
- Migrate labels

This file serves as a reference implementation for developers who want to
integrate the migrator into their own scripts or applications.
"""

from pathlib import Path
from github_migrator import Config, GitHubMigrator
from github_migrator.label_manager import Label

# Example 1: Load configuration and initialize migrator
config = Config.from_file(Path("config.json"))
config.github.token = "your-token-here"  # Or set GITHUB_TOKEN env var

migrator = GitHubMigrator(config)

# Example 2: Extract issues from source project
print("Extracting issues...")
migrator.extract_issues(
    project_id="PVT_kwDODKp0h84BGorz",
    output_path=Path("output/extracted_issues.xlsx"),
    limit=100  # Optional: limit number of issues
)

# Example 3: Map field values to GitHub IDs
print("Mapping fields...")
migrator.map_fields(
    input_path=Path("output/extracted_issues.xlsx"),
    output_path=Path("output/mapped_issues.xlsx")
)

# Example 4: Migrate issues to target repository
print("Migrating issues...")
summary = migrator.migrate_issues(
    input_path=Path("output/mapped_issues.xlsx"),
    output_path=Path("output/migration_results.xlsx")
)
print(f"Migration complete: {summary['success']} success, {summary['failed']} failed")

# Example 5: Migrate relationships
print("Migrating relationships...")
rel_summary = migrator.migrate_relationships(
    input_path=Path("output/relationships.xlsx"),
    output_path=Path("output/relationships_results.xlsx")
)
print(f"Relationships added: {rel_summary['relationships_added']}")

# Example 6: Migrate labels
print("Migrating labels...")
labels = [
    Label(name="bug", color="d73a4a", description="Something isn't working"),
    Label(name="enhancement", color="a2eeef", description="New feature or request"),
    Label(name="documentation", color="0075ca", description="Documentation improvements"),
]
labels_summary = migrator.migrate_labels(labels)
print(f"Labels migrated: {labels_summary['success']} success, {labels_summary['failed']} failed")

# Cleanup
migrator.close()
print("Done!")

