"""
Simple mapper for converting shorthand codes to full medical phrases.
Supports section-specific values and code extraction.
"""

import json
import re
from pathlib import Path
from typing import Optional


class SimpleMapper:
    """Maps shorthand codes to full medical phrases using sectioned JSON lookup."""

    def __init__(self, json_path: str = None):
        """Initialize mapper with phrases from sectioned JSON file."""
        if json_path is None:
            # Default to phrases_sectioned.json in data directory
            json_path = Path(__file__).parent.parent / "data" / "phrases_sectioned.json"

        with open(json_path, 'r') as f:
            self.mappings = json.load(f)

    def map_code(self, code: str, section: str = "main_body") -> Optional[str]:
        """
        Map a single shorthand code to its full phrase for a given section.

        Args:
            code: Shorthand code (e.g., "MM0", "TG5", "IFTA20")
            section: Current section ("main_body", "conclusion", "comments")

        Returns:
            Full medical phrase, empty string if no expansion, or None if key not found
        """
        # Normalize to lowercase
        code_lower = code.lower().strip()

        # Try direct lookup first
        if code_lower in self.mappings:
            entry = self.mappings[code_lower]
            value = entry.get(section, "")
            # Return None if empty string (frontend will keep original key)
            return value if value else None

        # Try regex patterns (prefixed with ~)
        for key, entry in self.mappings.items():
            if key.startswith('~'):
                pattern = key[1:]  # Remove ~ prefix
                match = re.match(pattern, code_lower, re.IGNORECASE)
                if match:
                    # Get template for this section
                    template = entry.get(section, "")
                    if not template:
                        return None

                    # Substitute captured groups into template
                    result = template
                    for i, group in enumerate(match.groups(), 1):
                        result = result.replace(f'{{{i}}}', group)
                    return result

        return None

    def get_conclusion_code(self, key: str, report_type: str = "transplant") -> Optional[str]:
        """
        Get database code for a conclusion key.

        Args:
            key: The shorthand key
            report_type: "transplant" or "native"

        Returns:
            The code value, or None if no code exists
        """
        key_lower = key.lower().strip()

        if key_lower not in self.mappings:
            return None

        codes = self.mappings[key_lower].get('codes', {})
        if not codes:
            return None

        # Map report type to code field
        if report_type == "transplant":
            code_value = codes.get('transplant')
        else:
            # For native, try native1 first, then native2
            code_value = codes.get('native1') or codes.get('native2')

        if not code_value:
            return None

        # If code is "VALUE", return the conclusion value itself
        if code_value == "VALUE":
            return self.mappings[key_lower].get('conclusion', '')

        return code_value

    def get_all_mappings(self) -> dict:
        """
        Return all mappings for the reference popup.
        Returns flat dict with section labels for keys that have values.

        Format: { "key [SECTION]": "value", ... }
        """
        result = {}
        section_labels = {
            'main_body': 'MAIN BODY',
            'conclusion': 'CONCLUSION',
            'comments': 'COMMENTS'
        }

        for key, entry in self.mappings.items():
            # Skip regex patterns for display (or show with pattern indicator)
            display_key = key[1:] + ' (pattern)' if key.startswith('~') else key

            for section, label in section_labels.items():
                value = entry.get(section, "")
                if value:  # Only include if value exists
                    result[f"{display_key} [{label}]"] = value

        return result

    def is_header(self, code: str) -> bool:
        """Check if a code represents a section header."""
        return code.lower().strip().startswith('!')
