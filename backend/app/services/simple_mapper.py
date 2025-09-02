"""
Simple mapper for converting shorthand codes to full medical phrases.
Replaces the complex 250+ line template_engine.py with ~50 lines.
"""

import json
import re
from pathlib import Path
from typing import Optional


class SimpleMapper:
    """Maps shorthand codes to full medical phrases using flat JSON lookup."""
    
    def __init__(self, json_path: str = None):
        """Initialize mapper with phrases from flat JSON file."""
        if json_path is None:
            # Default to phrases_flat.json in data directory
            json_path = Path(__file__).parent.parent / "data" / "phrases_flat.json"
        
        with open(json_path, 'r') as f:
            self.mappings = json.load(f)
    
    def map_code(self, code: str) -> Optional[str]:
        """
        Map a single shorthand code to its full phrase.
        
        Args:
            code: Shorthand code (e.g., "MM0", "TG5", "IFTA20")
            
        Returns:
            Full medical phrase or None if no match found
        """
        # Normalize to uppercase
        code = code.upper().strip()
        
        # Try direct lookup first (O(1) for most codes)
        if code in self.mappings:
            return self.mappings[code]
        
        # Try regex patterns (prefixed with ~)
        for key, template in self.mappings.items():
            if key.startswith('~'):
                pattern = key[1:]  # Remove ~ prefix
                match = re.match(pattern, code)
                if match:
                    # Substitute captured groups into template
                    result = template
                    for i, group in enumerate(match.groups(), 1):
                        result = result.replace(f'{{{i}}}', group)
                    return result
        
        return None
    
    def is_header(self, code: str) -> bool:
        """Check if a code represents a section header."""
        code = code.upper().strip()
        return code in self.mappings and self.mappings[code].startswith('!')