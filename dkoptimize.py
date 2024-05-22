import pandas as pd
import re

def get_dk_salaries(dfs_dir, week):
    full_dir = f"{dfs_dir}\\Week{week}"
    dk_csv_path = f"{full_dir}\\DKPool.csv"
    etr_csv_path = f"{full_dir}\\DKETRProj.csv"

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

def get_dk_opto(dfs_dir, week):
    full_dir = f"{dfs_dir}\\Week{week}"
    dk_csv_path = f"{full_dir}\\DKPool.csv"
    results_csv_path = f"{full_dir}\\DKOpto.csv"

    from pydfs_lineup_optimizer import get_optimizer, Site, Sport, CSVLineupExporter
    from pydfs_lineup_optimizer.stacks import GameStack, TeamStack, PositionsStack, NestedPlayersGroup, OptimizerStack, Stack, PlayersGroup

    DKOptimizer = get_optimizer(Site.DRAFTKINGS, Sport.FOOTBALL)
    DKOptimizer.load_players_from_csv(dk_csv_path)
    
    ## RULES SECTION
    # Rule for min salary used
    #DKOptimizer.set_min_salary_cap(49700)

    DKOptimizer.player_pool.lock_player('Christian McCaffrey')

    #adding 2 low owned players
    DKOptimizer.add_players_group(PlayersGroup(
        players=[player for player in DKOptimizer.players if player.projected_ownership <= 0.16],
        min_from_group=2
    ))
    
    #Double stack
    DKOptimizer.add_stack(PositionsStack(['QB', ('WR', 'TE'),('WR', 'TE')]))

    #DKOptimizer.restrict_positions_for_opposing_team(['QB'],['DST'])

    TDRBs = PlayersGroup(DKOptimizer.player_pool.get_players('David Montgomery', 'Gus Edwards'), max_from_group=1)
    DKOptimizer.add_players_group(TDRBs)
    CheapDETWRs = PlayersGroup(DKOptimizer.player_pool.get_players('Jameson Williams','Josh Reynolds'), max_from_group=1)
    DKOptimizer.add_players_group(CheapDETWRs)
    BALMinWRs = PlayersGroup(DKOptimizer.player_pool.get_players('Rashod Bateman', 'Nelson Agholor','Odell Beckham Jr.'), max_from_group=1)
    DKOptimizer.add_players_group(BALMinWRs)
    ## END RULES 
    
    lineups = list(DKOptimizer.optimize(150))
    DKOptimizer.export(results_csv_path)
    dk_csv = pd.read_csv(results_csv_path)
    def remove_parentheses(text): 
        return re.sub(r'\([^)]*\)', '', str(text))
    dk_csv = dk_csv.applymap(remove_parentheses)    
    dk_csv.to_csv(results_csv_path, index=False)

def get_dk_extras(dfs_dir, week): 
    full_dir = f"{dfs_dir}\\Week{week}"
    dk_opto_csv = f"{full_dir}\\DKOpto.csv"
    etr_csv_path = f"{full_dir}\\DKETRProj.csv"

    etr_csv = pd.read_csv(etr_csv_path)
    dk_opto = pd.read_csv(dk_opto_csv)

    additional_headers = ['Ownership', 'Ceiling']
    new_headers_df = pd.DataFrame(columns=additional_headers)
    df_with_headers = pd.concat([dk_opto, new_headers_df], axis=1)
    df_with_headers.to_csv(dk_opto_csv, index=False)

dfs_dir = "G:\\My Drive\\Fantasy Football\\DFS\\2023"
week = "19"
get_dk_salaries(dfs_dir, week)
get_dk_opto(dfs_dir, week)
get_dk_extras(dfs_dir, week)