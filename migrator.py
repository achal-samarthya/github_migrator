"""
Main migrator orchestrator - coordinates the migration process.

Author: Achal Samarthya

This module provides the main GitHubMigrator class that orchestrates the
entire migration process. It coordinates:
- Extracting issues from source GitHub projects using GraphQL queries
- Mapping field values from human-readable text to GitHub IDs
- Migrating issues to target repositories with all their metadata
- Migrating issue relationships (parent/sub-issues, dependencies)
- Migrating labels to target repositories

The GitHubMigrator class brings together all the other components
(ExcelHandler, FieldMapper, IssueManager, RelationshipManager, LabelManager)
to provide a complete migration solution. It handles the workflow from
extraction through mapping to final migration.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

from .config import Config
from .github_client import GitHubClient
from .excel_handler import ExcelHandler
from .field_mapper import FieldMapper
from .issue_manager import IssueManager
from .relationship_manager import RelationshipManager
from .label_manager import LabelManager, Label

logger = logging.getLogger(__name__)


class GitHubMigrator:
    """Main orchestrator for GitHub project migration."""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = GitHubClient(config.github)
        self.excel = ExcelHandler(config.processing.multi_value_separator)
        self.field_mapper = FieldMapper(config.field_mapping)
        self.issue_manager = IssueManager(
            self.client,
            config.project,
            config.processing
        )
        self.relationship_manager = RelationshipManager(
            self.client,
            config.processing
        )
        self.label_manager = LabelManager(
            self.client,
            config.processing
        )
        
        # Create output directory
        self.output_dir = Path(config.processing.output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_issues(
        self,
        project_id: str,
        output_path: Path,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Extract issues from a GitHub project.
        
        Args:
            project_id: Project node ID
            output_path: Output Excel file path
            limit: Maximum number of issues to extract (None for all)
        
        Returns:
            DataFrame with extracted issues
        """
        logger.info(f"Extracting issues from project {project_id}")
        
        query = """
        query($projectId: ID!, $first: Int!, $after: String) {
          node(id: $projectId) {
            ... on ProjectV2 {
              items(first: $first, after: $after) {
                nodes {
                  id
                  content {
                    __typename
                    ... on Issue {
                      id
                      number
                      title
                      url
                      body
                      repository {
                        id
                        nameWithOwner
                      }
                      issueType { id name }
                      milestone { id title }
                      assignees(first: 100) {
                        nodes { id login name }
                      }
                      labels(first: 100) {
                        nodes { id name }
                      }
                      comments(first: 100) {
                        nodes {
                          id
                          body
                          createdAt
                          author {
                            login
                            ... on User { name }
                          }
                        }
                      }
                    }
                  }
                }
                pageInfo { hasNextPage endCursor }
              }
            }
          }
        }
        """
        
        rows = []
        count = 0
        
        for item in self.client.paginate_graphql(
            query,
            {"projectId": project_id, "first": 100},
            page_info_path=["node", "items", "pageInfo"],
            nodes_path=["node", "items", "nodes"],
            max_pages=None if limit is None else (limit // 100 + 1)
        ):
            if limit and count >= limit:
                break
            
            content = item.get("content")
            if not content or content.get("__typename") != "Issue":
                continue
            
            issue = content
            repo = issue.get("repository", {})
            
            # Extract assignees
            assignees = [a.get("name") or a.get("login", "") 
                        for a in issue.get("assignees", {}).get("nodes", [])]
            
            # Extract labels
            labels = [l.get("name", "") 
                      for l in issue.get("labels", {}).get("nodes", [])]
            
            # Extract comments
            comments = [c.get("body", "") 
                       for c in issue.get("comments", {}).get("nodes", [])]
            comment_authors = [
                (c.get("author", {}).get("name") or c.get("author", {}).get("login", ""))
                for c in issue.get("comments", {}).get("nodes", [])
            ]
            
            row = {
                "issueTitle": self.excel.sanitize_text(issue.get("title", "")),
                "issueBody": self.excel.sanitize_text(issue.get("body", "")),
                "assigneeIds": self.excel.join_multi_value(assignees),
                "labelIds": self.excel.join_multi_value(labels),
                "comments": self.excel.join_multi_value(comments),
                "commentAuthors": self.excel.join_multi_value(comment_authors),
                "issueTypeId": (issue.get("issueType") or {}).get("name", ""),
                "milestoneId": (issue.get("milestone") or {}).get("title", ""),
                "repoId": repo.get("id", ""),
            }
            
            rows.append(row)
            count += 1
        
        df = pd.DataFrame(rows)
        self.excel.write_excel({"Issues": df}, output_path)
        logger.info(f"Extracted {len(df)} issues to {output_path}")
        
        return df
    
    def map_fields(self, input_path: Path, output_path: Path) -> pd.DataFrame:
        """
        Map text values to GitHub IDs in an Excel file.
        
        Args:
            input_path: Input Excel file path
            output_path: Output Excel file path
        
        Returns:
            Mapped DataFrame
        """
        logger.info(f"Mapping fields in {input_path}")
        
        sheets = self.excel.read_excel(input_path)
        processed_sheets = {}
        
        for sheet_name, df in sheets.items():
            df = df.copy()
            
            # Map each field
            if "iterationId" in df.columns:
                df["iterationId"] = df["iterationId"].apply(self.field_mapper.map_iteration)
            
            if "quarterIterationId" in df.columns:
                df["quarterIterationId"] = df["quarterIterationId"].apply(self.field_mapper.map_quarter)
            
            if "statusOptionId" in df.columns:
                df["statusOptionId"] = df["statusOptionId"].apply(self.field_mapper.map_status)
            
            if "teamOptionId" in df.columns:
                df["teamOptionId"] = df["teamOptionId"].apply(self.field_mapper.map_team)
            
            if "priorityOptionId" in df.columns:
                df["priorityOptionId"] = df["priorityOptionId"].apply(self.field_mapper.map_priority)
            
            if "readinessOptionId" in df.columns:
                df["readinessOptionId"] = df["readinessOptionId"].apply(self.field_mapper.map_readiness)
            
            if "estimatedEffortOptionId" in df.columns:
                df["estimatedEffortOptionId"] = df["estimatedEffortOptionId"].apply(self.field_mapper.map_effort)
            
            if "milestoneId" in df.columns:
                df["milestoneId"] = df["milestoneId"].apply(self.field_mapper.map_milestone)
            
            if "labelIds" in df.columns:
                df["labelIds"] = df["labelIds"].apply(
                    lambda x: self.field_mapper.map_labels(x, self.config.processing.multi_value_separator)
                )
            
            if "assigneeIds" in df.columns:
                df["assigneeIds"] = df["assigneeIds"].apply(
                    lambda x: self.field_mapper.map_users(x, self.config.processing.multi_value_separator)
                )
            
            if "commentAuthors" in df.columns:
                df["commentAuthors"] = df["commentAuthors"].apply(
                    lambda x: self.field_mapper.map_users(x, self.config.processing.multi_value_separator)
                )
            
            if "issueTypeId" in df.columns and "labelIds" in df.columns:
                df["issueTypeId"] = df.apply(
                    lambda row: self.field_mapper.map_issue_type(
                        row.get("issueTypeId"),
                        row.get("labelIds")
                    ),
                    axis=1
                )
            
            # Format dates
            if "startDate" in df.columns:
                df["startDate"] = df["startDate"].apply(self.field_mapper.format_date)
            
            if "endDate" in df.columns:
                df["endDate"] = df["endDate"].apply(self.field_mapper.format_date)
            
            # Add repo and project IDs
            df["repoId"] = self.config.project.target_repo_id
            df["projectId"] = self.config.project.target_project_id
            
            processed_sheets[sheet_name] = df
        
        self.excel.write_excel(processed_sheets, output_path)
        logger.info(f"Mapped fields written to {output_path}")
        
        return list(processed_sheets.values())[0] if processed_sheets else pd.DataFrame()
    
    def migrate_issues(
        self,
        input_path: Path,
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Migrate issues from Excel file to GitHub.
        
        Args:
            input_path: Input Excel file path
            output_path: Optional output Excel file path for results
        
        Returns:
            Summary dictionary
        """
        logger.info(f"Migrating issues from {input_path}")
        
        sheets = self.excel.read_excel(input_path)
        sheet_name = self.excel.find_sheet_by_name(input_path, "Issues") or list(sheets.keys())[0]
        df = sheets[sheet_name]
        
        results = []
        summary = {
            "total": len(df),
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        for idx, row in df.iterrows():
            try:
                # Extract data
                repo_id = str(row.get("repoId", self.config.project.target_repo_id)).strip()
                project_id = str(row.get("projectId", self.config.project.target_project_id)).strip()
                title = str(row.get("issueTitle", "")).strip()
                body = str(row.get("issueBody", "")).strip()
                
                if not title:
                    logger.warning(f"Row {idx}: Skipping - no title")
                    continue
                
                # Parse multi-value fields
                assignee_ids = self.excel.parse_multi_value(row.get("assigneeIds"))
                label_ids = self.excel.parse_multi_value(row.get("labelIds"))
                comments = self.excel.parse_multi_value(row.get("comments"))
                comment_authors = self.excel.parse_multi_value(row.get("commentAuthors"))
                
                # Build project fields dict
                project_fields = {}
                field_mappings = {
                    "startDate": ("PVTF_lADODKp0h84BGorzzg3n8DA", "date"),
                    "endDate": ("PVTF_lADODKp0h84BGorzzg3n8DE", "date"),
                    "iterationId": ("PVTIF_lADODKp0h84BGorzzg3n8C8", "iteration"),
                    "quarterIterationId": ("PVTIF_lADODKp0h84BGorzzg3n-8w", "iteration"),
                    "statusOptionId": ("PVTSSF_lADODKp0h84BGorzzg3n78s", "singleSelect"),
                    "teamOptionId": ("PVTSSF_lADODKp0h84BGorzzg3n9y8", "singleSelect"),
                    "priorityOptionId": ("PVTSSF_lADODKp0h84BGorzzg3n8Cw", "singleSelect"),
                    "readinessOptionId": ("PVTSSF_lADODKp0h84BGorzzg3oCKI", "singleSelect"),
                    "estimatedEffortOptionId": ("PVTSSF_lADODKp0h84BGorzzg3n8C0", "singleSelect"),
                }
                
                for field_name, (field_id, field_type) in field_mappings.items():
                    value = row.get(field_name)
                    if value and str(value).strip():
                        project_fields[field_id] = {
                            "value": str(value).strip(),
                            "type": field_type
                        }
                
                # Add comments with authors
                comments_with_authors = []
                for i, comment in enumerate(comments):
                    if i < len(comment_authors) and comment_authors[i]:
                        author = comment_authors[i]
                        comments_with_authors.append(f"[Author: {author}] {comment}")
                    else:
                        comments_with_authors.append(comment)
                
                # Create issue
                result = self.issue_manager.create_complete_issue(
                    repo_id=repo_id,
                    project_id=project_id,
                    title=title,
                    body=body,
                    milestone_id=str(row.get("milestoneId", "")).strip() or None,
                    issue_type_id=str(row.get("issueTypeId", "")).strip() or None,
                    assignee_ids=assignee_ids if assignee_ids else None,
                    project_fields=project_fields if project_fields else None,
                    comments=comments_with_authors if comments_with_authors else None,
                    label_ids=label_ids if label_ids else None
                )
                
                result_row = {
                    "row": idx,
                    "title": title,
                    "success": result.success,
                    "issueId": result.issue_id,
                    "issueNumber": result.issue_number,
                    "issueUrl": result.issue_url,
                    "projectItemId": result.project_item_id,
                    "errors": "; ".join(result.errors) if result.errors else ""
                }
                
                results.append(result_row)
                
                if result.success:
                    summary["success"] += 1
                else:
                    summary["failed"] += 1
                    summary["errors"].extend(result.errors)
                
            except Exception as e:
                logger.error(f"Row {idx} failed: {e}")
                summary["failed"] += 1
                summary["errors"].append(f"Row {idx}: {str(e)}")
                results.append({
                    "row": idx,
                    "title": str(row.get("issueTitle", "")),
                    "success": False,
                    "errors": str(e)
                })
        
        # Write results
        if output_path:
            results_df = pd.DataFrame(results)
            self.excel.write_excel({"Results": results_df}, output_path)
            logger.info(f"Results written to {output_path}")
        
        logger.info(f"Migration complete: {summary['success']} success, {summary['failed']} failed")
        return summary
    
    def migrate_relationships(
        self,
        input_path: Path,
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Migrate issue relationships from Excel file.
        
        Args:
            input_path: Input Excel file path with relationships
            output_path: Optional output Excel file path for results
        
        Returns:
            Summary dictionary
        """
        logger.info(f"Migrating relationships from {input_path}")
        
        df = self.excel.read_excel(input_path)
        sheet_name = list(df.keys())[0]
        df = df[sheet_name]
        
        results = []
        summary = {
            "total": len(df),
            "relationships_added": 0,
            "errors": []
        }
        
        for idx, row in df.iterrows():
            try:
                issue_id = str(row.get("issueTitle", "")).strip()
                if not issue_id:
                    continue
                
                parent_id = str(row.get("parentIssue", "")).strip() or None
                sub_issues = self.excel.parse_multi_value(row.get("subIssues"))
                blocked_by = self.excel.parse_multi_value(row.get("blockedBy"))
                blocking = self.excel.parse_multi_value(row.get("blocking"))
                
                result = self.relationship_manager.process_relationships(
                    issue_id=issue_id,
                    parent_issue_id=parent_id,
                    sub_issue_ids=sub_issues if sub_issues else None,
                    blocked_by_ids=blocked_by if blocked_by else None,
                    blocking_ids=blocking if blocking else None
                )
                
                results.append({
                    "row": idx,
                    "issueId": issue_id,
                    "relationships_added": result.relationships_added,
                    "errors": "; ".join(result.errors) if result.errors else ""
                })
                
                summary["relationships_added"] += result.relationships_added
                if result.errors:
                    summary["errors"].extend(result.errors)
                
            except Exception as e:
                logger.error(f"Row {idx} failed: {e}")
                summary["errors"].append(f"Row {idx}: {str(e)}")
        
        if output_path:
            results_df = pd.DataFrame(results)
            self.excel.write_excel({"Results": results_df}, output_path)
        
        logger.info(f"Relationships migration complete: {summary['relationships_added']} added")
        return summary
    
    def migrate_labels(
        self,
        labels: List[Label]
    ) -> Dict[str, Any]:
        """
        Migrate labels to target repository.
        
        Args:
            labels: List of Label objects
        
        Returns:
            Summary dictionary
        """
        logger.info(f"Migrating {len(labels)} labels")
        
        owner = self.config.project.target_owner
        repo = self.config.project.target_repo
        
        results = self.label_manager.upsert_labels(owner, repo, labels)
        
        summary = {
            "total": len(labels),
            "success": sum(1 for r in results.values() if r is not None),
            "failed": sum(1 for r in results.values() if r is None)
        }
        
        logger.info(f"Labels migration complete: {summary['success']} success, {summary['failed']} failed")
        return summary
    
    def close(self):
        """Close connections and cleanup."""
        self.client.close()

