#!/usr/bin/env python3
'''
Process data for a specific season.
Usage: python3 scripts/process_season_data.py --season 2023
'''

import pandas as pd
import numpy as np
import os
import glob
import argparse
from pathlib import Path

def process_season_data(season):
    """Process data for a specific season."""
    print(f"Processing {season} season data...")
    
    # Input and output directories
    input_dir = f"data/weekly_raw_{season}"
    output_dir = f"data/processed_{season}"
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {input_dir}!")
        return
    
    print(f"Found {len(csv_files)} files to process")
    
    # Process each file
    all_data = []
    successful_files = 0
    
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
            season_year = filename.split('_')[1]
            
            data_df['player_id'] = player_id
            data_df['season'] = int(season_year)
            data_df['source_file'] = filename
            
            # Save individual file
            output_filename = f"processed_{filename}"
            output_path = os.path.join(output_dir, output_filename)
            data_df.to_csv(output_path, index=False)
            
            print(f"  ✓ Processed {len(data_df)} games with {len(data_df.columns)} columns")
            
            all_data.append(data_df)
            successful_files += 1
            
        except Exception as e:
            print(f"  ✗ Error processing {csv_file}: {e}")
            continue
    
    if not all_data:
        print("No data could be processed!")
        return
    
    # Combine all data for this season
    print(f"\nCombining {successful_files} files for {season}...")
    
    # Get all unique columns
    all_columns = set()
    for df in all_data:
        all_columns.update(df.columns)
    
    all_columns = sorted(list(all_columns))
    
    # Standardize all dataframes
    standardized_dfs = []
    for df in all_data:
        df_copy = df.copy()
        for col in all_columns:
            if col not in df_copy.columns:
                df_copy[col] = np.nan
        df_copy = df_copy[all_columns]
        standardized_dfs.append(df_copy)
    
    # Combine
    combined_df = pd.concat(standardized_dfs, ignore_index=True)
    
    # Create injury indicators
    print("Creating injury indicators...")
    combined_df['injured'] = False
    
    # Check for injury indicators
    injury_indicators = ['Did Not Play', 'Inactive', 'Injured Reserve', 'PUP', 'Suspended']
    
    for col in ['GS', 'Result', 'Team']:
        if col in combined_df.columns:
            for indicator in injury_indicators:
                combined_df.loc[combined_df[col].astype(str).str.contains(indicator, case=False, na=False), 'injured'] = True
    
    # Also check if key stats are missing (might indicate injury)
    if 'Att' in combined_df.columns and 'Rec' in combined_df.columns:
        combined_df.loc[(combined_df['Att'].isna() | (combined_df['Att'] == 0)) & (combined_df['Rec'].isna() | (combined_df['Rec'] == 0)), 'injured'] = True
    
    # Save the combined data for this season
    output_file = os.path.join(output_dir, f"{season}_combined_data.csv")
    combined_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Successfully processed {season} season data!")
    print(f"Output file: {output_file}")
    print(f"Total games: {len(combined_df)}")
    print(f"Total players: {combined_df['player_id'].nunique()}")
    print(f"Total columns: {len(combined_df.columns)}")
    
    # Show sample
    print(f"\nSample of {season} data:")
    display_cols = ['player_id', 'Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'TD', 'Rec', 'injured']
    available_cols = [col for col in display_cols if col in combined_df.columns]
    if available_cols:
        print(combined_df[available_cols].head(5).to_string(index=False))

def main():
    parser = argparse.ArgumentParser(description='Process data for a specific season')
    parser.add_argument('--season', required=True, help='Season year (e.g., 2023)')
    
    args = parser.parse_args()
    process_season_data(args.season)

if __name__ == "__main__":
    main()
