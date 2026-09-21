#!/usr/bin/env python3
r"""
Build a simple NFL DFS ownership comparison report.

Run:
    python OwnershipReport.py --week 2

Hardcoded base directory:
    G:\My Drive\Fantasy Football\DFS\2026

Expected layout:
    G:\My Drive\Fantasy Football\DFS\2026\
        Week2\
            DKETRProj.csv
            Results\
                contest1.zip
                contest2.zip
                contest3.zip

Output:
    Week2\ownership_review.csv

The output is one row per projected player:

    Player | DK Salary | Team | Small Field | Large Field |
    Contest1 | Contest2 | Contest3 | ...

Each tournament ZIP automatically becomes its own Actual Ownership
column. You do not need to configure tournament names in the script.
"""

import argparse
import io
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd


BASE_DIR = Path(r"G:\My Drive\Fantasy Football\DFS\2026")


def normalize_player(name):
    """Lowercase, drop punctuation and Jr/Sr/II/III suffixes so that
    'Aaron Jones Sr.' == 'Aaron Jones' and 'D.J. Moore' == 'DJ Moore'."""
    if pd.isna(name):
        return ""
    name = str(name).strip().casefold()
    name = re.sub(r"[.'’`\-]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"\s+(jr|sr|ii|iii|iv|v)$", "", name)
    return name


def prize_size(path):
    """Prize pool parsed from the start of the ZIP name: 50k_BlindSide -> 50000,
    1.5m_Big -> 1500000. Names without a leading number sort last."""
    m = re.match(r"\s*\$?([\d,]*\.?\d+)\s*([kKmM]?)", path.stem)
    if not m:
        return float("-inf")
    value = float(m.group(1).replace(",", ""))
    mult = {"k": 1_000, "m": 1_000_000}.get(m.group(2).lower(), 1)
    return value * mult


def parse_percent(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.strip(),
        errors="coerce",
    )


def find_projection_file(week_dir):
    for name in ["DKETRProj.csv", "projections.csv"]:
        path = week_dir / name
        if path.exists():
            return path

    candidates = [
        p for p in sorted(week_dir.glob("*.csv"))
        if not p.name.lower().startswith("ownership_review")
    ]

    if len(candidates) == 1:
        return candidates[0]

    raise FileNotFoundError(
        f"Could not uniquely identify the projection CSV in {week_dir}. "
        f"Expected DKETRProj.csv or projections.csv. Found: "
        f"{[p.name for p in candidates]}"
    )


def read_projection(path):
    df = pd.read_csv(path)

    required = ["Player", "Small Field", "Large Field"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            f"Projection file is missing columns: {missing}"
        )

    # Keep the fields useful for the report, but don't require all of them.
    preferred = [
        "Player",
        "DK Salary",
        "Team",
        "DK Pos",
        "Small Field",
        "Large Field",
    ]

    keep = [c for c in preferred if c in df.columns]
    out = df[keep].copy()

    out["player_key"] = out["Player"].map(normalize_player)

    for col in ["Small Field", "Large Field"]:
        if col in out.columns:
            out[col] = parse_percent(out[col])

    out = out[out["player_key"] != ""].copy()
    out = out.drop_duplicates("player_key", keep="first")

    return out


def read_contest_zip(zip_path):
    """
    Read a DK contest ZIP and return:
        player_key -> actual ownership

    DK standings repeat each player once for every lineup containing them,
    so ownership is collapsed to one value per player.
    """
    frames = []

    with zipfile.ZipFile(zip_path) as z:
        for member in z.namelist():
            if member.endswith("/") or not member.lower().endswith(".csv"):
                continue

            try:
                df = pd.read_csv(io.BytesIO(z.read(member)))
            except Exception:
                continue

            if "Player" not in df.columns or "%Drafted" not in df.columns:
                continue

            out = df[["Player", "%Drafted"]].dropna(subset=["Player"]).copy()
            out["player_key"] = out["Player"].map(normalize_player)
            out["Actual Ownership"] = parse_percent(out["%Drafted"])

            out = out[
                (out["player_key"] != "") &
                out["Actual Ownership"].notna()
            ]

            if not out.empty:
                frames.append(out[["player_key", "Actual Ownership"]])

    if not frames:
        return None

    combined = pd.concat(frames, ignore_index=True)

    # DK's Classic standings list each player once PER ROSTER SLOT
    # (e.g. RB and FLEX) and %Drafted is the share of lineups using the
    # player in that slot. Total ownership is the SUM across slots.
    # (Median/mean would wrongly blend the slots together.)
    return combined.groupby("player_key")["Actual Ownership"].sum()


def main():
    parser = argparse.ArgumentParser(
        description="Build a player-by-tournament NFL DFS ownership CSV."
    )
    parser.add_argument(
        "--week",
        required=True,
        help="Week number, e.g. 1, 2, 3.",
    )
    parser.add_argument(
        "--projection",
        default=None,
        help="Optional projection CSV path.",
    )
    parser.add_argument(
        "--results-dir",
        default=None,
        help="Optional Results directory.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output CSV path.",
    )

    args = parser.parse_args()

    week = str(args.week)
    week_dir = BASE_DIR / (
        week if week.lower().startswith("week") else f"Week{week}"
    )

    if not week_dir.exists():
        raise FileNotFoundError(f"Week directory not found: {week_dir}")

    projection_path = (
        Path(args.projection).expanduser()
        if args.projection
        else find_projection_file(week_dir)
    )

    results_dir = (
        Path(args.results_dir).expanduser()
        if args.results_dir
        else week_dir / "Results"
    )

    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    # Largest prize pool first; ties broken alphabetically by name.
    zip_files = sorted(
        (
            p for p in results_dir.glob("*.zip")
            if "doubleup" not in p.name.casefold().replace("_", "").replace(" ", "").replace("-", "")
        ),
        key=lambda p: (-prize_size(p), p.name.casefold()),
    )

    if not zip_files:
        raise FileNotFoundError(
            f"No usable .zip files found in {results_dir} (DoubleUp files are excluded)"
        )

    projection = read_projection(projection_path)

    # Start with exactly the player/projection information the user wants.
    output_columns = [
        c for c in [
            "Player",
            "DK Salary",
            "Team",
            "DK Pos",
            "Small Field",
            "Large Field",
        ]
        if c in projection.columns
    ]

    report = projection[output_columns + ["player_key"]].copy()

    tournament_cols = []

    # Each ZIP becomes its own actual ownership column.
    for zip_path in zip_files:
        actual = read_contest_zip(zip_path)

        if actual is None:
            continue

        # Use the ZIP filename as the tournament name.
        # Example:
        #     8k_Huddle1.zip -> 8k_Huddle1
        #     25k_FairCatch.zip -> 25k_FairCatch
        tournament_name = zip_path.stem

        # Make sure the column name is unique.
        base_name = tournament_name
        counter = 2

        while tournament_name in report.columns:
            tournament_name = f"{base_name}_{counter}"
            counter += 1

        col = report["player_key"].map(actual)

        # Fallback for defenses: DK lists "Panthers"; projections may say
        # "Carolina Panthers". Match on the last word when unmatched.
        single = {k: v for k, v in actual.items() if " " not in k}
        fallback = report["player_key"].str.split().str[-1].map(single)
        col = col.fillna(fallback.where(col.isna()))

        report[tournament_name] = col
        tournament_cols.append(tournament_name)

    # Leave off players with 0 (or blank) projected ownership who also
    # have no ownership in any tournament.
    proj_cols = [c for c in ["Small Field", "Large Field"] if c in report.columns]
    zero_projected = (report[proj_cols].fillna(0) == 0).all(axis=1)
    no_actual = report[tournament_cols].isna().all(axis=1)
    before = len(report)
    report = report[~(zero_projected & no_actual)].copy()
    print(f"Dropped {before - len(report):,} players with 0 projected "
          f"and no tournament ownership")

    report = report.drop(columns=["player_key"])

    # Format ownership as percentages for easy viewing in Excel.
    # Keep numeric values in the CSV so they remain usable for calculations.
    output_path = (
        Path(args.output).expanduser()
        if args.output
        else week_dir / "ownership_review.csv"
    )

    report.to_csv(output_path, index=False)

    print(f"Created: {output_path}")
    print(f"Players: {len(report):,}")
    print(f"Tournaments: {len(zip_files):,}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)