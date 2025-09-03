"""
Aggregate weekly joined data into season-level features for injury risk modeling.
Input: CSV with joined weekly data (from join_weekly_with_schedule.py)
Output: Season-level dataset with injury risk features
"""
import argparse
import pandas as pd
import numpy as np

def aggregate_rb_features(df):
    """
    Aggregate weekly data into season-level features for injury risk modeling.
    
    Args:
        df: DataFrame with weekly joined data
        
    Returns:
        DataFrame with season-level features
    """
    # Group by player and year
    grouped = df.groupby(['player_id', 'player', 'year', 'team'])
    
    seasons = []
    
    for (player_id, player, year, team), group in grouped:
        # Sort by week
        group = group.sort_values('Week')
        
        # Basic season stats
        total_games = len(group)
        games_played = group['played'].sum()
        games_missed = total_games - games_played
        
        # Touch statistics
        total_touches = group['rush_att'].fillna(0).sum() + group['receptions'].fillna(0).sum()
        touches_per_game = total_touches / games_played if games_played > 0 else 0
        
        # Yards statistics
        total_rush_yds = group['rush_yds'].fillna(0).sum()
        total_rec_yds = group['rec_yds'].fillna(0).sum()
        yards_per_touch = (total_rush_yds + total_rec_yds) / total_touches if total_touches > 0 else 0
        
        # Age (use most common age)
        age = group['Age'].mode().iloc[0] if not group['Age'].isna().all() else None
        
        # Injury patterns
        # Look for consecutive missed games (potential injuries)
        played_series = group['played'].values
        consecutive_missed = 0
        max_consecutive_missed = 0
        
        for played in played_series:
            if played == 0:
                consecutive_missed += 1
                max_consecutive_missed = max(max_consecutive_missed, consecutive_missed)
            else:
                consecutive_missed = 0
        
        # Multi-week absences (potential injuries)
        multiweek_absences = 0
        if max_consecutive_missed >= 2:
            multiweek_absences = 1
        
        # Create season record
        season_record = {
            'player_id': player_id,
            'player': player,
            'year': year,
            'team': team,
            'age': age,
            'games_played': games_played,
            'games_missed': games_missed,
            'total_touches': total_touches,
            'touches_per_game': touches_per_game,
            'total_rush_yds': total_rush_yds,
            'total_rec_yds': total_rec_yds,
            'yards_per_touch': yards_per_touch,
            'multiweek_absences': multiweek_absences,
            'max_consecutive_missed': max_consecutive_missed
        }
        
        seasons.append(season_record)
    
    return pd.DataFrame(seasons)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_weekly", required=True, help="CSV with joined weekly data")
    ap.add_argument("--out_seasons", required=True, help="Output CSV for season features")
    args = ap.parse_args()
    
    print(f"Reading weekly data from {args.in_weekly}")
    weekly_data = pd.read_csv(args.in_weekly)
    
    print(f"Processing {len(weekly_data)} weekly records...")
    seasons = aggregate_rb_features(weekly_data)
    
    print(f"Writing {len(seasons)} season records to {args.out_seasons}")
    seasons.to_csv(args.out_seasons, index=False)
    
    print("Feature engineering complete!")
    print(f"Output columns: {list(seasons.columns)}")

if __name__ == "__main__":
    main()

