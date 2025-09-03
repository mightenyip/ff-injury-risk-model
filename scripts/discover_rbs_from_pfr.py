
"""
Discover RB player IDs/URLs for a season from PFR rushing page.
Saves a CSV with columns: player, player_id, pfr_url
"""
import time
import random
from typing import Optional
import argparse
import pandas as pd
import requests
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin

BASE = "https://www.pro-football-reference.com"

# Multiple User-Agents to rotate through
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
]

def _make_session() -> requests.Session:
    s = requests.Session()
    # Random User-Agent
    s.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.pro-football-reference.com/",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    })
    return s

def _get_with_retries(session: requests.Session, url: str, max_tries: int = 5, backoff: float = 2.0) -> requests.Response:
    for attempt in range(1, max_tries + 1):
        try:
            # Random delay between attempts
            if attempt > 1:
                delay = backoff * attempt + random.uniform(1, 3)
                print(f"Attempt {attempt}: Waiting {delay:.1f}s before retry...")
                time.sleep(delay)
            
            # Rotate User-Agent on retries
            if attempt > 1:
                session.headers["User-Agent"] = random.choice(USER_AGENTS)
                print(f"Rotated User-Agent for attempt {attempt}")
            
            print(f"Attempt {attempt}: Making request with User-Agent: {session.headers['User-Agent'][:50]}...")
            resp = session.get(url, timeout=30)
            print(f"Attempt {attempt}: Got response with status code {resp.status_code}")
            
            if resp.status_code == 200:
                return resp
            
            # If 403/429, back off and try again with a slightly different UA on later attempts
            if resp.status_code in (403, 429, 503):
                print(f"Attempt {attempt}: Got {resp.status_code} - backing off...")
                if attempt >= 3:
                    # rotate UA slightly to avoid naive blocks
                    current_ua = session.headers["User-Agent"]
                    if "Chrome" in current_ua and "120.0.0.0" in current_ua:
                        session.headers["User-Agent"] = current_ua.replace("120.0.0.0", f"120.0.{attempt}.0")
                    else:
                        # Fallback: just pick a different UA from our list
                        session.headers["User-Agent"] = random.choice(USER_AGENTS)
                    print(f"Modified User-Agent for attempt {attempt}")
                continue
            
            # Handle other error codes
            if resp.status_code == 403:
                print(f"403 Forbidden on attempt {attempt}. This might be a temporary block.")
            elif resp.status_code == 429:
                print(f"429 Too Many Requests on attempt {attempt}. Rate limited.")
            elif resp.status_code == 503:
                print(f"503 Service Unavailable on attempt {attempt}. Server overloaded.")
            else:
                print(f"HTTP {resp.status_code} on attempt {attempt}")
            
            if attempt == max_tries:
                print(f"Final attempt failed with status {resp.status_code}")
                resp.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            print(f"Request error on attempt {attempt}: {e}")
            if attempt == max_tries:
                raise e
    
    raise RuntimeError(f"Failed after {max_tries} attempts")

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
    comment_html: Optional[str] = None
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

def _extract_comment_block(html: str, table_id: str) -> str:
    """Return the raw HTML comment string that contains the table."""
    soup = BeautifulSoup(html, "lxml")
    wrapper = soup.find(id=f"all_{table_id}")
    if wrapper:
        for c in wrapper.find_all(string=lambda text: isinstance(text, Comment)):
            if f'id="{table_id}"' in c or f"id='{table_id}'" in c:
                return c
    # fallback
    for c in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if f'id="{table_id}"' in c or f"id='{table_id}'" in c:
            return c
    raise ValueError(f"Could not locate commented block for table '{table_id}'.")

def get_player_list(season: int) -> pd.DataFrame:
    """
    Returns the rushing leaderboard for a given season (e.g., 2024),
    including player links so you can later visit each player's page.
    """
    url = f"{BASE}/years/{season}/rushing.htm"
    session = _make_session()

    # Polite delay before making request
    print("Waiting before making request...")
    time.sleep(random.uniform(2, 4))

    print(f"Fetching {url}")
    resp = _get_with_retries(session, url)
    print("Successfully retrieved page")
    
    df = _parse_commented_table(resp.text, table_id="rushing")
    print(f"Parsed table with {len(df)} rows")

    # Clean up: remove headers embedded in the tbody and summary rows
    if "Rk" in df.columns:
        df = df[df["Rk"].apply(lambda x: str(x).isdigit())].copy()

    # Normalize column names
    df.columns = [c.strip().lower().replace("%", "pct").replace(" ", "_") for c in df.columns]

    # Rebuild absolute player URLs from the page anchors
    soup = BeautifulSoup(resp.text, "lxml")
    # Find the table again to map names -> href
    # Use the commented HTML to ensure we see <a> tags
    table_html = _parse_commented_table(resp.text, table_id="rushing")
    # The pandas table loses links, so we parse links from the comment soup instead:
    link_map = {}
    # Build a soup from the commented HTML block
    commented_soup = BeautifulSoup(str(_extract_comment_block(resp.text, "rushing")), "lxml")
    for a in commented_soup.select(f'table#rushing tbody tr td[data-stat="player"] a'):
        name = a.get_text(strip=True)
        href = a.get("href")
        if href:
            link_map[name] = urljoin(BASE, href)

    # Attach URLs by merging on player name (pfr uses "player" column)
    name_col = "player" if "player" in df.columns else None
    if name_col:
        df["player_url"] = df[name_col].map(link_map)

    return df.reset_index(drop=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2024)
    parser.add_argument("--out", required=True, help="Output CSV file path")
    args = parser.parse_args()

    print(f"Discovering RBs for {args.season} season...")
    print("Using enhanced anti-blocking measures...")
    
    try:
        df = get_player_list(args.season)
        
        # Keep only RBs if needed (PFR table includes all players who rushed)
        if "pos" in df.columns:
            df = df[df["pos"].isin(["RB", "HB", "FB"])].copy()
        
        # Extract player_id from URL for compatibility with existing scripts
        df["player_id"] = df["player_url"].str.extract(r"/players/([^/]+)/[^/]+\.htm")
        
        # Rename columns to match expected format
        df = df.rename(columns={"player_url": "pfr_url"})
        
        # Select only the columns we need
        output_df = df[["player", "player_id", "pfr_url"]].copy()
        
        # Save to CSV
        output_df.to_csv(args.out, index=False)
        print(f"✓ Saved {len(output_df)} RB players → {args.out}")
        print(f"Columns: {list(output_df.columns)}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Wait a few minutes and try again")
        print("2. Check if PFR is accessible in your browser")
        print("3. Try using a VPN if you're being geo-blocked")
        print("4. The site might be temporarily blocking automated requests")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
