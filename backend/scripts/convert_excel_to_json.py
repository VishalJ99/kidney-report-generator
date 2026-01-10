#!/usr/bin/env python3
"""
Convert Excel phrases file to JSON with section-specific structure.

Output structure:
{
  "key": {
    "main_body": "value for main body",
    "conclusion": "value for conclusion",
    "comments": "value for comments",
    "codes": { "transplant": "...", "native1": "...", "native2": "...", "kbc": "..." }
  }
}

- If key only exists in one section, only that section key is present
- If key exists in multiple sections with SAME value, all section keys have same value
- If key exists in multiple sections with DIFFERENT values, each has its own value
- codes is always present (empty {} if no codes)
"""

import argparse
import json
import pandas as pd
from pathlib import Path


def normalize_key(key: str) -> str:
    """Normalize key to lowercase, preserving regex patterns."""
    if pd.isna(key):
        return None
    key = str(key).strip()
    # Keep regex prefix ~ if present
    if key.startswith('~'):
        return key  # Keep as-is for regex patterns
    return key.lower()


def clean_value(value) -> str:
    """Clean and return value as string."""
    if pd.isna(value):
        return None
    return str(value).strip()


def read_main_body(xlsx_path: str) -> dict:
    """Read MAIN BODY sheet and return key -> value mapping."""
    df = pd.read_excel(xlsx_path, sheet_name='MAIN BODY', skiprows=4, header=None)
    df.columns = ['Notes', 'Key', 'Value']

    mappings = {}
    for _, row in df.iterrows():
        key = normalize_key(row['Key'])
        value = clean_value(row['Value'])
        if key and value:
            mappings[key] = value

    return mappings


def read_conclusion(xlsx_path: str) -> tuple[dict, dict]:
    """Read CONCLUSION sheet and return (key -> value, key -> codes) mappings."""
    df = pd.read_excel(xlsx_path, sheet_name='CONCLUSION', skiprows=2, header=None)
    df.columns = ['Key', 'Value', 'Code_Transplant', 'Code_Native1', 'Code_Native2', 'KBC_Code', 'Extra']

    mappings = {}
    codes = {}

    for _, row in df.iterrows():
        key = normalize_key(row['Key'])
        value = clean_value(row['Value'])

        if key and value:
            mappings[key] = value

            # Extract codes
            code_dict = {}
            if pd.notna(row['Code_Transplant']) and str(row['Code_Transplant']).strip():
                code_dict['transplant'] = str(row['Code_Transplant']).strip()
            if pd.notna(row['Code_Native1']) and str(row['Code_Native1']).strip():
                code_dict['native1'] = str(row['Code_Native1']).strip()
            if pd.notna(row['Code_Native2']) and str(row['Code_Native2']).strip():
                code_dict['native2'] = str(row['Code_Native2']).strip()
            if pd.notna(row['KBC_Code']) and str(row['KBC_Code']).strip():
                code_dict['kbc'] = str(row['KBC_Code']).strip()

            codes[key] = code_dict

    return mappings, codes


def read_comments(xlsx_path: str) -> dict:
    """Read COMMENTS sheet and return key -> value mapping."""
    df = pd.read_excel(xlsx_path, sheet_name='COMMENTS', skiprows=1, header=None)
    df.columns = ['Key', 'Value']

    mappings = {}
    for _, row in df.iterrows():
        key = normalize_key(row['Key'])
        value = clean_value(row['Value'])
        if key and value:
            mappings[key] = value

    return mappings


def merge_to_sectioned(main_body: dict, conclusion: dict, conclusion_codes: dict, comments: dict) -> dict:
    """
    Merge all sections into unified structure.

    Each key gets a dictionary with:
    - All 3 section keys (main_body, conclusion, comments) always present
    - Value is the actual value if key exists in that section's Excel sheet
    - Value is empty string "" if key doesn't exist in that section
    - codes: {} or actual codes dict

    Frontend logic: if value is empty string, return the original key (no expansion)
    """
    # Get all unique keys
    all_keys = set(main_body.keys()) | set(conclusion.keys()) | set(comments.keys())

    result = {}

    for key in sorted(all_keys):
        entry = {
            'main_body': main_body.get(key, ""),
            'conclusion': conclusion.get(key, ""),
            'comments': comments.get(key, ""),
            'codes': conclusion_codes.get(key, {})
        }

        result[key] = entry

    return result


def main():
    parser = argparse.ArgumentParser(description='Convert Excel phrases to JSON')
    parser.add_argument('--input', '-i',
                        default='backend/app/data/phrases_flat v4 2026_01_09.xlsx',
                        help='Input Excel file path')
    parser.add_argument('--output', '-o',
                        default='backend/app/data/phrases_sectioned.json',
                        help='Output JSON file path')
    parser.add_argument('--preview', '-p', action='store_true',
                        help='Preview output without writing file')

    args = parser.parse_args()

    print(f"Reading Excel file: {args.input}")

    # Read all sheets
    main_body = read_main_body(args.input)
    print(f"  MAIN BODY: {len(main_body)} entries")

    conclusion, conclusion_codes = read_conclusion(args.input)
    print(f"  CONCLUSION: {len(conclusion)} entries, {sum(1 for c in conclusion_codes.values() if c)} with codes")

    comments = read_comments(args.input)
    print(f"  COMMENTS: {len(comments)} entries")

    # Merge into sectioned structure
    result = merge_to_sectioned(main_body, conclusion, conclusion_codes, comments)
    print(f"\nTotal unique keys: {len(result)}")

    # Count section-specific keys
    section_specific = sum(1 for k, v in result.items()
                          if v.get('main_body') != v.get('conclusion') or
                             v.get('conclusion') != v.get('comments'))
    print(f"Section-specific keys (different values): {section_specific}")

    if args.preview:
        # Show a few examples
        print("\n=== PREVIEW ===")
        examples = ['cm', 't3', 'ati', 'nr', 'norm', '!conc']
        for ex in examples:
            if ex in result:
                print(f"\n{ex}:")
                print(json.dumps(result[ex], indent=2))
    else:
        # Write to file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"\nWritten to: {args.output}")


if __name__ == '__main__':
    main()
