#!/usr/bin/env python3
"""
Simple batch processor that processes files one by one.
"""

import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path

def main():
    """Main function to process all PFR data."""
    print("Simple Batch Processor")
    print("=" * 25)
    
    # Input and output directories
    input_dir = "data/weekly_raw"
    output_dir = "data/simple_batch_processed"
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    
    if not csv_files:
        print("No CSV files found!")
        return
    
    print(f"Found {len(csv_files)} files to process")
    
    # Process each file individually
    successful_files = 0
    all_data = []
    
    for csv_file in csv_files:
        print(f"Processing {os.path.basename(csv_file)}...")
        
        try:
            # Read with a large number of columns to capture everything
            df = pd.read_csv(csv_file, header=None, names=range(50))
            
            # Get the actual column names from row 1
            column_names = df.iloc[1].values
            col_list = column_names.tolist()
            
            clean_column_names = []
            for i, col in enumerate(col_list):
                if pd.isna(col):
                    clean_column_names.append(f'col_{i}')
                else:
                    clean_column_names.append(str(col))
            
            # Create a clean dataframe starting from row 2
            data_df = df.iloc[2:].copy()
            data_df.columns = clean_column_names
            
            # Remove columns that are all NaN
            data_df = data_df.dropna(axis=1, how='all')
            
            # Reset index
            data_df = data_df.reset_index(drop=True)
            
            # Add metadata
            filename = os.path.basename(csv_file)
            player_id = filename.split('_')[0]
            season = filename.split('_')[1]
            
            data_df['player_id'] = player_id
            data_df['season'] = int(season)
            data_df['source_file'] = filename
            
            # Save individual file
            output_filename = f"processed_{filename}"
            output_path = os.path.join(output_dir, output_filename)
            data_df.to_csv(output_path, index=False)
            
            print(f"  ✓ Processed {len(data_df)} games with {len(data_df.columns)} columns")
            
            # Show what columns we found
            key_cols = ['Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'TD', 'Rec']
            found_key_cols = [col for col in key_cols if col in data_df.columns]
            print(f"  Key columns found: {found_key_cols}")
            
            all_data.append(data_df)
            successful_files += 1
            
        except Exception as e:
            print(f"  ✗ Error processing {csv_file}: {e}")
            continue
    
    if not all_data:
        print("No data could be processed!")
        return
    
    print(f"\n✅ Successfully processed {successful_files} files!")
    print(f"Files saved in: {output_dir}")
    
    # Try to combine all data
    print(f"\nAttempting to combine {successful_files} files...")
    try:
        combined_df = pd.concat(all_data, ignore_index=True, sort=False)
        
        # Save combined data
        output_file = os.path.join(output_dir, "all_combined_data.csv")
        combined_df.to_csv(output_file, index=False)
        
        print(f"Combined file: {output_file}")
        print(f"Total games: {len(combined_df)}")
        print(f"Total players: {combined_df['player_id'].nunique()}")
        print(f"Total columns: {len(combined_df.columns)}")
        
        # Show sample
        print(f"\nSample of combined data:")
        display_cols = ['player_id', 'Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'TD', 'Rec']
        available_cols = [col for col in display_cols if col in combined_df.columns]
        if available_cols:
            print(combined_df[available_cols].head(10).to_string(index=False))
        
        # Show stats summary
        if 'Att' in combined_df.columns:
            print(f"\nRushing stats summary:")
            print(f"Total rushing attempts: {combined_df['Att'].sum():.0f}")
            print(f"Total rushing yards: {combined_df['Yds'].sum():.0f}")
            print(f"Total rushing TDs: {combined_df['TD'].sum():.0f}")
        
    except Exception as e:
        print(f"Could not combine files: {e}")
        print("But individual files were processed successfully!")

if __name__ == "__main__":
    main()
