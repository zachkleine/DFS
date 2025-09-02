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

dfs_dir = "G:\\My Drive\\Fantasy Football\\DFS\\2025"
dk_csv_path = f"{dfs_dir}\\Week{week}\\DKSalaries.csv"
etr_csv_path = f"{dfs_dir}\\Week{week}\\DKETRProj.csv"
results_csv_path = f"{dfs_dir}\\Week{week}\\DKOpto.csv"

def get_dk_salaries(dk_csv_path, etr_csv_path):
    dk_csv = pd.read_csv(dk_csv_path)
    etr_csv = pd.read_csv(etr_csv_path)
    for idx, row in dk_csv.iterrows():
        name = row['Name']

        # DK Projection -> AvgPointsPerGame
        lookuppts = etr_csv.loc[etr_csv['Player'] == name, 'DK Projection']
        dk_csv.at[idx, 'AvgPointsPerGame'] = lookuppts.iloc[0] if not lookuppts.empty else 0
        
        # DK Large Ownership -> Projected Ownership
        lookupown = etr_csv.loc[etr_csv['Player'] == name, 'DK Large Ownership']
        dk_csv.at[idx, 'Projected Ownership'] = lookupown.iloc[0] if not lookupown.empty else 0

        # DK Ceiling -> Projection Ceil
        lookupceiling = etr_csv.loc[etr_csv['Player'] == name, 'DK Ceiling']
        dk_csv.at[idx, 'Projection Ceil'] = lookupceiling.iloc[0] if not lookupceiling.empty else 0

    dk_csv.to_csv(dk_csv_path, index=False)

def get_dk_opto(dk_csv_path, results_csv_path):
    from pydfs_lineup_optimizer import get_optimizer, Site, Sport, CSVLineupExporter, PlayerFilter
    from pydfs_lineup_optimizer.stacks import GameStack, TeamStack, PositionsStack, NestedPlayersGroup, OptimizerStack, Stack, PlayersGroup
    DKOptimizer = get_optimizer(Site.DRAFTKINGS, Sport.FOOTBALL)
    DKOptimizer.load_players_from_csv(dk_csv_path)
    ## RULES SECTION
    #DKOptimizer.set_min_salary_cap(49800)
    ## END RULES
    list(DKOptimizer.optimize(150))
    DKOptimizer.export(results_csv_path)

def get_dk_ownership(dk_csv_path, results_csv_path):
    dk_csv = pd.read_csv(dk_csv_path)
    dk_opto = pd.read_csv(results_csv_path)

    # Player → (ownership, ceiling) lookup
    player_lookup = dk_csv.set_index('Name')[['Projected Ownership', 'Projection Ceil']].to_dict('index')

    # Add or reset columns
    dk_opto['Ownership'] = 0.0
    dk_opto['Ceiling'] = 0.0

    for idx, row in dk_opto.iterrows():
        team = row.iloc[:9]  # assumes first 9 columns = players
        totalOwn = 0.0
        totalCeil = 0.0
        for player in team:
            if player in player_lookup:
                totalOwn += player_lookup[player]['Projected Ownership']
                totalCeil += player_lookup[player]['Projection Ceil']
        dk_opto.at[idx, 'Ownership'] = totalOwn
        dk_opto.at[idx, 'Ceiling'] = totalCeil

    dk_opto.to_csv(results_csv_path, index=False)

get_dk_salaries(dk_csv_path, etr_csv_path)
get_dk_opto(dk_csv_path, results_csv_path)
get_dk_ownership(dk_csv_path, results_csv_path)