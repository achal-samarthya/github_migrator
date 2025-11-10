"""
Command-line interface for GitHub Migrator.

Author: Achal Samarthya

This module provides a command-line interface (CLI) for the GitHub Migrator tool.
It allows users to execute migration operations from the command line, including:
- Extracting issues from source projects
- Mapping field values to GitHub IDs
- Migrating issues to target repositories
- Migrating issue relationships (parent/sub-issues, dependencies)
- Migrating labels
- Running full migration workflows

The CLI supports various commands and options for flexible migration workflows.
"""

import argparse
import logging
import sys
from pathlib import Path
import getpass
import json

from .config import Config
from .migrator import GitHubMigrator
from .label_manager import Label

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_logging(level: str):
    """Configure logging level."""
    logging.getLogger().setLevel(getattr(logging, level.upper()))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="GitHub Project Migrator - Migrate GitHub projects between accounts"
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.json"),
        help="Path to configuration file (default: config.json)"
    )
    
    parser.add_argument(
        "--token",
        type=str,
        help="GitHub personal access token (or set GITHUB_TOKEN env var)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract issues from a project")
    extract_parser.add_argument("--project-id", required=True, help="Source project node ID")
    extract_parser.add_argument("--output", type=Path, required=True, help="Output Excel file path")
    extract_parser.add_argument("--limit", type=int, help="Maximum number of issues to extract")
    
    # Map command
    map_parser = subparsers.add_parser("map", help="Map field values to GitHub IDs")
    map_parser.add_argument("--input", type=Path, required=True, help="Input Excel file path")
    map_parser.add_argument("--output", type=Path, required=True, help="Output Excel file path")
    
    # Migrate issues command
    migrate_parser = subparsers.add_parser("migrate", help="Migrate issues to GitHub")
    migrate_parser.add_argument("--input", type=Path, required=True, help="Input Excel file path")
    migrate_parser.add_argument("--output", type=Path, help="Output results Excel file path")
    
    # Migrate relationships command
    rel_parser = subparsers.add_parser("relationships", help="Migrate issue relationships")
    rel_parser.add_argument("--input", type=Path, required=True, help="Input Excel file path")
    rel_parser.add_argument("--output", type=Path, help="Output results Excel file path")
    
    # Migrate labels command
    labels_parser = subparsers.add_parser("labels", help="Migrate labels to repository")
    labels_parser.add_argument("--input", type=Path, required=True, help="Input JSON file with labels")
    labels_parser.add_argument("--output", type=Path, help="Output results JSON file path")
    
    # Full migration command
    full_parser = subparsers.add_parser("full", help="Run full migration workflow")
    full_parser.add_argument("--extract-input", type=Path, help="Input file for extraction (if needed)")
    full_parser.add_argument("--migrate-input", type=Path, required=True, help="Input Excel file for migration")
    full_parser.add_argument("--relationships-input", type=Path, help="Input Excel file for relationships")
    full_parser.add_argument("--labels-input", type=Path, help="Input JSON file for labels")
    full_parser.add_argument("--output-dir", type=Path, help="Output directory for all results")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    setup_logging(args.log_level)
    
    # Load configuration
    try:
        config = Config.from_file(args.config)
    except FileNotFoundError:
        logger.warning(f"Config file not found: {args.config}. Using defaults.")
        config = Config()
    
    # Override token if provided
    if args.token:
        config.github.token = args.token
    elif not config.github.token:
        config.github.token = getpass.getpass("Enter GitHub token (input hidden): ").strip()
    
    if not config.github.token:
        logger.error("GitHub token is required")
        sys.exit(1)
    
    # Initialize migrator
    migrator = GitHubMigrator(config)
    
    try:
        if args.command == "extract":
            migrator.extract_issues(
                project_id=args.project_id,
                output_path=args.output,
                limit=args.limit
            )
        
        elif args.command == "map":
            migrator.map_fields(
                input_path=args.input,
                output_path=args.output
            )
        
        elif args.command == "migrate":
            summary = migrator.migrate_issues(
                input_path=args.input,
                output_path=args.output
            )
            print(f"\nMigration Summary:")
            print(f"  Total: {summary['total']}")
            print(f"  Success: {summary['success']}")
            print(f"  Failed: {summary['failed']}")
            if summary['errors']:
                print(f"  Errors: {len(summary['errors'])}")
        
        elif args.command == "relationships":
            summary = migrator.migrate_relationships(
                input_path=args.input,
                output_path=args.output
            )
            print(f"\nRelationships Summary:")
            print(f"  Total rows: {summary['total']}")
            print(f"  Relationships added: {summary['relationships_added']}")
            if summary['errors']:
                print(f"  Errors: {len(summary['errors'])}")
        
        elif args.command == "labels":
            with open(args.input, 'r', encoding='utf-8') as f:
                labels_data = json.load(f)
            
            labels = [
                Label(
                    name=item["name"],
                    color=item["color"],
                    description=item.get("description", "")
                )
                for item in labels_data
            ]
            
            summary = migrator.migrate_labels(labels)
            print(f"\nLabels Summary:")
            print(f"  Total: {summary['total']}")
            print(f"  Success: {summary['success']}")
            print(f"  Failed: {summary['failed']}")
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2)
        
        elif args.command == "full":
            output_dir = args.output_dir or Path(config.processing.output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Map fields if needed
            mapped_path = output_dir / "mapped_issues.xlsx"
            logger.info("Step 1: Mapping fields...")
            migrator.map_fields(
                input_path=args.migrate_input,
                output_path=mapped_path
            )
            
            # Step 2: Migrate issues
            logger.info("Step 2: Migrating issues...")
            issues_summary = migrator.migrate_issues(
                input_path=mapped_path,
                output_path=output_dir / "migration_results.xlsx"
            )
            
            # Step 3: Migrate relationships if provided
            if args.relationships_input:
                logger.info("Step 3: Migrating relationships...")
                rel_summary = migrator.migrate_relationships(
                    input_path=args.relationships_input,
                    output_path=output_dir / "relationships_results.xlsx"
                )
            
            # Step 4: Migrate labels if provided
            if args.labels_input:
                logger.info("Step 4: Migrating labels...")
                with open(args.labels_input, 'r', encoding='utf-8') as f:
                    labels_data = json.load(f)
                
                labels = [
                    Label(
                        name=item["name"],
                        color=item["color"],
                        description=item.get("description", "")
                    )
                    for item in labels_data
                ]
                
                labels_summary = migrator.migrate_labels(labels)
            
            print(f"\nFull Migration Complete!")
            print(f"  Issues: {issues_summary['success']}/{issues_summary['total']} successful")
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        migrator.close()


if __name__ == "__main__":
    main()

