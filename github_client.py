"""
GitHub API Client - Handles GraphQL and REST API interactions.

Author: Achal Samarthya

This module provides a unified client for interacting with GitHub's GraphQL
and REST APIs. It handles:
- GraphQL query and mutation execution
- REST API GET, POST, PATCH, and DELETE requests
- Automatic retry logic with exponential backoff
- Pagination support for GraphQL queries
- Request timeout and error handling
- Session management with connection pooling

The GitHubClient class abstracts away the complexity of API interactions,
providing a clean interface for other modules to interact with GitHub.
"""

import json
import time
import random
import logging
from typing import Dict, Any, Optional, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import GitHubConfig

logger = logging.getLogger(__name__)


class GitHubClient:
    """Unified client for GitHub GraphQL and REST APIs."""
    
    def __init__(self, config: GitHubConfig):
        self.config = config
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.config.max_retries,
            connect=self.config.max_retries,
            read=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["GET", "POST", "PATCH", "DELETE"]),
            raise_on_status=False,
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        session.headers.update({
            "Authorization": f"Bearer {self.config.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": self.config.api_version,
        })
        
        return session
    
    def graphql(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        features: Optional[List[str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query/mutation.
        
        Args:
            query: GraphQL query/mutation string
            variables: Variables for the query
            features: Optional GraphQL features (e.g., ["sub_issues"])
            timeout: Request timeout in seconds
        
        Returns:
            Response data dictionary
        
        Raises:
            RuntimeError: If the request fails or contains errors
        """
        headers = dict(self.session.headers)
        if features:
            headers["GraphQL-Features"] = ", ".join(features)
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        timeout = timeout or self.config.timeout
        
        try:
            response = self.session.post(
                self.config.api_url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "errors" in data:
                error_messages = [e.get("message", str(e)) for e in data["errors"]]
                raise RuntimeError(f"GraphQL errors: {'; '.join(error_messages)}")
            
            if "data" not in data:
                raise RuntimeError(f"No data in response: {data.get('message', 'Unknown error')}")
            
            return data["data"]
        
        except requests.exceptions.RequestException as e:
            logger.error(f"GraphQL request failed: {e}")
            raise RuntimeError(f"GraphQL request failed: {e}")
    
    def rest_get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> requests.Response:
        """
        Execute a REST GET request.
        
        Args:
            endpoint: API endpoint (e.g., "/repos/owner/repo/issues")
            params: Query parameters
            timeout: Request timeout in seconds
        
        Returns:
            Response object
        """
        url = f"{self.config.rest_url}{endpoint}"
        timeout = timeout or self.config.timeout
        
        response = self.session.get(url, params=params or {}, timeout=timeout)
        response.raise_for_status()
        return response
    
    def rest_post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> requests.Response:
        """
        Execute a REST POST request.
        
        Args:
            endpoint: API endpoint
            data: Form data
            json_data: JSON body
            timeout: Request timeout in seconds
        
        Returns:
            Response object
        """
        url = f"{self.config.rest_url}{endpoint}"
        timeout = timeout or self.config.timeout
        
        if json_data:
            response = self.session.post(url, json=json_data, timeout=timeout)
        else:
            response = self.session.post(url, data=data or {}, timeout=timeout)
        
        response.raise_for_status()
        return response
    
    def rest_patch(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> requests.Response:
        """
        Execute a REST PATCH request.
        
        Args:
            endpoint: API endpoint
            json_data: JSON body
            timeout: Request timeout in seconds
        
        Returns:
            Response object
        """
        url = f"{self.config.rest_url}{endpoint}"
        timeout = timeout or self.config.timeout
        
        response = self.session.patch(url, json=json_data or {}, timeout=timeout)
        response.raise_for_status()
        return response
    
    def rest_delete(
        self,
        endpoint: str,
        timeout: Optional[float] = None
    ) -> requests.Response:
        """
        Execute a REST DELETE request.
        
        Args:
            endpoint: API endpoint
            timeout: Request timeout in seconds
        
        Returns:
            Response object
        """
        url = f"{self.config.rest_url}{endpoint}"
        timeout = timeout or self.config.timeout
        
        response = self.session.delete(url, timeout=timeout)
        response.raise_for_status()
        return response
    
    def paginate_graphql(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        page_info_path: List[str] = None,
        nodes_path: List[str] = None,
        max_pages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Paginate through GraphQL results.
        
        Args:
            query: GraphQL query with pagination support
            variables: Initial variables
            page_info_path: Path to pageInfo in response (e.g., ["node", "items", "pageInfo"])
            nodes_path: Path to nodes in response (e.g., ["node", "items", "nodes"])
            max_pages: Maximum number of pages to fetch
        
        Returns:
            List of all nodes from all pages
        """
        if page_info_path is None:
            page_info_path = ["pageInfo"]
        if nodes_path is None:
            nodes_path = ["nodes"]
        
        all_nodes = []
        after = None
        page_count = 0
        variables = variables or {}
        
        while True:
            if max_pages and page_count >= max_pages:
                break
            
            variables["after"] = after
            data = self.graphql(query, variables)
            
            # Navigate to nodes
            nodes = data
            for key in nodes_path:
                nodes = nodes[key]
            
            all_nodes.extend(nodes)
            
            # Navigate to pageInfo
            page_info = data
            for key in page_info_path:
                page_info = page_info[key]
            
            if not page_info.get("hasNextPage"):
                break
            
            after = page_info.get("endCursor")
            page_count += 1
        
        return all_nodes
    
    def close(self):
        """Close the session."""
        self.session.close()

