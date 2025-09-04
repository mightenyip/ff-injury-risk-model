#!/usr/bin/env python3
"""
Browser Scraper Helper for Pro Football Reference
This script helps automate the browser-based scraping process by generating URLs
and instructions for each player, avoiding the need for server-side scraping.
"""

import pandas as pd
import os
from pathlib import Path

def load_rb_data(season):
    """Load RB data for a specific season"""
    csv_path = f"data/rbs_{season}_fixed.csv"
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    else:
        print(f"Warning: {csv_path} not found")
        return pd.DataFrame()

def generate_player_urls(season):
    """Generate PFR game log URLs for all RBs in a season"""
    df = load_rb_data(season)
    if df.empty:
        return []
    
    urls = []
    for _, row in df.iterrows():
        if pd.notna(row.get('pfr_url')) and pd.notna(row.get('player_id')):
            # Extract the player ID from the URL if available
            pfr_id = row.get('player_id', '')
            if pfr_id:
                # Create the game log URL
                game_log_url = f"https://www.pro-football-reference.com/players/{pfr_id[0]}/{pfr_id}/gamelog/{season}/"
                urls.append({
                    'player': row.get('player', 'Unknown'),
                    'season': season,
                    'pfr_id': pfr_id,
                    'url': game_log_url
                })
    
    return urls

def create_scraping_instructions():
    """Create the JavaScript code and instructions for browser scraping"""
    js_code = '''(() => {
  // Infer season & player id from URL
  const url = new URL(location.href);
  const seasonMatch = url.pathname.match(/gamelog\/(\\d{4})/);
  const season = seasonMatch ? seasonMatch[1] : (new Date().getFullYear() + '');
  const pid = url.pathname.split('/')[3]?.toLowerCase() || 'player';

  // Find a table that's sometimes hidden inside HTML comments
  function findCommentedTable(candidateIds) {
    for (const id of candidateIds) {
      const container = document.getElementById('all_' + id) || document;
      const walker = document.createTreeWalker(container, NodeFilter.SHOW_COMMENT, null);
      let node;
      while ((node = walker.nextNode())) {
        if (node.nodeValue.includes(`id="${id}"`)) {
          const div = document.createElement('div');
          div.innerHTML = node.nodeValue;
          const tbl = div.querySelector(`table#${id}`);
          if (tbl) return tbl;
        }
      }
      const live = document.querySelector(`table#${id}`);
      if (live) return live;
    }
    // Fallback: any game-loggy table
    return document.querySelector(
      'table#rushing_and_receiving, table#receiving_and_rushing, table#passing, table#receiving, table#defense'
    );
  }

  const table = findCommentedTable([
    'rushing_and_receiving', 'receiving_and_rushing', 'passing', 'receiving', 'defense'
  ]);
  if (!table) { console.warn('PFR: game-log table not found'); return; }

  // Build CSV (skip repeated header rows inside tbody)
  const clean = s => (s || '').replace(/\\s+/g, ' ').trim().replace(/"/g, '""');
  const thead = [...table.querySelectorAll('thead tr')].pop();
  const header = thead ? [...thead.children].map(c => `"${clean(c.innerText)}"`).join(',') + '\\n' : '';

  const rows = [...table.querySelectorAll('tbody tr')].filter(tr => !tr.classList.contains('thead'));
  const body = rows.map(tr => {
    const cells = [...tr.querySelectorAll('th,td')];
    return cells.map(c => `"${clean(c.innerText)}"`).join(',');
  }).join('\\n');

  const csv = header + body + '\\n';
  const blob = new Blob([csv], { type: 'text/csv' });
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(blob),
    download: `${pid}_${season}_gamelog.csv`
  });
  document.body.appendChild(a); a.click(); URL.revokeObjectURL(a.href); a.remove();
})();'''
    
    return js_code

def generate_scraping_plan():
    """Generate a complete scraping plan for all seasons"""
    seasons = [2021, 2022, 2023, 2024]
    all_urls = []
    
    print("=== PFR Browser Scraping Plan ===\n")
    
    for season in seasons:
        urls = generate_player_urls(season)
        all_urls.extend(urls)
        print(f"Season {season}: {len(urls)} players")
    
    print(f"\nTotal players to scrape: {len(all_urls)}")
    
    # Create the JavaScript code file
    js_file = "pfr_scraper.js"
    with open(js_file, 'w') as f:
        f.write(create_scraping_instructions())
    
    print(f"\nJavaScript scraper saved to: {js_file}")
    
    # Create a CSV with all URLs for easy access
    urls_df = pd.DataFrame(all_urls)
    urls_csv = "data/pfr_scraping_urls.csv"
    urls_df.to_csv(urls_csv, index=False)
    print(f"All URLs saved to: {urls_csv}")
    
    # Create step-by-step instructions
    instructions = f"""
=== STEP-BY-STEP SCRAPING INSTRUCTIONS ===

1. OPEN MULTIPLE TABS:
   - Open {len(all_urls)} browser tabs
   - Copy URLs from: {urls_csv}
   - Load each player's game log page

2. SETUP THE SCRAPER:
   - Open DevTools on any tab (F12 or Cmd+Option+I)
   - Go to Console tab
   - Copy the code from: {js_file}
   - Paste and press Enter

3. SCRAPE EACH TAB:
   - Go to each tab
   - Press F12 (or Cmd+Option+I) to open DevTools
   - Go to Console tab
   - Paste the JavaScript code and press Enter
   - CSV will automatically download

4. ORGANIZE DOWNLOADS:
   - Move all CSV files to: data/weekly_raw/
   - Files will be named: playerid_season_gamelog.csv

5. PROCESS THE DATA:
   - Run the data processing scripts to combine all CSVs
   - Apply the injury risk model

=== TIPS ===
- Open 10-15 tabs at once to speed up the process
- Use Cmd+Click (Mac) or Ctrl+Click (Windows) to open multiple tabs
- The scraper will automatically detect the correct table format
- Each CSV download includes the player ID and season in the filename

=== EXPECTED OUTPUT ===
- {len(all_urls)} CSV files with game log data
- Each file contains rushing/receiving statistics per game
- Data ready for injury risk model analysis
"""
    
    with open("PFR_SCRAPING_INSTRUCTIONS.txt", 'w') as f:
        f.write(instructions)
    
    print(f"\nDetailed instructions saved to: PFR_SCRAPING_INSTRUCTIONS.txt")
    
    return all_urls

def create_bookmarklet():
    """Create a bookmarklet version of the scraper"""
    js_code = create_scraping_instructions()
    # Convert to bookmarklet format
    bookmarklet = f"javascript:{js_code.replace(chr(10), '').replace(chr(13), '')}"
    
    with open("pfr_bookmarklet.txt", 'w') as f:
        f.write("=== PFR SCRAPER BOOKMARKLET ===\n\n")
        f.write("1. Create a new bookmark in your browser\n")
        f.write("2. Set the URL to the following code:\n\n")
        f.write(bookmarklet)
        f.write("\n\n3. Click the bookmark on any PFR game log page to download CSV\n")
    
    print("Bookmarklet instructions saved to: pfr_bookmarklet.txt")
    return bookmarklet

def main():
    """Main function to run the browser scraper helper"""
    print("Setting up PFR Browser Scraping Helper...\n")
    
    # Generate the scraping plan
    urls = generate_scraping_plan()
    
    # Create bookmarklet
    create_bookmarklet()
    
    print("\n=== SETUP COMPLETE ===")
    print("You now have everything needed to scrape PFR data using your browser:")
    print("1. pfr_scraper.js - JavaScript code for DevTools Console")
    print("2. pfr_bookmarklet.txt - Instructions for creating a bookmarklet")
    print("3. PFR_SCRAPING_INSTRUCTIONS.txt - Complete step-by-step guide")
    print("4. data/pfr_scraping_urls.csv - All player URLs to scrape")
    print("\nStart with opening a few tabs and testing the scraper on one player!")

if __name__ == "__main__":
    main()
