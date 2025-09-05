#!/usr/bin/env python3
"""
Extract actual game data from the PFR CSV files.
The data is embedded in the column structure and needs to be parsed properly.
"""

import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path
import re

def extract_game_data_from_csv(file_path):
    """Extract game data from a single CSV file."""
    print(f"Extracting data from {os.path.basename(file_path)}...")
    
    try:
        # Read the CSV
        df = pd.read_csv(file_path)
        
        # The data structure is complex - let's examine it
        print(f"  CSV shape: {df.shape}")
        print(f"  Columns: {list(df.columns)}")
        
        # The actual game data is in the "Unnamed: 0" column
        # Let's parse it properly
        game_data = []
        
        # Get player info
        filename = os.path.basename(file_path)
        player_id = filename.split('_')[0]
        season = filename.split('_')[1]
        
        # Look at the first few rows to understand the structure
        for idx, row in df.iterrows():
            if idx == 0:  # Skip header row
                continue
                
            # The game data is in the first column as a string
            game_row = str(row.iloc[0])
            
            # Skip empty or header-like rows
            if not game_row or game_row == 'nan' or 'Off%' in game_row:
                continue
            
            # Parse the game data - it's space-separated
            parts = game_row.split()
            
            if len(parts) >= 10:  # Should have at least basic game info
                try:
                    game_info = {
                        'player_id': player_id,
                        'season': int(season),
                        'source_file': filename,
                        'row_index': idx
                    }
                    
                    # Try to extract key fields
                    # The structure varies, so let's be flexible
                    if len(parts) >= 5:
                        game_info['week'] = parts[3] if parts[3].isdigit() else None
                        game_info['date'] = f"{season}-{parts[4]}" if len(parts) > 4 else None
                        game_info['team'] = parts[5] if len(parts) > 5 else None
                        game_info['opponent'] = parts[7] if len(parts) > 7 else None
                        game_info['result'] = parts[8] if len(parts) > 8 else None
                        
                        # Try to extract rushing stats
                        if len(parts) >= 15:
                            game_info['rushing_att'] = parts[10] if parts[10].isdigit() else 0
                            game_info['rushing_yds'] = parts[11] if parts[11].isdigit() else 0
                            game_info['rushing_td'] = parts[12] if parts[12].isdigit() else 0
                        
                        # Try to extract receiving stats
                        if len(parts) >= 20:
                            game_info['receiving_tgt'] = parts[14] if parts[14].isdigit() else 0
                            game_info['receiving_rec'] = parts[15] if parts[15].isdigit() else 0
                            game_info['receiving_yds'] = parts[16] if parts[16].isdigit() else 0
                            game_info['receiving_td'] = parts[18] if parts[18].isdigit() else 0
                    
                    game_data.append(game_info)
                    
                except Exception as e:
                    print(f"    Error parsing row {idx}: {e}")
                    continue
        
        print(f"  ✓ Extracted {len(game_data)} games")
        return pd.DataFrame(game_data)
        
    except Exception as e:
        print(f"  ✗ Error processing {file_path}: {e}")
        return None

def main():
    """Main function to extract game data from all files."""
    print("Extracting Game Data from PFR CSVs")
    print("=" * 40)
    
    # Input and output directories
    input_dir = "data/weekly_raw"
    output_dir = "data/game_data_extracted"
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    
    if not csv_files:
        print("No CSV files found in", input_dir)
        return
    
    print(f"Found {len(csv_files)} CSV files to process")
    
    # Process each file
    all_game_data = []
    successful_files = 0
    
    for csv_file in csv_files:
        game_df = extract_game_data_from_csv(csv_file)
        if game_df is not None and len(game_df) > 0:
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
    output_file = os.path.join(output_dir, "extracted_game_data.csv")
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

if __name__ == "__main__":
    main()
