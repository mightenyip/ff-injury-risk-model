"""
Download PFR weekly Receiving & Rushing logs using curl to bypass blocking.
Input: CSV with columns [player_id, player] (from discover_rbs_from_pfr.py)
Output: CSV per player in data/weekly_raw/{season}/{player_id}.csv
"""
import argparse
import os
import time
import subprocess
import pandas as pd
from bs4 import BeautifulSoup, Comment
from typing import Optional
import random

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
            
            cmd = _make_curl_command(url)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and result.stdout:
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
    """Fetch weekly game log data for a player using curl."""
    url = f"{BASE}/players/{player_id[0]}/{player_id}/gamelog/{season}/"
    
    html = _get_with_curl(url)
    
    # Try different table IDs that PFR might use
    table_ids = ["receiving_and_rushing", "rushing_and_receiving", "receiving", "rushing"]
    
    df = None
    for table_id in table_ids:
        try:
            df = _parse_commented_table(html, table_id)
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
    ap.add_argument("--pause", type=float, default=3.0, help="seconds between requests")
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


