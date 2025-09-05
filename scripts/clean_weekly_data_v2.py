#!/usr/bin/env python3
"""
Clean and restructure the weekly game log data from PFR - Version 2.
This script properly handles the multi-level header structure.
"""

import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path

def clean_individual_csv(file_path):
    """Clean an individual CSV file and return a cleaned DataFrame."""
    print(f"Cleaning {os.path.basename(file_path)}...")
    
    try:
        # Read the CSV - the structure has multi-level headers
        df = pd.read_csv(file_path)
        
        # The first row (index 0) contains the actual column names
        # The second row (index 1) contains sub-categories
        # The data starts from row 2 (index 2)
        
        if len(df) < 3:
            print(f"  ✗ Not enough rows in {file_path}")
            return None
        
        # Get the column names from the first row
        column_names = df.iloc[0].values
        
        # Clean up column names
        clean_columns = []
        for i, col in enumerate(column_names):
            if pd.isna(col) or str(col).strip() == '' or str(col).strip() == 'Unnamed: 0':
                # Use the column index as fallback
                clean_columns.append(f'col_{i}')
            else:
                clean_columns.append(str(col).strip())
        
        # Use the first row as headers and start data from row 2
        df_clean = df.iloc[2:].copy()
        df_clean.columns = clean_columns
        
        # Reset index
        df_clean = df_clean.reset_index(drop=True)
        
        # Add metadata
        filename = os.path.basename(file_path)
        player_id = filename.split('_')[0]
        season = filename.split('_')[1]
        
        df_clean['player_id'] = player_id
        df_clean['season'] = int(season)
        df_clean['source_file'] = filename
        
        # Clean up the data
        df_clean = clean_data_types(df_clean)
        
        print(f"  ✓ Cleaned {len(df_clean)} rows with {len(clean_columns)} columns")
        return df_clean
        
    except Exception as e:
        print(f"  ✗ Error cleaning {file_path}: {e}")
        return None

def clean_data_types(df):
    """Clean and convert data types."""
    # Convert numeric columns
    numeric_columns = ['Rk', 'Gcar', 'Gtm', 'Week', 'Att', 'Yds', 'TD', 'Y/A', 'Tgt', 'Rec', 'Y/R', 'Ctch%', 'Y/Tgt', 'Fmb', 'FL', 'FF', 'FR', 'FRTD', 'OffSnp', 'Off%', 'DefSnp', 'Def%', 'STSnp', 'ST%']
    
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
    """Main function to clean all weekly data."""
    print("Cleaning Weekly Game Log Data - Version 2")
    print("=" * 50)
    
    # Input and output directories
    input_dir = "data/weekly_raw"
    output_dir = "data/weekly_cleaned"
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    
    if not csv_files:
        print("No CSV files found in", input_dir)
        return
    
    print(f"Found {len(csv_files)} CSV files to clean")
    
    # Clean each file
    cleaned_data = []
    successful_files = 0
    
    for csv_file in csv_files:
        cleaned_df = clean_individual_csv(csv_file)
        if cleaned_df is not None:
            cleaned_data.append(cleaned_df)
            successful_files += 1
    
    if not cleaned_data:
        print("No files could be cleaned successfully!")
        return
    
    # Combine all cleaned data
    print(f"\nCombining {successful_files} cleaned files...")
    combined_df = pd.concat(cleaned_data, ignore_index=True)
    
    # Create injury indicators
    print("Creating injury indicators...")
    combined_df = create_injury_indicators(combined_df)
    
    # Save cleaned data
    output_file = os.path.join(output_dir, "cleaned_weekly_data_v2.csv")
    combined_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Successfully cleaned and saved data!")
    print(f"Output file: {output_file}")
    print(f"Total rows: {len(combined_df)}")
    print(f"Total players: {combined_df['player_id'].nunique()}")
    print(f"Columns: {list(combined_df.columns)}")
    
    # Show sample of cleaned data
    print(f"\nSample of cleaned data:")
    available_cols = ['player_id', 'Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'TD', 'Rec', 'injured']
    display_cols = [col for col in available_cols if col in combined_df.columns]
    print(combined_df[display_cols].head(10).to_string(index=False))
    
    # Show injury summary
    if 'injured' in combined_df.columns:
        injury_summary = combined_df.groupby('player_id')['injured'].sum().sort_values(ascending=False)
        print(f"\nInjury summary (games missed per player):")
        print(injury_summary.head(10).to_string())
    
    # Show column analysis
    print(f"\nColumn analysis:")
    print(f"Total columns: {len(combined_df.columns)}")
    print(f"Key columns found: {[col for col in ['Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'TD', 'Rec'] if col in combined_df.columns]}")

if __name__ == "__main__":
    main()
