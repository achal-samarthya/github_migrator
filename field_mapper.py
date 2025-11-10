"""
Field mapping utilities - converts human-readable values to GitHub IDs.

Author: Achal Samarthya

This module provides field mapping functionality to convert human-readable
values (like status names, team names, user names) into GitHub's internal
IDs required for API operations. It handles:
- Mapping iterations and quarters by number or name
- Mapping status, team, priority, readiness, and effort options
- Mapping milestones, labels, users, and issue types
- Formatting dates to YYYY-MM-DD format
- Normalizing values for case-insensitive matching
- Handling multi-value fields with separators

The FieldMapper class uses configuration mappings to translate text values
into the corresponding GitHub node IDs needed for GraphQL mutations.
"""

import re
import logging
from typing import Dict, Any, Optional, List
import pandas as pd

from .config import FieldMappingConfig

logger = logging.getLogger(__name__)


class FieldMapper:
    """Maps text values to GitHub IDs based on configuration."""
    
    def __init__(self, config: FieldMappingConfig):
        self.config = config
        self._normalized_mappings = self._build_normalized_mappings()
    
    def _build_normalized_mappings(self) -> Dict[str, Dict[str, str]]:
        """Build normalized mappings for case-insensitive matching."""
        return {
            "status": {self._normalize_key(k): v for k, v in self.config.status_mapping.items()},
            "team": {self._normalize_key(k): v for k, v in self.config.team_mapping.items()},
            "priority": {self._normalize_key(k): v for k, v in self.config.priority_mapping.items()},
            "readiness": {self._normalize_key(k): v for k, v in self.config.readiness_mapping.items()},
            "effort": {self._normalize_key(k): v for k, v in self.config.effort_mapping.items()},
            "milestone": {self._normalize_key(k): v for k, v in self.config.milestone_mapping.items()},
            "label": {self._normalize_key(k): v for k, v in self.config.label_mapping.items()},
            "user": {self._normalize_key(k): v for k, v in self.config.user_mapping.items()},
            "issue_type": {self._normalize_key(k): v for k, v in self.config.issue_type_mapping.items()},
        }
    
    def _normalize_key(self, key: str) -> str:
        """Normalize a key for matching."""
        key = str(key).strip().lower()
        key = key.replace("–", "-").replace("—", "-")
        key = re.sub(r"\s+", " ", key)
        return key
    
    def _normalize_value(self, value: Any) -> str:
        """Normalize a value for matching."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""
        return str(value).strip()
    
    def map_iteration(self, value: Any) -> str:
        """Map iteration number or name to iteration ID."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""
        
        # Try to extract number
        if isinstance(value, (int, float)):
            num = int(value)
            return self.config.iteration_mapping.get(num, "")
        
        # Try to parse from string
        s = str(value).strip()
        match = re.match(r"(?i)^\s*iteration\s*(\d+)\s*$", s)
        if match:
            num = int(match.group(1))
            return self.config.iteration_mapping.get(num, "")
        
        match = re.match(r"^\s*(\d+)\s*$", s)
        if match:
            num = int(match.group(1))
            return self.config.iteration_mapping.get(num, "")
        
        return ""
    
    def map_quarter(self, value: Any) -> str:
        """Map quarter number or name to quarter iteration ID."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""
        
        # Try to extract number
        if isinstance(value, (int, float)):
            num = int(value)
            return self.config.quarter_mapping.get(num, "")
        
        # Try to parse from string
        s = str(value).strip()
        match = re.match(r"(?i)^\s*quarter\s*(\d+)\s*$", s)
        if match:
            num = int(match.group(1))
            return self.config.quarter_mapping.get(num, "")
        
        match = re.match(r"^\s*(\d+)\s*$", s)
        if match:
            num = int(match.group(1))
            return self.config.quarter_mapping.get(num, "")
        
        return ""
    
    def map_status(self, value: Any) -> str:
        """Map status text to status option ID."""
        if self._is_hex8_id(value):
            return str(value).strip()
        
        normalized = self._normalize_key(value)
        return self._normalized_mappings["status"].get(normalized, "")
    
    def map_team(self, value: Any) -> str:
        """Map team text to team option ID."""
        if self._is_hex8_id(value):
            return str(value).strip()
        
        normalized = self._normalize_key(value)
        return self._normalized_mappings["team"].get(normalized, "")
    
    def map_priority(self, value: Any) -> str:
        """Map priority text to priority option ID."""
        if self._is_hex8_id(value):
            return str(value).strip()
        
        normalized = self._normalize_key(value)
        return self._normalized_mappings["priority"].get(normalized, "")
    
    def map_readiness(self, value: Any) -> str:
        """Map readiness text to readiness option ID."""
        if self._is_hex8_id(value):
            return str(value).strip()
        
        normalized = self._normalize_key(value)
        return self._normalized_mappings["readiness"].get(normalized, "")
    
    def map_effort(self, value: Any) -> str:
        """Map effort text to effort option ID."""
        if self._is_hex8_id(value):
            return str(value).strip()
        
        normalized = self._normalize_key(value)
        return self._normalized_mappings["effort"].get(normalized, "")
    
    def map_milestone(self, value: Any) -> str:
        """Map milestone text to milestone ID."""
        if self._is_milestone_id(value):
            return str(value).strip()
        
        normalized = self._normalize_key(value)
        return self._normalized_mappings["milestone"].get(normalized, "")
    
    def map_labels(self, value: Any, separator: str = "||") -> str:
        """Map label names to label IDs."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""
        
        labels = [l.strip() for l in str(value).split(separator) if l.strip()]
        mapped = []
        
        for label in labels:
            normalized = self._normalize_key(label)
            label_id = self._normalized_mappings["label"].get(normalized, label)
            mapped.append(label_id)
        
        return separator.join(mapped) if mapped else ""
    
    def map_users(self, value: Any, separator: str = "||") -> str:
        """Map user names/handles to user IDs."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""
        
        users = [u.strip() for u in str(value).split(separator) if u.strip()]
        mapped = []
        
        for user in users:
            # If already a user ID, keep it
            if self._is_user_id(user):
                mapped.append(user)
                continue
            
            # Try to map
            cleaned = self._clean_user_token(user)
            if not cleaned:
                continue
            
            normalized = self._normalize_key(cleaned)
            user_id = (
                self._normalized_mappings["user"].get(normalized) or
                self._normalized_mappings["user"].get(normalized.replace(" ", "")) or
                self._normalized_mappings["user"].get("@" + normalized)
            )
            
            if user_id:
                mapped.append(user_id)
        
        return separator.join(mapped) if mapped else ""
    
    def map_issue_type(self, value: Any, labels: Optional[str] = None) -> str:
        """Map issue type text or derive from labels."""
        # If labels provided and contain "bug", use bug type
        if labels:
            label_list = [l.lower() for l in str(labels).split("||") if l.strip()]
            if "bug" in label_list:
                bug_id = self._normalized_mappings["issue_type"].get("bug", "")
                if bug_id:
                    return bug_id
        
        # Try to map the value directly
        if value:
            normalized = self._normalize_key(value)
            return self._normalized_mappings["issue_type"].get(normalized, "")
        
        # Default type
        return self._normalized_mappings["issue_type"].get("default", "")
    
    def _is_hex8_id(self, value: Any) -> bool:
        """Check if value is an 8-character hex ID."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return False
        s = str(value).strip()
        return bool(re.fullmatch(r"[0-9a-fA-F]{8}", s))
    
    def _is_milestone_id(self, value: Any) -> bool:
        """Check if value is a milestone ID."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return False
        return str(value).strip().upper().startswith("MI_")
    
    def _is_user_id(self, value: Any) -> bool:
        """Check if value is a user ID."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return False
        return str(value).strip().startswith("U_")
    
    def _clean_user_token(self, token: str) -> str:
        """Clean a user token (name, handle, URL, etc.) for matching."""
        s = str(token).strip()
        
        # Extract from GitHub URL
        match = re.search(r"github\.com/([^/\s]+)", s, flags=re.I)
        if match:
            s = match.group(1)
        
        # Remove parentheses content
        s = re.sub(r"\(.*?\)", "", s)
        
        # Remove @ prefix
        s = s.lstrip("@")
        
        # Remove common separators
        s = s.strip(" ,;:|/-")
        
        # Normalize whitespace
        s = re.sub(r"\s+", " ", s).strip().lower()
        
        return s
    
    def format_date(self, value: Any) -> Optional[str]:
        """Format date value to YYYY-MM-DD format."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        
        try:
            dt = pd.to_datetime(value)
            return dt.date().isoformat()
        except Exception:
            s = str(value).strip()
            return s if s else None

