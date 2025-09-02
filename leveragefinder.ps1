Param(
    [CmdletBinding()]
    [Parameter(Mandatory=$False)][String]$DfsDir = "G:\My Drive\Fantasy Football\DFS\2024",
    [Parameter(Mandatory=$False)][int]$Week = "12"
)
function Get-ChalkPlayers {
    Param(
        [CmdletBinding()]
        [Parameter(Mandatory=$False)]$Projections
    )
    $ChalkMin = @{
        "QB"  = "15"
        "RB"  = "20"
        "WR"  = "25"
        "TE"  = "15"
        "DST" = "15"
    }
    $Chalk = @()
    foreach ($player in $Projections) {
        $position = $player.'DK Position'
        $ownership = [double]$player.'DK Large Ownership'
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
        "QB" = @("WR", "TE")
        "RB" = @("RB", "DST")
        "WR" = @("QB")
        "TE" = @("QB")
        "DST" = @("QB", "RB", "WR", "TE")
    }
    $TeamLeverage = @()
    foreach ($chalkPlayer in $Chalk) {
        $excludedPositions = $ExclusionRules[$chalkPlayer.'DK Position']         
        $TeamPlayers = $Projections | Where-Object {
            $_.Team -eq $chalkPlayer.Team `
            -and [double]$_.'DK Projection' -gt 10 `
            -and [double]$_.'DK Large Ownership' -le 15 `
            -and [double]$_.'DK Value' -ge -5.0 `
            -and ($excludedPositions -notcontains $_.'DK Position')
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
            $_.'DK Position' -notin @('DST','QB') `
            -and $_.'DK Position' -eq $chalkPlayer.'DK Position' `
            -and [double]$_.'DK Salary' -ge ([double]$chalkPlayer.'DK Salary' - 300) `
            -and [double]$_.'DK Salary' -le ([double]$chalkPlayer.'DK Salary' + 300) `
            -and [double]$_.'DK Large Ownership' -le 15 `
            -and [double]$_.'DK Value' -ge -5.0 `
            -and [double]$_.'DK Projection' -gt 10
        }
        $Pivots | Add-Member -MemberType NoteProperty -Name "Price Pivots" -Value $chalkPlayer.Player -Force
        $PricePivots += $Pivots
    }
    return $PricePivots
}

$FullDir = Join-Path -Path $DfsDir -ChildPath "week$Week\DKETRProj.csv"
$Projections = Import-Csv -Path $FullDir `
            | Select-Object -Property 'Player','Team','DK Position','DK Salary','DK Projection','DK Large Ownership','DK Value'
$Chalk = Get-ChalkPlayers -Projections $Projections
$TeamLeverage = Get-TeamLeverage -Projections $Projections -Chalk $Chalk
$PricePivots = Get-PricePivots -Projections $Projections -Chalk $Chalk
$LeveragePlays = $PricePivots + $TeamLeverage
$LeveragePlays | Select-Object -Property Player,Team, "DK Position", "DK Salary", "DK Projection", "DK Large Ownership", "DK Value", "Price Pivots", "Team Leverage" -Unique `
               | Sort-Object Player | Format-Table -AutoSize