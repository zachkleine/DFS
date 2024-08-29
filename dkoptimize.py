import pandas as pd
import argparse
import csv

def parse_args():
    parser = argparse.ArgumentParser(description="Process week parameter.")
    parser.add_argument('--week', type=str, required=True, help="Enter the week")
    return parser.parse_args()

if __name__ == '__main__': 
    args = parse_args()
    week = args.week

dfs_dir = "G:\\My Drive\\Fantasy Football\\DFS\\2023"
dk_csv_path = f"{dfs_dir}\\Week{week}\\DKSalaries.csv"
etr_csv_path = f"{dfs_dir}\\Week{week}\\DKETRProj.csv"
results_csv_path = f"{dfs_dir}\\Week{week}\\DKOpto.csv"

def get_dk_salaries(dk_csv_path, etr_csv_path):
    dk_csv = pd.read_csv(dk_csv_path)
    etr_csv = pd.read_csv(etr_csv_path)
    for _, row in dk_csv.iterrows():
        name = row['Name']
        lookuppts = etr_csv.loc[etr_csv['Player'] == name, 'DK Projection']
        if not lookuppts.empty:
            dk_csv.at[_, 'AvgPointsPerGame'] = lookuppts.iloc[0]
        else: 
            dk_csv.at[_, 'AvgPointsPerGame'] = 0
        lookupown = etr_csv.loc[etr_csv['Player'] == name, 'DK Large Ownership']
        if not lookupown.empty:
            dk_csv.at[_, 'Projected Ownership'] = lookupown.iloc[0]
        else: 
            dk_csv.at[_, 'Projected Ownership'] = 0
    dk_csv.to_csv(dk_csv_path, index=False)

def get_dk_opto(dk_csv_path, results_csv_path):
    from pydfs_lineup_optimizer import get_optimizer, Site, Sport, CSVLineupExporter
    from pydfs_lineup_optimizer.stacks import GameStack, TeamStack, PositionsStack, NestedPlayersGroup, OptimizerStack, Stack, PlayersGroup
    DKOptimizer = get_optimizer(Site.DRAFTKINGS, Sport.FOOTBALL)
    DKOptimizer.load_players_from_csv(dk_csv_path)
    ## RULES SECTION
    ## END RULES
    list(DKOptimizer.optimize(10))
    DKOptimizer.export(results_csv_path)

def get_dk_ownership(dk_csv_path, results_csv_path):
    # Read CSV files into DataFrames
    dk_csv = pd.read_csv(dk_csv_path)
    dk_opto = pd.read_csv(results_csv_path)
    
    # Add new columns 'Ownership' and 'Ceiling' with default values (e.g., NaN or 0)
    dk_opto['Ownership'] = pd.NA  # or you could use 0 or another default value
    dk_opto['Ceiling'] = pd.NA

    with open(results_csv_path) as file_obj:
        header = next(file_obj)
        reader = csv.reader(file_obj)
        for idx, row in enumerate(reader):
            team = (row[:9])
            totalOwn = 0
            for player in team:
                lookupown = dk_csv.loc[dk_csv['Name'] == player, 'Projected Ownership']
                if not lookupown.empty:
                    totalOwn += lookupown.iloc[0]
                dk_opto.at[idx, 'Ownership'] = totalOwn

    # Save the updated DataFrame back to the CSV file
    dk_opto.to_csv(results_csv_path, index=False)

get_dk_salaries(dk_csv_path, etr_csv_path)
get_dk_opto(dk_csv_path, results_csv_path)
get_dk_ownership(dk_csv_path, results_csv_path)