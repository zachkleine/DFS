Example file to reference common rules when working with optimizer

## Set Minimum salary cap a lineup has to use
FDOptimizer.set_min_salary_cap(59700)

## Lock a specific player to every lineup
FDOptimizer.player_pool.lock_player('')


TopPlays = PlayersGroup(FDOptimizer.player_pool.get_players('',
                                                            '',
                                                            '',
                                                            '',
                                                            ''), 
                                                            min_from_group=9)
    FDOptimizer.add_players_group(TopPlays)