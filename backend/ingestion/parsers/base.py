from abc import ABC, abstractmethod


class BaseParser(ABC):
    """
    Abstract base class for source-specific data parsers.
    
    Each parser must implement parse_row() which takes a raw dict (one row)
    and returns a normalized dict with standard fields, or raises ValueError
    for rows that can't be parsed.
    """

    @abstractmethod
    def parse_rows(self, rows: list[dict]) -> list[dict]:
        """
        Parse a list of raw row dicts into normalized records.
        
        Returns a list of dicts, each containing:
        - parsed: bool (True if successfully parsed)
        - errors: list[str] (parse errors if any)
        - normalized: dict with standard fields (if parsed)
        - flags: list[dict] with {reason, severity} (anomaly flags)
        - raw: dict (original row)
        """
        pass

    def detect_delimiter(self, content: str) -> str:
        """Auto-detect CSV delimiter from file content."""
        first_line = content.split('\n')[0]
        # Count potential delimiters in the header line
        counts = {
            ';': first_line.count(';'),
            ',': first_line.count(','),
            '\t': first_line.count('\t'),
            '|': first_line.count('|'),
        }
        # Return the most frequent delimiter
        return max(counts, key=counts.get)
