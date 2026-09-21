#!/usr/bin/env python3
"""
Compare projected NFL DFS ownership to actual DraftKings ownership.

Run from anywhere:
    python OwnershipReport.py --week 2

Expected layout:
    G:\My Drive\Fantasy Football\DFS\2026\
        Week2\
            DKETRProj.csv
            Results\
                contest1.zip
                contest2.zip
                ...

The base directory is hardcoded below.
"""

import argparse
import io
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd


BASE_DIR = Path(r"G:\My Drive\Fantasy Football\DFS\2026")

PROJECTION_COLUMNS = ["Player", "Small Field", "Large Field"]
RESULT_COLUMNS = ["Player", "%Drafted"]


def normalize_player(name):
    if pd.isna(name):
        return ""
    name = str(name).strip()
    name = re.sub(r"\s+", " ", name)
    return name.casefold()


def parse_percent(series):
    return pd.to_numeric(
        series.astype(str).str.replace("%", "", regex=False).str.strip(),
        errors="coerce",
    )


def find_projection_file(week_dir):
    for name in ["DKETRProj.csv", "projections.csv"]:
        path = week_dir / name
        if path.exists():
            return path

    candidates = sorted(week_dir.glob("*.csv"))
    candidates = [
        p for p in candidates
        if not p.name.lower().startswith(("ownership_review", "actual_ownership"))
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

    missing = [c for c in PROJECTION_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Projection file is missing columns: {missing}. "
            f"Found: {list(df.columns)}"
        )

    keep = ["Player", "Small Field", "Large Field"]
    for col in [
        "DK Pos", "Team", "Opp", "DK Salary",
        "DK Proj", "DK Floor", "DK Ceiling", "id"
    ]:
        if col in df.columns:
            keep.append(col)

    out = df[keep].copy()
    out["player_key"] = out["Player"].map(normalize_player)

    for col in ["Small Field", "Large Field"]:
        out[col] = parse_percent(out[col])

    out = out[out["player_key"] != ""].copy()
    out = out.drop_duplicates("player_key", keep="first")

    return out


def read_result_csv(raw_bytes, source_name):
    try:
        df = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as exc:
        print(f"  WARNING: Could not read {source_name}: {exc}")
        return None

    missing = [c for c in RESULT_COLUMNS if c not in df.columns]
    if missing:
        print(
            f"  SKIP: {source_name} does not look like a DK standings CSV "
            f"(missing {missing})"
        )
        return None

    out = df[["Player", "%Drafted"]].copy()
    out["player_key"] = out["Player"].map(normalize_player)
    out["Actual Ownership"] = parse_percent(out["%Drafted"])

    out = out[
        (out["player_key"] != "") &
        out["Actual Ownership"].notna()
    ].copy()

    out = (
        out.groupby("player_key", as_index=False)
        .agg(
            Player=("Player", "first"),
            **{"Actual Ownership": ("Actual Ownership", "median")},
        )
    )

    return out


def read_contest_zip(zip_path):
    frames = []

    with zipfile.ZipFile(zip_path) as z:
        for member in z.namelist():
            if member.endswith("/") or not member.lower().endswith(".csv"):
                continue

            raw = z.read(member)
            result = read_result_csv(
                raw,
                f"{zip_path.name}:{member}"
            )

            if result is not None and not result.empty:
                frames.append(result)

    if not frames:
        return None

    combined = pd.concat(frames, ignore_index=True)

    combined = (
        combined.groupby("player_key", as_index=False)
        .agg(
            Player=("Player", "first"),
            **{"Actual Ownership": ("Actual Ownership", "median")},
        )
    )

    return combined


def compare_contest(projection, actual, contest_name):
    merged = projection.merge(
        actual,
        on="player_key",
        how="inner",
        suffixes=("", "_actual"),
    )

    if merged.empty:
        return None

    merged["Contest"] = contest_name
    merged["Actual Ownership"] = pd.to_numeric(
        merged["Actual Ownership"],
        errors="coerce",
    )

    for field in ["Small Field", "Large Field"]:
        label = field.replace(" Field", "")
        merged[f"{label} Error"] = (
            merged["Actual Ownership"] - merged[field]
        )
        merged[f"{label} Abs Error"] = merged[f"{label} Error"].abs()

    return merged


def print_summary(df):
    print("\n" + "=" * 72)
    print("OWNERSHIP READ SUMMARY")
    print("=" * 72)
    print(f"Players matched: {len(df):,}")
    print(f"Actual ownership mean: {df['Actual Ownership'].mean():.2f}%")

    rows = []

    for label in ["Small", "Large"]:
        error = df[f"{label} Error"]
        abs_error = df[f"{label} Abs Error"]

        rows.append({
            "Projection": label,
            "MAE": abs_error.mean(),
            "Bias": error.mean(),
            "Median Abs Error": abs_error.median(),
            "Correlation": df[
                [f"{label} Field", "Actual Ownership"]
            ].corr().iloc[0, 1],
        })

    summary = pd.DataFrame(rows)

    print("\nOverall:")
    print(
        summary.to_string(
            index=False,
            formatters={
                "MAE": "{:.2f}%".format,
                "Bias": "{:+.2f}%".format,
                "Median Abs Error": "{:.2f}%".format,
                "Correlation": "{:.3f}".format,
            },
        )
    )

    print("\nBiggest underreads — Small Field:")
    cols = ["Player", "Small Field", "Actual Ownership", "Small Error"]
    print(
        df.nlargest(10, "Small Error")[cols].to_string(
            index=False,
            formatters={
                "Small Field": "{:.2f}%".format,
                "Actual Ownership": "{:.2f}%".format,
                "Small Error": "{:+.2f}%".format,
            },
        )
    )

    print("\nBiggest overreads — Small Field:")
    print(
        df.nsmallest(10, "Small Error")[cols].to_string(
            index=False,
            formatters={
                "Small Field": "{:.2f}%".format,
                "Actual Ownership": "{:.2f}%".format,
                "Small Error": "{:+.2f}%".format,
            },
        )
    )

    print("\nBiggest underreads — Large Field:")
    cols = ["Player", "Large Field", "Actual Ownership", "Large Error"]
    print(
        df.nlargest(10, "Large Error")[cols].to_string(
            index=False,
            formatters={
                "Large Field": "{:.2f}%".format,
                "Actual Ownership": "{:.2f}%".format,
                "Large Error": "{:+.2f}%".format,
            },
        )
    )

    print("\nBiggest overreads — Large Field:")
    print(
        df.nsmallest(10, "Large Error")[cols].to_string(
            index=False,
            formatters={
                "Large Field": "{:.2f}%".format,
                "Actual Ownership": "{:.2f}%".format,
                "Large Error": "{:+.2f}%".format,
            },
        )


def main():
    parser = argparse.ArgumentParser(
        description="Compare projected DFS ownership to actual DraftKings ownership."
    )

    parser.add_argument(
        "--week",
        required=True,
        help="Week identifier, e.g. 1 or Week1.",
    )

    parser.add_argument(
        "--projection",
        default=None,
        help="Optional explicit path to the projection CSV.",
    )

    parser.add_argument(
        "--results-dir",
        default=None,
        help="Optional explicit Results directory.",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Optional output CSV path. Defaults to WeekX/ownership_review.csv.",
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

    zip_files = sorted(results_dir.glob("*.zip"))

    if not zip_files:
        raise FileNotFoundError(
            f"No .zip files found in {results_dir}"
        )

    print(f"Base:       {BASE_DIR}")
    print(f"Week:       {week_dir.name}")
    print(f"Projection: {projection_path}")
    print(f"Results:    {results_dir}")
    print(f"ZIP files:  {len(zip_files)}")

    projection = read_projection(projection_path)

    all_contests = []

    for zip_path in zip_files:
        print(f"\nProcessing {zip_path.name}...")

        actual = read_contest_zip(zip_path)

        if actual is None:
            print("  No usable DK results CSV found.")
            continue

        compared = compare_contest(
            projection,
            actual,
            zip_path.stem,
        )

        if compared is None:
            print("  No player names matched the projection file.")
            continue

        print(f"  Matched {len(compared):,} players.")
        all_contests.append(compared)

    if not all_contests:
        raise RuntimeError("No contests could be compared.")

    combined = pd.concat(all_contests, ignore_index=True)

    output_path = (
        Path(args.output).expanduser()
        if args.output
        else week_dir / "ownership_review.csv"
    )

    combined.to_csv(output_path, index=False)

    print_summary(combined)

    print("\n" + "=" * 72)
    print(f"Detailed results saved to: {output_path}")
    print("=" * 72)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)
