import pandas as pd
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Process week parameter.")
    parser.add_argument('--week', type=str, required=True, help="Enter the week")
    return parser.parse_args()

if __name__ == '__main__': 
    args = parse_args()
    week = args.week

dfs_dir = "G:\\My Drive\\Fantasy Football\\DFS\\2023"
fd_csv_path = f"{dfs_dir}\\Week{week}\\FDSalaries.csv"
etr_csv_path = f"{dfs_dir}\\Week{week}\\FDETRProj.csv"
results_csv_path = f"{dfs_dir}\\Week{week}\\FDCashOpto.csv"

def get_fd_salaries(fd_csv_path, etr_csv_path):
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

def get_fd_opto(fd_csv_path, results_csv_path):
    from pydfs_lineup_optimizer import get_optimizer, Site, Sport, CSVLineupExporter, PlayersGroup
    FDOptimizer = get_optimizer(Site.FANDUEL, Sport.FOOTBALL)
    FDOptimizer.load_players_from_csv(fd_csv_path)
    ## RULES SECTION
    FDOptimizer.set_min_salary_cap(59700)
    FDOptimizer.player_pool.lock_player('')
    TopPlays = PlayersGroup(FDOptimizer.player_pool.get_players('',
                                                               '',
                                                               '',
                                                               '',
                                                               ''), 
                                                               min_from_group=9)
    FDOptimizer.add_players_group(TopPlays)
    ## END RULES
    list(FDOptimizer.optimize(50))
    FDOptimizer.export(results_csv_path)

get_fd_salaries(fd_csv_path, etr_csv_path)
get_fd_opto(fd_csv_path, results_csv_path)