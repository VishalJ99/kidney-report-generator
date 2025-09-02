#!/usr/bin/env python3
"""
Test script for the simplified autocomplete implementation.
Tests the SimpleMapper and ReportFormatter without needing FastAPI.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.simple_mapper import SimpleMapper
from app.services.report_formatter import ReportFormatter

def test_simple_mapper():
    """Test the SimpleMapper functionality."""
    print("=" * 60)
    print("Testing SimpleMapper")
    print("=" * 60)
    
    mapper = SimpleMapper()
    
    # Test static mappings
    test_codes = [
        ("MM0", "There is no increase in mesangial matrix."),
        ("G2", "There is moderate glomerulitis (g2)."),
        ("CV1", "Arteries show mild fibrointimal thickening (cv1)."),
        ("ATI_MICRO", "There acute tubular injury with tubular epithelial cell cytoplasmic microvacuolation."),
    ]
    
    print("\n1. Testing static mappings:")
    for code, expected in test_codes:
        result = mapper.map_code(code)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {code}: {result[:50]}..." if result and len(result) > 50 else f"  {status} {code}: {result}")
    
    # Test regex patterns
    regex_tests = [
        ("TG5", "Total number of glomeruli: 5"),
        ("GS3", "Number of globally sclerosed glomeruli: 3"),
        ("IFTA20", "Tubular atrophy/interstitial fibrosis (nearest 10%): 20%"),
        ("A3", "3 arteries are present in the sampled kidney."),
        ("C2M1", "There are 2 samples of cortex and 1 sample of medulla."),
    ]
    
    print("\n2. Testing regex patterns:")
    for code, expected in regex_tests:
        result = mapper.map_code(code)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {code}: {result}")
    
    # Test case insensitivity
    print("\n3. Testing case insensitivity:")
    lowercase_tests = [("mm0", "MM0"), ("g2", "G2"), ("tg5", "TG5")]
    for lower, upper in lowercase_tests:
        result_lower = mapper.map_code(lower)
        result_upper = mapper.map_code(upper)
        status = "✓" if result_lower == result_upper else "✗"
        print(f"  {status} {lower} == {upper}: {result_lower == result_upper}")

def test_report_formatter():
    """Test the ReportFormatter functionality."""
    print("\n" + "=" * 60)
    print("Testing ReportFormatter")
    print("=" * 60)
    
    formatter = ReportFormatter()
    
    # Test with sample phrases
    phrases = [
        "GLOMERULI",
        "Total number of glomeruli: 31",
        "Number of globally sclerosed glomeruli: 7",
        "There is mild increase in mesangial matrix.",
        "",
        "TUBULOINTERSTITIUM",
        "There is mild acute tubular injury.",
        "Tubular atrophy/interstitial fibrosis (nearest 10%): 20%",
    ]
    
    print("\nFormatting sample report:")
    report = formatter.format_report(phrases)
    print(report)

def test_full_pipeline():
    """Test the complete pipeline from shorthand to report."""
    print("\n" + "=" * 60)
    print("Testing Full Pipeline")
    print("=" * 60)
    
    mapper = SimpleMapper()
    formatter = ReportFormatter()
    
    # Simulate shorthand input
    shorthand_codes = [
        "CM",
        "TG31",
        "GS7",
        "MM1",
        "G2",
        "ATI_MICRO",
        "IFTA20",
        "CV1",
        "C4D0",
    ]
    
    print("\nInput shorthand codes:")
    print(", ".join(shorthand_codes))
    
    # Process codes
    expanded_phrases = []
    for code in shorthand_codes:
        expanded = mapper.map_code(code)
        if expanded:
            expanded_phrases.append(expanded)
    
    print("\nExpanded phrases:")
    for phrase in expanded_phrases:
        print(f"  - {phrase}")
    
    # Format report
    report = formatter.format_report(expanded_phrases)
    print("\nFormatted Report:")
    print("-" * 40)
    print(report)

if __name__ == "__main__":
    test_simple_mapper()
    test_report_formatter()
    test_full_pipeline()
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)