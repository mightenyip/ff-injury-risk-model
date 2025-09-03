
"""
Merge a player's weekly log with their team's schedule to make a full 1..18 week table.
Adds played (1/0), reason (optional), targets/rush_att/receptions defaulting to 0 on DNPs.
"""
import argparse, os, pandas as pd

def merge_player_schedule(weekly_csv:str, schedule_csv:str, out_csv:str):
    w = pd.read_csv(weekly_csv)
    s = pd.read_csv(schedule_csv)
    team = (w["team"].dropna().astype(str).str.upper().iloc[0]) if "team" in w.columns and len(w["team"].dropna())>0 else s["team"].iloc[0]
    year = int(w["year"].iloc[0]) if "year" in w.columns else int(s["year"].iloc[0])
    s_use = s[["Week","team","year"]].copy()
    s_use = s_use[(s_use["team"]==team) & (s_use["year"]==year)]
    merged = s_use.merge(w, on="Week", how="left", suffixes=("","_w"))
    merged["played"] = merged["player"].notna().astype(int)
    for col, default in [("targets",0),("receptions",0),("rush_att",0)]:
        if col not in merged.columns:
            merged[col] = 0
        merged[col] = merged[col].fillna(default)
    if "reason" not in merged.columns:
        merged["reason"] = None
    keep = ["player","player_id","year","team","Week","targets","receptions","rush_att","played","reason"]
    for k in keep:
        if k not in merged.columns: merged[k] = None
    out = merged[keep]
    out.to_csv(out_csv, index=False)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weekly_csv", required=True)
    ap.add_argument("--schedule_csv", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = merge_player_schedule(args.weekly_csv, args.schedule_csv, args.out)
    print(f"Wrote joined weekly+sched to {args.out} ({len(out)} rows)")

if __name__ == "__main__":
    main()
