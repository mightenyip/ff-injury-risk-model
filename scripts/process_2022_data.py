#!/usr/bin/env python3
"""
Process 2022 season data using the same approach that worked for 2023.
"""

import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path

def parse_2022_file(filepath):
    """Parse a 2022 CSV file with the same approach as 2023."""
    try:
        # Read the file with pandas, handling the multi-level headers
        # Skip the first row (category headers) and use the second row as column names
        df = pd.read_csv(filepath, skiprows=1, header=0)
        
        # Clean up column names (remove quotes and extra spaces)
        df.columns = [col.strip('"').strip() for col in df.columns]
        
        # Add metadata
        filename = os.path.basename(filepath)
        parts = filename.replace('_gamelog.csv', '').split('_')
        player_id = parts[0]
        season = int(parts[1])
        df['player_id'] = player_id
        df['season'] = season
        df['source_file'] = filename
        
        # Clean up the data
        # Remove rows that are just headers repeated
        if 'Rk' in df.columns:
            df = df[df['Rk'].astype(str).str.lower() != 'rk']
            df = df[df['Rk'].astype(str).str.lower() != 'nan']
            df = df[df['Rk'].astype(str).str.lower() != '']
        
        # Convert numeric columns
        numeric_cols = ['Week', 'Att', 'Yds', 'TD', 'Rec', 'Y/A', 'Tgt', 'Y/R', 'Ctch%', 'Y/Tgt']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        print(f"  ✓ Parsed {len(df)} games with {len(df.columns)} columns")
        
        # Show key columns
        key_columns = ['Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'TD', 'Rec']
        found_key_columns = [col for col in key_columns if col in df.columns]
        if found_key_columns and len(df) > 0:
            print(f"  Key columns: {found_key_columns}")
            print("  Sample data:")
            print(df[found_key_columns].head(3).to_string())
        
        return df
        
    except Exception as e:
        print(f"  ✗ Error parsing {filepath}: {e}")
        return None

def process_2022_data():
    """Process all 2022 CSV files."""
    print("Processing 2022 Season Data")
    print("=" * 30)
    
    input_dir = "data/weekly_raw_2022"
    output_dir = "data/processed_2022"
    
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
        
        parsed_df = parse_2022_file(csv_file)
        if parsed_df is not None and len(parsed_df) > 0:
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
    
    print(f"\nCombining {successful_files} files for 2022...")
    
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
    
    # Save the combined data for 2022
    output_file = os.path.join(output_dir, "2022_combined_data.csv")
    combined_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Successfully processed 2022 season data!")
    print(f"Output file: {output_file}")
    print(f"Total games: {len(combined_df)}")
    print(f"Total players: {combined_df['player_id'].nunique()}")
    print(f"Total columns: {len(combined_df.columns)}")
    
    # Show sample
    print(f"\nSample of 2022 data:")
    display_cols = ['player_id', 'Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'TD', 'Rec', 'injured']
    available_cols = [col for col in display_cols if col in combined_df.columns]
    if available_cols:
        print(combined_df[available_cols].head(5).to_string(index=False))
    
    # Show injury summary
    print(f"\nInjury summary for 2022:")
    injury_summary = combined_df.groupby('player_id')['injured'].sum().sort_values(ascending=False)
    print(injury_summary[injury_summary > 0].to_string())
    
    # Show player summary (only if columns exist)
    print(f"\nPlayer summary for 2022:")
    summary_cols = {}
    if 'Week' in combined_df.columns:
        summary_cols['Games'] = ('Week', 'count')
    if 'Att' in combined_df.columns:
        summary_cols['Rush_Att'] = ('Att', 'sum')
    if 'Yds' in combined_df.columns:
        summary_cols['Rush_Yds'] = ('Yds', 'sum')
    if 'TD' in combined_df.columns:
        summary_cols['Rush_TD'] = ('TD', 'sum')
    if 'Rec' in combined_df.columns:
        summary_cols['Rec'] = ('Rec', 'sum')
    if 'injured' in combined_df.columns:
        summary_cols['Injured_Games'] = ('injured', 'sum')
    
    if summary_cols:
        agg_dict = {col: (orig_col, func) for col, (orig_col, func) in summary_cols.items()}
        player_summary = combined_df.groupby('player_id').agg(agg_dict).round(1)
        print(player_summary.head(10).to_string())
    
    return combined_df

def main():
    """Main function."""
    process_2022_data()

if __name__ == "__main__":
    main()
