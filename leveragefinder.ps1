Param(
    [CmdletBinding()]
    [Parameter(Mandatory=$False)][String]$DfsDir = "G:\My Drive\Fantasy Football\DFS\2025",
    [Parameter(Mandatory=$False)][int]$Week = "1"
)
function Get-ChalkPlayers {
    Param(
        [CmdletBinding()]
        [Parameter(Mandatory=$False)]$Projections
    )
    $ChalkMin = @{
        "QB"  = "10"
        "RB"  = "25"
        "WR"  = "20"
        "TE"  = "15"
        "DST" = "15"
    }
    $Chalk = @()
    foreach ($player in $Projections) {
        $position = $player.'DK Pos'
        $ownership = [double]$player.'Large Field'
        if ($ChalkMin.ContainsKey($position) -and $ownership -ge $ChalkMin[$position]) {
            $Chalk += $player
        }
    }
    return $Chalk
}
function Get-TeamLeverage {
    Param(
        [Parameter(Mandatory=$True)]$Projections,
        [Parameter(Mandatory=$True)]$Chalk
    )
    $ExclusionRules = @{
        "QB" = @("WR", "TE", "QB")
        "RB" = @("RB", "DST")
        "WR" = @("QB")
        "TE" = @("QB")
        "DST" = @("QB", "RB", "WR", "TE")
    }
    $TeamLeverage = @()
    foreach ($chalkPlayer in $Chalk) {
        $excludedPositions = $ExclusionRules[$chalkPlayer.'DK Pos']         
        $TeamPlayers = $Projections | Where-Object {
            $_.Team -eq $chalkPlayer.Team `
            -and [double]$_.'DK Proj' -gt 10 `
            -and [double]$_.'Large Field' -le 10 `
            -and [double]$_.'DK Value' -ge -5.0 `
            -and ($excludedPositions -notcontains $_.'DK Pos')
        }
        $TeamPlayers | Add-Member -MemberType NoteProperty -Name "Team Leverage" -Value $chalkPlayer.Player -Force
        $TeamLeverage += $TeamPlayers
        
    }
    return $TeamLeverage
}

function Get-PricePivots {
    Param(
        [Parameter(Mandatory=$True)]$Projections,
        [Parameter(Mandatory=$True)]$Chalk
    )
    $PricePivots = @()
    foreach ($chalkPlayer in $Chalk) {
        $Pivots = $Projections | Where-Object {
            $_.'DK Pos' -notin @('DST','QB') `
            -and $_.'DK Pos' -eq $chalkPlayer.'DK Pos' `
            -and [double]$_.'DK Salary' -ge ([double]$chalkPlayer.'DK Salary' - 300) `
            -and [double]$_.'DK Salary' -le ([double]$chalkPlayer.'DK Salary' + 300) `
            -and [double]$_.'Large Field' -le 10 `
            -and [double]$_.'DK Value' -ge -5.0 `
            -and [double]$_.'DK Proj' -gt 10
        }
        $Pivots | Add-Member -MemberType NoteProperty -Name "Price Pivots" -Value $chalkPlayer.Player -Force
        $PricePivots += $Pivots
    }
    return $PricePivots
}

$FullDir = Join-Path -Path $DfsDir -ChildPath "week$Week\DKETRProj.csv"
$Projections = Import-Csv -Path $FullDir `
            | Select-Object -Property 'Player','Team','DK Pos','DK Salary','DK Proj','Large Field','DK Value'
$Chalk = Get-ChalkPlayers -Projections $Projections
$TeamLeverage = Get-TeamLeverage -Projections $Projections -Chalk $Chalk
$PricePivots = Get-PricePivots -Projections $Projections -Chalk $Chalk
$LeveragePlays = $PricePivots + $TeamLeverage
$LeveragePlays | Select-Object -Property 'Player','Team', "DK Pos", "DK Salary", "DK Proj", "Large Field", "DK Value", "Price Pivots", "Team Leverage" -Unique `
               | Sort-Object Player | Format-Table -AutoSize