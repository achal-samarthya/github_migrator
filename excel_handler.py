"""
Excel file handler for reading and writing migration data.

Author: Achal Samarthya

This module provides utilities for reading and writing Excel files used in
the GitHub migration process. It handles:
- Reading Excel files with multiple sheets
- Writing DataFrames to Excel files with multiple sheets
- Finding sheets by name (with fuzzy matching support)
- Parsing and joining multi-value fields (using separators like "||")
- Sanitizing text for Excel compatibility (removing illegal XML characters)
- Normalizing column names for matching

The ExcelHandler class is used throughout the migration process to read
source data and write migration results.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

logger = logging.getLogger(__name__)


class ExcelHandler:
    """Handles Excel file operations for migration data."""
    
    def __init__(self, multi_value_separator: str = "||"):
        self.separator = multi_value_separator
    
    def read_excel(
        self,
        file_path: Path,
        sheet_name: Optional[str] = None,
        engine: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Read Excel file, returning a dictionary of sheet names to DataFrames.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Specific sheet name or None for all sheets
            engine: Engine to use ('openpyxl' for .xlsx, 'xlrd' for .xls)
        
        Returns:
            Dictionary mapping sheet names to DataFrames
        """
        if engine is None:
            engine = "openpyxl" if file_path.suffix.lower() == ".xlsx" else "xlrd"
        
        try:
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine)
                return {sheet_name: df}
            else:
                return pd.read_excel(file_path, sheet_name=None, engine=engine)
        except Exception as e:
            logger.error(f"Failed to read Excel file {file_path}: {e}")
            raise
    
    def write_excel(
        self,
        data: Dict[str, pd.DataFrame],
        file_path: Path,
        engine: str = "openpyxl"
    ):
        """
        Write multiple DataFrames to an Excel file with multiple sheets.
        
        Args:
            data: Dictionary mapping sheet names to DataFrames
            file_path: Output file path
            engine: Engine to use
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with pd.ExcelWriter(file_path, engine=engine) as writer:
                for sheet_name, df in data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            logger.info(f"Wrote Excel file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to write Excel file {file_path}: {e}")
            raise
    
    def find_sheet_by_name(
        self,
        file_path: Path,
        target_name: str,
        fuzzy: bool = True
    ) -> Optional[str]:
        """
        Find a sheet by name (exact or fuzzy match).
        
        Args:
            file_path: Path to Excel file
            target_name: Target sheet name
            fuzzy: Use fuzzy matching if exact match not found
        
        Returns:
            Sheet name if found, None otherwise
        """
        sheets = self.read_excel(file_path)
        
        # Try exact match (case-insensitive)
        target_lower = target_name.lower()
        for sheet in sheets.keys():
            if sheet.lower() == target_lower:
                return sheet
        
        # Try fuzzy match
        if fuzzy:
            import difflib
            matches = difflib.get_close_matches(
                target_name,
                list(sheets.keys()),
                n=1,
                cutoff=0.6
            )
            if matches:
                return matches[0]
        
        return None
    
    def parse_multi_value(self, value: Any) -> List[str]:
        """
        Parse a cell value that may contain multiple values separated by separator.
        
        Args:
            value: Cell value (string, list, or None)
        
        Returns:
            List of non-empty strings
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return []
        
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        
        s = str(value).strip()
        if not s:
            return []
        
        if self.separator in s:
            parts = [p.strip() for p in s.split(self.separator)]
            return [p for p in parts if p]
        
        return [s]
    
    def join_multi_value(self, values: List[str]) -> str:
        """
        Join multiple values with separator.
        
        Args:
            values: List of strings
        
        Returns:
            Joined string
        """
        return self.separator.join([str(v).strip() for v in values if str(v).strip()])
    
    def sanitize_text(self, value: Any) -> str:
        """
        Sanitize text for Excel compatibility (remove illegal XML characters).
        
        Args:
            value: Input value
        
        Returns:
            Sanitized string
        """
        import re
        if value is None:
            return ""
        
        if not isinstance(value, str):
            value = str(value)
        
        # Remove illegal XML characters
        illegal_chars = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
        return illegal_chars.sub("", value)
    
    def normalize_column_name(self, name: str) -> str:
        """
        Normalize column name for matching (remove spaces, special chars).
        
        Args:
            name: Column name
        
        Returns:
            Normalized name
        """
        import re
        return re.sub(r"[ _\-]+", "", str(name).strip().lower())

