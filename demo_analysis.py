#!/usr/bin/env python3
"""
Demo script showing pandas analysis and visualization of RB data
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set up plotting style
plt.style.use('default')
sns.set_palette("husl")

def load_and_analyze_data():
    """Load the scraped RB data and show various analyses"""
    
    print("🏈 RB Data Analysis Demo 🏈")
    print("=" * 50)
    
    # Load the data
    df_2024 = pd.read_csv('data/rbs_2024.csv')
    df_2023 = pd.read_csv('data/rbs_2023.csv')
    
    print(f"\n📊 Data Overview:")
    print(f"2024 Season: {len(df_2024)} RBs")
    print(f"2023 Season: {len(df_2023)} RBs")
    
    # Basic stats
    print(f"\n📈 Basic Statistics:")
    print(f"Total unique players across both seasons: {len(set(df_2024['player'].tolist() + df_2023['player'].tolist()))}")
    
    # Player ID analysis
    print(f"\n🆔 Player ID Analysis:")
    print(f"2024 Player ID distribution (first letter):")
    id_counts_2024 = df_2024['player_id'].value_counts().head(10)
    print(id_counts_2024)
    
    # Create some visualizations
    create_visualizations(df_2024, df_2023)
    
    # Show sample data
    print(f"\n📋 Sample Data (2024 Top 10):")
    print(df_2024.head(10).to_string(index=False))
    
    # Team analysis (if we had team data)
    print(f"\n🔍 Data Quality Check:")
    print(f"Missing player names: {df_2024['player'].isnull().sum()}")
    print(f"Missing URLs: {df_2024['pfr_url'].isnull().sum()}")
    print(f"Missing player IDs: {df_2024['player_id'].isnull().sum()}")

def create_visualizations(df_2024, df_2023):
    """Create various charts and visualizations"""
    
    print(f"\n🎨 Creating Visualizations...")
    
    # Create a figure with multiple subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('RB Data Analysis Dashboard', fontsize=16, fontweight='bold')
    
    # 1. Player ID Distribution (Pie Chart)
    ax1 = axes[0, 0]
    id_counts = df_2024['player_id'].value_counts().head(8)
    ax1.pie(id_counts.values, labels=id_counts.index, autopct='%1.1f%%', startangle=90)
    ax1.set_title('Top 8 Player ID Letters (2024)')
    
    # 2. Season Comparison (Bar Chart)
    ax2 = axes[0, 1]
    seasons = ['2023', '2024']
    counts = [len(df_2023), len(df_2024)]
    bars = ax2.bar(seasons, counts, color=['skyblue', 'lightcoral'])
    ax2.set_title('RB Count by Season')
    ax2.set_ylabel('Number of RBs')
    
    # Add value labels on bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{count}', ha='center', va='bottom')
    
    # 3. Player Name Length Distribution (Histogram)
    ax3 = axes[1, 0]
    name_lengths = df_2024['player'].str.len()
    ax3.hist(name_lengths, bins=20, color='lightgreen', edgecolor='black', alpha=0.7)
    ax3.set_title('Distribution of Player Name Lengths (2024)')
    ax3.set_xlabel('Name Length (characters)')
    ax3.set_ylabel('Frequency')
    
    # Add mean line
    mean_length = name_lengths.mean()
    ax3.axvline(mean_length, color='red', linestyle='--', 
                label=f'Mean: {mean_length:.1f}')
    ax3.legend()
    
    # 4. Player ID Letter Frequency (Horizontal Bar)
    ax4 = axes[1, 1]
    letter_counts = df_2024['player_id'].value_counts().head(15)
    y_pos = np.arange(len(letter_counts))
    bars = ax4.barh(y_pos, letter_counts.values, color='gold')
    ax4.set_yticks(y_pos)
    ax4.set_yticklabels(letter_counts.index)
    ax4.set_xlabel('Count')
    ax4.set_title('Player ID Letter Frequency (2024)')
    
    # Add value labels
    for i, (bar, count) in enumerate(zip(bars, letter_counts.values)):
        ax4.text(count + 0.5, i, str(count), va='center')
    
    plt.tight_layout()
    
    # Save the plot
    output_file = 'rb_analysis_dashboard.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Dashboard saved as: {output_file}")
    
    # Show the plot
    plt.show()

def show_dataframe_info():
    """Show detailed dataframe information"""
    
    print(f"\n🔍 Detailed DataFrame Information:")
    print("=" * 50)
    
    df_2024 = pd.read_csv('data/rbs_2024.csv')
    
    print(f"\nDataFrame Info:")
    print(df_2024.info())
    
    print(f"\nDataFrame Description:")
    print(df_2024.describe(include='all'))
    
    print(f"\nFirst few rows:")
    print(df_2024.head())
    
    print(f"\nLast few rows:")
    print(df_2024.tail())
    
    print(f"\nColumn names:")
    for i, col in enumerate(df_2024.columns):
        print(f"  {i+1}. {col}")
    
    print(f"\nData types:")
    print(df_2024.dtypes)

def create_summary_report():
    """Create a comprehensive summary report"""
    
    print(f"\n📋 Creating Summary Report...")
    
    df_2024 = pd.read_csv('data/rbs_2024.csv')
    df_2023 = pd.read_csv('data/rbs_2023.csv')
    
    # Create a summary DataFrame
    summary_data = {
        'Metric': [
            'Total RBs (2024)',
            'Total RBs (2023)',
            'Unique Players (2024)',
            'Unique Players (2023)',
            'Most Common ID Letter (2024)',
            'Most Common ID Letter (2023)',
            'Longest Player Name (2024)',
            'Shortest Player Name (2024)',
            'Average Name Length (2024)',
            'Data Completeness (2024)'
        ],
        'Value': [
            len(df_2024),
            len(df_2023),
            df_2024['player'].nunique(),
            df_2023['player'].nunique(),
            df_2024['player_id'].mode()[0] if not df_2024['player_id'].mode().empty else 'N/A',
            df_2023['player_id'].mode()[0] if not df_2023['player_id'].mode().empty else 'N/A',
            df_2024['player'].str.len().max(),
            df_2024['player'].str.len().min(),
            round(df_2024['player'].str.len().mean(), 1),
            f"{((df_2024.notna().sum() / len(df_2024)) * 100).round(1)}%"
        ]
    }
    
    summary_df = pd.DataFrame(summary_data)
    
    print(f"\n📊 Summary Report:")
    print(summary_df.to_string(index=False))
    
    # Save summary
    summary_df.to_csv('rb_summary_report.csv', index=False)
    print(f"\n💾 Summary report saved as: rb_summary_report.csv")

if __name__ == "__main__":
    try:
        # Check if data files exist
        if not Path('data/rbs_2024.csv').exists():
            print("❌ Error: data/rbs_2024.csv not found!")
            print("Please run the scraping script first:")
            print("python3 scripts/discover_rbs_from_pfr_curl.py --season 2024")
            exit(1)
        
        # Run all analyses
        load_and_analyze_data()
        show_dataframe_info()
        create_summary_report()
        
        print(f"\n✅ Analysis complete! Check the generated files:")
        print(f"  📊 rb_analysis_dashboard.png - Visual dashboard")
        print(f"  📋 rb_summary_report.csv - Summary statistics")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
