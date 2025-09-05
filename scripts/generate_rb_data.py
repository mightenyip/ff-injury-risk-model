#!/usr/bin/env python3
"""
Generate realistic RB data for 2021-2024 that matches the injury model structure.
This creates synthetic data that can be used to test and validate the injury model.
"""
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def generate_rb_season_data(season, n_players=50):
    """Generate realistic RB data for a given season."""
    
    # Set seed for reproducibility
    np.random.seed(42 + season)
    random.seed(42 + season)
    
    # Generate realistic player data
    data = []
    
    for i in range(n_players):
        # Age distribution: most RBs are 22-28, some veterans 29-32
        if random.random() < 0.8:
            age = np.random.normal(25, 2)  # Young RBs
        else:
            age = np.random.normal(30, 2)  # Veteran RBs
        age = max(21, min(35, int(age)))
        
        # Games played: most play 12-17 games, some get injured
        if random.random() < 0.7:
            games_played = np.random.poisson(15)  # Healthy season
        else:
            games_played = np.random.poisson(8)   # Injury-shortened
        games_played = max(1, min(18, games_played))
        
        # Touches per game: varies by role (starter vs backup)
        if random.random() < 0.6:
            touches_per_game = np.random.normal(18, 4)  # Starter
        else:
            touches_per_game = np.random.normal(8, 3)   # Backup
        touches_per_game = max(1, touches_per_game)
        
        # Yards per touch: typically 4-6 yards
        yards_per_touch = np.random.normal(4.5, 0.8)
        yards_per_touch = max(2.5, min(7.0, yards_per_touch))
        
        # Injury history: 30% have previous injuries
        injury_history = np.random.binomial(1, 0.3)
        
        # Position (all RBs for this dataset)
        position = 'RB'
        
        # Create injury risk based on realistic factors
        # Age has U-shaped relationship with injury risk
        age_risk = 0.1 * ((age - 25) ** 2) / 25
        
        # Touches per game increases injury risk
        touches_risk = 0.05 * np.log(1 + touches_per_game / 5)
        
        # Previous injury history increases risk
        history_risk = 0.3 * injury_history
        
        # Season-specific factors (2021 had more injuries due to COVID impact)
        season_factor = 1.0
        if season == 2021:
            season_factor = 1.2  # Higher injury rate in 2021
        elif season == 2024:
            season_factor = 0.9  # Lower injury rate in 2024 (better conditioning)
        
        # Combine risks
        total_risk = (age_risk + touches_risk + history_risk) * season_factor
        
        # Add some randomness
        total_risk += np.random.normal(0, 0.1)
        
        # Convert to binary injury outcome (1 = injured, 0 = healthy)
        # Higher risk = more likely to be injured
        injury_probability = 1 / (1 + np.exp(-(total_risk - 0.5)))
        injury = np.random.binomial(1, injury_probability)
        
        # Generate player name
        first_names = ['James', 'Michael', 'David', 'John', 'Robert', 'William', 'Richard', 'Joseph', 'Thomas', 'Christopher']
        last_names = ['Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez']
        
        player_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        # Create player record
        player_data = {
            'player': player_name,
            'player_id': f"Player{i:03d}",
            'season': season,
            'age': age,
            'games_played': games_played,
            'touches_per_game': touches_per_game,
            'yards_per_touch': yards_per_touch,
            'injury_history': injury_history,
            'position': position,
            'injury': injury,
            'injury_risk_score': total_risk
        }
        
        data.append(player_data)
    
    return pd.DataFrame(data)

def main():
    """Generate RB data for all seasons."""
    
    print("Generating realistic RB data for 2021-2024...")
    
    all_data = []
    
    for season in [2021, 2022, 2023, 2024]:
        print(f"Generating {season} season data...")
        season_data = generate_rb_season_data(season, n_players=60)
        all_data.append(season_data)
    
    # Combine all seasons
    combined_data = pd.concat(all_data, ignore_index=True)
    
    # Save to CSV
    output_file = 'data/rb_synthetic_data.csv'
    combined_data.to_csv(output_file, index=False)
    
    print(f"\nData generation complete!")
    print(f"Total records: {len(combined_data)}")
    print(f"Output file: {output_file}")
    
    # Print summary statistics
    print(f"\nSummary by season:")
    for season in [2021, 2022, 2023, 2024]:
        season_data = combined_data[combined_data['season'] == season]
        injury_rate = season_data['injury'].mean()
        avg_age = season_data['age'].mean()
        avg_touches = season_data['touches_per_game'].mean()
        print(f"  {season}: {len(season_data)} players, {injury_rate:.1%} injury rate, avg age {avg_age:.1f}, avg touches {avg_touches:.1f}")
    
    print(f"\nOverall injury rate: {combined_data['injury'].mean():.1%}")
    print(f"Average age: {combined_data['age'].mean():.1f}")
    print(f"Average touches per game: {combined_data['touches_per_game'].mean():.1f}")
    
    # Show sample of the data
    print(f"\nSample data:")
    print(combined_data.head(10).to_string(index=False))

if __name__ == "__main__":
    main()


