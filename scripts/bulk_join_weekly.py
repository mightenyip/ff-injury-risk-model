"""
Bulk process weekly data by joining with team schedules.
This script processes all weekly CSV files and creates joined datasets.
"""
import argparse
import os
import glob
import pandas as pd
from join_weekly_with_schedule import merge_player_schedule

def get_team_from_weekly_csv(csv_path):
    """Extract team abbreviation from weekly CSV filename or content."""
    # Try to get team from the CSV content first
    try:
        df = pd.read_csv(csv_path)
        if 'team' in df.columns and not df['team'].isna().all():
            team = df['team'].dropna().iloc[0]
            if pd.notna(team) and team != '':
                return str(team).upper()
    except:
        pass
    
    # Fallback: try to extract from filename
    filename = os.path.basename(csv_path)
    # Look for team abbreviation in filename (3-letter codes)
    import re
    team_match = re.search(r'([A-Z]{3})', filename)
    if team_match:
        return team_match.group(1)
    
    return None

def bulk_join_weekly(weekly_dir, schedules_dir, output_dir, season):
    """
    Process all weekly CSV files and join them with team schedules.
    
    Args:
        weekly_dir: Directory containing weekly CSV files
        schedules_dir: Directory containing team schedule CSV files
        output_dir: Directory to save joined CSV files
        season: Season year
    """
    # Create output directory
    season_output_dir = os.path.join(output_dir, str(season))
    os.makedirs(season_output_dir, exist_ok=True)
    
    # Get all weekly CSV files
    weekly_pattern = os.path.join(weekly_dir, str(season), "*.csv")
    weekly_files = glob.glob(weekly_pattern)
    
    print(f"Found {len(weekly_files)} weekly CSV files for {season}")
    
    # Process each weekly file
    joined_files = []
    
    for i, weekly_file in enumerate(weekly_files):
        try:
            # Extract player ID from filename
            player_id = os.path.basename(weekly_file).replace('.csv', '')
            
            # Determine team
            team = get_team_from_weekly_csv(weekly_file)
            if not team:
                print(f"Warning: Could not determine team for {player_id}, skipping...")
                continue
            
            # Look for corresponding schedule file
            schedule_file = os.path.join(schedules_dir, f"{team.lower()}_{season}.csv")
            if not os.path.exists(schedule_file):
                print(f"Warning: Schedule file not found for {team} {season}, skipping {player_id}...")
                continue
            
            # Create output filename
            output_file = os.path.join(season_output_dir, f"{player_id}_joined.csv")
            
            # Join weekly data with schedule
            print(f"[{i+1}/{len(weekly_files)}] Processing {player_id} ({team})...")
            merged_data = merge_player_schedule(weekly_file, schedule_file, output_file)
            
            joined_files.append(output_file)
            print(f"  ✓ Saved to {output_file}")
            
        except Exception as e:
            print(f"  ✗ Error processing {weekly_file}: {e}")
            continue
    
    # Combine all joined files into one
    if joined_files:
        print(f"\nCombining {len(joined_files)} joined files...")
        all_data = []
        
        for joined_file in joined_files:
            try:
                df = pd.read_csv(joined_file)
                all_data.append(df)
            except Exception as e:
                print(f"Warning: Could not read {joined_file}: {e}")
                continue
        
        if all_data:
            combined_data = pd.concat(all_data, ignore_index=True)
            combined_output = os.path.join(season_output_dir, "all_joined.csv")
            combined_data.to_csv(combined_output, index=False)
            print(f"✓ Combined data saved to {combined_output}")
            print(f"  Total records: {len(combined_data)}")
            print(f"  Unique players: {combined_data['player_id'].nunique()}")
        else:
            print("No data could be combined.")
    else:
        print("No files were successfully processed.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weekly_dir", default="data/weekly_raw", help="Directory with weekly CSV files")
    ap.add_argument("--schedules_dir", default="data/schedules", help="Directory with team schedule CSV files")
    ap.add_argument("--output_dir", default="data/weekly_joined", help="Directory to save joined CSV files")
    ap.add_argument("--season", type=int, required=True, help="Season year to process")
    args = ap.parse_args()
    
    print(f"Bulk joining weekly data for {args.season}")
    print(f"Weekly directory: {args.weekly_dir}")
    print(f"Schedules directory: {args.schedules_dir}")
    print(f"Output directory: {args.output_dir}")
    print("-" * 60)
    
    bulk_join_weekly(args.weekly_dir, args.schedules_dir, args.output_dir, args.season)
    
    print("\nBulk processing complete!")

if __name__ == "__main__":
    main()

