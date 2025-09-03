#!/usr/bin/env python3
"""
Advanced pandas demo with RB data
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load all seasons
seasons = {}
for year in [2021, 2022, 2023, 2024]:
    df = pd.read_csv(f'data/rbs_{year}.csv')
    df['season'] = year
    seasons[year] = df

# Combine all data
all_data = pd.concat(seasons.values(), ignore_index=True)

print("🔥 Advanced Pandas Features Demo 🔥")
print("=" * 50)

# 1. Pivot Tables
print("\n1️⃣ Pivot Table - Player ID counts by season:")
pivot = all_data.pivot_table(
    values='player', 
    index='player_id', 
    columns='season', 
    aggfunc='count', 
    fill_value=0
)
print(pivot.head(10))

# 2. Cross-tabulation
print("\n2️⃣ Cross-tabulation - Player ID vs Season:")
crosstab = pd.crosstab(all_data['player_id'], all_data['season'], margins=True)
print(crosstab.head(10))

# 3. GroupBy operations
print("\n3️⃣ GroupBy Analysis:")
season_stats = all_data.groupby('season').agg({
    'player': ['count', 'nunique'],
    'player_id': lambda x: x.mode()[0] if not x.mode().empty else 'N/A'
}).round(2)
print(season_stats)

# 4. Advanced filtering with query
print("\n4️⃣ Advanced Filtering with .query():")
# Players whose names contain 'Williams'
williams_players = all_data.query("player.str.contains('Williams')", engine='python')
print(f"Players with 'Williams' in name: {len(williams_players)}")
print(williams_players[['player', 'season']].drop_duplicates().head())

# 5. String operations and regex
print("\n5️⃣ Advanced String Operations:")
# Extract first names
all_data['first_name'] = all_data['player'].str.split().str[0]
first_name_counts = all_data['first_name'].value_counts().head(10)
print("Most common first names:")
print(first_name_counts)

# 6. Window functions
print("\n6️⃣ Window Functions - Player name length ranking by season:")
all_data['name_length'] = all_data['player'].str.len()
all_data['name_rank'] = all_data.groupby('season')['name_length'].rank(method='dense', ascending=False)
longest_names = all_data.nsmallest(10, 'name_rank')[['player', 'season', 'name_length', 'name_rank']]
print(longest_names)

# 7. Create a heatmap
print("\n7️⃣ Creating Heatmap...")
plt.figure(figsize=(12, 8))

# Create a matrix of player ID counts by season
heatmap_data = all_data.pivot_table(
    values='player', 
    index='player_id', 
    columns='season', 
    aggfunc='count', 
    fill_value=0
)

sns.heatmap(heatmap_data, annot=True, cmap='YlOrRd', fmt='d', cbar_kws={'label': 'Number of Players'})
plt.title('Player ID Distribution Heatmap (2021-2024)', fontsize=14, fontweight='bold')
plt.ylabel('Player ID Letter')
plt.xlabel('Season')
plt.tight_layout()
plt.savefig('rb_heatmap.png', dpi=200, bbox_inches='tight')
print("📊 Heatmap saved as: rb_heatmap.png")

# 8. Export advanced analysis
print("\n8️⃣ Exporting Advanced Analysis...")

# Players who appeared in all seasons
four_season_df = all_data[all_data['player'].isin(
    all_data.groupby('player')['season'].nunique()[lambda x: x == 4].index
)]
four_season_df.to_csv('players_all_four_seasons.csv', index=False)
print(f"  - Players in all 4 seasons → players_all_four_seasons.csv")

# Player career summary
career_summary = all_data.groupby('player').agg({
    'season': ['count', 'min', 'max'],
    'player_id': 'first'
}).round(2)
career_summary.columns = ['seasons_played', 'first_season', 'last_season', 'player_id']
career_summary = career_summary.reset_index()
career_summary.to_csv('player_career_summary.csv', index=False)
print(f"  - Player career summary → player_career_summary.csv")

print(f"\n✨ Advanced analysis complete!")
print(f"Generated files:")
print(f"  📊 rb_heatmap.png - Player ID heatmap")
print(f"  📋 players_all_four_seasons.csv - Consistent players")
print(f"  📋 player_career_summary.csv - Career spans")
