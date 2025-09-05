#!/usr/bin/env python3
"""
Advanced PFR scraper with better browser simulation and cookie handling.
This approach uses more sophisticated techniques to bypass blocking.
"""
import requests
import pandas as pd
import time
import random
from bs4 import BeautifulSoup
import os
import json
from urllib.parse import urljoin, urlparse
import re

class AdvancedPFRScraper:
    """Advanced scraper with better browser simulation."""
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_advanced_headers()
        self.base_url = "https://www.pro-football-reference.com"
        
    def setup_advanced_headers(self):
        """Set up very realistic browser headers."""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Referer': 'https://www.pro-football-reference.com/',
            'Origin': 'https://www.pro-football-reference.com'
        })
        
        # Set some cookies that might help
        self.session.cookies.set('sr_cookie', '1', domain='.pro-football-reference.com')
        
    def get_page_with_retry(self, url, max_retries=5):
        """Get a page with advanced retry logic."""
        
        # First, try to get the main page to establish a session
        if not hasattr(self, '_session_established'):
            print("  Establishing session with main page...")
            try:
                main_response = self.session.get(self.base_url, timeout=30)
                if main_response.status_code == 200:
                    self._session_established = True
                    print("  ✓ Session established")
                    time.sleep(random.uniform(2, 5))
                else:
                    print(f"  ✗ Main page failed: {main_response.status_code}")
            except Exception as e:
                print(f"  ✗ Session establishment failed: {e}")
        
        for attempt in range(max_retries):
            try:
                print(f"  Attempt {attempt + 1}: Fetching {url}")
                
                # Add a small random delay
                time.sleep(random.uniform(1, 3))
                
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    print(f"  ✓ Success! Status: {response.status_code}")
                    return response.text
                elif response.status_code == 403:
                    print(f"  ✗ Forbidden (403) - attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        # Try different strategies
                        self.rotate_strategy(attempt)
                        wait_time = random.uniform(10, 20)
                        print(f"  Waiting {wait_time:.1f}s before retry...")
                        time.sleep(wait_time)
                elif response.status_code == 429:
                    print(f"  ✗ Rate limited (429) - attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        wait_time = random.uniform(30, 60)
                        print(f"  Waiting {wait_time:.1f}s for rate limit...")
                        time.sleep(wait_time)
                else:
                    print(f"  ✗ HTTP {response.status_code} - attempt {attempt + 1}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Request error: {e} - attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(5, 15))
        
        print(f"  ✗ Failed after {max_retries} attempts")
        return None
    
    def rotate_strategy(self, attempt):
        """Rotate different strategies to avoid detection."""
        strategies = [
            self.rotate_user_agent,
            self.rotate_headers,
            self.clear_cookies,
            self.add_proxy_headers
        ]
        
        strategy = strategies[attempt % len(strategies)]
        strategy()
    
    def rotate_user_agent(self):
        """Rotate user agent."""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        new_ua = random.choice(user_agents)
        self.session.headers['User-Agent'] = new_ua
        print(f"  Rotated to User-Agent: {new_ua[:50]}...")
    
    def rotate_headers(self):
        """Rotate other headers."""
        accept_languages = [
            'en-US,en;q=0.9',
            'en-US,en;q=0.8,en;q=0.7',
            'en-GB,en;q=0.9,en;q=0.8',
            'en-CA,en;q=0.9,en;q=0.8'
        ]
        self.session.headers['Accept-Language'] = random.choice(accept_languages)
        print(f"  Rotated Accept-Language")
    
    def clear_cookies(self):
        """Clear cookies and start fresh."""
        self.session.cookies.clear()
        print(f"  Cleared cookies")
    
    def add_proxy_headers(self):
        """Add headers that might help with proxy detection."""
        self.session.headers['X-Forwarded-For'] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        print(f"  Added proxy headers")
    
    def try_alternative_urls(self, player_id, season):
        """Try alternative URL patterns if the main one fails."""
        alternative_patterns = [
            f"https://www.pro-football-reference.com/players/{player_id[0]}/{player_id}/gamelog/{season}/",
            f"https://www.pro-football-reference.com/players/{player_id[0]}/{player_id}/gamelog/{season}",
            f"https://www.pro-football-reference.com/players/{player_id[0]}/{player_id}/gamelog/",
            f"https://www.pro-football-reference.com/players/{player_id[0]}/{player_id}/"
        ]
        
        for pattern in alternative_patterns:
            print(f"  Trying alternative URL: {pattern}")
            html_content = self.get_page_with_retry(pattern)
            if html_content:
                return html_content
        
        return None
    
    def scrape_player_stats_advanced(self, player_id, season):
        """Advanced player stats scraping with multiple fallback methods."""
        
        # Try main URL first
        main_url = f"https://www.pro-football-reference.com/players/{player_id[0]}/{player_id}/gamelog/{season}/"
        html_content = self.get_page_with_retry(main_url)
        
        # If main URL fails, try alternatives
        if not html_content:
            print(f"  Main URL failed, trying alternatives...")
            html_content = self.try_alternative_urls(player_id, season)
        
        if not html_content:
            print(f"  ✗ All URL attempts failed for {player_id} {season}")
            return None
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for stats table with multiple possible IDs
        stats_table = None
        possible_ids = ['stats', 'gamelog', 'game_logs', 'player_stats']
        
        for table_id in possible_ids:
            stats_table = soup.find('table', {'id': table_id})
            if stats_table:
                print(f"  ✓ Found stats table with ID: {table_id}")
                break
        
        if not stats_table:
            # Try to find any table that looks like stats
            all_tables = soup.find_all('table')
            for table in all_tables:
                if table.find('th', text=re.compile(r'Week|Game|Rush|Rec', re.I)):
                    stats_table = table
                    print(f"  ✓ Found stats table by content")
                    break
        
        if not stats_table:
            print(f"  ✗ No stats table found for {player_id} {season}")
            return None
        
        # Extract table data
        rows = stats_table.find_all('tr')
        game_stats = []
        
        for row in rows[1:]:  # Skip header row
            cells = row.find_all(['td', 'th'])
            if len(cells) > 8:  # Ensure we have enough columns
                game_data = {}
                
                try:
                    # Extract key stats (be more flexible with column positions)
                    game_data['week'] = cells[0].get_text(strip=True) if len(cells) > 0 else ''
                    game_data['date'] = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                    game_data['team'] = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                    game_data['opponent'] = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                    
                    # Look for rushing and receiving stats in various positions
                    for i, cell in enumerate(cells):
                        cell_text = cell.get_text(strip=True)
                        if 'Rush' in cell_text or 'Att' in cell_text:
                            if i + 2 < len(cells):
                                game_data['rush_att'] = cells[i].get_text(strip=True)
                                game_data['rush_yds'] = cells[i+1].get_text(strip=True)
                                game_data['rush_td'] = cells[i+2].get_text(strip=True)
                        elif 'Rec' in cell_text:
                            if i + 2 < len(cells):
                                game_data['rec'] = cells[i].get_text(strip=True)
                                game_data['rec_yds'] = cells[i+1].get_text(strip=True)
                                game_data['rec_td'] = cells[i+2].get_text(strip=True)
                    
                    # Set defaults if not found
                    game_data.setdefault('rush_att', '0')
                    game_data.setdefault('rush_yds', '0')
                    game_data.setdefault('rush_td', '0')
                    game_data.setdefault('rec', '0')
                    game_data.setdefault('rec_yds', '0')
                    game_data.setdefault('rec_td', '0')
                    
                    # Only add if it's a regular season game
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
    
    def scrape_season_rbs_advanced(self, season, max_players=3):
        """Advanced season scraping with better error handling."""
        print(f"\n{'='*60}")
        print(f"ADVANCED SCRAPING {season} SEASON RB DATA")
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
            
            # Get season stats directly (skip player info for now)
            game_stats = self.scrape_player_stats_advanced(player_id, season)
            
            if game_stats:
                # Calculate season totals
                season_totals = {
                    'player_id': player_id,
                    'player_name': player_name,
                    'season': season,
                    'age': None,  # We'll add this later if needed
                    'games_played': len(game_stats),
                    'total_rush_att': sum(int(g.get('rush_att', 0)) for g in game_stats),
                    'total_rush_yds': sum(int(g.get('rush_yds', 0)) for g in game_stats),
                    'total_rec': sum(int(g.get('rec', 0)) for g in game_stats),
                    'total_rec_yds': sum(int(g.get('rec_yds', 0)) for g in game_stats),
                    'total_touches': sum(int(g.get('rush_att', 0)) + int(g.get('rec', 0)) for g in game_stats),
                    'avg_touches_per_game': sum(int(g.get('rush_att', 0)) + int(g.get('rec', 0)) for g in game_stats) / len(game_stats) if game_stats else 0
                }
                
                # Calculate yards per touch
                total_touches = season_totals['total_touches']
                if total_touches > 0:
                    total_yards = season_totals['total_rush_yds'] + season_totals['total_rec_yds']
                    season_totals['avg_yards_per_touch'] = total_yards / total_touches
                else:
                    season_totals['avg_yards_per_touch'] = 0
                
                all_data.append(season_totals)
                print(f"  ✓ Added season totals for {player_name}")
                
                # Save individual game data
                game_data_file = f"data/weekly_raw/{season}/{player_id}_games.csv"
                os.makedirs(os.path.dirname(game_data_file), exist_ok=True)
                
                games_df = pd.DataFrame(game_stats)
                games_df.to_csv(game_data_file, index=False)
                print(f"  ✓ Saved {len(game_stats)} games to {game_data_file}")
            
            # Longer delay between players
            delay = random.uniform(15, 30)
            print(f"  Waiting {delay:.1f}s before next player...")
            time.sleep(delay)
        
        if all_data:
            # Save season summary
            season_df = pd.DataFrame(all_data)
            output_file = f"data/rb_{season}_scraped_advanced.csv"
            season_df.to_csv(output_file, index=False)
            print(f"\n✓ Saved {len(all_data)} players to {output_file}")
            
            return season_df
        else:
            print(f"\n✗ No data collected for {season}")
            return None

def main():
    """Main function to run the advanced scraper."""
    print("Advanced PFR RB Scraper")
    print("=" * 50)
    
    scraper = AdvancedPFRScraper()
    
    # Test with a very small sample first
    print("\nStarting with 2024 season (limited to 2 players for testing)...")
    
    # Scrape 2024 season with limited players
    season_data = scraper.scrape_season_rbs_advanced(2024, max_players=2)
    
    if season_data is not None:
        print(f"\n✓ Successfully scraped {len(season_data)} players!")
        print("\nSample data:")
        print(season_data.head().to_string(index=False))
        
        # Ask if user wants to continue
        print(f"\n{'='*60}")
        response = input("Continue with more players/seasons? (y/n): ").strip().lower()
        
        if response == 'y':
            # Try more players from 2024
            print(f"\nTrying more players from 2024...")
            scraper.scrape_season_rbs_advanced(2024, max_players=5)
        
        print(f"\nAdvanced scraping complete!")
    else:
        print(f"\n✗ Advanced scraping failed. PFR may have very strict blocking.")

if __name__ == "__main__":
    main()


