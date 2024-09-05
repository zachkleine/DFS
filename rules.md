Example file to reference common rules when working with optimizer

## Set Minimum salary cap a lineup has to use
Optimizer.set_min_salary_cap(59700)

## Lock a specific player to every lineup
Optimizer.player_pool.lock_player('')

## Takes listed players from group and builds based on that. Good for top plays on FD
Group = PlayersGroup(Optimizer.player_pool.get_players(''), 
        min_from_group=1)
Optimizer.add_players_group(Group)

## Prevents opponents of DST from being in lineup
Optimizer.restrict_positions_for_opposing_team(['DST'],['QB','RB','WR','TE'])

## Stacking
# Stacks QB with 1 WR and either WR or TE from listed teams
Optimizer.add_stack(PositionsStack(['QB','WR',('WR','TE')], for_teams=[''], max_exposure=0.x))

# Stack 3 players from listed positions from listed teams. Does not force QB stacking. Does not force additional stacks, will use PositionStack
Optimizer.add_stack(TeamStack(3, for_teams=[''], for_positions=['QB','RB','WR','TE']))

# Forces single WR bring back 
Optimizer.force_positions_for_opposing_team(('QB', 'WR'))

# Forces WR AND TE bring back
Optimizer.force_positions_for_opposing_team(('QB', 'WR'),('QB','TE'))

