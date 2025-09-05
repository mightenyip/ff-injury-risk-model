#!/usr/bin/env python3
"""
Process 2023 season data with the correct CSV format handling.
"""

import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path

def parse_2023_file(filepath):
    """Parse a 2023 CSV file with the correct format."""
    try:
        # Read the CSV with the correct format
        # Row 0: Category headers (Rushing, Receiving, Fumbles, Snap Counts)
        # Row 1: Specific stat headers (Rk, Gcar, Gtm, Week, Date, Team, etc.)
        # Row 2+: Data
        
        # First, read just the first two rows to get headers
        header_df = pd.read_csv(filepath, nrows=2, header=None)
        
        # Get category headers (row 0)
        category_headers = header_df.iloc[0].fillna('').astype(str).values
        # Get specific headers (row 1)
        specific_headers = header_df.iloc[1].fillna('').astype(str).values
        
        # Combine headers
        final_headers = []
        current_category = ""
        
        for i in range(len(specific_headers)):
            # If category header exists and is not empty
            if i < len(category_headers) and category_headers[i] and category_headers[i] != 'nan':
                current_category = category_headers[i].strip()
            
            specific_header = specific_headers[i].strip()
            
            # Skip empty headers
            if not specific_header or specific_header == 'nan':
                final_headers.append(f'col_{i}')
                continue
            
            # Combine category and specific header if category exists
            if current_category and current_category not in ['', 'nan']:
                if specific_header.startswith(current_category):
                    final_headers.append(specific_header)
                else:
                    final_headers.append(f'{current_category}_{specific_header}')
            else:
                final_headers.append(specific_header)
        
        # Remove duplicate headers
        seen = {}
        for i, header in enumerate(final_headers):
            if header in seen:
                seen[header] += 1
                final_headers[i] = f"{header}_{seen[header]}"
            else:
                seen[header] = 1
        
        # Now read the data starting from row 2
        data_df = pd.read_csv(filepath, skiprows=2, header=None)
        
        # Ensure column count matches
        if len(final_headers) != data_df.shape[1]:
            if len(final_headers) > data_df.shape[1]:
                final_headers = final_headers[:data_df.shape[1]]
            else:
                final_headers.extend([f'extra_col_{j}' for j in range(data_df.shape[1] - len(final_headers))])
        
        data_df.columns = final_headers
        
        # Add metadata
        filename = os.path.basename(filepath)
        parts = filename.replace('_gamelog.csv', '').split('_')
        player_id = parts[0]
        season = int(parts[1])
        data_df['player_id'] = player_id
        data_df['season'] = season
        data_df['source_file'] = filename
        
        # Clean up the data
        # Remove rows that are just headers repeated
        if 'Rk' in data_df.columns:
            data_df = data_df[data_df['Rk'].astype(str).str.lower() != 'rk']
            data_df = data_df[data_df['Rk'].astype(str).str.lower() != 'nan']
        
        # Convert numeric columns
        numeric_cols = ['Week', 'Att', 'Yds', 'TD', 'Rec', 'Y/A', 'Tgt', 'Y/R', 'Ctch%', 'Y/Tgt']
        for col in numeric_cols:
            if col in data_df.columns:
                data_df[col] = pd.to_numeric(data_df[col], errors='coerce')
        
        print(f"  ✓ Parsed {len(data_df)} games with {len(data_df.columns)} columns")
        
        # Show key columns
        key_columns = ['Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'TD', 'Rec']
        found_key_columns = [col for col in key_columns if col in data_df.columns]
        if found_key_columns:
            print(f"  Key columns: {found_key_columns}")
            print("  Sample data:")
            print(data_df[found_key_columns].head(3).to_string())
        
        return data_df
        
    except Exception as e:
        print(f"  ✗ Error parsing {filepath}: {e}")
        return None

def process_2023_data():
    """Process all 2023 CSV files."""
    print("Processing 2023 Season Data (Fixed)")
    print("=" * 40)
    
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
        
        parsed_df = parse_2023_file(csv_file)
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
    
    # Show player summary
    print(f"\nPlayer summary for 2023:")
    player_summary = combined_df.groupby('player_id').agg({
        'Week': 'count',
        'Att': 'sum',
        'Yds': 'sum',
        'TD': 'sum',
        'Rec': 'sum',
        'injured': 'sum'
    }).round(1)
    player_summary.columns = ['Games', 'Rush_Att', 'Rush_Yds', 'Rush_TD', 'Rec', 'Injured_Games']
    print(player_summary.head(10).to_string())
    
    return combined_df

def main():
    """Main function."""
    process_2023_data()

if __name__ == "__main__":
    main()
