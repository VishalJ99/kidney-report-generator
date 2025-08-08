# Clinical Kidney Biopsy Reporting Automation Project

## Project Overview
This project aims to build an intelligent reporting tool for pathologists that automates the creation of standardized kidney biopsy reports from shorthand input. The tool will significantly reduce the time and cognitive load associated with manual report writing.

## Problem Statement
Current pathology reporting involves:
- Manual copying and pasting from standard phrase banks
- High cognitive load from friction in the process
- Time-consuming template filling
- 80% of reports consist of standard phrases that could be automated
- Risk of inconsistency in terminology and reporting standards

## Solution Architecture

### Input Processing
Pathologists enter shorthand codes that represent standardized medical observations. Examples:
- `CM` → "The sample consists of cortex and medulla"
- `G2` → "There is moderate glomerulitis (g2)"
- `IFTA20` → "Tubular atrophy/interstitial fibrosis (nearest 10%): 20%"
- `ATI_micro` → "Acute tubular injury with tubular epithelial cell cytoplasmic microvacuolation"

### Output Generation
The system produces:
1. **Clinical Diagnostic Report**: Structured text ready for LIMS (Laboratory Information Management System)
2. **Registry Data**: CSV file with standardized codes for local/national disease registries
3. **FHIR-Compatible Format**: For interoperability with other healthcare systems

## Document Structure

### 1. Templates
Two main templates exist:
- **Transplant Biopsy Template** (`transplant biopsy template.txt`)
- **Native Biopsy Template** (`native biopsy template.txt`)

Both templates follow a standard structure:
```
- Patient Information (NHS, Hospital, NS numbers, Name)
- A. LIGHT MICROSCOPY
  - Sample description
  - Glomeruli assessment
  - Tubulointerstitium evaluation
  - Blood vessels analysis
- B. ELECTRON MICROSCOPY
- C. IMMUNOFLUORESCENCE
- CONCLUSION
- COMMENT
```

### 2. Standard Phrases Mapping

#### Transplant Biopsy Phrases
The `Standard phrases - Transplant v2.md` contains ~450 mappings organized by section:

**Sample Description Codes:**
- `C` → "The sample consists of cortex only"
- `M` → "The sample consists of medulla only"
- `CM` → "The sample consists of cortex and medulla"
- `C2M1` → "There are 2 samples of cortex and 1 sample of medulla"

**Glomeruli Codes:**
- `GSx` → "Number of globally sclerosed glomeruli: x"
- `SSx_NOS` → "x glomeruli show segmental sclerosis (NOS)"
- `MM0-3` → Mesangial matrix grades (none/mild/moderate/marked)
- `MC0-3` → Mesangial cellularity grades
- `G0-3` → Glomerulitis grades
- `CG0-3` → Capillary wall double contours grades

**Tubulointerstitium Codes:**
- `ATI1` → "There is mild acute tubular injury"
- `ATI2` → "There is severe acute tubular injury, with granular casts"
- `ATI_micro` → "There acute tubular injury with tubular epithelial cell cytoplasmic microvacuolation"
- `IFTAxx` → "Tubular atrophy/interstitial fibrosis (nearest 10%): xx%"
- `T0-3` → Tubulitis grades
- `I0-3_I-IFTA0-3` → Complex inflammation scoring combinations

**Vascular Codes:**
- `Ax` → "x arteries are present in the sampled kidney"
- `CV0-3` → Arterial fibrointimal thickening grades
- `V0-3` → Endarteritis grades
- `AH0-3` → Arteriolar hyalinosis grades
- `PTC0-3` → Peritubular capillaritis grades

**Immunohistochemistry Codes:**
- `C4d0-3` → C4d staining percentages in peritubular capillaries
- `SV40_0-2` → SV40 (BKV) staining patterns

**Conclusion Codes:**
- `ATI` → "Acute tubular injury"
- `BL` → "Borderline for T cell-mediated rejection"
- `TCMR1a/1b` → T cell-mediated rejection grades
- `MVI+` → "Microcirculation inflammation present, C4d-negative, DSA-negative"
- `MildIFTA/ModIFTA` → Interstitial fibrosis/tubular atrophy severity

**Comment Codes:**
- `NR` → "There is no evidence of rejection"
- `DP` → Digital pathology disclaimer
- `EM` → Electron microscopy accreditation disclaimer
- Various diagnostic explanations (FSGS, MVI+, pAMR, TMA, etc.)

#### Native Biopsy Phrases
The `Standard phrases - Native.txt` contains simpler mappings for non-transplant biopsies:
- Glomerular assessments (SS0-2, ISCH1-2, MH0-3, E0-1, FN0-x, CC0-x)
- Tubulointerstitial findings (I-IFTA1-2, I0-2T)
- Standard diagnostic comments

### 3. Database Coding (Excel)
The `Transplant biopsy dataset.xlsx` maps shorthand to structured database fields:
- Path number, NHS Number, Patient identifiers
- Sample presence indicators (IF, EM samples)
- Banff scores (standardized transplant pathology scoring)
- Diagnostic codes (DIagnosis 1-4)
- Individual lesion scores (C4d, IFTA%, CT, CI, I, iIFTA, TI, T, CV, CAA, V, AH, etc.)

## Shorthand Entry Pattern

### Example 1 - Complex Transplant Case:
**Input Shorthand:**
```
NHS: 234 4567 2345
NS: 25-67890
Name: Smith
Coder: CR
Consent: PISv.8
Date: 12/07/2025
LM: CM, C2M1
Glom: 31, Gs7, Ss1_NOS, Mm1, Mc1, G2, Cg1
TI: ATI micro, IFTA20, CTCI1, T1, I1_I-IFTA3, TI2
Ves: A3, 2IL_1Ar, Cv2, Caa0, V0, Ah1, Ptc1
IHC: C4d0, SV40_0
EM: EM0
IFFR: FR_0
CONCLUSION: BL, MVI+, MildIFTA
COMMENT: MVI+, DP
```

**Generated Report:** Full structured report with all sections populated using standard phrases

### Example 2 - Simple Case:
**Input Shorthand:**
```
NHS: 987 6543 2109
NS: 25-54321
Name: Patel
LM: C, C2
Glom: 10, Gs1, Ss0, G0, Cg0
TI: ATI_micro, IFTA10, CTCI1, T0, I0_I-IFTA1, TI0
Ves: A1, 1IL_0Ar, Cv1, Caa0, V0, Ah0, Ptc0
CONCLUSION: ATI_micro
COMMENT: ATI_micro, DP
```

## Key Implementation Considerations

### 1. Parsing Logic
- Shorthand codes are context-sensitive (section matters)
- Some codes include variables (e.g., `GSx` where x is a number)
- Complex codes like `I1_I-IFTA3` map to full sentences with multiple scoring components
- Order of phrases within sections should match template structure

### 2. Intelligence Requirements
- **Section Detection**: Identify which template section each shorthand belongs to
- **Variable Substitution**: Replace placeholders (x, xx) with actual values
- **Phrase Combination**: Some conclusions require multiple phrases
- **Context Preservation**: Maintain medical accuracy and coherence

### 3. Future Enhancements
- **Fuzzy Matching**: Handle noisy/imperfect shorthand input
- **Auto-suggestion**: Predict likely codes based on partial input
- **Validation**: Check for required fields and logical consistency
- **Integration**: Direct LIMS integration to eliminate copy-paste
- **ML Training**: Use accumulated reports for improved predictions

## Technical Requirements

### Core Functionality
1. **Parser**: Convert shorthand to structured data
2. **Template Engine**: Populate templates with standard phrases
3. **Mapping Dictionary**: Maintain shorthand-to-phrase mappings
4. **Report Generator**: Assemble final report in correct format
5. **CSV Exporter**: Generate registry-compatible data files

### Data Structures
```python
# Example mapping structure
transplant_phrases = {
    "light_microscopy": {
        "sample": {
            "C": "The sample consists of cortex only.",
            "CM": "The sample consists of cortex and medulla.",
            # ...
        },
        "glomeruli": {
            "GSx": "Number of globally sclerosed glomeruli: {x}",
            # ...
        }
    }
}
```

## Stakeholders
- **Primary Users**: Renal pathologists
- **Organizations**: UK Renal Pathology Network, NHS England, UK Kidney Association
- **Systems**: LIMS, Renal Registry databases
- **Standards**: FHIR/HL7 compatibility required

## Success Metrics
- Time saved per report (target: >50% reduction)
- Consistency of terminology usage
- Accuracy of database coding
- User satisfaction scores
- Registry data quality improvement

## Commercial Solutions Referenced
- **mTuitive**: Cancer-focused, customizable algorithms
- **Tiro.Health**: Voice dictation support, €12K/year for 10 consultants
- **Celerato**: Structured reporting platform

## Development Approach
1. **Proof of Concept**: Demonstrate basic shorthand-to-report conversion
2. **Stakeholder Buy-in**: Get pathologist feedback and iterate
3. **Validation**: Compare generated reports with manual ones
4. **Integration Planning**: LIMS and registry connectivity
5. **Deployment**: Phased rollout with training

## Notes for Implementation
- Start with transplant biopsies (more standardized)
- Maintain flexibility for non-standard phrases (20% of reports)
- Consider voice input integration (like Tiro.Health)
- Ensure UKAS accreditation compatibility
- Build in audit trail for regulatory compliance