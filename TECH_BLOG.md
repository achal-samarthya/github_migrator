# Building a GitHub Project Migrator: A Deep Dive into Automating Issue Migration

**Author:** Achal Samarthya  
**Published:** January 2025

---

## Introduction

Migrating GitHub projects between organizations or accounts is a common challenge in software development. Whether you're consolidating repositories, moving to a new organization, or restructuring your project management workflow, manually migrating issues, labels, relationships, and project fields is tedious, error-prone, and time-consuming.

In this blog post, I'll walk you through how I built **GitHub Migrator**—a Python-based tool that automates the entire migration process while preserving all the metadata, relationships, and project configurations that make your GitHub projects valuable.

## The Problem

When migrating GitHub projects, you need to preserve:

- **Issues** with titles, descriptions, and metadata
- **Project fields** (status, priority, team assignments, iterations, dates)
- **Labels** with colors and descriptions
- **Issue relationships** (parent/sub-issues, dependencies)
- **Comments** and their authors
- **Assignees** and **milestones**
- **Custom field mappings** between source and target projects

Doing this manually would require:
- Copy-pasting hundreds or thousands of issues
- Recreating all project fields
- Manually establishing relationships
- Risking data loss or corruption

## The Solution: GitHub Migrator

GitHub Migrator is a comprehensive Python tool that automates the entire migration process. It uses GitHub's GraphQL and REST APIs to extract, transform, and migrate all project data while maintaining data integrity.

### Key Features

1. **Automated Issue Extraction** - Extract all issues from source projects with full metadata
2. **Intelligent Field Mapping** - Convert human-readable values to GitHub IDs automatically
3. **Relationship Preservation** - Maintain parent/sub-issue hierarchies and dependencies
4. **Label Migration** - Recreate labels with colors and descriptions
5. **Excel-Based Workflow** - Use Excel files for data review and transformation
6. **CLI and Programmatic API** - Use from command line or integrate into scripts
7. **Error Handling** - Comprehensive error tracking and recovery

## Architecture & Design

### Modular Design

The project follows a modular architecture with clear separation of concerns:

```
github_migrator/
├── github_client.py      # Unified API client (GraphQL + REST)
├── excel_handler.py      # Excel file operations
├── field_mapper.py       # Value-to-ID mapping
├── issue_manager.py      # Issue CRUD operations
├── relationship_manager.py # Relationship management
├── label_manager.py      # Label operations
├── migrator.py          # Main orchestrator
└── cli.py               # Command-line interface
```

### Core Components

#### 1. GitHub Client (`github_client.py`)

The foundation of the tool is a unified client that handles both GraphQL and REST API interactions:

```python
class GitHubClient:
    """Unified client for GitHub GraphQL and REST APIs."""
    
    def __init__(self, config: GitHubConfig):
        self.config = config
        self.session = self._create_session()
    
    def graphql(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a GraphQL query/mutation."""
        # Handles authentication, retries, error handling
        
    def paginate_graphql(self, query: str, ...) -> List[Dict[str, Any]]:
        """Paginate through GraphQL results."""
        # Automatically handles cursor-based pagination
```

**Key Features:**
- Automatic retry logic with exponential backoff
- Connection pooling for performance
- Pagination support for large datasets
- Comprehensive error handling

#### 2. Field Mapper (`field_mapper.py`)

One of the trickiest parts of migration is converting human-readable values (like "In Progress" or "High Priority") into GitHub's internal IDs. The FieldMapper handles this:

```python
class FieldMapper:
    """Maps text values to GitHub IDs based on configuration."""
    
    def map_status(self, value: Any) -> str:
        """Map status text to status option ID."""
        if self._is_hex8_id(value):
            return str(value).strip()
        
        normalized = self._normalize_key(value)
        return self._normalized_mappings["status"].get(normalized, "")
```

**Challenges Solved:**
- Case-insensitive matching
- Handling variations in naming (e.g., "In Progress" vs "in-progress")
- Supporting both text values and existing IDs
- Multi-value field parsing (e.g., multiple labels separated by "||")

#### 3. Issue Manager (`issue_manager.py`)

The IssueManager orchestrates the complex process of creating fully-configured issues:

```python
def create_complete_issue(
    self,
    repo_id: str,
    project_id: str,
    title: str,
    body: str = "",
    milestone_id: Optional[str] = None,
    issue_type_id: Optional[str] = None,
    assignee_ids: Optional[List[str]] = None,
    project_fields: Optional[Dict[str, Dict[str, Any]]] = None,
    comments: Optional[List[str]] = None,
    label_ids: Optional[List[str]] = None
) -> IssueResult:
    """Create a complete issue with all fields, comments, and labels."""
```

This method performs a multi-step process:
1. Create the issue
2. Add it to the project
3. Update issue-level fields (milestone, type, assignees)
4. Update project-level fields (status, team, priority, dates)
5. Add labels
6. Add comments

#### 4. Relationship Manager (`relationship_manager.py`)

Maintaining issue relationships is crucial for preserving project structure:

```python
def add_sub_issue(self, parent_issue_id: str, child_issue_id: str) -> bool:
    """Add a sub-issue relationship."""
    query = """
    mutation($parent: ID!, $child: ID!) {
      addSubIssue(input: { issueId: $parent, subIssueId: $child }) {
        issue { id }
        subIssue { id }
      }
    }
    """
```

**Features:**
- Parent/sub-issue relationships
- Dependency tracking (blocked-by, blocking)
- Duplicate prevention
- Batch processing

#### 5. Excel Handler (`excel_handler.py`)

Excel files serve as an intermediate format for data review and transformation:

```python
class ExcelHandler:
    """Handles Excel file operations for migration data."""
    
    def read_excel(self, file_path: Path, ...) -> Dict[str, pd.DataFrame]:
        """Read Excel file, returning a dictionary of sheet names to DataFrames."""
    
    def parse_multi_value(self, value: Any) -> List[str]:
        """Parse a cell value that may contain multiple values separated by separator."""
```

**Benefits:**
- Human-readable format for review
- Easy data manipulation before migration
- Support for multiple sheets
- Data sanitization for Excel compatibility

## Technical Implementation Details

### GraphQL vs REST API

The tool uses both APIs strategically:

- **GraphQL** for:
  - Complex queries (fetching issues with all related data)
  - Mutations (creating/updating issues, relationships)
  - Efficient data fetching (only requested fields)

- **REST API** for:
  - Label management (simpler REST endpoints)
  - Dependency relationships (REST-specific endpoints)

### Error Handling & Resilience

```python
retry_strategy = Retry(
    total=self.config.max_retries,
    connect=self.config.max_retries,
    read=self.config.max_retries,
    backoff_factor=self.config.retry_delay,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=frozenset(["GET", "POST", "PATCH", "DELETE"]),
    raise_on_status=False,
)
```

**Features:**
- Automatic retry on transient failures
- Rate limit handling (429 errors)
- Continue-on-error mode for batch operations
- Detailed error logging

### Configuration Management

The tool uses a flexible configuration system:

```json
{
  "github": {
    "token": "your-token",
    "api_url": "https://api.github.com/graphql",
    "timeout": 60,
    "max_retries": 5
  },
  "project": {
    "source_project_id": "PVT_...",
    "target_repo_id": "R_...",
    "target_project_id": "PVT_..."
  },
  "field_mapping": {
    "status_mapping": {
      "In Progress": "abc123",
      "Done": "def456"
    }
  }
}
```

**Benefits:**
- JSON-based (human-readable)
- Environment variable support
- Command-line overrides
- Default values with sensible defaults

## Usage Examples

### Command-Line Interface

```bash
# Extract issues from source project
github-migrator extract \
  --project-id PVT_kwDODKp0h84BGorz \
  --output extracted_issues.xlsx

# Map field values to GitHub IDs
github-migrator map \
  --input extracted_issues.xlsx \
  --output mapped_issues.xlsx

# Migrate issues to target repository
github-migrator migrate \
  --input mapped_issues.xlsx \
  --output migration_results.xlsx

# Migrate relationships
github-migrator relationships \
  --input relationships.xlsx \
  --output relationships_results.xlsx
```

### Programmatic Usage

```python
from pathlib import Path
from github_migrator import Config, GitHubMigrator

# Load configuration
config = Config.from_file(Path("config.json"))
config.github.token = "your-token"

# Initialize migrator
migrator = GitHubMigrator(config)

# Extract issues
migrator.extract_issues(
    project_id="PVT_kwDODKp0h84BGorz",
    output_path=Path("output/extracted_issues.xlsx"),
    limit=100
)

# Map fields
migrator.map_fields(
    input_path=Path("output/extracted_issues.xlsx"),
    output_path=Path("output/mapped_issues.xlsx")
)

# Migrate issues
summary = migrator.migrate_issues(
    input_path=Path("output/mapped_issues.xlsx"),
    output_path=Path("output/migration_results.xlsx")
)

print(f"Migration complete: {summary['success']} success, {summary['failed']} failed")
```

## Challenges & Solutions

### Challenge 1: Field ID Mapping

**Problem:** GitHub uses opaque IDs (like `PVTSSF_lADODKp0h84BGorzzg3n78s`) for project fields, but users work with human-readable values.

**Solution:** Created a mapping system that:
- Normalizes text values (case-insensitive, whitespace handling)
- Supports both text-to-ID and ID-to-ID mapping
- Handles variations in naming conventions
- Provides configuration for custom mappings

### Challenge 2: Relationship Dependencies

**Problem:** Issues must exist before relationships can be established, but relationships define the project structure.

**Solution:** Implemented a two-phase approach:
1. Create all issues first
2. Establish relationships in a second pass
3. Track processed relationships to avoid duplicates

### Challenge 3: Rate Limiting

**Problem:** GitHub API has strict rate limits that can cause failures during large migrations.

**Solution:**
- Automatic retry with exponential backoff
- Configurable delays between requests
- Batch processing with progress tracking
- Graceful error handling with continue-on-error mode

### Challenge 4: Data Integrity

**Problem:** Ensuring all data is migrated correctly without loss or corruption.

**Solution:**
- Comprehensive logging at each step
- Result tracking with success/failure status
- Excel output for verification
- Dry-run mode for testing

## Performance Considerations

For large migrations (1000+ issues):

- **Pagination:** Automatically handles GraphQL pagination
- **Batch Processing:** Configurable batch sizes
- **Connection Pooling:** Reuses HTTP connections
- **Parallel Processing:** Can be extended for concurrent operations

**Typical Performance:**
- ~2-5 issues per second (respecting rate limits)
- 1000 issues ≈ 5-10 minutes
- Relationship migration: ~1-2 relationships per second

## Future Improvements

1. **Parallel Processing** - Migrate multiple issues concurrently
2. **Progress Tracking** - Real-time progress bars and ETA
3. **Resume Capability** - Resume interrupted migrations
4. **Webhook Support** - Real-time migration status
5. **GUI Interface** - Web-based interface for non-technical users
6. **Migration Templates** - Pre-configured templates for common scenarios
7. **Validation Tools** - Pre-migration validation and conflict detection

## Lessons Learned

1. **Start with GraphQL** - More efficient for complex queries, but REST is simpler for some operations
2. **Excel as Intermediate Format** - Provides human review and debugging capabilities
3. **Modular Design** - Makes testing and maintenance easier
4. **Comprehensive Logging** - Essential for debugging migration issues
5. **Configuration Flexibility** - Users have diverse needs and setups

## Conclusion

Building GitHub Migrator taught me a lot about:
- GitHub's API architecture (GraphQL vs REST)
- Handling large-scale data migrations
- Building resilient systems with proper error handling
- Creating developer-friendly tools with both CLI and programmatic interfaces

The tool has successfully migrated thousands of issues across multiple projects, saving countless hours of manual work while ensuring data integrity.

If you're facing a similar migration challenge, I encourage you to check out the project on GitHub: [github.com/achal-samarthya/github_migrator](https://github.com/achal-samarthya/github_migrator)

## Resources

- **GitHub Repository:** [github.com/achal-samarthya/github_migrator](https://github.com/achal-samarthya/github_migrator)
- **GitHub GraphQL API Docs:** [docs.github.com/en/graphql](https://docs.github.com/en/graphql)
- **GitHub REST API Docs:** [docs.github.com/en/rest](https://docs.github.com/en/rest)

---

**About the Author**

Achal Samarthya is a software developer passionate about automation and developer tooling. When not building tools to make developers' lives easier, you can find him contributing to open-source projects or writing about software engineering.

**Connect:**
- GitHub: [@achal-samarthya](https://github.com/achal-samarthya)
- Repository: [github.com/achal-samarthya/github_migrator](https://github.com/achal-samarthya/github_migrator)

---

*This blog post was written as part of documenting the GitHub Migrator project. Feel free to share, fork, or contribute to the project!*

