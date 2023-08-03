import pandas as pd

def get_dk_salaries(dfs_dir, week):
    full_dir = f"{dfs_dir}\\Week{week}"
    dk_csv_path = f"{full_dir}\\DKSalaries.csv"
    etr_csv_path = f"{full_dir}\\ETRProj.csv"

    dk_csv = pd.read_csv(dk_csv_path)
    etr_csv = pd.read_csv(etr_csv_path)

    for _, row in dk_csv.iterrows():
        name = row['Name']
        lookup = etr_csv.loc[etr_csv['Name'] == name, 'DK Projection']
        if not lookup.empty:
            dk_csv.at[_, 'AvgPointsPerGame'] = lookup.iloc[0]

    dk_csv.to_csv(dk_csv_path, index=False)

dfs_dir = "G:\\My Drive\\Fantasy Football\\DFS\\2023"
week = int(input("Enter Week #"))
get_dk_salaries(dfs_dir, week)

"""
Need to call PyDFS program
from pydfs_lineup_optimizer import get_optimizer, Site, Sport, CSVLineupExporter

DKoptimizer = get_optimizer(Site.DRAFTKINGS, Sport.FOOTBALL)
DKoptimizer.load_players_from_csv('DKSalaries.csv')

lineups = list(DKoptimizer.optimize(10))
DKoptimizer.export('result.csv')
"""