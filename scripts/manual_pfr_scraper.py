#!/usr/bin/env python3
"""
Manual PFR scraper for RB data with better headers and manual verification.
This approach should bypass the blocking issues we encountered.
"""
import requests
import pandas as pd
import time
import random
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

class ManualPFRScraper:
    """Manual scraper for Pro Football Reference with enhanced headers."""
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_headers()
        
    def setup_headers(self):
        """Set up realistic browser headers."""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
    
    def get_page(self, url, max_retries=3):
        """Get a page with retry logic and better error handling."""
        for attempt in range(max_retries):
            try:
                print(f"  Attempt {attempt + 1}: Fetching {url}")
                
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    print(f"  ✓ Success! Status: {response.status_code}")
                    return response.text
                elif response.status_code == 403:
                    print(f"  ✗ Forbidden (403) - attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        wait_time = random.uniform(5, 15)
                        print(f"  Waiting {wait_time:.1f}s before retry...")
                        time.sleep(wait_time)
                        # Rotate user agent
                        self.rotate_user_agent()
                else:
                    print(f"  ✗ HTTP {response.status_code} - attempt {attempt + 1}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Request error: {e} - attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(3, 8))
        
        print(f"  ✗ Failed after {max_retries} attempts")
        return None
    
    def rotate_user_agent(self):
        """Rotate user agent to avoid detection."""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        new_ua = random.choice(user_agents)
        self.session.headers['User-Agent'] = new_ua
        print(f"  Rotated to User-Agent: {new_ua[:50]}...")
    
    def scrape_player_stats(self, player_id, season):
        """Scrape individual player stats for a season."""
        url = f"https://www.pro-football-reference.com/players/{player_id[0]}/{player_id}/gamelog/{season}/"
        
        print(f"\nScraping {player_id} for {season}...")
        html_content = self.get_page(url)
        
        if not html_content:
            return None
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for the main stats table
        stats_table = soup.find('table', {'id': 'stats'})
        if not stats_table:
            print(f"  ✗ No stats table found for {player_id} {season}")
            return None
        
        # Extract table data
        rows = stats_table.find_all('tr')
        game_stats = []
        
        for row in rows[1:]:  # Skip header row
            cells = row.find_all(['td', 'th'])
            if len(cells) > 10:  # Ensure we have enough columns
                game_data = {}
                
                # Extract key stats (adjust indices based on actual table structure)
                try:
                    game_data['week'] = cells[0].get_text(strip=True) if len(cells) > 0 else ''
                    game_data['date'] = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                    game_data['team'] = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                    game_data['opponent'] = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                    game_data['result'] = cells[4].get_text(strip=True) if len(cells) > 4 else ''
                    
                    # Rushing stats
                    game_data['rush_att'] = cells[5].get_text(strip=True) if len(cells) > 5 else '0'
                    game_data['rush_yds'] = cells[6].get_text(strip=True) if len(cells) > 6 else '0'
                    game_data['rush_td'] = cells[7].get_text(strip=True) if len(cells) > 7 else '0'
                    
                    # Receiving stats
                    game_data['rec'] = cells[8].get_text(strip=True) if len(cells) > 8 else '0'
                    game_data['rec_yds'] = cells[9].get_text(strip=True) if len(cells) > 9 else '0'
                    game_data['rec_td'] = cells[10].get_text(strip=True) if len(cells) > 10 else '0'
                    
                    # Only add if it's a regular season game (not preseason/playoffs)
                    if game_data['week'].isdigit() and int(game_data['week']) <= 18:
                        game_stats.append(game_data)
                        
                except (IndexError, ValueError) as e:
                    continue
        
        if game_stats:
            print(f"  ✓ Found {len(game_stats)} regular season games")
            return game_stats
        else:
            print(f"  ✗ No regular season games found")
            return None
    
    def scrape_player_info(self, player_id):
        """Scrape basic player information."""
        url = f"https://www.pro-football-reference.com/players/{player_id[0]}/{player_id}.htm"
        
        print(f"\nScraping player info for {player_id}...")
        html_content = self.get_page(url)
        
        if not html_content:
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        player_info = {'player_id': player_id}
        
        # Get player name
        name_elem = soup.find('h1', {'itemprop': 'name'})
        if name_elem:
            player_info['name'] = name_elem.get_text(strip=True)
        
        # Get position
        position_elem = soup.find('strong', text=lambda x: x and 'Position:' in x)
        if position_elem and position_elem.parent:
            position_text = position_elem.parent.get_text()
            if 'RB' in position_text:
                player_info['position'] = 'RB'
            else:
                player_info['position'] = 'Other'
        
        # Get birth date for age calculation
        birth_elem = soup.find('span', {'id': 'necro-birth'})
        if birth_elem and birth_elem.get('data-birth'):
            birth_date = birth_elem['data-birth']
            player_info['birth_date'] = birth_date
            
            # Calculate age for 2024 season
            try:
                birth_year = int(birth_date.split('-')[0])
                player_info['age_2024'] = 2024 - birth_year
            except:
                player_info['age_2024'] = None
        
        print(f"  ✓ Player info: {player_info.get('name', 'Unknown')} - {player_info.get('position', 'Unknown')}")
        return player_info
    
    def scrape_season_rbs(self, season, max_players=20):
        """Scrape RB data for a specific season."""
        print(f"\n{'='*60}")
        print(f"SCRAPING {season} SEASON RB DATA")
        print(f"{'='*60}")
        
        # Load the fixed player IDs for this season
        csv_file = f"data/rbs_{season}_fixed.csv"
        if not os.path.exists(csv_file):
            print(f"❌ File not found: {csv_file}")
            print("Please run scripts/fix_player_ids.py first!")
            return None
        
        players_df = pd.read_csv(csv_file)
        print(f"Loaded {len(players_df)} players from {csv_file}")
        
        # Limit to max_players for testing
        if len(players_df) > max_players:
            print(f"Limiting to first {max_players} players for testing...")
            players_df = players_df.head(max_players)
        
        all_data = []
        
        for idx, row in players_df.iterrows():
            player_id = row['player_id']
            player_name = row['player']
            
            print(f"\n[{idx+1}/{len(players_df)}] Processing {player_name} ({player_id})")
            
            # Get player info first
            player_info = self.scrape_player_info(player_id)
            if not player_info or player_info.get('position') != 'RB':
                print(f"  Skipping {player_name} - not a RB")
                continue
            
            # Get season stats
            game_stats = self.scrape_player_stats(player_id, season)
            
            if game_stats:
                # Calculate season totals
                season_totals = {
                    'player_id': player_id,
                    'player_name': player_name,
                    'season': season,
                    'age': player_info.get('age_2024'),
                    'games_played': len(game_stats),
                    'total_rush_att': sum(int(g.get('rush_att', 0)) for g in game_stats),
                    'total_rush_yds': sum(int(g.get('rush_yds', 0)) for g in game_stats),
                    'total_rec': sum(int(g.get('rec', 0)) for g in game_stats),
                    'total_rec_yds': sum(int(g.get('rec_yds', 0)) for g in game_stats),
                    'total_touches': sum(int(g.get('rush_att', 0)) + int(g.get('rec', 0)) for g in game_stats),
                    'avg_touches_per_game': sum(int(g.get('rush_att', 0)) + int(g.get('rec', 0)) for g in game_stats) / len(game_stats) if game_stats else 0,
                    'avg_yards_per_touch': 0
                }
                
                # Calculate yards per touch separately to avoid complex one-liner
                total_touches = sum(int(g.get('rush_att', 0)) + int(g.get('rec', 0)) for g in game_stats)
                if total_touches > 0:
                    total_yards = sum(int(g.get('rush_yds', 0)) + int(g.get('rec_yds', 0)) for g in game_stats)
                    season_totals['avg_yards_per_touch'] = total_yards / total_touches
                
                all_data.append(season_totals)
                print(f"  ✓ Added season totals for {player_name}")
                
                # Save individual game data
                game_data_file = f"data/weekly_raw/{season}/{player_id}_games.csv"
                os.makedirs(os.path.dirname(game_data_file), exist_ok=True)
                
                games_df = pd.DataFrame(game_stats)
                games_df.to_csv(game_data_file, index=False)
                print(f"  ✓ Saved {len(game_stats)} games to {game_data_file}")
            
            # Random delay between players
            delay = random.uniform(3, 8)
            print(f"  Waiting {delay:.1f}s before next player...")
            time.sleep(delay)
        
        if all_data:
            # Save season summary
            season_df = pd.DataFrame(all_data)
            output_file = f"data/rb_{season}_scraped.csv"
            season_df.to_csv(output_file, index=False)
            print(f"\n✓ Saved {len(all_data)} players to {output_file}")
            
            return season_df
        else:
            print(f"\n✗ No data collected for {season}")
            return None

def main():
    """Main function to run the manual scraper."""
    print("Manual PFR RB Scraper")
    print("=" * 50)
    
    scraper = ManualPFRScraper()
    
    # Test with a small sample first
    print("\nStarting with 2024 season (limited to 5 players for testing)...")
    
    # Scrape 2024 season with limited players
    season_data = scraper.scrape_season_rbs(2024, max_players=5)
    
    if season_data is not None:
        print(f"\n✓ Successfully scraped {len(season_data)} players!")
        print("\nSample data:")
        print(season_data.head().to_string(index=False))
        
        # Ask if user wants to continue with more seasons
        print(f"\n{'='*60}")
        response = input("Continue with more seasons? (y/n): ").strip().lower()
        
        if response == 'y':
            seasons = [2021, 2022, 2023]
            for season in seasons:
                print(f"\nScraping {season} season...")
                scraper.scrape_season_rbs(season, max_players=10)
                time.sleep(random.uniform(10, 20))  # Longer delay between seasons
        
        print(f"\nManual scraping complete!")
    else:
        print(f"\n✗ Scraping failed. Check the output above for errors.")

if __name__ == "__main__":
    main()
