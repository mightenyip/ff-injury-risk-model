
"""
Fetch a team's schedule table (weeks, opponents) from PFR and save CSV.
"""
import argparse
import os
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup, Comment
from typing import Optional

BASE = "https://www.pro-football-reference.com"

def _make_session() -> requests.Session:
    """Create a session with realistic browser headers."""
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/118.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Referer": "https://www.pro-football-reference.com/",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
    })
    return s

def _get_with_retries(session: requests.Session, url: str, max_tries: int = 3, backoff: float = 2.0) -> requests.Response:
    """Get URL with retry logic and exponential backoff."""
    for attempt in range(1, max_tries + 1):
        try:
            resp = session.get(url, timeout=30)
            if resp.status_code == 200:
                return resp
            # If 403/429, back off and try again
            if resp.status_code in (403, 429, 503):
                time.sleep(backoff * attempt)
                if attempt >= 2:
                    # rotate UA slightly to avoid naive blocks
                    session.headers["User-Agent"] = session.headers["User-Agent"].replace("118.0.0.0", f"118.0.{attempt}.0")
                continue
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            if attempt == max_tries:
                raise e
            time.sleep(backoff * attempt)
            continue
    resp.raise_for_status()
    return resp

def _parse_commented_table(html: str, table_id: str) -> Optional[pd.DataFrame]:
    """Parse table that might be wrapped in HTML comments."""
    soup = BeautifulSoup(html, "lxml")
    
    # Try direct table first
    table = soup.find("table", id=table_id)
    if table is not None:
        try:
            return pd.read_html(str(table))[0]
        except:
            pass
    
    # Look for commented table
    wrapper = soup.find(id=f"all_{table_id}")
    if wrapper:
        for comment in wrapper.find_all(string=lambda text: isinstance(text, Comment)):
            if f'id="{table_id}"' in comment or f"id='{table_id}'" in comment:
                try:
                    return pd.read_html(str(comment))[0]
                except:
                    continue
    
    # Fallback: search any comment on the page
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if f'id="{table_id}"' in comment or f"id='{table_id}'" in comment:
            try:
                return pd.read_html(str(comment))[0]
            except:
                continue
    
    return None

def team_id_from_abbrev(abbrev: str) -> str:
    """Convert team abbreviation to PFR team ID."""
    return abbrev.lower()

def fetch_schedule(team_abbrev: str, season: int) -> pd.DataFrame:
    """Fetch team schedule from PFR."""
    tid = team_id_from_abbrev(team_abbrev)
    url = f"{BASE}/teams/{tid}/{season}.htm"
    
    session = _make_session()
    
    # Polite delay
    time.sleep(1.0)
    
    resp = _get_with_retries(session, url)
    
    # Try to parse the games table
    df = _parse_commented_table(resp.text, "games")
    
    if df is None or len(df) == 0:
        raise RuntimeError(f"Could not find games table for {team_abbrev} {season}")
    
    # Clean up the data
    df = df[pd.to_numeric(df["Week"], errors="coerce").notna()]
    df["Week"] = df["Week"].astype(int)
    
    # Ensure we have the columns we need
    keep = ["Week", "Date", "Opponent", "Result"]
    for k in keep:
        if k not in df.columns:
            df[k] = None
    
    # Select and rename columns
    out = df[keep].copy()
    out.rename(columns={"Opponent": "opp"}, inplace=True)
    
    # Add team and year columns
    out.insert(0, "team", team_abbrev.upper())
    out.insert(1, "year", season)
    
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--team", required=True, help="Team abbreviation, e.g., GNB, DAL, SFO")
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    
    print(f"Fetching schedule for {args.team} {args.season}...")
    
    try:
        df = fetch_schedule(args.team, args.season)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        
        df.to_csv(args.out, index=False)
        print(f"✓ Wrote schedule to {args.out} ({len(df)} rows)")
        print(f"Weeks: {df['Week'].min()} - {df['Week'].max()}")
        
    except Exception as e:
        print(f"✗ Error fetching schedule: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
