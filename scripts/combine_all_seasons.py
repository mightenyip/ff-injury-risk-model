#!/usr/bin/env python3
"""
Combine all seasons (2021-2024) into a final multi-season dataset.
"""

import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path

def combine_all_seasons():
    """Combine data from all seasons into a final dataset."""
    print("Combining All Seasons (2021-2024)")
    print("=" * 40)
    
    # Input directories for each season
    season_dirs = {
        '2021': 'data/processed_2021',
        '2022': 'data/processed_2022', 
        '2023': 'data/processed_2023',
        '2024': 'data/final_combined'
    }
    
    # Output directory
    output_dir = "data/multi_season_final"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    all_season_data = []
    seasons_processed = 0
    
    for season, dir_path in season_dirs.items():
        print(f"\n📅 Processing {season} season...")
        
        # Look for combined data file
        combined_file = os.path.join(dir_path, f"{season}_combined_data.csv")
        if season == '2024':
            combined_file = os.path.join(dir_path, "final_combined_data.csv")
        
        if os.path.exists(combined_file):
            try:
                df = pd.read_csv(combined_file)
                all_season_data.append(df)
                seasons_processed += 1
                print(f"  ✅ Loaded {len(df)} games from {season}")
            except Exception as e:
                print(f"  ❌ Error loading {season}: {e}")
        else:
            print(f"  ⚠️  No combined data found for {season} at {combined_file}")
    
    if not all_season_data:
        print("\n❌ No season data found to combine!")
        return
    
    print(f"\n🔄 Combining {seasons_processed} seasons...")
    
    # Get all unique columns
    all_columns = set()
    for df in all_season_data:
        all_columns.update(df.columns)
    
    all_columns = sorted(list(all_columns))
    print(f"Total unique columns: {len(all_columns)}")
    
    # Standardize all dataframes
    standardized_dfs = []
    for df in all_season_data:
        df_copy = df.copy()
        for col in all_columns:
            if col not in df_copy.columns:
                df_copy[col] = np.nan
        df_copy = df_copy[all_columns]
        standardized_dfs.append(df_copy)
    
    # Combine all seasons
    final_df = pd.concat(standardized_dfs, ignore_index=True)
    
    # Create additional features for injury modeling
    print("Creating additional features for injury modeling...")
    
    # Sort by player and season for proper feature engineering
    final_df = final_df.sort_values(['player_id', 'season', 'Week']).reset_index(drop=True)
    
    # Create rolling features
    final_df['touches_prev'] = final_df.groupby('player_id')['Att'].shift(1).fillna(0)
    final_df['touches_prev_2'] = final_df.groupby('player_id')['Att'].shift(2).fillna(0)
    final_df['touches_prev_3'] = final_df.groupby('player_id')['Att'].shift(3).fillna(0)
    
    # Career touches prior to current game
    final_df['career_touches_prior'] = final_df.groupby('player_id')['Att'].expanding().sum().shift(1).fillna(0)
    
    # Prior multi-week injuries (games missed in previous 3 weeks)
    final_df['prior_multiweek_prev'] = final_df.groupby('player_id')['injured'].rolling(3, min_periods=1).sum().shift(1).fillna(0)
    
    # Age (approximate based on season)
    final_df['age'] = final_df['season'] - 1995  # Rough estimate, can be refined
    
    # Save the final multi-season dataset
    output_file = os.path.join(output_dir, "multi_season_injury_data.csv")
    final_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Successfully created multi-season dataset!")
    print(f"Output file: {output_file}")
    print(f"Total games: {len(final_df)}")
    print(f"Total players: {final_df['player_id'].nunique()}")
    print(f"Seasons: {sorted(final_df['season'].unique())}")
    print(f"Total columns: {len(final_df.columns)}")
    
    # Show season breakdown
    print(f"\n📊 Season breakdown:")
    season_summary = final_df.groupby('season').agg({
        'player_id': 'nunique',
        'Week': 'count',
        'injured': 'sum'
    }).round(1)
    season_summary.columns = ['Players', 'Games', 'Injured_Games']
    print(season_summary.to_string())
    
    # Show injury summary
    print(f"\n🏥 Injury summary:")
    injury_summary = final_df.groupby('player_id').agg({
        'season': 'count',
        'injured': 'sum',
        'Att': 'sum',
        'Yds': 'sum',
        'TD': 'sum'
    }).round(1)
    injury_summary.columns = ['Total_Games', 'Injured_Games', 'Total_Att', 'Total_Yds', 'Total_TD']
    injury_summary = injury_summary.sort_values('Injured_Games', ascending=False)
    print(injury_summary.head(10).to_string())
    
    # Show sample of final data
    print(f"\n📋 Sample of final dataset:")
    display_cols = ['player_id', 'season', 'Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'TD', 'injured', 'touches_prev', 'career_touches_prior']
    available_cols = [col for col in display_cols if col in final_df.columns]
    print(final_df[available_cols].head(10).to_string(index=False))
    
    # Show feature engineering results
    print(f"\n🔧 Feature engineering summary:")
    print(f"- touches_prev: {final_df['touches_prev'].sum():.0f} total previous touches")
    print(f"- career_touches_prior: {final_df['career_touches_prior'].sum():.0f} total career touches")
    print(f"- prior_multiweek_prev: {final_df['prior_multiweek_prev'].sum():.0f} total prior multi-week injuries")
    
    return final_df

def main():
    """Main function."""
    final_df = combine_all_seasons()
    
    if final_df is not None:
        print(f"\n🎯 READY FOR INJURY MODELING!")
        print(f"The dataset is now ready for building the injury risk model.")
        print(f"Key features available:")
        print(f"- Game statistics: Att, Yds, TD, Rec, etc.")
        print(f"- Injury history: injured, prior_multiweek_prev")
        print(f"- Workload features: touches_prev, career_touches_prior")
        print(f"- Player metadata: player_id, season, age")

if __name__ == "__main__":
    main()
