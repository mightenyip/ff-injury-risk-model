#!/usr/bin/env python3
"""
Simple data processor for the PFR weekly data.
This script processes the data as-is without trying to restructure it.
"""

import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path

def process_single_file(file_path):
    """Process a single CSV file."""
    print(f"Processing {os.path.basename(file_path)}...")
    
    try:
        # Read the CSV
        df = pd.read_csv(file_path)
        
        # Add metadata
        filename = os.path.basename(file_path)
        player_id = filename.split('_')[0]
        season = filename.split('_')[1]
        
        # Add player info to every row
        df['player_id'] = player_id
        df['season'] = int(season)
        df['source_file'] = filename
        
        print(f"  ✓ Processed {len(df)} rows")
        return df
        
    except Exception as e:
        print(f"  ✗ Error processing {file_path}: {e}")
        return None

def main():
    """Main function to process all weekly data."""
    print("Simple Weekly Data Processor")
    print("=" * 40)
    
    # Input and output directories
    input_dir = "data/weekly_raw"
    output_dir = "data/weekly_processed"
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    
    if not csv_files:
        print("No CSV files found in", input_dir)
        return
    
    print(f"Found {len(csv_files)} CSV files to process")
    
    # Process each file
    processed_data = []
    successful_files = 0
    
    for csv_file in csv_files:
        processed_df = process_single_file(csv_file)
        if processed_df is not None:
            processed_data.append(processed_df)
            successful_files += 1
    
    if not processed_data:
        print("No files could be processed successfully!")
        return
    
    # Save each file individually first
    print(f"\nSaving {successful_files} processed files...")
    for i, df in enumerate(processed_data):
        filename = df['source_file'].iloc[0]
        output_file = os.path.join(output_dir, f"processed_{filename}")
        df.to_csv(output_file, index=False)
        print(f"  ✓ Saved {filename}")
    
    # Try to combine them
    print(f"\nAttempting to combine files...")
    try:
        # Use a simple approach - just concatenate
        combined_df = pd.concat(processed_data, ignore_index=True, sort=False)
        
        # Save combined data
        output_file = os.path.join(output_dir, "all_processed_data.csv")
        combined_df.to_csv(output_file, index=False)
        
        print(f"✅ Successfully processed and saved data!")
        print(f"Combined output file: {output_file}")
        print(f"Total rows: {len(combined_df)}")
        print(f"Total players: {combined_df['player_id'].nunique()}")
        print(f"Columns: {list(combined_df.columns)}")
        
        # Show sample
        print(f"\nSample of processed data:")
        print(combined_df[['player_id', 'season', 'source_file']].head(10).to_string(index=False))
        
    except Exception as e:
        print(f"Could not combine files: {e}")
        print("But individual files were saved successfully!")

if __name__ == "__main__":
    main()
