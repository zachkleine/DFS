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
        "RB"  = "15"
        "WR"  = "15"
        "TE"  = "12"
        "DST" = "10"
    }
    $Chalk = @()
    foreach ($player in $Projections) {
        $position = $player.'Position'
        $ownership = [double]$player.'Ownership'
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
        $excludedPositions = $ExclusionRules[$chalkPlayer.'Position']         
        $TeamPlayers = $Projections | Where-Object {
            $_.Team -eq $chalkPlayer.Team `
            -and [double]$_.'Projection' -gt 10 `
            -and [double]$_.'Ownership' -le 10 `
            -and [double]$_.'Value' -ge -5.0 `
            -and ($excludedPositions -notcontains $_.'Position')
        }
        $TeamPlayers | Add-Member -MemberType NoteProperty -Name "Team Leverage" -Value $chalkPlayer.Name -Force
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
            $_.'Position' -notin @('DST','QB') `
            -and $_.'Position' -eq $chalkPlayer.'Position' `
            -and [double]$_.'Salary' -ge ([double]$chalkPlayer.'Salary' - 300) `
            -and [double]$_.'Salary' -le ([double]$chalkPlayer.'Salary' + 300) `
            -and [double]$_.'Ownership' -le 10 `
            -and [double]$_.'Value' -ge -5.0 `
            -and [double]$_.'Projection' -gt 10
        }
        $Pivots | Add-Member -MemberType NoteProperty -Name "Price Pivots" -Value $chalkPlayer.Name -Force
        $PricePivots += $Pivots
    }
    return $PricePivots
}

$FullDir = Join-Path -Path $DfsDir -ChildPath "week$Week\DKETRProj.csv"
$Projections = Import-Csv -Path $FullDir `
            | Select-Object -Property 'Name','Team','Position','Salary','Projection','Ownership','Value'
$Chalk = Get-ChalkPlayers -Projections $Projections
$TeamLeverage = Get-TeamLeverage -Projections $Projections -Chalk $Chalk
$PricePivots = Get-PricePivots -Projections $Projections -Chalk $Chalk
$LeveragePlays = $PricePivots + $TeamLeverage
$LeveragePlays | Select-Object -Property Name,Team, "Position", "Salary", "Projection", "Ownership", "Value", "Price Pivots", "Team Leverage" -Unique `
               | Sort-Object Player | Format-Table -AutoSize