import pandas as pd
import re

def get_dk_salaries(dfs_dir, week):
    full_dir = f"{dfs_dir}\\Week{week}"
    dk_csv_path = f"{full_dir}\\DKSalaries.csv"
    etr_csv_path = f"{full_dir}\\DKETRProj.csv"

    dk_csv = pd.read_csv(dk_csv_path)
    etr_csv = pd.read_csv(etr_csv_path)

    for _, row in dk_csv.iterrows():
        name = row['Name']
        lookup = etr_csv.loc[etr_csv['Name'] == name, 'DK Projection']
        if not lookup.empty:
            dk_csv.at[_, 'AvgPointsPerGame'] = lookup.iloc[0]
        else: 
            dk_csv.at[_, 'AvgPointsPerGame'] = 0

    dk_csv.to_csv(dk_csv_path, index=False)

def get_dk_opto(dfs_dir, week):
    full_dir = f"{dfs_dir}\\Week{week}"
    dk_csv_path = f"{full_dir}\\DKSalaries.csv"
    results_csv_path = f"{full_dir}\\dkcashopto.csv"

    from pydfs_lineup_optimizer import get_optimizer, Site, Sport, CSVLineupExporter
    DKOptimizer = get_optimizer(Site.DRAFTKINGS, Sport.FOOTBALL)
    DKOptimizer.load_players_from_csv(dk_csv_path)
    lineups = list(DKOptimizer.optimize(100))
    DKOptimizer.export(results_csv_path)

    dk_csv = pd.read_csv(results_csv_path)
    def remove_parentheses(text): 
        return re.sub(r'\([^)]*\)', '', str(text))
    dk_csv = dk_csv.applymap(remove_parentheses)    
    dk_csv.to_csv(results_csv_path, index=False)

def get_dk_extras(dfs_dir, week): 
    full_dir = f"{dfs_dir}\\Week{week}"
    dk_opto_csv = f"{full_dir}\\dkcashopto.csv"
    etr_csv_path = f"{full_dir}\\DKETRProj.csv"

    etr_csv = pd.read_csv(etr_csv_path)
    dk_opto = pd.read_csv(dk_opto_csv)

    additional_headers = ['Ownership', 'Ceiling']
    new_headers_df = pd.DataFrame(columns=additional_headers)
    df_with_headers = pd.concat([dk_opto, new_headers_df], axis=1)
    df_with_headers.to_csv(dk_opto_csv, index=False)

dfs_dir = "G:\\My Drive\\Fantasy Football\\DFS\\2023"
week = "15"
get_dk_salaries(dfs_dir, week)
get_dk_opto(dfs_dir, week)
get_dk_extras(dfs_dir, week)