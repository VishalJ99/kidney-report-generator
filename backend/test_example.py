#!/usr/bin/env python3
"""
Test script to verify the backend works with the provided examples
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.parser import ShorthandParser
from app.services.template_engine import TemplateEngine

# Example 1 shorthand from the document
example1_shorthand = """NHS: 234 4567 2345
HN: 31098674
NS: 25-67890
Name: Smith
Coder: CR
Consent: PISv.8
Date of biopsy: 12/07/2025
LM: CM, C2M1
Glom: 31, Gs7, Ss1_NOS, Mm1, Mc1, G2, Cg1
TI: ATI micro, IFTA20, CTCI1, T1, I1_I-IFTA3, TI2
Ves: A3, 2IL_1Ar, Cv2, Caa0, V0, Ah1, Ptc1
IHC: C4d0, SV40_0
EM: EM0
IFFR: FR_0
CONCLUSION: BL, MVI+, MildIFTA
COMMENT: MVI+, DP"""

# Example 2 shorthand
example2_shorthand = """NHS: 987 6543 2109
HN: 31045678
NS: 25-54321
Name: Patel
Coder: AS
Consent: U
Date of biopsy: 13/07/2025
LM: C, C2
Glom: 10, Gs1, Ss0, G0, Cg0
TI: ATI_micro, IFTA10, CTCI1, T0, I0_I-IFTA1, TI0
Ves: A1, 1IL_0Ar, Cv1, Caa0, V0, Ah0, Ptc0
IHC: C4d0, SV40_0
EM: EM0
IFFR: FR0
CONCLUSION: ATI_micro
COMMENT: ATI_micro, DP"""

def test_example(shorthand, example_num):
    print(f"\n{'='*60}")
    print(f"Testing Example {example_num}")
    print('='*60)
    
    # Parse the shorthand
    parser = ShorthandParser()
    parsed_data = parser.parse(shorthand)
    
    print("\nParsed Data:")
    print(f"Patient Info: {parsed_data['patient_info']}")
    print(f"Sections: {list(parsed_data['sections'].keys())}")
    
    # Generate the report
    engine = TemplateEngine()
    report = engine.generate_report(parsed_data)
    
    print("\nGenerated Report:")
    print("-" * 40)
    print(report)
    print("-" * 40)
    
    return report

if __name__ == "__main__":
    # Test Example 1
    report1 = test_example(example1_shorthand, 1)
    
    # Test Example 2
    report2 = test_example(example2_shorthand, 2)
    
    print("\n" + "="*60)
    print("Testing complete!")
    print("="*60)