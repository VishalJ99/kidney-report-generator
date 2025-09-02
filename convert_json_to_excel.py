#!/usr/bin/env python3
"""
Convert phrases_flat.json to Excel format with keys and values in separate columns.
"""

import json
import pandas as pd
import argparse

def convert_json_to_excel(json_file_path, excel_file_path):
    """Convert JSON file to Excel with keys and values in separate columns."""
    
    # Read the JSON file
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    # Create DataFrame with keys and values
    df = pd.DataFrame(list(data.items()), columns=['Key', 'Value'])
    
    # Write to Excel
    df.to_excel(excel_file_path, index=False)
    print(f"Successfully converted {json_file_path} to {excel_file_path}")
    print(f"Total entries: {len(df)}")

def main():
    parser = argparse.ArgumentParser(description='Convert phrases_flat.json to Excel format')
    parser.add_argument('--input', '-i', default='backend/app/data/phrases_flat.json',
                       help='Input JSON file path (default: backend/app/data/phrases_flat.json)')
    parser.add_argument('--output', '-o', default='phrases_flat.xlsx',
                       help='Output Excel file path (default: phrases_flat.xlsx)')
    
    args = parser.parse_args()
    
    convert_json_to_excel(args.input, args.output)

if __name__ == '__main__':
    main()