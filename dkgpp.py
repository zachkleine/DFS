import pandas as pd
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Process week parameter.")
    parser.add_argument('--week', type=int, required=True, help="Enter the week")
    parser.add_argument('--lineups', type=int, default=50, help="Number of lineups to generate")
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    week = args.week
    num_lineups = args.lineups

dfs_dir = "G:\\My Drive\\Fantasy Football\\DFS\\2025"
dk_csv_path = f"{dfs_dir}\\Week{week}\\DKSalaries.csv"
etr_csv_path = f"{dfs_dir}\\Week{week}\\DKETRProj.csv"
results_csv_path = f"{dfs_dir}\\Week{week}\\DKGPP.csv"

def get_dk_salaries(dk_csv_path, etr_csv_path):
    dk_csv = pd.read_csv(dk_csv_path)
    etr_csv = pd.read_csv(etr_csv_path)
    for idx, row in dk_csv.iterrows():
        name = row['Name']

        # DK Projection -> AvgPointsPerGame
        lookuppts = etr_csv.loc[etr_csv['Name'] == name, 'Projection']
        dk_csv.at[idx, 'AvgPointsPerGame'] = lookuppts.iloc[0] if not lookuppts.empty else 0
        
        # DK Large Ownership -> Projected Ownership
        lookupown = etr_csv.loc[etr_csv['Name'] == name, 'Ownership']
        dk_csv.at[idx, 'Projected Ownership'] = lookupown.iloc[0] if not lookupown.empty else 0

        # DK Ceiling -> Projection Ceil
        lookupceiling = etr_csv.loc[etr_csv['Name'] == name, 'Ceiling']
        dk_csv.at[idx, 'Projection Ceil'] = lookupceiling.iloc[0] if not lookupceiling.empty else 0

    dk_csv.to_csv(dk_csv_path, index=False)

def get_dk_opto(dk_csv_path, results_csv_path):
    from pydfs_lineup_optimizer import get_optimizer, Site, Sport, CSVLineupExporter, PlayerFilter, AfterEachExposureStrategy, RandomFantasyPointsStrategy
    from pydfs_lineup_optimizer.stacks import GameStack, TeamStack, PositionsStack, NestedPlayersGroup, OptimizerStack, Stack, PlayersGroup
    DKOptimizer = get_optimizer(Site.DRAFTKINGS, Sport.FOOTBALL)
    DKOptimizer.load_players_from_csv(dk_csv_path)
    DKOptimizer.player_pool.add_filters(
        PlayerFilter(from_value=4.0)
    )
    #DKOptimizer.set_fantasy_points_strategy(RandomFantasyPointsStrategy(max_deviation=0.75))

    ## RULES SECTION
    ## Base Rules
    DKOptimizer.set_min_salary_cap(49800)
    DKOptimizer.restrict_positions_for_opposing_team(['DST'],['QB','RB','WR','TE'])
    DKOptimizer.restrict_positions_for_opposing_team(['RB'],['RB'])
    #DKOptimizer.add_stack(PositionsStack(['RB','DST'],max_exposure=0.8))
    DKOptimizer.add_players_group(PlayersGroup(
        players=[player for player in DKOptimizer.players
            if player.projected_ownership <= 0.15],
        min_from_group=2
    ))

    ## Player Groups
    # Core = PlayersGroup(DKOptimizer.player_pool.get_players(''), min_from_group=1)
    # DKOptimizer.add_players_group(Core)

    # RBPool = PlayersGroup(DKOptimizer.player_pool.get_players(''), min_from_group=2)
    # DKOptimizer.add_players_group(RBPool)
    
    # Chalk = PlayersGroup(DKOptimizer.player_pool.get_players(''),max_from_group=3)
    # DKOptimizer.add_players_group(Chalk)

    Leverage = PlayersGroup(DKOptimizer.player_pool.get_players("Darnell Mooney", "Stefon Diggs", "Sam LaPorta", "Amon-Ra St. Brown", "Jameson Williams", "Marvin Harrison Jr.", "Travis Hunter", "Deebo Samuel Sr.", "Jaylen Waddle",
                                                                "Chris Olave", "Ashton Jeanty", "Kyren Williams", "Matthew Golden", "Michael Pittman Jr.", "Jakobi Meyers", "Romeo Doubs", "Rashid Shaheed"),
                                                                min_from_group=1)    
    DKOptimizer.add_players_group(Leverage)

    CINDouble = PlayersGroup(DKOptimizer.player_pool.get_players('Joe Burrow','Chase Brown','Jamarr Chase','Tee Higgins'),
                         max_from_group=3,min_from_group=3,
                         depends_on=DKOptimizer.player_pool.get_player_by_name('Joe Burrow'),strict_depend=False)
    INDSingle = PlayersGroup(DKOptimizer.player_pool.get_players('Daniel Jones','Michael Pittman','Josh Downs'),
                         max_from_group=2,min_from_group=2,
                         depends_on=DKOptimizer.player_pool.get_player_by_name('Daniel Jones'),strict_depend=False)
    MIABB = PlayersGroup(DKOptimizer.player_pool.get_players('Daniel Jones','Tyreek Hill','Devon Achane','Jaylen Waddle'),
                    max_from_group=3,min_from_group=3,
                    depends_on=DKOptimizer.player_pool.get_player_by_name('Daniel Jones'),strict_depend=False)
    WASStack = PlayersGroup(DKOptimizer.player_pool.get_players('Jayden Daniels','Deebo Samuel','Malik Nabers'),
                    max_from_group=3,min_from_group=3,
                    depends_on=DKOptimizer.player_pool.get_player_by_name('Jayden Daniels'),strict_depend=False)
    MIADouble = PlayersGroup(DKOptimizer.player_pool.get_players('Tua Tagovailoa','Tyreek Hill','Devon Achane','Jaylen Waddle'),
                    max_from_group=3,min_from_group=3,
                    depends_on=DKOptimizer.player_pool.get_player_by_name('Tua Tagovailoa'),strict_depend=False)
    INDBB = PlayersGroup(DKOptimizer.player_pool.get_players('Tua Tagovailoa','Jonathan Taylor','Michael Pittman','Josh Downs'),
                        max_from_group=2,min_from_group=2,
                        depends_on=DKOptimizer.player_pool.get_player_by_name('Tua Tagovailoa'),strict_depend=False)
    ATLDouble = PlayersGroup(DKOptimizer.player_pool.get_players('Michael Penix Jr.','Drake London','Ray-Ray McCloud III','Darnell Mooney'),
                    max_from_group=3,min_from_group=3,
                    depends_on=DKOptimizer.player_pool.get_player_by_name('Michael Penix Jr.'),strict_depend=False)
    TBBB = PlayersGroup(DKOptimizer.player_pool.get_players('Michael Penix Jr.','Mike Evans','Bucky Irving','Emeka Egbuka'),
                    max_from_group=3,min_from_group=2,
                    depends_on=DKOptimizer.player_pool.get_player_by_name('Michael Penix Jr.'),strict_depend=False)
    JAXDouble = PlayersGroup(DKOptimizer.player_pool.get_players('Trevor Lawrence','Brian Thomas Jr.','Brenton Strange','Travis Hunter','Tetairoa McMillan'),
                    max_from_group=3,min_from_group=3,
                    depends_on=DKOptimizer.player_pool.get_player_by_name('Trevor Lawrence'),strict_depend=False)
    SFDouble = PlayersGroup(DKOptimizer.player_pool.get_players('Brock Purdy','George Kittle','Ricky Pearsall'),
                    max_from_group=3,min_from_group=3,
                    depends_on=DKOptimizer.player_pool.get_player_by_name('Brock Purdy'),strict_depend=False)

    # #LimitStackExposure = DKOptimizer.player_pool.get_player_by_name([''])
    # #LimitStackExposure.max_exposure = 0.01

    DKOptimizer.add_stack(Stack([CINDouble,INDSingle,MIABB,WASStack,MIADouble,INDBB,ATLDouble,TBBB,JAXDouble,SFDouble]))
    DKOptimizer.add_stack(PositionsStack(['QB',('WR','TE')],for_teams=['SF','NE','ATL','WAS','JAX','IND','MIA','CIN'],max_exposure=0.13))
    # DKOptimizer.force_positions_for_opposing_team(('QB','WR'))

    ## END RULES
    list(DKOptimizer.optimize(num_lineups,exposure_strategy=AfterEachExposureStrategy))
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