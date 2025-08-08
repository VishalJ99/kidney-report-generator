"""
Template engine for generating kidney biopsy reports
Populates templates with standard phrases based on shorthand codes
"""

import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path


class TemplateEngine:
    """Engine for populating report templates with phrases"""
    
    def __init__(self, phrases_file: str = None):
        """Initialize with phrases dictionary"""
        if phrases_file:
            self.phrases = self._load_phrases(phrases_file)
        else:
            # Load default transplant phrases
            data_dir = Path(__file__).parent.parent / 'data'
            self.phrases = self._load_phrases(str(data_dir / 'phrases_transplant.json'))
    
    def _load_phrases(self, filepath: str) -> Dict:
        """Load phrases from JSON file"""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def generate_report(self, parsed_data: Dict[str, Any]) -> str:
        """
        Generate complete report from parsed shorthand data
        
        Args:
            parsed_data: Structured data from parser
            
        Returns:
            Complete formatted report text
        """
        report_lines = []
        
        # Add patient information
        patient_info = parsed_data.get('patient_info', {})
        if patient_info:
            report_lines.extend(self._format_patient_info(patient_info))
            report_lines.append("")
        
        # Add sections
        sections = parsed_data.get('sections', {})
        
        # Light Microscopy
        if 'light_microscopy' in sections or 'glomeruli' in sections or 'tubulointerstitium' in sections or 'blood_vessels' in sections:
            report_lines.append("A. LIGHT MICROSCOPY")
            
            # Sample description
            if 'light_microscopy' in sections:
                lm_phrases = self._process_light_microscopy(sections['light_microscopy'])
                report_lines.extend(lm_phrases)
            
            # Glomeruli
            if 'glomeruli' in sections:
                report_lines.append("")
                report_lines.append("GLOMERULI")
                glom_phrases = self._process_glomeruli(sections['glomeruli'])
                report_lines.extend(glom_phrases)
            
            # Tubulointerstitium
            if 'tubulointerstitium' in sections:
                report_lines.append("")
                report_lines.append("TUBULOINTERSTITIUM")
                ti_phrases = self._process_tubulointerstitium(sections['tubulointerstitium'])
                report_lines.extend(ti_phrases)
            
            # Blood Vessels
            if 'blood_vessels' in sections:
                report_lines.append("")
                report_lines.append("BLOOD VESSELS")
                ves_phrases = self._process_blood_vessels(sections['blood_vessels'])
                report_lines.extend(ves_phrases)
        
        # Immunohistochemistry
        if 'immunohistochemistry' in sections:
            report_lines.append("")
            report_lines.append("IMMUNOHISTOCHEMISTRY")
            ihc_phrases = self._process_immunohistochemistry(sections['immunohistochemistry'])
            report_lines.extend(ihc_phrases)
        
        # Electron Microscopy
        if 'electron_microscopy' in sections:
            report_lines.append("")
            report_lines.append("B.ELECTRON MICROSCOPY")
            em_phrases = self._process_electron_microscopy(sections['electron_microscopy'])
            report_lines.extend(em_phrases)
        
        # Immunofluorescence
        if 'immunofluorescence' in sections:
            if sections['immunofluorescence'] and sections['immunofluorescence'][0] != 'FR_0':
                report_lines.append("")
                report_lines.append("C.IMMUNOFLUORESCENCE (frozen tissue sample)")
                if_phrases = self._process_immunofluorescence(sections['immunofluorescence'])
                report_lines.extend(if_phrases)
        
        # Conclusion
        if 'conclusion' in sections:
            report_lines.append("")
            report_lines.append("CONCLUSION")
            report_lines.append("Transplant kidney biopsy:")
            conclusion_phrases = self._process_conclusion(sections['conclusion'])
            for i, phrase in enumerate(conclusion_phrases, 1):
                report_lines.append(f"\t{phrase}")
        
        # Comment
        if 'comment' in sections:
            report_lines.append("")
            report_lines.append("COMMENT")
            comment_phrases = self._process_comment(sections['comment'])
            report_lines.extend(comment_phrases)
        
        return '\n'.join(report_lines)
    
    def _format_patient_info(self, patient_info: Dict) -> List[str]:
        """Format patient information section"""
        lines = []
        
        if 'nhs_number' in patient_info:
            lines.append(f"NHS number: {patient_info['nhs_number']}")
        if 'hospital_number' in patient_info:
            lines.append(f"Hospital number: {patient_info['hospital_number']}")
        if 'ns_number' in patient_info:
            lines.append(f"NS number: NS{patient_info['ns_number']}")
        if 'name' in patient_info:
            lines.append(f"Name: {patient_info['name']}")
        
        return lines
    
    def _process_light_microscopy(self, codes: List[str]) -> List[str]:
        """Process light microscopy section codes"""
        phrases = []
        
        for code in codes:
            # Handle sample description
            if code in self.phrases['light_microscopy']['sample']:
                phrases.append(self.phrases['light_microscopy']['sample'][code])
            # Handle sample counts (C2M1)
            elif re.match(r'C\d+M\d+', code):
                match = re.match(r'C(\d+)M(\d+)', code)
                if match:
                    c_count = int(match.group(1))
                    m_count = int(match.group(2))
                    if c_count == 2 and m_count == 1:
                        phrases.append("There are 2 samples of cortex and 1 sample of medulla.")
                    else:
                        phrases.append(f"There are {c_count} samples of cortex and {m_count} samples of medulla.")
            elif re.match(r'C\d+', code):
                match = re.match(r'C(\d+)', code)
                if match:
                    count = int(match.group(1))
                    if count == 1:
                        phrases.append("There is 1 sample of cortex.")
                    else:
                        phrases.append(f"There are {count} samples of cortex.")
        
        return phrases
    
    def _process_glomeruli(self, codes: List[str]) -> List[str]:
        """Process glomeruli section codes"""
        phrases = []
        
        for code in codes:
            # Total glomeruli count (just a number)
            if code.isdigit():
                phrases.append(f"Total number of glomeruli: {code}")
            
            # Globally sclerosed
            elif code.startswith('GS') or code.startswith('Gs'):
                match = re.match(r'[Gg][Ss](\d+)', code)
                if match:
                    count = int(match.group(1))
                    phrases.append(f"Number of globally sclerosed glomeruli: {count}")
            
            # Segmental sclerosis
            elif code.startswith('SS') or code.startswith('Ss'):
                if code == 'SS0' or code == 'Ss0':
                    phrases.append("No segmental sclerosis is seen.")
                elif '_NOS' in code:
                    match = re.match(r'[Ss][Ss](\d+)_NOS', code)
                    if match:
                        count = int(match.group(1))
                        if count == 1:
                            phrases.append("One glomerulus shows segmental sclerosis (NOS).")
                        else:
                            phrases.append(f"{count} glomeruli show segmental sclerosis (NOS)")
            
            # Mesangial matrix
            elif code.upper() in ['MM0', 'MM1', 'MM2', 'MM3']:
                key = code.upper()
                if key in self.phrases['glomeruli']['mesangial_matrix']:
                    phrases.append(self.phrases['glomeruli']['mesangial_matrix'][key])
            
            # Mesangial cellularity
            elif code.upper() in ['MC0', 'MC1', 'MC2', 'MC3']:
                key = code.upper()
                if key in self.phrases['glomeruli']['mesangial_cellularity']:
                    phrases.append(self.phrases['glomeruli']['mesangial_cellularity'][key])
            
            # Glomerulitis
            elif code.upper() in ['G0', 'G1', 'G2', 'G3']:
                key = code.upper()
                if key in self.phrases['glomeruli']['glomerulitis']:
                    phrases.append(self.phrases['glomeruli']['glomerulitis'][key])
            
            # Capillary double contours
            elif code.upper() in ['CG0', 'CG1', 'CG2', 'CG3']:
                key = code.upper()
                if key in self.phrases['glomeruli']['capillary_double_contours']:
                    phrases.append(self.phrases['glomeruli']['capillary_double_contours'][key])
        
        return phrases
    
    def _process_tubulointerstitium(self, codes: List[str]) -> List[str]:
        """Process tubulointerstitium section codes"""
        phrases = []
        ifta_phrase = None
        ctci_phrase = None
        
        for code in codes:
            # Acute tubular injury
            if code in ['ATI1', 'ATI2', 'ATI_micro', 'ATI micro']:
                if code == 'ATI micro':
                    code = 'ATI1'  # Map to ATI1
                if code in self.phrases['tubulointerstitium']['acute_tubular_injury']:
                    phrases.append(self.phrases['tubulointerstitium']['acute_tubular_injury'][code])
            
            # IFTA percentage
            elif code.startswith('IFTA'):
                match = re.match(r'IFTA(\d+)', code)
                if match:
                    percentage = match.group(1)
                    ifta_phrase = f"Tubular atrophy/interstitial fibrosis (nearest 10%): {percentage}%"
            
            # CT/CI scores
            elif code.upper() in ['CT1CI0', 'CTCI1', 'CTCI2', 'CTCI3']:
                key = code.upper()
                if key in self.phrases['tubulointerstitium']['ct_ci_scores']:
                    ctci_phrase = self.phrases['tubulointerstitium']['ct_ci_scores'][key]
            
            # Tubulitis
            elif code.upper() in ['T0', 'T1', 'T2', 'T3']:
                key = code.upper()
                if key in self.phrases['tubulointerstitium']['tubulitis']:
                    phrases.append(self.phrases['tubulointerstitium']['tubulitis'][key])
            
            # Inflammation scores
            elif '_I-IFTA' in code.upper():
                key = code.upper().replace('-', '-')
                if key in self.phrases['tubulointerstitium']['inflammation']:
                    phrases.append(self.phrases['tubulointerstitium']['inflammation'][key])
            
            # Total inflammation
            elif code.upper() in ['TI0', 'TI1', 'TI2', 'TI3']:
                key = code.upper()
                if key in self.phrases['tubulointerstitium']['total_inflammation']:
                    phrases.append(self.phrases['tubulointerstitium']['total_inflammation'][key])
        
        # Add IFTA and CT/CI together
        if ifta_phrase:
            if ctci_phrase:
                phrases.insert(1 if phrases else 0, f"{ifta_phrase} {ctci_phrase}")
            else:
                phrases.insert(1 if phrases else 0, ifta_phrase)
        
        return phrases
    
    def _process_blood_vessels(self, codes: List[str]) -> List[str]:
        """Process blood vessels section codes"""
        phrases = []
        
        for code in codes:
            # Artery count
            if code.startswith('A') and code[1:].isdigit():
                count = int(code[1:])
                if count == 1:
                    phrases.append("One artery is present in the sampled kidney.")
                elif count == 2:
                    phrases.append("Two arteries are present in the sampled kidney.")
                elif count == 3:
                    phrases.append("Three arteries are present in the sampled kidney.")
                else:
                    phrases.append(f"{count} arteries are present in the sampled kidney.")
            
            # Artery types
            elif 'IL' in code and 'Ar' in code:
                if code == '1IL_0Ar':
                    phrases.append("One is interlobular.")
                elif code == '2IL_1Ar':
                    phrases.append("Two are interlobular, 1 is arcuate.")
                else:
                    match = re.match(r'(\d+)IL_(\d+)Ar', code)
                    if match:
                        il_count = int(match.group(1))
                        ar_count = int(match.group(2))
                        phrases.append(f"{il_count} are interlobular, {ar_count} are arcuate.")
            
            # CV scores
            elif code.upper() in ['CV0', 'CV1', 'CV2', 'CV3']:
                key = code.upper()
                if key in self.phrases['blood_vessels']['fibrointimal_thickening']:
                    phrases.append(self.phrases['blood_vessels']['fibrointimal_thickening'][key])
            
            # CAA scores
            elif code.upper() in ['CAA0', 'CAA1']:
                key = code.upper()
                if key in self.phrases['blood_vessels']['chronic_allograft_arteriopathy']:
                    phrases.append(self.phrases['blood_vessels']['chronic_allograft_arteriopathy'][key])
            
            # V scores
            elif code.upper() in ['V0', 'V1', 'V2', 'V3']:
                key = code.upper()
                if key in self.phrases['blood_vessels']['endarteritis']:
                    phrases.append(self.phrases['blood_vessels']['endarteritis'][key])
            
            # AH scores
            elif code.upper() in ['AH0', 'AH1', 'AH2', 'AH3']:
                key = code.upper()
                if key in self.phrases['blood_vessels']['arteriolar_hyalinosis']:
                    phrases.append(self.phrases['blood_vessels']['arteriolar_hyalinosis'][key])
            
            # PTC scores
            elif code.upper() in ['PTC0', 'PTC1', 'PTC2', 'PTC3']:
                key = code.upper()
                if key in self.phrases['blood_vessels']['peritubular_capillaritis']:
                    phrases.append(self.phrases['blood_vessels']['peritubular_capillaritis'][key])
        
        return phrases
    
    def _process_immunohistochemistry(self, codes: List[str]) -> List[str]:
        """Process immunohistochemistry section codes"""
        phrases = []
        
        for code in codes:
            # C4d staining
            if code.upper() in ['C4D0', 'C4D1', 'C4D2', 'C4D3']:
                key = code.upper()
                if key in self.phrases['immunohistochemistry']['c4d']:
                    phrases.append(self.phrases['immunohistochemistry']['c4d'][key])
            
            # SV40 staining
            elif code in ['SV40_0', 'SV40_1', 'SV40_2']:
                if code in self.phrases['immunohistochemistry']['sv40']:
                    phrases.append(self.phrases['immunohistochemistry']['sv40'][code])
        
        return phrases
    
    def _process_electron_microscopy(self, codes: List[str]) -> List[str]:
        """Process electron microscopy section codes"""
        phrases = []
        
        for code in codes:
            if code in self.phrases['electron_microscopy']:
                phrases.append(self.phrases['electron_microscopy'][code])
        
        return phrases
    
    def _process_immunofluorescence(self, codes: List[str]) -> List[str]:
        """Process immunofluorescence section codes"""
        phrases = []
        
        for code in codes:
            if code in self.phrases['immunofluorescence']:
                phrases.append(self.phrases['immunofluorescence'][code])
        
        return phrases
    
    def _process_conclusion(self, codes: List[str]) -> List[str]:
        """Process conclusion section codes"""
        phrases = []
        
        for code in codes:
            if code in self.phrases['conclusion']:
                phrases.append(self.phrases['conclusion'][code])
        
        return phrases
    
    def _process_comment(self, codes: List[str]) -> List[str]:
        """Process comment section codes"""
        phrases = []
        
        for code in codes:
            if code in self.phrases['comment']:
                phrases.append(self.phrases['comment'][code])
        
        return phrases