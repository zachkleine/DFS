import pandas as pd
import re

def get_fd_salaries(dfs_dir, week):
    full_dir = f"{dfs_dir}\\Week{week}"
    fd_csv_path = f"{full_dir}\\FDSalaries.csv"
    etr_csv_path = f"{full_dir}\\FDETRProj.csv"

    fd_csv = pd.read_csv(fd_csv_path)
    etr_csv = pd.read_csv(etr_csv_path)

    for _, row in fd_csv.iterrows():
        name = row['Nickname']
        lookup = etr_csv.loc[etr_csv['Player'] == name, 'FD Projection']
        if not lookup.empty:
            fd_csv.at[_, 'FPPG'] = lookup.iloc[0]
        else: 
            fd_csv.at[_, 'FPPG'] = 0

    fd_csv.to_csv(fd_csv_path, index=False)

def get_fd_opto(dfs_dir, week):
    full_dir = f"{dfs_dir}\\Week{week}"
    fd_csv_path = f"{full_dir}\\FDSalaries.csv"
    results_csv_path = f"{full_dir}\\fdcashopto.csv"

    from pydfs_lineup_optimizer import get_optimizer, Site, Sport, CSVLineupExporter
    FDOptimizer = get_optimizer(Site.FANDUEL, Sport.FOOTBALL)
    FDOptimizer.load_players_from_csv(fd_csv_path)
    lineups = list(FDOptimizer.optimize(50))
    FDOptimizer.export(results_csv_path)

    #fd_csv = pd.read_csv(results_csv_path)
    #def remove_parentheses(text): 
    #    return re.sub(r'\([^)]*\)', '', str(text))
    #fd_csv = fd_csv.applymap(remove_parentheses)    
    #fd_csv.to_csv(results_csv_path, index=False)

def get_fd_extras(dfs_dir, week): 
    full_dir = f"{dfs_dir}\\Week{week}"
    fd_opto_csv = f"{full_dir}\\fdcashopto.csv"
    etr_csv_path = f"{full_dir}\\FDETRProj.csv"

    etr_csv = pd.read_csv(etr_csv_path)
    fd_opto = pd.read_csv(fd_opto_csv)

    additional_headers = ['Ownership', 'Ceiling']
    new_headers_df = pd.DataFrame(columns=additional_headers)
    df_with_headers = pd.concat([fd_opto, new_headers_df], axis=1)
    df_with_headers.to_csv(fd_opto_csv, index=False)

dfs_dir = "G:\\My Drive\\Fantasy Football\\DFS\\2023"
week = "2"
get_fd_salaries(dfs_dir, week)
get_fd_opto(dfs_dir, week)
get_fd_extras(dfs_dir, week)