Example file to reference common rules when working with optimizer

## Set Minimum salary cap a lineup has to use
Optimizer.set_min_salary_cap(59700)

## Lock a specific player to every lineup
Optimizer.player_pool.lock_player('')

## Takes listed players from group and builds based on that. Good for top plays on FD
Group = PlayersGroup(Optimizer.player_pool.get_players(''), 
        min_from_group=9)
Optimizer.add_players_group(Group)

## Prevents opponents of DST from being in lineup
Optimizer.restrict_positions_for_opposing_team(['DST'],['QB','RB','WR','TE'])

## Stacking
# Stacks QB with 1 WR and either WR or TE from listed teams
Optimizer.add_stack(PositionsStack(['QB','WR',('WR','TE')], for_teams=[''], max_exposure=0.x))

# Stack 3 players from listed positions from listed teams. Does not force QB stacking. Does not force additional stacks if PositionStack is called
Optimizer.add_stack(TeamStack(3, for_teams=[''], for_positions=['QB','RB','WR','TE']))

# Stacks 3 players from same game. Does not force additional stacks if PositionStack is called
Optimizer.add_stack(GameStack(3))

# Forces single WR bring back 
Optimizer.force_positions_for_opposing_team(('QB', 'WR'))

# Forces WR AND TE bring back
Optimizer.force_positions_for_opposing_team(('QB', 'WR'),('QB','TE'))

# Keeps max two players over 20% ownership
Optimizer.add_players_group(PlayersGroup(
        players=[player for player in Optimizer.players if player.projected_ownership >= 0.20],
        max_from_group=2,
))

# Ensure two players under 10% ownership
Optimizer.add_players_group(PlayersGroup(
        players=[player for player in Optimizer.players if player.projected_ownership >= 0.20],
        max_from_group=2,
    ))

# Add secondary game stack with at least two players from two teams with players with projection over x
GameStack = PlayersGroup(Optimizer.player_pool.get_players(
        PlayerFilter(teams=['','']),
        PlayerFilter(filter_by='fppg',from_value=x)),
        min_from_group=2,
    )