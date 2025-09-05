#!/usr/bin/env python3
"""
Simple parser for PFR data that handles the structure correctly.
"""

import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path

def parse_single_file(file_path):
    """Parse a single PFR CSV file."""
    print(f"Parsing {os.path.basename(file_path)}...")
    
    try:
        # Read the CSV
        df = pd.read_csv(file_path)
        
        # Get column names from row 1
        column_names = df.iloc[1].values
        
        # Clean column names
        clean_columns = []
        for col in column_names:
            if pd.isna(col):
                clean_columns.append('Unknown')
            else:
                clean_columns.append(str(col).strip())
        
        # Create clean dataframe starting from row 2
        clean_df = df.iloc[2:].copy()
        clean_df.columns = clean_columns
        
        # Reset index
        clean_df = clean_df.reset_index(drop=True)
        
        # Add metadata
        filename = os.path.basename(file_path)
        player_id = filename.split('_')[0]
        season = filename.split('_')[1]
        
        clean_df['player_id'] = player_id
        clean_df['season'] = int(season)
        clean_df['source_file'] = filename
        
        print(f"  ✓ Parsed {len(clean_df)} games")
        return clean_df
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None

def main():
    """Main function."""
    print("Simple PFR Data Parser")
    print("=" * 25)
    
    # Input and output directories
    input_dir = "data/weekly_raw"
    output_dir = "data/simple_parsed"
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    
    if not csv_files:
        print("No CSV files found!")
        return
    
    print(f"Found {len(csv_files)} files")
    
    # Process each file individually
    successful_files = 0
    
    for csv_file in csv_files:
        parsed_df = parse_single_file(csv_file)
        if parsed_df is not None:
            # Save individual file
            filename = os.path.basename(csv_file)
            output_file = os.path.join(output_dir, f"parsed_{filename}")
            parsed_df.to_csv(output_file, index=False)
            successful_files += 1
    
    print(f"\n✅ Successfully parsed {successful_files} files!")
    print(f"Files saved in: {output_dir}")
    
    # Try to combine them
    print("\nAttempting to combine files...")
    try:
        all_files = glob.glob(os.path.join(output_dir, "parsed_*.csv"))
        if all_files:
            # Read first file to get structure
            first_df = pd.read_csv(all_files[0])
            print(f"Sample columns from first file: {list(first_df.columns)}")
            
            # Show sample data
            print(f"\nSample data from {os.path.basename(all_files[0])}:")
            print(first_df.head(3).to_string())
            
    except Exception as e:
        print(f"Could not combine files: {e}")

if __name__ == "__main__":
    main()
