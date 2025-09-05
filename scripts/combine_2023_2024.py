#!/usr/bin/env python3
"""
Combine 2023 and 2024 season data into a final dataset.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

def combine_2023_2024():
    """Combine 2023 and 2024 season data."""
    print("Combining 2023 and 2024 Season Data")
    print("=" * 40)
    
    # Input files
    file_2023 = "data/processed_2023/2023_combined_data.csv"
    file_2024 = "data/final_combined/final_combined_data.csv"
    
    # Output directory
    output_dir = "data/multi_season_final"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load the data
    print("Loading 2023 data...")
    df_2023 = pd.read_csv(file_2023)
    print(f"  ✅ Loaded {len(df_2023)} games from 2023")
    
    print("Loading 2024 data...")
    df_2024 = pd.read_csv(file_2024)
    print(f"  ✅ Loaded {len(df_2024)} games from 2024")
    
    # Get all unique columns
    all_columns = set(df_2023.columns) | set(df_2024.columns)
    all_columns = sorted(list(all_columns))
    print(f"Total unique columns: {len(all_columns)}")
    
    # Standardize both dataframes
    print("Standardizing dataframes...")
    for col in all_columns:
        if col not in df_2023.columns:
            df_2023[col] = np.nan
        if col not in df_2024.columns:
            df_2024[col] = np.nan
    
    # Reorder columns
    df_2023 = df_2023[all_columns]
    df_2024 = df_2024[all_columns]
    
    # Combine the dataframes
    print("Combining dataframes...")
    combined_df = pd.concat([df_2023, df_2024], ignore_index=True)
    
    # Sort by player, season, and week for proper ordering
    combined_df = combined_df.sort_values(['player_id', 'season', 'Week']).reset_index(drop=True)
    
    # Create simple features for injury modeling
    print("Creating features for injury modeling...")
    
    # Previous game touches (rushing attempts)
    combined_df['touches_prev'] = combined_df.groupby('player_id')['Att'].shift(1).fillna(0)
    combined_df['touches_prev_2'] = combined_df.groupby('player_id')['Att'].shift(2).fillna(0)
    combined_df['touches_prev_3'] = combined_df.groupby('player_id')['Att'].shift(3).fillna(0)
    
    # Career touches prior to current game
    combined_df['career_touches_prior'] = combined_df.groupby('player_id')['Att'].expanding().sum().shift(1).fillna(0)
    
    # Prior multi-week injuries (games missed in previous 3 weeks)
    combined_df['prior_multiweek_prev'] = combined_df.groupby('player_id')['injured'].rolling(3, min_periods=1).sum().shift(1).fillna(0)
    
    # Age (approximate based on season)
    combined_df['age'] = combined_df['season'] - 1995  # Rough estimate, can be refined
    
    # Save the final dataset
    output_file = os.path.join(output_dir, "multi_season_injury_data.csv")
    combined_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Successfully created multi-season dataset!")
    print(f"Output file: {output_file}")
    print(f"Total games: {len(combined_df)}")
    print(f"Total players: {combined_df['player_id'].nunique()}")
    print(f"Seasons: {sorted(combined_df['season'].unique())}")
    print(f"Total columns: {len(combined_df.columns)}")
    
    # Show season breakdown
    print(f"\n📊 Season breakdown:")
    season_summary = combined_df.groupby('season').agg({
        'player_id': 'nunique',
        'Week': 'count',
        'injured': 'sum'
    }).round(1)
    season_summary.columns = ['Players', 'Games', 'Injured_Games']
    print(season_summary.to_string())
    
    # Show injury summary
    print(f"\n🏥 Injury summary:")
    injury_summary = combined_df.groupby('player_id').agg({
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
    available_cols = [col for col in display_cols if col in combined_df.columns]
    print(combined_df[available_cols].head(10).to_string(index=False))
    
    # Show feature engineering results
    print(f"\n🔧 Feature engineering summary:")
    print(f"- touches_prev: {combined_df['touches_prev'].sum():.0f} total previous touches")
    print(f"- career_touches_prior: {combined_df['career_touches_prior'].sum():.0f} total career touches")
    print(f"- prior_multiweek_prev: {combined_df['prior_multiweek_prev'].sum():.0f} total prior multi-week injuries")
    
    return combined_df

def main():
    """Main function."""
    final_df = combine_2023_2024()
    
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
