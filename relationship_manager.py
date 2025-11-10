"""
Relationship management - handle parent/sub-issues and dependencies.

Author: Achal Samarthya

This module manages issue relationships in GitHub, including:
- Parent/sub-issue relationships (hierarchical issue structures)
- Dependency relationships (blocked-by and blocking)
- Tracking processed relationships to avoid duplicates
- Getting issue context (owner, repo, number) from node IDs

The RelationshipManager class handles the complex task of establishing
relationships between issues after they have been migrated, ensuring that
the hierarchical structure and dependencies are preserved in the target
repository.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass

from .github_client import GitHubClient
from .config import ProcessingConfig

logger = logging.getLogger(__name__)


@dataclass
class RelationshipResult:
    """Result of a relationship operation."""
    success: bool
    relationships_added: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class RelationshipManager:
    """Manages issue relationships (parent/sub-issues, dependencies)."""
    
    def __init__(
        self,
        client: GitHubClient,
        processing_config: ProcessingConfig
    ):
        self.client = client
        self.processing = processing_config
        self._processed_edges: Set[Tuple[str, str]] = set()
    
    def get_issue_context(self, issue_node_id: str) -> Tuple[str, str, int, int]:
        """
        Get issue context (owner, repo, number, databaseId) from node ID.
        
        Args:
            issue_node_id: Issue node ID
        
        Returns:
            Tuple of (owner, repo, number, databaseId)
        """
        query = """
        query($id: ID!) {
          node(id: $id) {
            ... on Issue {
              number
              databaseId
              repository {
                name
                owner { login }
              }
            }
          }
        }
        """
        
        data = self.client.graphql(query, {"id": issue_node_id})
        node = data["node"]
        
        if not node:
            raise RuntimeError(f"Issue not found: {issue_node_id}")
        
        owner = node["repository"]["owner"]["login"]
        repo = node["repository"]["name"]
        number = int(node["number"])
        database_id = int(node["databaseId"])
        
        return owner, repo, number, database_id
    
    def add_sub_issue(
        self,
        parent_issue_id: str,
        child_issue_id: str
    ) -> bool:
        """
        Add a sub-issue relationship (child is a sub-issue of parent).
        
        Args:
            parent_issue_id: Parent issue node ID
            child_issue_id: Child issue node ID
        
        Returns:
            True if successful
        """
        edge_key = (parent_issue_id, child_issue_id)
        if edge_key in self._processed_edges:
            logger.debug(f"Sub-issue relationship already processed: {parent_issue_id} -> {child_issue_id}")
            return True
        
        if self.processing.dry_run:
            logger.info(f"[DRY RUN] Would add sub-issue: {parent_issue_id} -> {child_issue_id}")
            self._processed_edges.add(edge_key)
            return True
        
        query = """
        mutation($parent: ID!, $child: ID!) {
          addSubIssue(input: { issueId: $parent, subIssueId: $child }) {
            issue { id }
            subIssue { id }
          }
        }
        """
        
        try:
            self.client.graphql(
                query,
                {"parent": parent_issue_id, "child": child_issue_id},
                features=["sub_issues"]
            )
            self._processed_edges.add(edge_key)
            return True
        except Exception as e:
            logger.error(f"Failed to add sub-issue: {e}")
            return False
    
    def add_blocked_by(
        self,
        blocked_issue_id: str,
        blocker_issue_id: str
    ) -> bool:
        """
        Add a 'blocked by' dependency (blocked_issue is blocked by blocker_issue).
        
        Args:
            blocked_issue_id: Issue node ID that is blocked
            blocker_issue_id: Issue node ID that blocks
        
        Returns:
            True if successful
        """
        edge_key = (blocked_issue_id, blocker_issue_id)
        if edge_key in self._processed_edges:
            logger.debug(f"Blocked-by relationship already processed: {blocked_issue_id} <- {blocker_issue_id}")
            return True
        
        if self.processing.dry_run:
            logger.info(f"[DRY RUN] Would add blocked-by: {blocked_issue_id} <- {blocker_issue_id}")
            self._processed_edges.add(edge_key)
            return True
        
        try:
            # Get context for blocked issue
            blocked_owner, blocked_repo, blocked_number, _ = self.get_issue_context(blocked_issue_id)
            
            # Get database ID for blocker issue
            _, _, _, blocker_dbid = self.get_issue_context(blocker_issue_id)
            
            # Use REST API
            endpoint = f"/repos/{blocked_owner}/{blocked_repo}/issues/{blocked_number}/dependencies/blocked_by"
            self.client.rest_post(endpoint, json_data={"issue_id": blocker_dbid})
            
            self._processed_edges.add(edge_key)
            return True
        except Exception as e:
            logger.error(f"Failed to add blocked-by: {e}")
            return False
    
    def add_blocking(
        self,
        blocking_issue_id: str,
        blocked_issue_id: str
    ) -> bool:
        """
        Add a 'blocking' dependency (blocking_issue blocks blocked_issue).
        This is implemented by adding blocked_issue as 'blocked by' blocking_issue.
        
        Args:
            blocking_issue_id: Issue node ID that blocks
            blocked_issue_id: Issue node ID that is blocked
        
        Returns:
            True if successful
        """
        return self.add_blocked_by(blocked_issue_id, blocking_issue_id)
    
    def process_relationships(
        self,
        issue_id: str,
        parent_issue_id: Optional[str] = None,
        sub_issue_ids: Optional[List[str]] = None,
        blocked_by_ids: Optional[List[str]] = None,
        blocking_ids: Optional[List[str]] = None
    ) -> RelationshipResult:
        """
        Process all relationships for an issue.
        
        Args:
            issue_id: Current issue node ID
            parent_issue_id: Parent issue node ID
            sub_issue_ids: List of sub-issue node IDs
            blocked_by_ids: List of issue IDs that block this issue
            blocking_ids: List of issue IDs blocked by this issue
        
        Returns:
            RelationshipResult with summary
        """
        result = RelationshipResult(success=True)
        
        # Parent relationship (this issue is a child of parent)
        if parent_issue_id:
            if self.add_sub_issue(parent_issue_id, issue_id):
                result.relationships_added += 1
            else:
                result.errors.append(f"Failed to add parent relationship: {parent_issue_id}")
                result.success = False
        
        # Sub-issue relationships (these issues are children of this issue)
        if sub_issue_ids:
            for child_id in sub_issue_ids:
                if child_id and child_id.strip():
                    if self.add_sub_issue(issue_id, child_id.strip()):
                        result.relationships_added += 1
                    else:
                        result.errors.append(f"Failed to add sub-issue: {child_id}")
                        if not self.processing.continue_on_error:
                            result.success = False
        
        # Blocked-by relationships
        if blocked_by_ids:
            for blocker_id in blocked_by_ids:
                if blocker_id and blocker_id.strip():
                    if self.add_blocked_by(issue_id, blocker_id.strip()):
                        result.relationships_added += 1
                    else:
                        result.errors.append(f"Failed to add blocked-by: {blocker_id}")
                        if not self.processing.continue_on_error:
                            result.success = False
        
        # Blocking relationships
        if blocking_ids:
            for blocked_id in blocking_ids:
                if blocked_id and blocked_id.strip():
                    if self.add_blocking(issue_id, blocked_id.strip()):
                        result.relationships_added += 1
                    else:
                        result.errors.append(f"Failed to add blocking: {blocked_id}")
                        if not self.processing.continue_on_error:
                            result.success = False
        
        return result

