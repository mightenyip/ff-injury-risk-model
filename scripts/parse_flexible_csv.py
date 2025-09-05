#!/usr/bin/env python3
"""
Parse PFR CSV files with flexible column handling.
The CSV files have more columns than headers, so we need to handle this properly.
"""

import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path

def parse_flexible_csv(file_path):
    """Parse a PFR CSV file with flexible column handling."""
    print(f"Parsing {os.path.basename(file_path)}...")
    
    try:
        # First, let's read the file as text to understand the structure
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        print(f"  File has {len(lines)} lines")
        
        # Read with a large number of columns to capture everything
        df = pd.read_csv(file_path, header=None, names=range(50))  # Assume max 50 columns
        
        print(f"  Raw shape: {df.shape}")
        
        # The structure is:
        # Row 0: Column group headers (like "Rushing", "Receiving", etc.)
        # Row 1: Actual column names
        # Row 2+: Data
        
        # Get the actual column names from row 1
        column_names = df.iloc[1].values
        
        # Remove NaN values from column names
        column_names = [str(col) if not pd.isna(col) else f'col_{i}' for i, col in enumerate(column_names)]
        
        # Create a clean dataframe starting from row 2
        data_df = df.iloc[2:].copy()
        data_df.columns = column_names
        
        # Remove columns that are all NaN
        data_df = data_df.dropna(axis=1, how='all')
        
        # Reset index
        data_df = data_df.reset_index(drop=True)
        
        # Add metadata
        filename = os.path.basename(file_path)
        player_id = filename.split('_')[0]
        season = filename.split('_')[1]
        
        data_df['player_id'] = player_id
        data_df['season'] = int(season)
        data_df['source_file'] = filename
        
        # Clean up the data
        data_df = clean_data_types(data_df)
        
        print(f"  ✓ Parsed {len(data_df)} games with {len(data_df.columns)} columns")
        print(f"  Key columns found: {[col for col in ['Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'TD', 'Rec'] if col in data_df.columns]}")
        
        return data_df
        
    except Exception as e:
        print(f"  ✗ Error parsing {file_path}: {e}")
        return None

def clean_data_types(df):
    """Clean and convert data types."""
    # Convert numeric columns
    numeric_columns = ['Rk', 'Gcar', 'Gtm', 'Week', 'Att', 'Yds', 'TD', 'Y/A', 'Tgt', 'Rec', 'Y/R', 'Ctch%', 'Y/Tgt', 'Fmb', 'FL', 'FF', 'FR', 'FRTD', 'OffSnp', 'Off%', 'DefSnp', 'Def%', 'STSnp', 'ST%', 'Cmp', 'Int', 'Sk']
    
    for col in numeric_columns:
        if col in df.columns:
            # Replace empty strings and 'NaN' with actual NaN
            df[col] = df[col].replace(['', 'NaN', 'nan', 'Did Not Play'], np.nan)
            # Convert to numeric, errors='coerce' will turn non-numeric to NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Clean date column
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # Clean text columns
    text_columns = ['Team', 'Opp', 'Result', 'GS']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).replace('nan', np.nan)
    
    return df

def create_injury_indicators(df):
    """Create injury indicators from the data."""
    # A player is considered injured if they have "Did Not Play" or similar indicators
    injury_indicators = [
        'Did Not Play',
        'Inactive',
        'Injured Reserve',
        'PUP',
        'Suspended'
    ]
    
    # Check various columns for injury indicators
    df['injured'] = False
    
    for col in ['GS', 'Result', 'Team']:
        if col in df.columns:
            for indicator in injury_indicators:
                df.loc[df[col].astype(str).str.contains(indicator, case=False, na=False), 'injured'] = True
    
    # Also check if key stats are missing (might indicate injury)
    if 'Att' in df.columns and 'Rec' in df.columns:
        df.loc[(df['Att'].isna() | (df['Att'] == 0)) & (df['Rec'].isna() | (df['Rec'] == 0)), 'injured'] = True
    
    return df

def main():
    """Main function to parse all PFR data with flexible column handling."""
    print("Parsing PFR Game Data with Flexible Columns")
    print("=" * 50)
    
    # Input and output directories
    input_dir = "data/weekly_raw"
    output_dir = "data/flexible_game_data"
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    
    if not csv_files:
        print("No CSV files found!")
        return
    
    print(f"Found {len(csv_files)} files to parse")
    
    # Parse each file
    parsed_data = []
    successful_files = 0
    
    for csv_file in csv_files:
        parsed_df = parse_flexible_csv(csv_file)
        if parsed_df is not None and len(parsed_df) > 0:
            parsed_data.append(parsed_df)
            successful_files += 1
    
    if not parsed_data:
        print("No data could be parsed!")
        return
    
    # Combine all parsed data
    print(f"\nCombining {successful_files} files...")
    
    # Get all unique columns
    all_columns = set()
    for df in parsed_data:
        all_columns.update(df.columns)
    
    all_columns = sorted(list(all_columns))
    
    # Standardize all dataframes
    standardized_dfs = []
    for df in parsed_data:
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
    combined_df = create_injury_indicators(combined_df)
    
    # Save the parsed data
    output_file = os.path.join(output_dir, "flexible_game_data.csv")
    combined_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Successfully parsed flexible game data!")
    print(f"Output file: {output_file}")
    print(f"Total games: {len(combined_df)}")
    print(f"Total players: {combined_df['player_id'].nunique()}")
    print(f"Total columns: {len(combined_df.columns)}")
    print(f"Columns: {list(combined_df.columns)}")
    
    # Show sample
    print(f"\nSample of parsed data:")
    display_cols = ['player_id', 'Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'TD', 'Rec', 'injured']
    available_cols = [col for col in display_cols if col in combined_df.columns]
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

if __name__ == "__main__":
    main()
