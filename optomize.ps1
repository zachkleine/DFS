Param(
    [CmdletBinding()]
    [Parameter(Mandatory=$False)][String]$DfsDir = "G:\My Drive\Fantasy Football\DFS\2022",
    [Parameter(Mandatory=$False)][int]$Week = "13"
)
Function Get-DKSalaries {
    Param(
        [CmdletBinding()]
        [Parameter(Mandatory=$False)][String]$DfsDir,
        [Parameter(Mandatory=$False)][int]$Week
    )
    $FullDir = $DfsDir+"\Week$Week"
    $DKCsv = Import-Csv -Path $FullDir"\DKSalaries.csv"
    $ETRCsv = Import-Csv -Path $FullDir"\ETRProj.csv"
    foreach ($row in $DKCsv) {
        $name = $row.Name
        $lookup = $ETRCsv `
            | Where-Object {$_.Name -eq $name} `
            | Select-Object -ExpandProperty 'DK Projection'
        $row.AvgPointsPerGame = $lookup
    }
    $DKCsv | Export-Csv -Path $FullDir"\DKSalaries.csv" -NoTypeInformation -Force
}
Get-DKSalaries -DfsDir $DfsDir -Week $Week

<#  Need to call PyDFS program
from pydfs_lineup_optimizer import get_optimizer, Site, Sport, CSVLineupExporter

DKoptimizer = get_optimizer(Site.DRAFTKINGS, Sport.FOOTBALL)
DKoptimizer.load_players_from_csv('DKSalaries.csv')

lineups = list(DKoptimizer.optimize(10))
DKoptimizer.export('result.csv')
#>