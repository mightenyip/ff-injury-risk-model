#!/usr/bin/env python3
"""
Comprehensive RB analysis across multiple seasons (2021-2024)
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style
plt.style.use('default')
sns.set_palette("Set2")

def load_all_seasons():
    """Load all season data"""
    seasons = {}
    for year in [2021, 2022, 2023, 2024]:
        file_path = f'data/rbs_{year}.csv'
        if Path(file_path).exists():
            df = pd.read_csv(file_path)
            df['season'] = year
            seasons[year] = df
            print(f"✓ Loaded {year}: {len(df)} RBs")
        else:
            print(f"✗ Missing {file_path}")
    return seasons

def create_multi_season_dashboard(seasons):
    """Create a comprehensive dashboard across seasons"""
    
    # Combine all seasons
    all_data = pd.concat(seasons.values(), ignore_index=True)
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('RB Analysis Dashboard (2021-2024)', fontsize=16, fontweight='bold')
    
    # 1. RB Count by Season
    ax1 = axes[0, 0]
    season_counts = all_data['season'].value_counts().sort_index()
    bars = ax1.bar(season_counts.index, season_counts.values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
    ax1.set_title('RB Count by Season')
    ax1.set_xlabel('Season')
    ax1.set_ylabel('Number of RBs')
    
    # Add value labels
    for bar, count in zip(bars, season_counts.values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                str(count), ha='center', va='bottom', fontweight='bold')
    
    # 2. Player ID Distribution (Overall)
    ax2 = axes[0, 1]
    id_counts = all_data['player_id'].value_counts().head(12)
    ax2.pie(id_counts.values, labels=id_counts.index, autopct='%1.1f%%', startangle=90)
    ax2.set_title('Player ID Distribution (All Seasons)')
    
    # 3. Name Length Distribution by Season
    ax3 = axes[0, 2]
    for year, df in seasons.items():
        ax3.hist(df['player'].str.len(), alpha=0.6, label=str(year), bins=15)
    ax3.set_title('Name Length Distribution by Season')
    ax3.set_xlabel('Name Length (characters)')
    ax3.set_ylabel('Frequency')
    ax3.legend()
    
    # 4. Top Player IDs by Season (Stacked Bar)
    ax4 = axes[1, 0]
    season_id_data = []
    top_ids = all_data['player_id'].value_counts().head(8).index
    
    for season_year in sorted(seasons.keys()):
        season_df = seasons[season_year]
        counts = [len(season_df[season_df['player_id'] == pid]) for pid in top_ids]
        season_id_data.append(counts)
    
    season_id_data = np.array(season_id_data).T
    bottom = np.zeros(len(seasons))
    colors = plt.cm.Set3(np.linspace(0, 1, len(top_ids)))
    
    for i, (pid, color) in enumerate(zip(top_ids, colors)):
        ax4.bar(sorted(seasons.keys()), season_id_data[i], bottom=bottom, 
                label=pid, color=color)
        bottom += season_id_data[i]
    
    ax4.set_title('Top Player IDs by Season (Stacked)')
    ax4.set_xlabel('Season')
    ax4.set_ylabel('Count')
    ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 5. Unique vs Total Players
    ax5 = axes[1, 1]
    season_stats = []
    for year in sorted(seasons.keys()):
        df = seasons[year]
        season_stats.append({
            'Season': year,
            'Total': len(df),
            'Unique': df['player'].nunique()
        })
    
    stats_df = pd.DataFrame(season_stats)
    x = np.arange(len(stats_df))
    width = 0.35
    
    ax5.bar(x - width/2, stats_df['Total'], width, label='Total RBs', color='lightblue')
    ax5.bar(x + width/2, stats_df['Unique'], width, label='Unique Players', color='lightcoral')
    
    ax5.set_title('Total vs Unique Players by Season')
    ax5.set_xlabel('Season')
    ax5.set_ylabel('Count')
    ax5.set_xticks(x)
    ax5.set_xticklabels(stats_df['Season'])
    ax5.legend()
    
    # 6. Player Career Span
    ax6 = axes[1, 2]
    player_seasons = all_data.groupby('player')['season'].agg(['count', 'min', 'max'])
    career_lengths = player_seasons['count']
    
    career_counts = career_lengths.value_counts().sort_index()
    ax6.bar(career_counts.index, career_counts.values, color='gold')
    ax6.set_title('Player Career Spans (2021-2024)')
    ax6.set_xlabel('Number of Seasons')
    ax6.set_ylabel('Number of Players')
    
    # Add value labels
    for i, (seasons_played, count) in enumerate(career_counts.items()):
        ax6.text(seasons_played, count + 1, str(count), ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('multi_season_rb_dashboard.png', dpi=300, bbox_inches='tight')
    print("📊 Multi-season dashboard saved as: multi_season_rb_dashboard.png")
    
    return all_data

def analyze_player_careers(all_data):
    """Analyze player careers across seasons"""
    
    print("\n🏃‍♂️ Player Career Analysis:")
    print("=" * 50)
    
    # Players who appeared in all 4 seasons
    player_seasons = all_data.groupby('player')['season'].nunique()
    four_season_players = player_seasons[player_seasons == 4].index.tolist()
    
    print(f"Players in all 4 seasons ({len(four_season_players)}):")
    for player in sorted(four_season_players):
        print(f"  - {player}")
    
    # Players who appeared in 3 seasons
    three_season_players = player_seasons[player_seasons == 3].index.tolist()
    print(f"\nPlayers in 3 seasons ({len(three_season_players)}):")
    for player in sorted(three_season_players)[:10]:  # Show first 10
        seasons_list = all_data[all_data['player'] == player]['season'].tolist()
        print(f"  - {player} ({seasons_list})")
    if len(three_season_players) > 10:
        print(f"  ... and {len(three_season_players) - 10} more")
    
    # New players each season
    print(f"\n🆕 New Players by Season:")
    for year in sorted([2022, 2023, 2024]):
        prev_players = set()
        for prev_year in range(2021, year):
            if prev_year in [2021, 2022, 2023, 2024]:
                prev_file = f'data/rbs_{prev_year}.csv'
                if Path(prev_file).exists():
                    prev_df = pd.read_csv(prev_file)
                    prev_players.update(prev_df['player'].tolist())
        
        curr_file = f'data/rbs_{year}.csv'
        if Path(curr_file).exists():
            curr_df = pd.read_csv(curr_file)
            curr_players = set(curr_df['player'].tolist())
            new_players = curr_players - prev_players
            print(f"  {year}: {len(new_players)} new RBs")

def main():
    print("🏈 Multi-Season RB Analysis 🏈")
    print("=" * 50)
    
    # Load all seasons
    seasons = load_all_seasons()
    
    if not seasons:
        print("❌ No season data found!")
        return
    
    # Basic overview
    print(f"\n�� Season Overview:")
    total_rbs = sum(len(df) for df in seasons.values())
    for year, df in sorted(seasons.items()):
        print(f"  {year}: {len(df):3d} RBs")
    print(f"  Total: {total_rbs:3d} RB entries")
    
    # Create visualizations
    all_data = create_multi_season_dashboard(seasons)
    
    # Analyze careers
    analyze_player_careers(all_data)
    
    # Create summary table
    summary_data = []
    for year in sorted(seasons.keys()):
        df = seasons[year]
        summary_data.append({
            'Season': year,
            'Total_RBs': len(df),
            'Unique_Players': df['player'].nunique(),
            'Avg_Name_Length': round(df['player'].str.len().mean(), 1),
            'Most_Common_ID': df['player_id'].mode()[0] if not df['player_id'].mode().empty else 'N/A'
        })
    
    summary_df = pd.DataFrame(summary_data)
    print(f"\n📋 Season Summary:")
    print(summary_df.to_string(index=False))
    
    # Save summary
    summary_df.to_csv('multi_season_summary.csv', index=False)
    print(f"\n💾 Summary saved as: multi_season_summary.csv")
    
    print(f"\n✅ Analysis complete! Generated files:")
    print(f"  📊 multi_season_rb_dashboard.png - Comprehensive dashboard")
    print(f"  📋 multi_season_summary.csv - Season statistics")

if __name__ == "__main__":
    main()
