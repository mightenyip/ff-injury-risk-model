#!/usr/bin/env python3
"""
Final data extractor for PFR game data.
"""

import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path

def extract_game_data(file_path):
    """Extract game data from a PFR CSV file."""
    print(f"Processing {os.path.basename(file_path)}...")
    
    try:
        # Read the CSV
        df = pd.read_csv(file_path)
        
        # Get player info
        filename = os.path.basename(file_path)
        player_id = filename.split('_')[0]
        season = filename.split('_')[1]
        
        # The game data is in the first column as a complex string
        game_data = []
        
        # Process each row starting from row 2 (skip headers)
        for i in range(2, len(df)):
            row = df.iloc[i]
            game_string = str(row.iloc[0])
            
            # Skip empty or header-like rows
            if game_string == 'nan' or 'Off%' in game_string or len(game_string) < 10:
                continue
            
            # Parse the game string
            parts = game_string.split()
            
            if len(parts) >= 10:
                try:
                    game_info = {
                        'player_id': player_id,
                        'season': int(season),
                        'source_file': filename,
                        'game_index': i - 2
                    }
                    
                    # Extract basic info
                    if len(parts) >= 5:
                        game_info['week'] = parts[3] if parts[3].isdigit() else None
                        game_info['date'] = parts[4] if len(parts) > 4 else None
                        game_info['team'] = parts[5] if len(parts) > 5 else None
                        game_info['opponent'] = parts[7] if len(parts) > 7 else None
                        game_info['result'] = parts[8] if len(parts) > 8 else None
                    
                    # Extract rushing stats
                    if len(parts) >= 15:
                        game_info['rushing_att'] = parts[10] if parts[10].isdigit() else 0
                        game_info['rushing_yds'] = parts[11] if parts[11].isdigit() else 0
                        game_info['rushing_td'] = parts[12] if parts[12].isdigit() else 0
                    
                    # Extract receiving stats
                    if len(parts) >= 20:
                        game_info['receiving_tgt'] = parts[14] if parts[14].isdigit() else 0
                        game_info['receiving_rec'] = parts[15] if parts[15].isdigit() else 0
                        game_info['receiving_yds'] = parts[16] if parts[16].isdigit() else 0
                        game_info['receiving_td'] = parts[18] if parts[18].isdigit() else 0
                    
                    game_data.append(game_info)
                    
                except Exception as e:
                    print(f"    Error parsing row {i}: {e}")
                    continue
        
        if game_data:
            game_df = pd.DataFrame(game_data)
            print(f"  ✓ Extracted {len(game_df)} games")
            return game_df
        else:
            print(f"  ✗ No game data extracted")
            return None
        
    except Exception as e:
        print(f"  ✗ Error processing {file_path}: {e}")
        return None

def main():
    """Main function."""
    print("Final PFR Game Data Extractor")
    print("=" * 35)
    
    # Input and output directories
    input_dir = "data/weekly_raw"
    output_dir = "data/final_game_data"
    
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
        game_df = extract_game_data(csv_file)
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
    output_file = os.path.join(output_dir, "final_game_data.csv")
    combined_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Successfully extracted game data!")
    print(f"Output file: {output_file}")
    print(f"Total games: {len(combined_df)}")
    print(f"Total players: {combined_df['player_id'].nunique()}")
    print(f"Columns: {list(combined_df.columns)}")
    
    # Show sample
    print(f"\nSample of extracted data:")
    display_cols = ['player_id', 'week', 'team', 'opponent', 'rushing_att', 'rushing_yds', 'rushing_td', 'receiving_rec', 'receiving_yds', 'injured']
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
