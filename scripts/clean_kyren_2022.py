#!/usr/bin/env python3
"""
Remove Kyren Williams' 2022 rookie season data to create a cleaner dataset.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

def clean_kyren_2022():
    """Remove Kyren Williams' 2022 data and create a cleaned dataset."""
    print("Cleaning Kyren Williams 2022 Rookie Season Data")
    print("=" * 50)
    
    # Input file
    input_file = "data/multi_season_final/three_season_injury_data.csv"
    
    # Output directory
    output_dir = "data/multi_season_final"
    
    # Load the data
    print("Loading three-season dataset...")
    df = pd.read_csv(input_file)
    print(f"  ✅ Loaded {len(df)} total games")
    
    # Show Kyren's 2022 data before removal
    kyren_2022 = df[(df['player_id'] == 'willky02') & (df['season'] == 2022)]
    print(f"\nKyren Williams 2022 data to be removed:")
    print(f"  Games: {len(kyren_2022)}")
    print(f"  Injured games: {kyren_2022['injured'].sum()}")
    print(f"  Total rushing attempts: {kyren_2022['Att'].sum()}")
    print(f"  Total rushing yards: {kyren_2022['Yds'].sum()}")
    
    # Show sample of his 2022 data
    if len(kyren_2022) > 0:
        print(f"\nSample of Kyren's 2022 data:")
        display_cols = ['Week', 'Date', 'Team', 'Opp', 'Att', 'Yds', 'TD', 'injured']
        available_cols = [col for col in display_cols if col in kyren_2022.columns]
        print(kyren_2022[available_cols].head(10).to_string(index=False))
    
    # Remove Kyren's 2022 data
    print(f"\nRemoving Kyren Williams 2022 data...")
    df_cleaned = df[~((df['player_id'] == 'willky02') & (df['season'] == 2022))]
    
    print(f"  ✅ Removed {len(df) - len(df_cleaned)} games")
    print(f"  ✅ Remaining games: {len(df_cleaned)}")
    
    # Recalculate features for Kyren (since we removed his 2022 data)
    print(f"\nRecalculating features for Kyren Williams...")
    kyren_mask = df_cleaned['player_id'] == 'willky02'
    kyren_data = df_cleaned[kyren_mask].copy()
    
    if len(kyren_data) > 0:
        # Recalculate features for Kyren
        kyren_data['touches_prev'] = kyren_data['Att'].shift(1).fillna(0)
        kyren_data['touches_prev_2'] = kyren_data['Att'].shift(2).fillna(0)
        kyren_data['touches_prev_3'] = kyren_data['Att'].shift(3).fillna(0)
        kyren_data['career_touches_prior'] = kyren_data['Att'].expanding().sum().shift(1).fillna(0)
        kyren_data['prior_multiweek_prev'] = kyren_data['injured'].rolling(3, min_periods=1).sum().shift(1).fillna(0)
        
        # Update the main dataframe
        df_cleaned.loc[kyren_mask, 'touches_prev'] = kyren_data['touches_prev']
        df_cleaned.loc[kyren_mask, 'touches_prev_2'] = kyren_data['touches_prev_2']
        df_cleaned.loc[kyren_mask, 'touches_prev_3'] = kyren_data['touches_prev_3']
        df_cleaned.loc[kyren_mask, 'career_touches_prior'] = kyren_data['career_touches_prior']
        df_cleaned.loc[kyren_mask, 'prior_multiweek_prev'] = kyren_data['prior_multiweek_prev']
    
    # Save the cleaned dataset
    output_file = os.path.join(output_dir, "cleaned_three_season_injury_data.csv")
    df_cleaned.to_csv(output_file, index=False)
    
    print(f"\n✅ Successfully created cleaned dataset!")
    print(f"Output file: {output_file}")
    print(f"Total games: {len(df_cleaned)}")
    print(f"Total players: {df_cleaned['player_id'].nunique()}")
    print(f"Seasons: {sorted(df_cleaned['season'].unique())}")
    print(f"Total columns: {len(df_cleaned.columns)}")
    
    # Show season breakdown
    print(f"\n📊 Season breakdown (cleaned):")
    season_summary = df_cleaned.groupby('season').agg({
        'player_id': 'nunique',
        'Week': 'count',
        'injured': 'sum'
    }).round(1)
    season_summary.columns = ['Players', 'Games', 'Injured_Games']
    print(season_summary.to_string())
    
    # Show injury summary
    print(f"\n🏥 Injury summary (cleaned):")
    injury_summary = df_cleaned.groupby('player_id').agg({
        'season': 'count',
        'injured': 'sum',
        'Att': 'sum',
        'Yds': 'sum',
        'TD': 'sum'
    }).round(1)
    injury_summary.columns = ['Total_Games', 'Injured_Games', 'Total_Att', 'Total_Yds', 'Total_TD']
    injury_summary = injury_summary.sort_values('Injured_Games', ascending=False)
    print(injury_summary.head(10).to_string())
    
    # Show Kyren's updated data
    kyren_cleaned = df_cleaned[df_cleaned['player_id'] == 'willky02']
    print(f"\nKyren Williams updated data:")
    print(f"  Total games: {len(kyren_cleaned)}")
    print(f"  Injured games: {kyren_cleaned['injured'].sum()}")
    print(f"  Total rushing attempts: {kyren_cleaned['Att'].sum()}")
    print(f"  Total rushing yards: {kyren_cleaned['Yds'].sum()}")
    print(f"  Seasons: {sorted(kyren_cleaned['season'].unique())}")
    
    # Show injury rate by season
    print(f"\n📈 Injury rates by season (cleaned):")
    for season in sorted(df_cleaned['season'].unique()):
        season_data = df_cleaned[df_cleaned['season'] == season]
        injury_rate = season_data['injured'].mean() * 100
        print(f"  {season}: {injury_rate:.1f}% injury rate ({season_data['injured'].sum()}/{len(season_data)} games)")
    
    # Show feature engineering results
    print(f"\n🔧 Feature engineering summary (cleaned):")
    print(f"- touches_prev: {df_cleaned['touches_prev'].sum():.0f} total previous touches")
    print(f"- career_touches_prior: {df_cleaned['career_touches_prior'].sum():.0f} total career touches")
    print(f"- prior_multiweek_prev: {df_cleaned['prior_multiweek_prev'].sum():.0f} total prior multi-week injuries")
    
    return df_cleaned

def main():
    """Main function."""
    final_df = clean_kyren_2022()
    
    if final_df is not None:
        print(f"\n🎯 READY FOR INJURY MODELING!")
        print(f"The cleaned dataset is now ready for building the injury risk model.")
        print(f"Key improvements:")
        print(f"- Removed Kyren Williams' 2022 rookie season data")
        print(f"- Recalculated features for Kyren's remaining seasons")
        print(f"- Cleaner dataset with more consistent player data")
        print(f"\nThis is a more robust dataset for injury risk modeling!")

if __name__ == "__main__":
    main()
