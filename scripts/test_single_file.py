#!/usr/bin/env python3
"""
Test parsing a single PFR CSV file.
"""

import pandas as pd
import numpy as np

def test_single_file():
    """Test parsing a single file."""
    file_path = 'data/weekly_raw/barksa00_2024_gamelog.csv'
    
    print(f"Testing {file_path}...")
    
    try:
        # Read with a large number of columns to capture everything
        df = pd.read_csv(file_path, header=None, names=range(50))
        print(f"  Raw shape: {df.shape}")
        
        # Get the actual column names from row 1
        column_names = df.iloc[1].values
        col_list = column_names.tolist()
        
        clean_column_names = []
        for i, col in enumerate(col_list):
            if pd.isna(col):
                clean_column_names.append(f'col_{i}')
            else:
                clean_column_names.append(str(col))
        
        print(f"  Column names: {clean_column_names[:10]}...")
        
        # Create a clean dataframe starting from row 2
        data_df = df.iloc[2:].copy()
        data_df.columns = clean_column_names
        
        # Remove columns that are all NaN
        data_df = data_df.dropna(axis=1, how='all')
        
        # Reset index
        data_df = data_df.reset_index(drop=True)
        
        # Add metadata
        filename = 'barksa00_2024_gamelog.csv'
        player_id = filename.split('_')[0]
        season = filename.split('_')[1]
        
        data_df['player_id'] = player_id
        data_df['season'] = int(season)
        data_df['source_file'] = filename
        
        print(f"  ✓ Parsed {len(data_df)} games with {len(data_df.columns)} columns")
        
        # Show what columns we found
        key_cols = ['Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'TD', 'Rec']
        found_key_cols = [col for col in key_cols if col in data_df.columns]
        print(f"  Key columns found: {found_key_cols}")
        
        # Show sample data
        if found_key_cols:
            print(f"  Sample data:")
            print(data_df[found_key_cols].head(3).to_string(index=False))
        
        return data_df
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_single_file()
    if result is not None:
        print(f"\n✅ Success! Parsed {len(result)} games")
    else:
        print(f"\n❌ Failed to parse file")
