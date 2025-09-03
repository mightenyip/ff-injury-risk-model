#!/usr/bin/env python3
"""
Example workflow demonstrating the complete NFL injury risk modeling pipeline.
This script shows how to use all the components together.
"""

import os
import subprocess
import sys

def run_command(cmd, description):
    """Run a command and print the result."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"COMMAND: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("✓ SUCCESS")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("✗ FAILED")
        print("Error:", e.stderr)
        return False

def main():
    """Run the complete workflow example."""
    print("NFL INJURY RISK MODELING - COMPLETE WORKFLOW EXAMPLE")
    print("=" * 60)
    print("This script demonstrates the complete pipeline from data scraping to model training.")
    print("Note: This will take some time and requires internet access.")
    
    # Check if we're in the right directory
    if not os.path.exists('scripts'):
        print("Error: Please run this script from the project root directory.")
        sys.exit(1)
    
    # Step 1: Discover RBs for 2024 season
    print("\nStarting with 2024 season data...")
    if not run_command(
        "python3 scripts/discover_rbs_from_pfr.py --season 2024 --out data/rb_2024_players.csv",
        "Discover RB players for 2024 season"
    ):
        print("Failed to discover players. Stopping workflow.")
        return
    
    # Step 2: Download weekly logs (with a small sample for demo)
    print("\nNote: For demo purposes, we'll only process a few players to avoid overwhelming PFR servers.")
    if not run_command(
        "head -5 data/rb_2024_players.csv > data/rb_2024_sample.csv",
        "Create sample player list for demo"
    ):
        print("Failed to create sample list. Stopping workflow.")
        return
    
    if not run_command(
        "python3 scripts/scrape_pfr_weeklies.py --season 2024 --players_csv data/rb_2024_sample.csv --out_dir data/weekly_raw --pause 2.0",
        "Download weekly logs for sample players"
    ):
        print("Failed to download weekly logs. Stopping workflow.")
        return
    
    # Step 3: Get team schedules (for teams in our sample)
    print("\nGetting team schedules for teams in our sample...")
    # Extract unique teams from weekly data
    if not run_command(
        "find data/weekly_raw/2024 -name '*.csv' -exec head -1 {} \\; | grep -o '[A-Z][A-Z][A-Z]' | sort | uniq > data/teams_needed.txt",
        "Extract teams from weekly data"
    ):
        print("Failed to extract teams. Stopping workflow.")
        return
    
    # Read teams and get schedules
    try:
        with open('data/teams_needed.txt', 'r') as f:
            teams = [line.strip() for line in f if line.strip()]
        
        for team in teams[:3]:  # Limit to 3 teams for demo
            if not run_command(
                f"python3 scripts/scrape_team_schedule.py --team {team} --season 2024 --out data/schedules/{team.lower()}_2024.csv",
                f"Get schedule for {team}"
            ):
                print(f"Warning: Failed to get schedule for {team}, continuing...")
    except Exception as e:
        print(f"Warning: Could not process team schedules: {e}")
    
    # Step 4: Join weekly data with schedules
    if not run_command(
        "python3 scripts/bulk_join_weekly.py --season 2024",
        "Join weekly data with team schedules"
    ):
        print("Failed to join weekly data. Stopping workflow.")
        return
    
    # Step 5: Create season-level features
    if not run_command(
        "python3 scripts/build_rb_seasons.py --in_weekly data/weekly_joined/2024/all_joined.csv --out_seasons data/rb_seasons.csv",
        "Create season-level features"
    ):
        print("Failed to create season features. Stopping workflow.")
        return
    
    # Step 6: Train the model
    if not run_command(
        "python3 -m src.models.rb_model --in data/rb_seasons.csv --out data/rb_model.pkl",
        "Train injury risk model"
    ):
        print("Failed to train model. Stopping workflow.")
        return
    
    # Step 7: Test scoring (if we have enough data)
    print("\nTesting player scoring...")
    if not run_command(
        "python3 scripts/score_player.py --type rb --model data/rb_model.pkl --player '{\"age\":25,\"touches_prev\":250,\"career_touches_prior\":800,\"prior_multiweek_prev\":0}'",
        "Score example player"
    ):
        print("Warning: Player scoring failed, but model training was successful.")
    
    print("\n" + "="*60)
    print("WORKFLOW COMPLETE!")
    print("="*60)
    print("What was created:")
    print("✓ Player discovery: data/rb_2024_players.csv")
    print("✓ Weekly logs: data/weekly_raw/2024/")
    print("✓ Team schedules: data/schedules/")
    print("✓ Joined data: data/weekly_joined/2024/")
    print("✓ Season features: data/rb_seasons.csv")
    print("✓ Trained model: data/rb_model.pkl")
    print("\nYou can now:")
    print("1. Process more players by editing the sample list")
    print("2. Add more seasons for better model training")
    print("3. Use the trained model to score new players")
    print("4. Modify the feature engineering in build_rb_seasons.py")

if __name__ == "__main__":
    main()

