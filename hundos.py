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

dfs_dir = "G:\\My Drive\\Fantasy Football\\DFS\\2024"
dk_csv_path = f"{dfs_dir}\\Week{week}\\DKSalaries.csv"
etr_csv_path = f"{dfs_dir}\\Week{week}\\DKETRProj.csv"
results_csv_path = f"{dfs_dir}\\Week{week}\\DKHundo.csv"

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
        
        lookupceiling = etr_csv.loc[etr_csv['Player'] == name, 'DK Ceiling']
        if not lookupceiling.empty:
            dk_csv.at[_, 'Projection Ceil'] = lookupceiling.iloc[0]
        else: 
            dk_csv.at[_, 'Projection Ceil'] = 0

    dk_csv.to_csv(dk_csv_path, index=False)

def get_dk_opto(dk_csv_path, results_csv_path):
    from pydfs_lineup_optimizer import get_optimizer, Site, Sport, CSVLineupExporter, PlayerFilter, AfterEachExposureStrategy, RandomFantasyPointsStrategy
    from pydfs_lineup_optimizer.stacks import GameStack, TeamStack, PositionsStack, NestedPlayersGroup, OptimizerStack, Stack, PlayersGroup
    DKOptimizer = get_optimizer(Site.DRAFTKINGS, Sport.FOOTBALL)
    DKOptimizer.load_players_from_csv(dk_csv_path)
    DKOptimizer.player_pool.add_filters(
        PlayerFilter(from_value=4.7)
    )
    DKOptimizer.set_fantasy_points_strategy(RandomFantasyPointsStrategy(max_deviation=0.1))

    ## RULES SECTION
    ## Base Rules
    DKOptimizer.set_min_salary_cap(49800)
    DKOptimizer.restrict_positions_for_opposing_team(['DST'],['QB','RB','WR','TE'])
    DKOptimizer.restrict_positions_for_opposing_team(['RB'],['RB'])
    #DKOptimizer.add_stack(PositionsStack(['RB','DST'],max_exposure=0.8))
    #DKOptimizer.restrict_positions_for_same_team(('QB','RB'))
    DKOptimizer.add_players_group(PlayersGroup(
        players=[player for player in DKOptimizer.players
            if player.projected_ownership <= 0.1],
        min_from_group=1
    ))

    ## Player Groups
    Core = PlayersGroup(DKOptimizer.player_pool.get_players('Christian McCaffrey','Devon Achane','Alvin Kamara'), min_from_group=1)
    DKOptimizer.add_players_group(Core)

    RBPool = PlayersGroup(DKOptimizer.player_pool.get_players('Christian McCaffrey','Devon Achane','Alvin Kamara','Rhamondre Stevenson','David Montgomery',
                                                              'Deandre Swift','Kareem Hunt','Kenneth Walker III','Josh Jacobs','Jahmyr Gibbs','Breece Hall',
                                                              'Jonathan Taylor','Bijan Robinson','Kyren Williams'), min_from_group=2)
    DKOptimizer.add_players_group(RBPool)
    
    Chalk = PlayersGroup(DKOptimizer.player_pool.get_players('Christian McCaffrey','Devon Achane','Alvin Kamara'), min_from_group=1,max_from_group=3)
    DKOptimizer.add_players_group(Chalk)

    #Leverage = PlayersGroup(DKOptimizer.player_pool.get_players(), max_exposure=0.8,min_from_group=1)    
    #DKOptimizer.add_players_group(Leverage)

    SFStack = PlayersGroup(DKOptimizer.player_pool.get_players('Brock Purdy','George Kittle','Christian McCaffrey','Deebo Samuel','Jauan Jennings','Ricky Pearsall'),
                        max_from_group=3,min_from_group=3,
                        depends_on=DKOptimizer.player_pool.get_player_by_name('Brock Purdy'),strict_depend=False)
    BUFStack = PlayersGroup(DKOptimizer.player_pool.get_players('Josh Allen','James Cook','Amari Cooper','Khalil Shakir','Dawson Knox'),
                        max_from_group=3,min_from_group=2,
                        depends_on=DKOptimizer.player_pool.get_player_by_name('Josh Allen'),strict_depend=False)
    PITStack = PlayersGroup(DKOptimizer.player_pool.get_players('Russell Wilson','George Pickens'),
                        max_from_group=2,min_from_group=2,
                        depends_on=DKOptimizer.player_pool.get_player_by_name('Russell Wilson'),strict_depend=False)
    NEStack = PlayersGroup(DKOptimizer.player_pool.get_players('Drake Maye','Kayshon Boutte','Hunter Henry','DeMario Douglas'),
                        max_from_group=2,min_from_group=2,
                        depends_on=DKOptimizer.player_pool.get_player_by_name('Drake Maye'),strict_depend=False)
    CLEStack = PlayersGroup(DKOptimizer.player_pool.get_players('Jameis Winston','Cedric Tillman','David Njoku','Jerry Jeudy','Elijah Moore'),
                        max_from_group=2,min_from_group=2,
                        depends_on=DKOptimizer.player_pool.get_player_by_name('Jameis Winstons'),strict_depend=False)
    DETRule = PlayersGroup(DKOptimizer.player_pool.get_players(
        PlayerFilter(teams=['DET']),
        PlayerFilter(filter_by='fppg',from_value=10)),
        min_from_group=1,
        max_exposure=0.8
    )

    #LimitStackExposure = DKOptimizer.player_pool.get_player_by_name([''])
    #LimitStackExposure.max_exposure = 0.01
    DKOptimizer.add_stack(Stack([SFStack,BUFStack,PITStack,NEStack,CLEStack,DETRule]))
    DKOptimizer.add_stack(PositionsStack(['QB',('WR','TE')],for_teams=['PIT']))
    #DKOptimizer.force_positions_for_opposing_team(('QB','WR'))

    ## END RULES
    list(DKOptimizer.optimize(500,exposure_strategy=AfterEachExposureStrategy))
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
            totalCeiling = 0
            for player in team:
                lookupown = dk_csv.loc[dk_csv['Name'] == player, 'Projected Ownership']
                if not lookupown.empty:
                    totalOwn += lookupown.iloc[0]
                dk_opto.at[idx, 'Ownership'] = totalOwn
                lookupceiling = dk_csv.loc[dk_csv['Name'] == player, 'Projection Ceil']
                if not lookupceiling.empty: 
                    totalCeiling += lookupceiling.iloc[0]
                dk_opto.at[idx, 'Ceiling'] = totalCeiling
    # Save the updated DataFrame back to the CSV file
    dk_opto.to_csv(results_csv_path, index=False)

get_dk_salaries(dk_csv_path, etr_csv_path)
get_dk_opto(dk_csv_path, results_csv_path)
get_dk_ownership(dk_csv_path, results_csv_path)