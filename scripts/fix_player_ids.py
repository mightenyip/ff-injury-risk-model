#!/usr/bin/env python3
"""
Fix player IDs by extracting them from PFR URLs.
The current CSV files have single-letter IDs, but we need the full PFR IDs.
"""
import pandas as pd
import re
import argparse
import os

def extract_pfr_id(url):
    """Extract PFR player ID from URL like https://www.pro-football-reference.com/players/T/TaylJo02.htm"""
    match = re.search(r'/players/[A-Z]/([A-Za-z0-9]+)\.htm$', url)
    if match:
        return match.group(1)
    return None

def fix_player_ids(input_csv, output_csv):
    """Fix player IDs in the CSV file."""
    df = pd.read_csv(input_csv)
    
    print(f"Processing {len(df)} players...")
    
    # Extract PFR IDs from URLs
    df['pfr_id'] = df['pfr_url'].apply(extract_pfr_id)
    
    # Check for any missing IDs
    missing_ids = df[df['pfr_id'].isna()]
    if len(missing_ids) > 0:
        print(f"Warning: {len(missing_ids)} players have missing PFR IDs:")
        for _, row in missing_ids.iterrows():
            print(f"  {row['player']}: {row['pfr_url']}")
    
    # Replace the old player_id column with the new PFR ID
    df['player_id'] = df['pfr_id']
    
    # Drop the temporary pfr_id column
    df = df.drop('pfr_id', axis=1)
    
    # Save the fixed CSV
    df.to_csv(output_csv, index=False)
    
    print(f"Fixed player IDs saved to: {output_csv}")
    print(f"Sample of new IDs:")
    print(df[['player', 'player_id']].head(10).to_string(index=False))
    
    return df

def main():
    parser = argparse.ArgumentParser(description='Fix player IDs in RB CSV files')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found!")
        return
    
    fix_player_ids(args.input, args.output)

if __name__ == "__main__":
    main()

