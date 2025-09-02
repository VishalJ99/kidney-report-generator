"""
Report formatter for organizing medical phrases into structured sections.
Handles section headers and proper report formatting.
"""

from typing import List, Dict, Any


class ReportFormatter:
    """Formats expanded medical phrases into a structured report."""
    
    def __init__(self):
        """Initialize the formatter with section ordering."""
        # Define the order of sections in the final report
        self.section_order = [
            "A. LIGHT MICROSCOPY",
            "GLOMERULI",
            "TUBULOINTERSTITIUM",
            "BLOOD VESSELS",
            "IMMUNOHISTOCHEMISTRY",
            "B. ELECTRON MICROSCOPY",
            "C. IMMUNOFLUORESCENCE (frozen tissue sample)",
            "CONCLUSION",
            "COMMENT"
        ]
    
    def format_entries(self, entries: List[Dict[str, str]]) -> str:
        """
        Format a list of expanded entries into a structured report.
        
        Args:
            entries: List of dicts with 'type' (header/content) and 'text'
            
        Returns:
            Formatted report text
        """
        formatted = []
        
        for entry in entries:
            if entry.get("type") == "header":
                # Add spacing around headers
                formatted.append(f"\n{entry['text']}\n")
            else:
                # Regular content
                formatted.append(entry.get('text', ''))
        
        # Join and clean up extra blank lines
        report = '\n'.join(formatted)
        # Remove multiple consecutive blank lines
        while '\n\n\n' in report:
            report = report.replace('\n\n\n', '\n\n')
        
        return report.strip()
    
    def organize_by_sections(self, phrases: List[str]) -> List[Dict[str, str]]:
        """
        Organize a list of phrases into sections based on headers.
        
        Args:
            phrases: List of expanded medical phrases
            
        Returns:
            List of entries with type (header/content) and text
        """
        entries = []
        
        for phrase in phrases:
            if phrase and phrase.strip():
                # Check if this is a header (from ! prefix codes)
                if phrase.upper() in [s.upper() for s in self.section_order]:
                    entries.append({"type": "header", "text": phrase})
                else:
                    entries.append({"type": "content", "text": phrase})
        
        return entries
    
    def format_report(self, phrases: List[str]) -> str:
        """
        Main method to format a list of phrases into a complete report.
        
        Args:
            phrases: List of expanded medical phrases
            
        Returns:
            Formatted report text
        """
        entries = self.organize_by_sections(phrases)
        return self.format_entries(entries)