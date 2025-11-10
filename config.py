"""
Configuration management for GitHub Migrator.
Supports JSON config files, environment variables, and command-line overrides.

Author: Achal Samarthya

This module handles all configuration management for the GitHub Migrator tool.
It provides data classes for organizing configuration settings including:
- GitHub API configuration (tokens, URLs, timeouts, retries)
- Project configuration (source and target repository/project IDs)
- Field mapping configuration (mappings for iterations, quarters, status, teams, etc.)
- Processing configuration (batch sizes, dry-run mode, error handling)

The module supports loading configuration from JSON files and provides methods
to save configuration back to files.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class GitHubConfig:
    """GitHub API configuration."""
    token: str = ""
    api_url: str = "https://api.github.com/graphql"
    rest_url: str = "https://api.github.com"
    api_version: str = "2022-11-28"
    timeout: int = 60
    max_retries: int = 5
    retry_delay: float = 1.0


@dataclass
class ProjectConfig:
    """Source and target project configuration."""
    source_repo_id: str = ""
    source_project_id: str = ""
    target_repo_id: str = ""
    target_project_id: str = ""
    target_owner: str = ""
    target_repo: str = ""


@dataclass
class FieldMappingConfig:
    """Field mapping configuration."""
    iteration_mapping: Dict[int, str] = field(default_factory=dict)
    quarter_mapping: Dict[int, str] = field(default_factory=dict)
    status_mapping: Dict[str, str] = field(default_factory=dict)
    team_mapping: Dict[str, str] = field(default_factory=dict)
    priority_mapping: Dict[str, str] = field(default_factory=dict)
    readiness_mapping: Dict[str, str] = field(default_factory=dict)
    effort_mapping: Dict[str, str] = field(default_factory=dict)
    milestone_mapping: Dict[str, str] = field(default_factory=dict)
    label_mapping: Dict[str, str] = field(default_factory=dict)
    user_mapping: Dict[str, str] = field(default_factory=dict)
    issue_type_mapping: Dict[str, str] = field(default_factory=dict)


@dataclass
class ProcessingConfig:
    """Processing options and settings."""
    batch_size: int = 100
    sleep_between_requests: float = 0.0
    dry_run: bool = False
    continue_on_error: bool = True
    multi_value_separator: str = "||"
    output_directory: str = "output"
    log_level: str = "INFO"


@dataclass
class Config:
    """Main configuration container."""
    github: GitHubConfig = field(default_factory=GitHubConfig)
    project: ProjectConfig = field(default_factory=ProjectConfig)
    field_mapping: FieldMappingConfig = field(default_factory=FieldMappingConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)

    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """Load configuration from JSON file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        config = cls()
        
        # Load GitHub config
        if "github" in data:
            github_data = data["github"]
            config.github = GitHubConfig(
                token=os.getenv("GITHUB_TOKEN", github_data.get("token", "")),
                api_url=github_data.get("api_url", config.github.api_url),
                rest_url=github_data.get("rest_url", config.github.rest_url),
                api_version=github_data.get("api_version", config.github.api_version),
                timeout=github_data.get("timeout", config.github.timeout),
                max_retries=github_data.get("max_retries", config.github.max_retries),
                retry_delay=github_data.get("retry_delay", config.github.retry_delay),
            )
        
        # Load project config
        if "project" in data:
            proj_data = data["project"]
            config.project = ProjectConfig(
                source_repo_id=proj_data.get("source_repo_id", ""),
                source_project_id=proj_data.get("source_project_id", ""),
                target_repo_id=proj_data.get("target_repo_id", ""),
                target_project_id=proj_data.get("target_project_id", ""),
                target_owner=proj_data.get("target_owner", ""),
                target_repo=proj_data.get("target_repo", ""),
            )
        
        # Load field mapping config
        if "field_mapping" in data:
            fm_data = data["field_mapping"]
            config.field_mapping = FieldMappingConfig(
                iteration_mapping=fm_data.get("iteration_mapping", {}),
                quarter_mapping=fm_data.get("quarter_mapping", {}),
                status_mapping=fm_data.get("status_mapping", {}),
                team_mapping=fm_data.get("team_mapping", {}),
                priority_mapping=fm_data.get("priority_mapping", {}),
                readiness_mapping=fm_data.get("readiness_mapping", {}),
                effort_mapping=fm_data.get("effort_mapping", {}),
                milestone_mapping=fm_data.get("milestone_mapping", {}),
                label_mapping=fm_data.get("label_mapping", {}),
                user_mapping=fm_data.get("user_mapping", {}),
                issue_type_mapping=fm_data.get("issue_type_mapping", {}),
            )
        
        # Load processing config
        if "processing" in data:
            proc_data = data["processing"]
            config.processing = ProcessingConfig(
                batch_size=proc_data.get("batch_size", 100),
                sleep_between_requests=proc_data.get("sleep_between_requests", 0.0),
                dry_run=proc_data.get("dry_run", False),
                continue_on_error=proc_data.get("continue_on_error", True),
                multi_value_separator=proc_data.get("multi_value_separator", "||"),
                output_directory=proc_data.get("output_directory", "output"),
                log_level=proc_data.get("log_level", "INFO"),
            )
        
        return config

    def to_file(self, config_path: Path):
        """Save configuration to JSON file."""
        data = {
            "github": {
                "api_url": self.github.api_url,
                "rest_url": self.github.rest_url,
                "api_version": self.github.api_version,
                "timeout": self.github.timeout,
                "max_retries": self.github.max_retries,
                "retry_delay": self.github.retry_delay,
            },
            "project": {
                "source_repo_id": self.project.source_repo_id,
                "source_project_id": self.project.source_project_id,
                "target_repo_id": self.project.target_repo_id,
                "target_project_id": self.project.target_project_id,
                "target_owner": self.project.target_owner,
                "target_repo": self.project.target_repo,
            },
            "field_mapping": {
                "iteration_mapping": self.field_mapping.iteration_mapping,
                "quarter_mapping": self.field_mapping.quarter_mapping,
                "status_mapping": self.field_mapping.status_mapping,
                "team_mapping": self.field_mapping.team_mapping,
                "priority_mapping": self.field_mapping.priority_mapping,
                "readiness_mapping": self.field_mapping.readiness_mapping,
                "effort_mapping": self.field_mapping.effort_mapping,
                "milestone_mapping": self.field_mapping.milestone_mapping,
                "label_mapping": self.field_mapping.label_mapping,
                "user_mapping": self.field_mapping.user_mapping,
                "issue_type_mapping": self.field_mapping.issue_type_mapping,
            },
            "processing": {
                "batch_size": self.processing.batch_size,
                "sleep_between_requests": self.processing.sleep_between_requests,
                "dry_run": self.processing.dry_run,
                "continue_on_error": self.processing.continue_on_error,
                "multi_value_separator": self.processing.multi_value_separator,
                "output_directory": self.processing.output_directory,
                "log_level": self.processing.log_level,
            },
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

