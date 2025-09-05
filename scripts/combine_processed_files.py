#!/usr/bin/env python3
"""
Combine the individually processed files into a final dataset.
"""

import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path

def main():
    """Main function to combine processed files."""
    print("Combining Processed Files")
    print("=" * 30)
    
    # Input and output directories
    input_dir = "data/simple_batch_processed"
    output_dir = "data/final_combined"
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all processed CSV files
    csv_files = glob.glob(os.path.join(input_dir, "processed_*.csv"))
    
    if not csv_files:
        print("No processed CSV files found!")
        return
    
    print(f"Found {len(csv_files)} processed files to combine")
    
    # Read all files
    all_data = []
    for csv_file in csv_files:
        print(f"Reading {os.path.basename(csv_file)}...")
        try:
            df = pd.read_csv(csv_file)
            all_data.append(df)
            print(f"  ✓ Read {len(df)} games with {len(df.columns)} columns")
        except Exception as e:
            print(f"  ✗ Error reading {csv_file}: {e}")
            continue
    
    if not all_data:
        print("No data could be read!")
        return
    
    # Combine all data
    print(f"\nCombining {len(all_data)} files...")
    
    # Get all unique columns
    all_columns = set()
    for df in all_data:
        all_columns.update(df.columns)
    
    all_columns = sorted(list(all_columns))
    print(f"Total unique columns: {len(all_columns)}")
    
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
    
    # Save the combined data
    output_file = os.path.join(output_dir, "final_combined_data.csv")
    combined_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Successfully combined all game data!")
    print(f"Output file: {output_file}")
    print(f"Total games: {len(combined_df)}")
    print(f"Total players: {combined_df['player_id'].nunique()}")
    print(f"Total columns: {len(combined_df.columns)}")
    
    # Show sample
    print(f"\nSample of combined data:")
    display_cols = ['player_id', 'Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'TD', 'Rec', 'injured']
    available_cols = [col for col in display_cols if col in combined_df.columns]
    if available_cols:
        print(combined_df[available_cols].head(10).to_string(index=False))
    
    # Show injury summary
    if 'injured' in combined_df.columns:
        injury_summary = combined_df.groupby('player_id')['injured'].sum().sort_values(ascending=False)
        print(f"\nInjury summary (games missed per player):")
        print(injury_summary.head(10).to_string())
    
    # Show stats summary
    if 'Att' in combined_df.columns:
        print(f"\nRushing stats summary:")
        print(f"Total rushing attempts: {combined_df['Att'].sum():.0f}")
        print(f"Total rushing yards: {combined_df['Yds'].sum():.0f}")
        print(f"Total rushing TDs: {combined_df['TD'].sum():.0f}")
    
    # Show player summary
    print(f"\nPlayer summary:")
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

if __name__ == "__main__":
    main()
