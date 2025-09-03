"""
Alternative RB discovery script using curl to bypass Python-specific blocking.
This script uses subprocess to call curl, which often works when Python requests are blocked.
"""
import argparse
import subprocess
import time
import random
import pandas as pd
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin
import os
import re

BASE = "https://www.pro-football-reference.com"

def _make_curl_command(url: str) -> list:
    """Create a curl command with realistic browser headers."""
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    ]
    
    user_agent = random.choice(user_agents)
    
    return [
        "curl",
        "-s",  # Silent mode
        "-L",  # Follow redirects
        "-H", f"User-Agent: {user_agent}",
        "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "-H", "Accept-Language: en-US,en;q=0.9",
        "-H", "Accept-Encoding: gzip, deflate, br",
        "-H", "Connection: keep-alive",
        "-H", f"Referer: {BASE}/",
        "-H", "Sec-Fetch-Dest: document",
        "-H", "Sec-Fetch-Mode: navigate",
        "-H", "Sec-Fetch-Site: same-origin",
        "-H", "Sec-Fetch-User: ?1",
        "-H", "Upgrade-Insecure-Requests: 1",
        "--compressed",
        url
    ]

def _get_with_curl(url: str, max_tries: int = 3) -> str:
    """Fetch URL content using curl."""
    for attempt in range(1, max_tries + 1):
        try:
            if attempt > 1:
                delay = random.uniform(2, 5)
                print(f"Attempt {attempt}: Waiting {delay:.1f}s before retry...")
                time.sleep(delay)
            
            print(f"Fetching {url} (attempt {attempt})")
            cmd = _make_curl_command(url)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and result.stdout:
                print("✓ Successfully retrieved page")
                return result.stdout
            else:
                print(f"✗ Curl failed (attempt {attempt}): {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"Timeout on attempt {attempt}")
        except Exception as e:
            print(f"Error on attempt {attempt}: {e}")
        
        if attempt == max_tries:
            raise RuntimeError(f"Failed to fetch {url} after {max_tries} attempts")
    
    raise RuntimeError("Unexpected error in _get_with_curl")

def _parse_commented_table(html: str, table_id: str) -> pd.DataFrame:
    """
    PFR often wraps tables in <!-- ... -->. This extracts the comment content
    that contains the table and reads it with pandas.
    """
    soup = BeautifulSoup(html, "lxml")
    # Try direct first (if not commented)
    table = soup.find("table", id=table_id)
    if table is not None:
        return pd.read_html(str(table))[0]

    # Look under the "all_" wrapper div and find HTML comments
    wrapper = soup.find(id=f"all_{table_id}")
    comment_html = None
    if wrapper:
        for c in wrapper.find_all(string=lambda text: isinstance(text, Comment)):
            if f'id="{table_id}"' in c or f"id='{table_id}'" in c:
                comment_html = c
                break
    if not comment_html:
        # Fallback: search any comment on the page (slower but robust)
        for c in soup.find_all(string=lambda text: isinstance(text, Comment)):
            if f'id="{table_id}"' in c or f"id='{table_id}'" in c:
                comment_html = c
                break

    if not comment_html:
        raise ValueError(f"Could not locate table '{table_id}' in page (might be renamed).")

    return pd.read_html(str(comment_html))[0]

def get_player_list(season: int) -> pd.DataFrame:
    """
    Returns the rushing leaderboard for a given season using curl.
    """
    url = f"{BASE}/years/{season}/rushing.htm"
    
    # Polite delay before making request
    print("Waiting before making request...")
    time.sleep(random.uniform(2, 4))
    
    html_content = _get_with_curl(url)
    
    # Save HTML for debugging if needed
    debug_file = f"debug_pfr_{season}.html"
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
        print(f"Saved HTML to {debug_file} for debugging")
    
    df = _parse_commented_table(html_content, table_id="rushing")
    print(f"Parsed table with {len(df)} rows")

    # Clean up: remove headers embedded in the tbody and summary rows
    # After flattening columns, check for 'rk' column
    if "rk" in df.columns:
        df = df[df["rk"].apply(lambda x: str(x).isdigit())].copy()
        print(f"After cleaning: {len(df)} rows remaining")
    else:
        print(f"Warning: 'rk' column not found. Available columns: {list(df.columns)}")

    # Normalize column names - handle multi-level columns
    if isinstance(df.columns, pd.MultiIndex):
        # Flatten multi-level columns
        df.columns = [col[1] if col[0].startswith('Unnamed') else f"{col[0]}_{col[1]}" for col in df.columns]
    
    # Normalize column names
    df.columns = [str(c).strip().lower().replace("%", "pct").replace(" ", "_") for c in df.columns]
    
    print(f"Normalized columns: {list(df.columns)}")
    
    # Debug: show the actual dataframe structure after processing
    print(f"Dataframe columns: {list(df.columns)}")
    print(f"Dataframe shape: {df.shape}")
    print(f"First few rows of player column: {df['player'].head(10).tolist() if 'player' in df.columns else 'No player column'}")
    
    # Debug: show the actual data in the first few rows
    print("First 3 rows of dataframe:")
    for i in range(min(3, len(df))):
        row = df.iloc[i]
        print(f"Row {i}: {dict(row)}")
    
    # Debug: check if player column exists and has data
    if 'player' in df.columns:
        print(f"Player column dtype: {df['player'].dtype}")
        print(f"Player column non-null count: {df['player'].count()}")
        print(f"Player column unique values (first 10): {df['player'].unique()[:10]}")
    else:
        print("Player column not found in dataframe")
        print(f"Available columns: {list(df.columns)}")

    # Extract player links using regex as the most reliable method
    link_map = {}
    print("Extracting player links using regex...")
    
    # Use regex to find all player links
    pattern = r'<a href="(/players/[^"]+\.htm)">([^<]+)</a>'
    matches = re.findall(pattern, html_content)
    
    for href, name in matches:
        if href.startswith("/players/") and "/gamelog/" not in href:
            if name and name in df["player"].values:
                link_map[name] = urljoin(BASE, href)
    
    print(f"Found {len(link_map)} player links with regex method")
    
    # Attach URLs by merging on player name
    name_col = "player" if "player" in df.columns else None
    if name_col:
        df["player_url"] = df[name_col].map(link_map)
    else:
        print(f"Warning: 'player' column not found. Available columns: {list(df.columns)}")
        df["player_url"] = None

    return df.reset_index(drop=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2024)
    # No output parameter needed - using default naming
    args = parser.parse_args()

    print(f"Discovering RBs for {args.season} season using curl...")
    print("This approach often bypasses Python-specific blocking.")
    
    try:
        df = get_player_list(args.season)
        
        # Keep only RBs if needed (PFR table includes all players who rushed)
        if "pos" in df.columns:
            df = df[df["pos"].isin(["RB", "HB", "FB"])].copy()
        
        # Extract player_id from URL for compatibility with existing scripts
        # Handle the case where player_url might be None
        df["player_id"] = df["player_url"].astype(str).str.extract(r"/players/([^/]+)/[^/]+\.htm")
        
        # Rename columns to match expected format
        df = df.rename(columns={"player_url": "pfr_url"})
        
        # Select only the columns we need
        output_df = df[["player", "player_id", "pfr_url"]].copy()
        
        # Save to CSV with default naming
        out = f"data/rbs_{args.season}.csv"
        output_df.to_csv(out, index=False)
        print(f"✓ Saved {len(output_df)} RB players → {out}")
        print(f"Columns: {list(output_df.columns)}")
        
        print(f"Dataframe columns: {list(df.columns)}")
        print(f"Dataframe shape: {df.shape}")
        print(f"First few rows of player column: {df['player'].head(10).tolist() if 'player' in df.columns else 'No player column'}")
        
        # Debug: show the actual data in the first few rows
        print("First 3 rows of dataframe:")
        for i in range(min(3, len(df))):
            row = df.iloc[i]
            print(f"Row {i}: {dict(row)}")
        
        # Debug: check if player column exists and has data
        if 'player' in df.columns:
            print(f"Player column dtype: {df['player'].dtype}")
            print(f"Player column non-null count: {df['player'].count()}")
            print(f"Player column unique values (first 10): {df['player'].unique()[:10]}")
        else:
            print("Player column not found in dataframe")
            print(f"Available columns: {list(df.columns)}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure curl is installed on your system")
        print("2. Check if PFR is accessible in your browser")
        print("3. Try using a VPN if you're being geo-blocked")
        print("4. The site might be temporarily blocking all automated requests")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
