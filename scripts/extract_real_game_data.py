#!/usr/bin/env python3
"""
Extract real game data from the PFR CSV files.
The actual game stats are embedded in the 'Unnamed: 0' column.
"""

import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path
import re

def extract_game_stats_from_string(game_string):
    """Extract game statistics from the complex string format."""
    if pd.isna(game_string) or str(game_string) == 'nan':
        return None
    
    # The string contains space-separated values
    parts = str(game_string).split()
    
    if len(parts) < 10:
        return None
    
    try:
        # Parse the game data based on the structure we observed
        game_data = {}
        
        # Basic game info
        game_data['rk'] = parts[0] if parts[0].isdigit() else None
        game_data['gcar'] = parts[1] if parts[1].isdigit() else None
        game_data['gtm'] = parts[2] if parts[2].isdigit() else None
        game_data['week'] = parts[3] if parts[3].isdigit() else None
        game_data['date'] = parts[4] if len(parts) > 4 else None
        game_data['team'] = parts[5] if len(parts) > 5 else None
        game_data['opp'] = parts[7] if len(parts) > 7 else None
        game_data['result'] = parts[8] if len(parts) > 8 else None
        game_data['gs'] = parts[9] if len(parts) > 9 else None
        
        # Rushing stats
        if len(parts) >= 15:
            game_data['rushing_att'] = parts[10] if parts[10].isdigit() else 0
            game_data['rushing_yds'] = parts[11] if parts[11].isdigit() else 0
            game_data['rushing_td'] = parts[12] if parts[12].isdigit() else 0
            game_data['rushing_ypa'] = parts[13] if len(parts) > 13 else 0
        
        # Receiving stats
        if len(parts) >= 20:
            game_data['receiving_tgt'] = parts[14] if parts[14].isdigit() else 0
            game_data['receiving_rec'] = parts[15] if parts[15].isdigit() else 0
            game_data['receiving_yds'] = parts[16] if parts[16].isdigit() else 0
            game_data['receiving_ypc'] = parts[17] if len(parts) > 17 else 0
            game_data['receiving_td'] = parts[18] if parts[18].isdigit() else 0
        
        return game_data
        
    except Exception as e:
        print(f"    Error parsing game string: {e}")
        return None

def parse_pfr_file(file_path):
    """Parse a PFR CSV file and extract game statistics."""
    print(f"Parsing {os.path.basename(file_path)}...")
    
    try:
        # Read the CSV
        df = pd.read_csv(file_path)
        
        # Get player info
        filename = os.path.basename(file_path)
        player_id = filename.split('_')[0]
        season = filename.split('_')[1]
        
        # Extract game data from the 'Unnamed: 0' column
        game_data = []
        
        for idx, row in df.iterrows():
            # Skip header rows
            if idx < 2:
                continue
            
            # Get the game string from the first column
            game_string = row.iloc[0]
            
            # Extract game stats
            stats = extract_game_stats_from_string(game_string)
            
            if stats:
                # Add player metadata
                stats['player_id'] = player_id
                stats['season'] = int(season)
                stats['source_file'] = filename
                stats['game_index'] = idx - 2  # Adjust for header rows
                
                game_data.append(stats)
        
        if game_data:
            game_df = pd.DataFrame(game_data)
            print(f"  ✓ Extracted {len(game_df)} games")
            return game_df
        else:
            print(f"  ✗ No game data extracted")
            return None
        
    except Exception as e:
        print(f"  ✗ Error parsing {file_path}: {e}")
        return None

def main():
    """Main function to extract game data from all files."""
    print("Extracting Real Game Data from PFR CSVs")
    print("=" * 45)
    
    # Input and output directories
    input_dir = "data/weekly_raw"
    output_dir = "data/real_game_data"
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    
    if not csv_files:
        print("No CSV files found!")
        return
    
    print(f"Found {len(csv_files)} files to process")
    
    # Process each file
    all_game_data = []
    successful_files = 0
    
    for csv_file in csv_files:
        game_df = parse_pfr_file(csv_file)
        if game_df is not None:
            all_game_data.append(game_df)
            successful_files += 1
    
    if not all_game_data:
        print("No game data could be extracted!")
        return
    
    # Combine all game data
    print(f"\nCombining {successful_files} files...")
    combined_df = pd.concat(all_game_data, ignore_index=True)
    
    # Clean up the data
    print("Cleaning extracted data...")
    
    # Convert numeric columns
    numeric_cols = ['week', 'rushing_att', 'rushing_yds', 'rushing_td', 'receiving_tgt', 'receiving_rec', 'receiving_yds', 'receiving_td']
    for col in numeric_cols:
        if col in combined_df.columns:
            combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce').fillna(0)
    
    # Create injury indicators
    combined_df['injured'] = (combined_df['rushing_att'] == 0) & (combined_df['receiving_rec'] == 0)
    
    # Save the extracted data
    output_file = os.path.join(output_dir, "real_game_data.csv")
    combined_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Successfully extracted game data!")
    print(f"Output file: {output_file}")
    print(f"Total games: {len(combined_df)}")
    print(f"Total players: {combined_df['player_id'].nunique()}")
    print(f"Columns: {list(combined_df.columns)}")
    
    # Show sample
    print(f"\nSample of extracted data:")
    display_cols = ['player_id', 'week', 'team', 'opp', 'rushing_att', 'rushing_yds', 'rushing_td', 'receiving_rec', 'receiving_yds', 'injured']
    available_cols = [col for col in display_cols if col in combined_df.columns]
    print(combined_df[available_cols].head(10).to_string(index=False))
    
    # Show injury summary
    if 'injured' in combined_df.columns:
        injury_summary = combined_df.groupby('player_id')['injured'].sum().sort_values(ascending=False)
        print(f"\nInjury summary (games missed per player):")
        print(injury_summary.head(10).to_string())
    
    # Show stats summary
    if 'rushing_att' in combined_df.columns:
        print(f"\nRushing stats summary:")
        print(f"Total rushing attempts: {combined_df['rushing_att'].sum():.0f}")
        print(f"Total rushing yards: {combined_df['rushing_yds'].sum():.0f}")
        print(f"Total rushing TDs: {combined_df['rushing_td'].sum():.0f}")

if __name__ == "__main__":
    main()
