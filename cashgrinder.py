import re
import os
import argparse
import zipfile
import pandas as pd
import csv

def parse_args():
    parser = argparse.ArgumentParser(description="Process week parameter.")
    parser.add_argument('--week', type=int, required=True, help="Enter the week")
    return parser.parse_args()

def normalize_name(name):
    """Normalize player name: strip, lowercase, remove extra spaces."""
    if pd.isna(name):
        return ""
    name = str(name).strip().lower()
    name = re.sub(r"\s+", " ", name)
    return name

def extract_usernames(dfs_dir):
    """
    Extract all usernames from lobby.txt by removing x<number> and Play tokens.
    Deduplicates usernames while preserving order.
    """
    file_path = os.path.join(dfs_dir, "lobby.txt")
    if not os.path.exists(file_path):
        print(f"⚠️ Lobby file not found: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Remove x<number> and Play
    text = re.sub(r'x\d+', '', text)
    text = text.replace('Play', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    usernames = text.split(' ') if text else []

    # Deduplicate while preserving order
    seen = set()
    clean_usernames = []
    for u in usernames:
        if u not in seen and u:
            seen.add(u)
            clean_usernames.append(u)

    return clean_usernames

def split_lineup(lineup_str):
    """Split a DFS lineup string into individual player names with positions."""
    if pd.isna(lineup_str):
        return []

    positions = {'QB', 'RB', 'WR', 'TE', 'FLEX', 'DST'}
    tokens = lineup_str.split()
    players = []
    current_pos = None
    current_name = []

    for token in tokens:
        if token.upper() in positions:
            if current_pos and current_name:
                players.append((current_pos.upper(), " ".join(current_name).strip()))
            current_pos = token.upper()
            current_name = []
        else:
            current_name.append(token)

    if current_pos and current_name:
        players.append((current_pos.upper(), " ".join(current_name).strip()))

    return players

def order_lineup(players):
    """Reorder lineup into standard DFS order."""
    order = ["QB", "RB", "RB", "WR", "WR", "WR", "TE", "FLEX", "DST"]
    ordered = []
    used = set()

    for pos in order:
        for p in players:
            if p[0] == pos and p not in used:
                ordered.append(p)
                used.add(p)
                break
    return ordered

def get_points_and_lineup_from_previous_week(dfs_dir, usernames, prev_week):
    """Return Points and Lineup for matched usernames from previous week's double-up CSVs."""
    prev_week_dir = os.path.join(os.path.dirname(dfs_dir), f"Week{prev_week}", "results")
    if not os.path.exists(prev_week_dir):
        print(f"⚠️ Previous week results directory not found: {prev_week_dir}")
        return []

    results = []

    for file in os.listdir(prev_week_dir):
        if file.lower().endswith(".zip") and "doubleup" in file.lower():
            zip_path = os.path.join(prev_week_dir, file)
            try:
                with zipfile.ZipFile(zip_path, "r") as z:
                    csv_files = [f for f in z.namelist() if f.lower().endswith(".csv")]
                    for csv_file in csv_files:
                        with z.open(csv_file) as csvdata:
                            df = pd.read_csv(csvdata)
                            if "EntryName" in df.columns:
                                df["EntryName"] = df["EntryName"].astype(str)
                                matched_rows = df[df["EntryName"].isin(usernames)]
                                if not matched_rows.empty:
                                    cols_to_keep = ["EntryName"]
                                    if "Points" in df.columns:
                                        cols_to_keep.append("Points")
                                    if "Lineup" in df.columns:
                                        cols_to_keep.append("Lineup")
                                    matched_rows = matched_rows[cols_to_keep]
                                    for _, row in matched_rows.iterrows():
                                        results.append({
                                            "username": row["EntryName"],
                                            "points": row.get("Points", None),
                                            "lineup": split_lineup(row.get("Lineup", "")),
                                        })
            except Exception as e:
                print(f"Error reading {file}: {e}")

    # Remove duplicates by username + points + lineup
    unique_results = []
    seen = set()
    for r in results:
        key = (r["username"], r["points"], tuple(r["lineup"]))
        if key not in seen:
            unique_results.append(r)
            seen.add(key)
    return unique_results

def calculate_projected_total(results, prev_week, dfs_dir):
    """Add projected points from DKETRProj.csv (column 'DK Proj') in previous week folder."""
    prev_week_dir = os.path.join(os.path.dirname(dfs_dir), f"Week{prev_week}")
    proj_file = os.path.join(prev_week_dir, "DKETRProj.csv")
    
    if not os.path.exists(proj_file):
        print(f"⚠️ Projection file not found: {proj_file}")
        return [], []

    proj_df = pd.read_csv(proj_file)
    proj_df["Player"] = proj_df["Player"].apply(normalize_name)
    proj_dict = dict(zip(proj_df["Player"], proj_df["DK Proj"]))

    enhanced_results = []
    missing_players = []

    for r in results:
        total_proj = 0
        lineup_proj = []
        ordered_lineup = order_lineup(r["lineup"])

        for pos, player in ordered_lineup:
            norm_name = normalize_name(player)
            proj_points = proj_dict.get(norm_name, 0)
            lineup_proj.append({"pos": pos, "player": player, "proj_points": proj_points})
            total_proj += proj_points

            if proj_points == 0:
                missing_players.append(player)

        enhanced_results.append({
            "username": r["username"],
            "points": r.get("points", None),
            "lineup": lineup_proj,
            "total_proj": total_proj
        })

    return enhanced_results, missing_players

if __name__ == '__main__':
    args = parse_args()
    week = args.week
    dfs_dir = f"G:\\My Drive\\Fantasy Football\\DFS\\2025\\Week{week}"

    usernames = extract_usernames(dfs_dir)
    print(f"✅ Extracted {len(usernames)} usernames from Week{week}.")

    prev_week = week - 1
    results = get_points_and_lineup_from_previous_week(dfs_dir, usernames, prev_week)
    matched_usernames = {r["username"] for r in results}
    unmatched_usernames = [u for u in usernames if u not in matched_usernames]

    final_results, missing_players = calculate_projected_total(results, prev_week, dfs_dir)

    if final_results:
        csv_data = []
        for r in final_results:
            lineup_names = [p["player"] for p in r['lineup']]
            csv_data.append({
                "username": r['username'],
                "actual_points": r.get('points', None),
                "total_proj": round(r['total_proj'], 2),
                "lineup": ", ".join(lineup_names)
            })

        # Sort by projected total (descending)
        csv_data.sort(key=lambda x: x['total_proj'], reverse=True)

        output_csv = os.path.join(dfs_dir, f"Week{week}_Lineups_Projected.csv")

        with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["username", "actual_points", "total_proj", "lineup"])
            writer.writeheader()
            writer.writerows(csv_data)

        # ✅ Summary
        print("\n📊 SUMMARY")
        print("──────────────")
        print(f"✅ Lineups processed: {len(final_results)}")
        print(f"⚠️ Usernames not matched in results: {len(unmatched_usernames)}")
        if unmatched_usernames:
            print("   ↳ " + ", ".join(unmatched_usernames))
        print(f"⚠️ Players not found in projections: {len(set(missing_players))}")
        if missing_players:
            print("   ↳ " + ", ".join(sorted(set(missing_players))))
        print(f"\n📄 Output written to: {output_csv}")

    else:
        print("\n❌ No matches found or projection file missing.")
