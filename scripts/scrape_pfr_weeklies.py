
"""
Download PFR weekly Receiving & Rushing logs for many players for a given season.
Input: CSV with columns [player_id, player] (from discover_rbs_from_pfr.py)
Output: CSV per player in data/weekly_raw/{season}/{player_id}.csv
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

def fetch_weekly(player_id: str, season: int) -> pd.DataFrame:
    """Fetch weekly game log data for a player."""
    url = f"{BASE}/players/{player_id[0]}/{player_id}/gamelog/{season}/"
    session = _make_session()
    
    resp = _get_with_retries(session, url)
    
    # Try different table IDs that PFR might use
    table_ids = ["receiving_and_rushing", "rushing_and_receiving", "receiving", "rushing"]
    
    df = None
    for table_id in table_ids:
        try:
            df = _parse_commented_table(resp.text, table_id)
            if df is not None and len(df) > 0:
                break
        except:
            continue
    
    if df is None or len(df) == 0:
        raise RuntimeError(f"No weekly table found for {player_id} {season}")
    
    # Ensure we have the columns we need
    keep = ["Week", "Age", "Tm", "Opp", "Tgt", "Rec", "Yds", "TD", "Att", "Yds.1", "TD.1", "GS"]
    for k in keep:
        if k not in df.columns:
            df[k] = None
    
    # Select and rename columns
    out = df[keep].copy()
    out.rename(columns={
        "Tm": "team", "Opp": "opp", "Att": "rush_att", "Rec": "receptions", 
        "Tgt": "targets", "Yds": "rec_yds", "TD": "rec_td", 
        "Yds.1": "rush_yds", "TD.1": "rush_td"
    }, inplace=True)
    
    # Clean up Week column - keep only numeric weeks
    out = out[pd.to_numeric(out["Week"], errors="coerce").notna()]
    out["Week"] = out["Week"].astype(int)
    
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--players_csv", required=True, help="CSV with at least player_id, player")
    ap.add_argument("--out_dir", default="data/weekly_raw")
    ap.add_argument("--pause", type=float, default=1.5, help="seconds between requests")
    args = ap.parse_args()

    players = pd.read_csv(args.players_csv)
    out_root = os.path.join(args.out_dir, str(args.season))
    os.makedirs(out_root, exist_ok=True)

    print(f"Processing {len(players)} players for {args.season} season...")
    print(f"Output directory: {out_root}")
    print(f"Pause between requests: {args.pause}s")

    successful = 0
    failed = 0

    for i, r in players.iterrows():
        pid = r["player_id"]
        name = r.get("player", pid)
        
        try:
            df = fetch_weekly(pid, args.season)
            df.insert(0, "player_id", pid)
            df.insert(1, "player", name)
            df.insert(2, "year", args.season)
            
            path = os.path.join(out_root, f"{pid}.csv")
            df.to_csv(path, index=False)
            
            successful += 1
            print(f"[{i+1}/{len(players)}] ✓ {name} → {path} ({len(df)} weeks)")
            
        except Exception as e:
            failed += 1
            print(f"[{i+1}/{len(players)}] ✗ {name} FAILED: {e}")
        
        # Polite delay between requests
        if i < len(players) - 1:  # Don't sleep after the last request
            time.sleep(args.pause)

    print(f"\nProcessing complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/(successful+failed)*100:.1f}%")

if __name__ == "__main__":
    main()
