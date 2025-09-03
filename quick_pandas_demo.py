#!/usr/bin/env python3
"""
Quick pandas demo with RB data
"""

import pandas as pd
import matplotlib.pyplot as plt

# Load the data
df = pd.read_csv('data/rbs_2024.csv')

print("🚀 Quick Pandas Demo with RB Data 🚀")
print("=" * 50)

# 1. Basic DataFrame operations
print("\n1️⃣ Basic DataFrame Info:")
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(f"Data types:\n{df.dtypes}")

# 2. Data exploration
print("\n2️⃣ Data Exploration:")
print(f"First 5 rows:\n{df.head()}")
print(f"\nLast 5 rows:\n{df.tail()}")
print(f"\nRandom 5 rows:\n{df.sample(5)}")

# 3. Descriptive statistics
print("\n3️⃣ Descriptive Statistics:")
print(f"Player count: {len(df)}")
print(f"Unique players: {df['player'].nunique()}")
print(f"Unique player IDs: {df['player_id'].nunique()}")

# 4. Value counts and grouping
print("\n4️⃣ Value Counts:")
print(f"Player ID distribution:\n{df['player_id'].value_counts().head(10)}")

# 5. String operations
print("\n5️⃣ String Operations:")
print(f"Longest player name: '{df['player'].str.len().idxmax()}' ({df['player'].str.len().max()} chars)")
print(f"Shortest player name: '{df['player'].str.len().idxmin()}' ({df['player'].str.len().min()} chars)")
print(f"Average name length: {df['player'].str.len().mean():.1f} characters")

# 6. Filtering examples
print("\n6️⃣ Filtering Examples:")
print(f"Players with names starting with 'A': {len(df[df['player'].str.startswith('A')])}")
print(f"Players with names ending with 'n': {len(df[df['player'].str.endswith('n')])}")
print(f"Players with 'Jr' in name: {len(df[df['player'].str.contains('Jr')])}")

# 7. Create a simple visualization
print("\n7️⃣ Creating Simple Chart...")
plt.figure(figsize=(10, 6))
id_counts = df['player_id'].value_counts().head(15)
bars = plt.bar(range(len(id_counts)), id_counts.values, color='skyblue')
plt.title('Top 15 Player ID Letters (2024 RBs)', fontsize=14, fontweight='bold')
plt.xlabel('Player ID Letter')
plt.ylabel('Count')
plt.xticks(range(len(id_counts)), id_counts.index)
plt.grid(axis='y', alpha=0.3)

# Add value labels on bars
for i, (bar, count) in enumerate(zip(bars, id_counts.values)):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
             str(count), ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig('quick_rb_chart.png', dpi=150, bbox_inches='tight')
print("📊 Chart saved as: quick_rb_chart.png")

# 8. Data export examples
print("\n8️⃣ Data Export Examples:")
print("Exporting filtered data...")

# Export players with names starting with 'A'
a_players = df[df['player'].str.startswith('A')]
a_players.to_csv('players_starting_with_A.csv', index=False)
print(f"  - Players starting with 'A': {len(a_players)} → players_starting_with_A.csv")

# Export top 10 by player ID frequency
top_ids = df['player_id'].value_counts().head(10)
top_ids.to_csv('top_player_ids.csv')
print(f"  - Top 10 player IDs → top_player_ids.csv")

# Export sample data
df.sample(20).to_csv('random_20_players.csv', index=False)
print(f"  - Random 20 players → random_20_players.csv")

print("\n✅ Demo complete! Check the generated files:")
print("  📊 quick_rb_chart.png - Simple bar chart")
print("  📋 players_starting_with_A.csv - Filtered data")
print("  📋 top_player_ids.csv - Top player IDs")
print("  📋 random_20_players.csv - Random sample")
