"""
Label management - create and update repository labels.

Author: Achal Samarthya

This module handles label management for GitHub repositories. It provides:
- Fetching existing labels from repositories
- Creating new labels with colors and descriptions
- Updating existing labels
- Getting label node IDs for use in API operations
- Caching label data to avoid redundant API calls

The LabelManager class ensures that labels are properly migrated from
source repositories to target repositories, creating them if they don't exist
or updating them if they do.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from .github_client import GitHubClient
from .config import ProcessingConfig

logger = logging.getLogger(__name__)


@dataclass
class Label:
    """Label definition."""
    name: str
    color: str
    description: str = ""


class LabelManager:
    """Manages repository labels."""
    
    def __init__(
        self,
        client: GitHubClient,
        processing_config: ProcessingConfig
    ):
        self.client = client
        self.processing = processing_config
        self._label_cache: Dict[str, Dict] = {}
    
    def get_existing_labels(
        self,
        owner: str,
        repo: str
    ) -> Dict[str, Dict]:
        """
        Get all existing labels for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
        
        Returns:
            Dictionary mapping label name (lowercase) to label data
        """
        cache_key = f"{owner}/{repo}"
        if cache_key in self._label_cache:
            return self._label_cache[cache_key]
        
        labels = {}
        page = 1
        per_page = 100
        
        while True:
            try:
                endpoint = f"/repos/{owner}/{repo}/labels"
                response = self.client.rest_get(
                    endpoint,
                    params={"per_page": per_page, "page": page}
                )
                
                page_labels = response.json()
                if not page_labels:
                    break
                
                for label in page_labels:
                    labels[label["name"].lower()] = label
                
                if len(page_labels) < per_page:
                    break
                
                page += 1
            except Exception as e:
                logger.error(f"Failed to fetch labels: {e}")
                break
        
        self._label_cache[cache_key] = labels
        return labels
    
    def upsert_label(
        self,
        owner: str,
        repo: str,
        label: Label
    ) -> Optional[Dict]:
        """
        Create or update a label.
        
        Args:
            owner: Repository owner
            repo: Repository name
            label: Label definition
        
        Returns:
            Label data or None if failed
        """
        if self.processing.dry_run:
            logger.info(f"[DRY RUN] Would upsert label: {label.name}")
            return {"name": label.name, "color": label.color, "description": label.description}
        
        existing = self.get_existing_labels(owner, repo)
        label_key = label.name.lower()
        
        # Normalize color (remove # if present)
        color = label.color.lstrip("#").lower()
        
        try:
            if label_key in existing:
                # Update existing label
                existing_label = existing[label_key]
                endpoint = f"/repos/{owner}/{repo}/labels/{existing_label['name']}"
                response = self.client.rest_patch(
                    endpoint,
                    json_data={
                        "new_name": label.name,
                        "color": color,
                        "description": label.description
                    }
                )
                result = response.json()
                logger.info(f"Updated label: {label.name}")
            else:
                # Create new label
                endpoint = f"/repos/{owner}/{repo}/labels"
                response = self.client.rest_post(
                    endpoint,
                    json_data={
                        "name": label.name,
                        "color": color,
                        "description": label.description
                    }
                )
                result = response.json()
                logger.info(f"Created label: {label.name}")
            
            return result
        except Exception as e:
            logger.error(f"Failed to upsert label {label.name}: {e}")
            return None
    
    def upsert_labels(
        self,
        owner: str,
        repo: str,
        labels: List[Label]
    ) -> Dict[str, Optional[Dict]]:
        """
        Create or update multiple labels.
        
        Args:
            owner: Repository owner
            repo: Repository name
            labels: List of label definitions
        
        Returns:
            Dictionary mapping label name to result (or None if failed)
        """
        results = {}
        
        for label in labels:
            result = self.upsert_label(owner, repo, label)
            results[label.name] = result
        
        return results
    
    def get_label_node_id(
        self,
        owner: str,
        repo: str,
        label_name: str
    ) -> Optional[str]:
        """
        Get the node ID for a label by name.
        
        Args:
            owner: Repository owner
            repo: Repository name
            label_name: Label name
        
        Returns:
            Label node ID or None if not found
        """
        existing = self.get_existing_labels(owner, repo)
        label_key = label_name.lower()
        
        if label_key in existing:
            return existing[label_key].get("node_id")
        
        return None

