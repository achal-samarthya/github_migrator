"""
Issue management - create, update, delete issues and manage project fields.

Author: Achal Samarthya

This module provides comprehensive issue management functionality for GitHub.
It handles:
- Creating new issues with titles and bodies
- Adding issues to GitHub projects
- Updating issue-level fields (milestones, issue types, assignees)
- Updating project-level fields (status, team, priority, dates, iterations)
- Adding comments to issues
- Adding labels to issues
- Deleting issues
- Creating complete issues with all fields, comments, and labels in one operation

The IssueManager class orchestrates multiple API calls to create fully
configured issues with all their metadata and relationships.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .github_client import GitHubClient
from .config import ProjectConfig, ProcessingConfig

logger = logging.getLogger(__name__)


@dataclass
class IssueResult:
    """Result of an issue operation."""
    success: bool
    issue_id: str = ""
    issue_number: int = 0
    issue_url: str = ""
    project_item_id: str = ""
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class IssueManager:
    """Manages GitHub issues and project items."""
    
    def __init__(
        self,
        client: GitHubClient,
        project_config: ProjectConfig,
        processing_config: ProcessingConfig
    ):
        self.client = client
        self.project_config = project_config
        self.processing = processing_config
    
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
        if self.processing.dry_run:
            logger.info(f"[DRY RUN] Would create issue: {title}")
            return IssueResult(success=True, issue_id="DRY_RUN_ID")
        
        query = """
        mutation ($repoId: ID!, $title: String!, $body: String!) {
          createIssue(input: { repositoryId: $repoId, title: $title, body: $body }) {
            issue {
              id
              number
              url
            }
          }
        }
        """
        
        try:
            data = self.client.graphql(query, {
                "repoId": repo_id,
                "title": title,
                "body": body or ""
            })
            
            issue = data["createIssue"]["issue"]
            return IssueResult(
                success=True,
                issue_id=issue["id"],
                issue_number=issue["number"],
                issue_url=issue["url"]
            )
        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            return IssueResult(success=False, errors=[str(e)])
    
    def add_to_project(
        self,
        project_id: str,
        issue_id: str
    ) -> Optional[str]:
        """
        Add an issue to a project.
        
        Args:
            project_id: Project node ID
            issue_id: Issue node ID
        
        Returns:
            Project item ID or None if failed
        """
        if self.processing.dry_run:
            logger.info(f"[DRY RUN] Would add issue {issue_id} to project {project_id}")
            return "DRY_RUN_ITEM_ID"
        
        query = """
        mutation ($projectId: ID!, $issueId: ID!) {
          addProjectV2ItemById(input: { projectId: $projectId, contentId: $issueId }) {
            item { id }
          }
        }
        """
        
        try:
            data = self.client.graphql(query, {
                "projectId": project_id,
                "issueId": issue_id
            })
            
            return data["addProjectV2ItemById"]["item"]["id"]
        except Exception as e:
            logger.error(f"Failed to add issue to project: {e}")
            return None
    
    def update_issue_fields(
        self,
        issue_id: str,
        milestone_id: Optional[str] = None,
        issue_type_id: Optional[str] = None,
        assignee_ids: Optional[List[str]] = None
    ) -> bool:
        """
        Update issue-level fields (milestone, issue type, assignees).
        
        Args:
            issue_id: Issue node ID
            milestone_id: Milestone node ID
            issue_type_id: Issue type ID
            assignee_ids: List of user node IDs
        
        Returns:
            True if successful
        """
        if self.processing.dry_run:
            logger.info(f"[DRY RUN] Would update issue {issue_id}")
            return True
        
        updates = {}
        if milestone_id:
            updates["milestoneId"] = milestone_id
        if issue_type_id:
            updates["issueTypeId"] = issue_type_id
        
        if updates:
            query = """
            mutation ($issueId: ID!, $input: UpdateIssueInput!) {
              updateIssue(input: $input) {
                issue { id number url }
              }
            }
            """
            
            try:
                input_data = {"id": issue_id, **updates}
                self.client.graphql(query, {
                    "issueId": issue_id,
                    "input": input_data
                })
            except Exception as e:
                logger.error(f"Failed to update issue: {e}")
                return False
        
        if assignee_ids:
            query = """
            mutation ($issueId: ID!, $assigneeIds: [ID!]!) {
              addAssigneesToAssignable(
                input: { assignableId: $issueId, assigneeIds: $assigneeIds }
              ) {
                assignable { ... on Issue { id number url } }
              }
            }
            """
            
            try:
                self.client.graphql(query, {
                    "issueId": issue_id,
                    "assigneeIds": assignee_ids
                })
            except Exception as e:
                logger.error(f"Failed to add assignees: {e}")
                return False
        
        return True
    
    def update_project_field(
        self,
        project_id: str,
        item_id: str,
        field_id: str,
        value: Any,
        field_type: str = "singleSelect"
    ) -> bool:
        """
        Update a project field value.
        
        Args:
            project_id: Project node ID
            item_id: Project item node ID
            field_id: Field node ID
            value: Field value (format depends on field_type)
            field_type: Type of field (date, iteration, singleSelect, etc.)
        
        Returns:
            True if successful
        """
        if self.processing.dry_run:
            logger.info(f"[DRY RUN] Would update project field {field_id}")
            return True
        
        # Build value input based on field type
        value_input = {}
        if field_type == "date":
            value_input = {"date": value}
        elif field_type == "iteration":
            value_input = {"iterationId": str(value)}
        elif field_type == "singleSelect":
            value_input = {"singleSelectOptionId": str(value)}
        else:
            logger.warning(f"Unknown field type: {field_type}")
            return False
        
        query = """
        mutation ($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
          updateProjectV2ItemFieldValue(
            input: { projectId: $projectId, itemId: $itemId, fieldId: $fieldId, value: $value }
          ) {
            projectV2Item { id }
          }
        }
        """
        
        try:
            self.client.graphql(query, {
                "projectId": project_id,
                "itemId": item_id,
                "fieldId": field_id,
                "value": value_input
            })
            return True
        except Exception as e:
            logger.error(f"Failed to update project field: {e}")
            return False
    
    def add_comment(
        self,
        issue_id: str,
        body: str
    ) -> bool:
        """
        Add a comment to an issue.
        
        Args:
            issue_id: Issue node ID
            body: Comment body
        
        Returns:
            True if successful
        """
        if self.processing.dry_run:
            logger.info(f"[DRY RUN] Would add comment to issue {issue_id}")
            return True
        
        query = """
        mutation ($issueId: ID!, $body: String!) {
          addComment(input: { subjectId: $issueId, body: $body }) {
            commentEdge {
              node {
                id
                url
                body
                createdAt
                author { login }
              }
            }
          }
        }
        """
        
        try:
            self.client.graphql(query, {
                "issueId": issue_id,
                "body": body
            })
            return True
        except Exception as e:
            logger.error(f"Failed to add comment: {e}")
            return False
    
    def add_labels(
        self,
        issue_id: str,
        label_ids: List[str]
    ) -> bool:
        """
        Add labels to an issue.
        
        Args:
            issue_id: Issue node ID
            label_ids: List of label node IDs
        
        Returns:
            True if successful
        """
        if self.processing.dry_run:
            logger.info(f"[DRY RUN] Would add labels to issue {issue_id}")
            return True
        
        query = """
        mutation ($issueId: ID!, $labelIds: [ID!]!) {
          addLabelsToLabelable(
            input: { labelableId: $issueId, labelIds: $labelIds }
          ) {
            labelable { ... on Issue { id number url } }
          }
        }
        """
        
        try:
            self.client.graphql(query, {
                "issueId": issue_id,
                "labelIds": label_ids
            })
            return True
        except Exception as e:
            logger.error(f"Failed to add labels: {e}")
            return False
    
    def delete_issue(
        self,
        issue_id: str
    ) -> bool:
        """
        Delete an issue.
        
        Args:
            issue_id: Issue node ID
        
        Returns:
            True if successful
        """
        if self.processing.dry_run:
            logger.info(f"[DRY RUN] Would delete issue {issue_id}")
            return True
        
        query = """
        mutation ($issueId: ID!) {
          deleteIssue(input: { issueId: $issueId }) {
            clientMutationId
          }
        }
        """
        
        try:
            self.client.graphql(query, {"issueId": issue_id})
            return True
        except Exception as e:
            logger.error(f"Failed to delete issue: {e}")
            return False
    
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
        """
        Create a complete issue with all fields, comments, and labels.
        
        Args:
            repo_id: Repository node ID
            project_id: Project node ID
            title: Issue title
            body: Issue body
            milestone_id: Milestone node ID
            issue_type_id: Issue type ID
            assignee_ids: List of assignee user IDs
            project_fields: Dict mapping field_id to {value, type}
            comments: List of comment bodies
            label_ids: List of label node IDs
        
        Returns:
            IssueResult with all details
        """
        result = IssueResult(success=False)
        
        # Step 1: Create issue
        create_result = self.create_issue(repo_id, title, body)
        if not create_result.success:
            result.errors.extend(create_result.errors)
            return result
        
        result.issue_id = create_result.issue_id
        result.issue_number = create_result.issue_number
        result.issue_url = create_result.issue_url
        
        # Step 2: Add to project
        item_id = self.add_to_project(project_id, result.issue_id)
        if not item_id:
            result.errors.append("Failed to add issue to project")
            if not self.processing.continue_on_error:
                return result
        else:
            result.project_item_id = item_id
        
        # Step 3: Update issue fields
        if milestone_id or issue_type_id or assignee_ids:
            if not self.update_issue_fields(
                result.issue_id,
                milestone_id,
                issue_type_id,
                assignee_ids
            ):
                result.errors.append("Failed to update issue fields")
        
        # Step 4: Update project fields
        if project_fields and result.project_item_id:
            for field_id, field_data in project_fields.items():
                if not self.update_project_field(
                    project_id,
                    result.project_item_id,
                    field_id,
                    field_data["value"],
                    field_data.get("type", "singleSelect")
                ):
                    result.errors.append(f"Failed to update project field {field_id}")
        
        # Step 5: Add labels
        if label_ids:
            if not self.add_labels(result.issue_id, label_ids):
                result.errors.append("Failed to add labels")
        
        # Step 6: Add comments
        if comments:
            for comment in comments:
                if not self.add_comment(result.issue_id, comment):
                    result.errors.append(f"Failed to add comment")
        
        result.success = len(result.errors) == 0 or self.processing.continue_on_error
        return result

