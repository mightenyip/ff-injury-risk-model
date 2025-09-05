#!/usr/bin/env python3
"""
Process 2023 season data using the same approach that worked for 2024.
"""

import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path

def parse_single_file(filepath):
    """Parse a single CSV file using the working approach from 2024."""
    try:
        # Read the CSV, assuming no header initially to inspect raw rows
        df_raw = pd.read_csv(filepath, header=None)
        print(f"  Raw shape: {df_raw.shape}")

        # Identify the header row (usually the second row, index 1)
        # and the actual data start row (usually the third row, index 2)
        column_names_row = df_raw.iloc[1].values
        data_start_row_index = 2

        # Clean column names: remove NaN, combine multi-level headers if necessary
        # For PFR, the first row often contains category headers (Rushing, Receiving)
        # and the second row contains specific stat headers (Att, Yds, TD)
        # We need to combine them or select the most granular ones.

        # Let's try to reconstruct headers from the first two rows
        # The first row has broad categories, the second has specific stats
        # We need to handle the case where a category spans multiple specific stats
        header_row_0 = df_raw.iloc[0].fillna('').astype(str).values
        header_row_1 = df_raw.iloc[1].fillna('').astype(str).values

        # Create a list for final column names
        final_columns = []
        current_category = ""
        for i in range(len(header_row_1)):
            # If header_row_0 has a value, it's a new category
            if header_row_0[i] and header_row_0[i] != 'nan' and header_row_0[i] != 'Unnamed: 0':
                current_category = header_row_0[i].strip()
            
            col_name = header_row_1[i].strip()
            if col_name == 'nan' or col_name == '': # Skip empty or NaN columns
                final_columns.append(f'col_{i}') # Placeholder for now
                continue

            if current_category and current_category not in ['Unnamed: 0', 'Fumbles', 'Snap Counts', 'Kick Returns', 'Punt Returns', 'Passing']:
                # Avoid duplicating category name if it's already part of the specific stat
                if not col_name.startswith(current_category):
                    final_columns.append(f'{current_category}_{col_name}')
                else:
                    final_columns.append(col_name)
            else:
                final_columns.append(col_name)
        
        # Remove duplicate column names by appending a suffix
        seen = {}
        for i, col in enumerate(final_columns):
            if col in seen:
                seen[col] += 1
                final_columns[i] = f"{col}_{seen[col]}"
            else:
                seen[col] = 1

        # Read the data starting from the third row (index 2) with the new column names
        data_df = pd.read_csv(filepath, skiprows=2, header=None)
        
        # Ensure the number of columns matches
        if len(final_columns) != data_df.shape[1]:
            print(f"  Warning: Column count mismatch. Expected {len(final_columns)}, got {data_df.shape[1]}. Adjusting columns.")
            # If data_df has more columns, truncate final_columns or vice versa
            if len(final_columns) > data_df.shape[1]:
                final_columns = final_columns[:data_df.shape[1]]
            else: # data_df has fewer columns, pad final_columns
                final_columns.extend([f'extra_col_{j}' for j in range(data_df.shape[1] - len(final_columns))])

        data_df.columns = final_columns
        
        # Add player_id and season from filename
        filename = os.path.basename(filepath)
        parts = filename.replace('_gamelog.csv', '').split('_')
        player_id = parts[0]
        season = int(parts[1])
        data_df['player_id'] = player_id
        data_df['season'] = season
        data_df['source_file'] = filename

        # Drop rows that are just headers repeated in the middle of the table
        data_df = data_df[data_df['Rk'].astype(str).str.lower() != 'rk']
        data_df = data_df[data_df['Rk'].astype(str).str.lower() != 'nan'] # Remove rows with NaN in Rk

        # Identify key columns for display
        key_columns = ['Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'TD', 'Rec']
        found_key_columns = [col for col in key_columns if col in data_df.columns]
        
        print(f"  ✓ Parsed {len(data_df)} games with {len(data_df.columns)} columns")
        print(f"  Key columns found: {found_key_columns}")
        print("  Sample data:")
        print(data_df[found_key_columns].head(3).to_string())
        
        return data_df

    except Exception as e:
        print(f"  ✗ Error parsing {filepath}: {e}")
        return None

def process_2023_data():
    """Process all 2023 CSV files."""
    print("Processing 2023 Season Data")
    print("=" * 30)
    
    input_dir = "data/weekly_raw_2023"
    output_dir = "data/processed_2023"
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {input_dir}!")
        return
    
    print(f"Found {len(csv_files)} files to process")
    
    # Process each file individually and save
    all_dataframes = []
    successful_files = 0
    
    for csv_file in csv_files:
        print(f"Processing {os.path.basename(csv_file)}...")
        
        parsed_df = parse_single_file(csv_file)
        if parsed_df is not None:
            # Save individual processed file
            filename = os.path.basename(csv_file)
            output_filename = f"processed_{filename}"
            output_path = os.path.join(output_dir, output_filename)
            parsed_df.to_csv(output_path, index=False)
            
            all_dataframes.append(parsed_df)
            successful_files += 1
        else:
            print(f"  ✗ Failed to process {csv_file}")
    
    if not all_dataframes:
        print("No dataframes could be processed.")
        return
    
    print(f"\nCombining {successful_files} files for 2023...")
    
    # Get all unique columns
    all_columns = set()
    for df in all_dataframes:
        all_columns.update(df.columns)
    
    all_columns = sorted(list(all_columns))
    print(f"Total unique columns: {len(all_columns)}")
    
    # Standardize all dataframes
    standardized_dfs = []
    for df in all_dataframes:
        df_copy = df.copy()
        for col in all_columns:
            if col not in df_copy.columns:
                df_copy[col] = np.nan
        df_copy = df_copy[all_columns]
        standardized_dfs.append(df_copy)
    
    # Combine all dataframes
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
    
    # Save the combined data for 2023
    output_file = os.path.join(output_dir, "2023_combined_data.csv")
    combined_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Successfully processed 2023 season data!")
    print(f"Output file: {output_file}")
    print(f"Total games: {len(combined_df)}")
    print(f"Total players: {combined_df['player_id'].nunique()}")
    print(f"Total columns: {len(combined_df.columns)}")
    
    # Show sample
    print(f"\nSample of 2023 data:")
    display_cols = ['player_id', 'Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'TD', 'Rec', 'injured']
    available_cols = [col for col in display_cols if col in combined_df.columns]
    if available_cols:
        print(combined_df[available_cols].head(5).to_string(index=False))
    
    # Show injury summary
    print(f"\nInjury summary for 2023:")
    injury_summary = combined_df.groupby('player_id')['injured'].sum().sort_values(ascending=False)
    print(injury_summary[injury_summary > 0].to_string())
    
    return combined_df

def main():
    """Main function."""
    process_2023_data()

if __name__ == "__main__":
    main()
