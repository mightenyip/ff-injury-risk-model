#!/usr/bin/env python3
"""
Test Browser Scraper Setup
This script helps test the browser scraper with a single player before starting the full process.
"""

import pandas as pd
import os

def test_single_player():
    """Test the browser scraper setup with a single player"""
    
    # Load the URLs
    urls_file = "data/pfr_scraping_urls.csv"
    if not os.path.exists(urls_file):
        print("❌ URLs file not found. Run browser_scraper_helper.py first!")
        return
    
    urls_df = pd.read_csv(urls_file)
    
    # Get a test player (first one from 2024 season)
    test_player = urls_df[urls_df['season'] == 2024].iloc[0]
    
    print("=== BROWSER SCRAPER TEST ===")
    print(f"Testing with: {test_player['player']} ({test_player['season']})")
    print(f"URL: {test_player['url']}")
    print()
    
    print("=== TEST STEPS ===")
    print("1. Open this URL in your browser:")
    print(f"   {test_player['url']}")
    print()
    print("2. Open DevTools (F12 or Cmd+Option+I)")
    print("3. Go to Console tab")
    print("4. Copy the code from: pfr_scraper.js")
    print("5. Paste and press Enter")
    print("6. Check if a CSV downloads")
    print()
    
    print("=== EXPECTED RESULT ===")
    print(f"File should download as: {test_player['pfr_id']}_{test_player['season']}_gamelog.csv")
    print()
    
    print("=== IF IT WORKS ===")
    print("✅ Great! The scraper is working. You can now:")
    print("   - Open multiple tabs (10-15 at a time)")
    print("   - Run the scraper on each tab")
    print("   - Process all 664 players")
    print()
    
    print("=== IF IT FAILS ===")
    print("❌ Check the console for error messages")
    print("   - Make sure you're on the game log page")
    print("   - Try refreshing the page")
    print("   - Check if PFR is blocking your IP")
    print()
    
    # Show the JavaScript code location
    js_file = "pfr_scraper.js"
    if os.path.exists(js_file):
        print(f"JavaScript code is in: {js_file}")
        print("Copy the entire contents of that file to paste in the console.")
    else:
        print("❌ JavaScript file not found!")

def show_quick_start():
    """Show quick start instructions"""
    print("\n=== QUICK START ===")
    print("1. Run this test with one player first")
    print("2. If successful, open 10-15 tabs with different players")
    print("3. Run the scraper on each tab")
    print("4. Move downloaded CSVs to data/weekly_raw/")
    print("5. Process the data with your injury model")
    print()
    print("The browser approach avoids all anti-bot measures!")
    print("Each CSV download takes just a few seconds.")

def main():
    """Main function"""
    print("Browser Scraper Test Setup")
    print("=" * 40)
    
    test_single_player()
    show_quick_start()

if __name__ == "__main__":
    main()
