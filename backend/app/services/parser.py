"""
Shorthand parser for kidney biopsy reports
Parses shorthand codes into structured data
"""

import re
from typing import Dict, List, Any, Optional


class ShorthandParser:
    """Parser for converting shorthand notation to structured data"""
    
    def __init__(self):
        self.section_mapping = {
            'LM': 'light_microscopy',
            'Glom': 'glomeruli',
            'TI': 'tubulointerstitium',
            'Ves': 'blood_vessels',
            'IHC': 'immunohistochemistry',
            'EM': 'electron_microscopy',
            'IFFR': 'immunofluorescence',
            'CONCLUSION': 'conclusion',
            'COMMENT': 'comment'
        }
    
    def parse(self, shorthand_text: str) -> Dict[str, Any]:
        """
        Parse shorthand text into structured data
        
        Args:
            shorthand_text: Multi-line shorthand input
            
        Returns:
            Structured dictionary with parsed data
        """
        result = {
            'patient_info': {},
            'sections': {}
        }
        
        lines = shorthand_text.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if it's a section header
            if ':' in line:
                parts = line.split(':', 1)
                key = parts[0].strip()
                value = parts[1].strip() if len(parts) > 1 else ''
                
                # Check if it's a known section
                if key in self.section_mapping:
                    current_section = self.section_mapping[key]
                    result['sections'][current_section] = self._parse_section_codes(value)
                # Otherwise it's patient info
                else:
                    self._parse_patient_info(key, value, result['patient_info'])
        
        return result
    
    def _parse_patient_info(self, key: str, value: str, patient_info: Dict):
        """Parse patient information fields"""
        key_lower = key.lower()
        
        if key_lower == 'nhs':
            patient_info['nhs_number'] = value
        elif key_lower == 'hn':
            patient_info['hospital_number'] = value
        elif key_lower == 'ns':
            patient_info['ns_number'] = value
        elif key_lower == 'name':
            patient_info['name'] = value
        elif key_lower == 'coder':
            patient_info['coder'] = value
        elif key_lower == 'consent':
            patient_info['consent'] = value
        elif 'date' in key_lower:
            patient_info['date_of_biopsy'] = value
    
    def _parse_section_codes(self, codes_str: str) -> List[str]:
        """Parse comma-separated codes from a section"""
        if not codes_str:
            return []
        
        # Split by comma but preserve spaces in codes like "ATI micro"
        codes = []
        current_code = ""
        
        for part in codes_str.split(','):
            part = part.strip()
            if part:
                codes.append(part)
        
        return codes
    
    def extract_numeric_value(self, code: str) -> Optional[int]:
        """Extract numeric value from codes like GS7, IFTA20"""
        match = re.search(r'\d+', code)
        if match:
            return int(match.group())
        return None
    
    def parse_compound_code(self, code: str) -> Dict[str, Any]:
        """Parse compound codes like I1_I-IFTA3 or 2IL_1Ar"""
        result = {'raw': code}
        
        # Handle inflammation codes (I1_I-IFTA3)
        if '_I-IFTA' in code:
            parts = code.split('_')
            if len(parts) == 2:
                result['i_score'] = parts[0]
                result['ifta_score'] = parts[1]
        
        # Handle artery types (2IL_1Ar)
        elif 'IL' in code and 'Ar' in code:
            match = re.match(r'(\d+)IL_(\d+)Ar', code)
            if match:
                result['interlobular'] = int(match.group(1))
                result['arcuate'] = int(match.group(2))
        
        # Handle IFTA percentage
        elif code.startswith('IFTA'):
            value = self.extract_numeric_value(code)
            if value:
                result['percentage'] = value
        
        # Handle glomeruli counts
        elif code.startswith('GS'):
            value = self.extract_numeric_value(code)
            if value:
                result['count'] = value
                result['type'] = 'globally_sclerosed'
        
        # Handle segmental sclerosis
        elif code.startswith('SS'):
            if '_' in code:
                parts = code.split('_')
                value = self.extract_numeric_value(parts[0])
                if value:
                    result['count'] = value
                    result['variant'] = parts[1] if len(parts) > 1 else 'NOS'
        
        # Handle sample counts (C2M1)
        elif re.match(r'C\d+M\d+', code):
            match = re.match(r'C(\d+)M(\d+)', code)
            if match:
                result['cortex_count'] = int(match.group(1))
                result['medulla_count'] = int(match.group(2))
        elif re.match(r'C\d+', code):
            match = re.match(r'C(\d+)', code)
            if match:
                result['cortex_count'] = int(match.group(1))
        
        # Handle artery count (A3)
        elif re.match(r'A\d+', code):
            value = self.extract_numeric_value(code)
            if value:
                result['artery_count'] = value
        
        return result