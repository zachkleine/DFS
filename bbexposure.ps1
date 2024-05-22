Param(
    [CmdletBinding()]
    [Parameter(Mandatory=$False)][String]$BBDir = "G:\My Drive\Fantasy Football\BestBall\",
    [Parameter(Mandatory=$False)][String]$ExcelFile = "BestBallBuddy.xlsx",
    [Parameter(Mandatory=$False)][String]$UD_csv = "UD_Exposure_Raw.csv",
    [Parameter(Mandatory=$False)][String]$DK_csv = "DK_Exposure_Raw.csv"
)
Import-Module -Name ImportExcel
Function Get-UDExposure {
    Param(
        [CmdletBinding()]
        [Parameter(Mandatory=$False)][String]$UD_csv
    )
    $FilePath = Join-Path -Path $BBDir -ChildPath $UD_csv
    $ExposureCsv = Import-Csv -Path $FilePath | Select-Object -Property "First Name", "Last Name", "Draft", "Name", "Team", "Position"
    $DraftCount = ($ExposureCsv.Draft | Get-Unique).Count
    foreach ($Line in $ExposureCsv) {
        $Line."Name" = $Line."First Name"+" "+$Line."Last Name"
    }
    $PlayerCounts = $ExposureCsv."Name" | Group-Object | Select-Object Name, Count, Exposure, Team, Position
    foreach ($Player in $PlayerCounts) {
        $Exposure = (($Player.Count/$DraftCount) * 100).ToString("N2") + "%"
        $Player.Exposure = $Exposure
        $Player.Position = ($ExposureCsv | Select-Object -Property "Position", "Name" | Where-Object {$_.Name -eq $Player.Name}).Position | Get-Unique
        $Player.Team = ($ExposureCsv | Select-Object -Property "Team", "Name" | Where-Object {$_.Name -eq $Player.Name}).Team | Get-Unique
    }
    return $PlayerCounts | Select-Object -Property Name,Position,Team,Exposure
}
Function Get-DKExposure {
    Param(
        [CmdletBinding()]
        [Parameter(Mandatory=$False)][String]$DK_csv
    )
    $FilePath = Join-Path -Path $BBDir -ChildPath $DK_csv
    $ExposureCsv = Import-Csv -Path $FilePath | Select-Object -Property "Player", "Round", "Pos", "Team"
    $DraftCount = ($ExposureCsv.Round | Where-Object {$_ -eq "1"}).Count
    $PlayerCounts = $ExposureCsv.Player | Group-Object | Select-Object -Property "Name", "Count", "Exposure", "Team", "Pos"
    foreach ($Player in $PlayerCounts) {
        $Exposure = (($Player.Count/$DraftCount) * 100).ToString("N2") + "%"
        $Player.Exposure = $Exposure
        $Player.Pos = ($ExposureCsv | Select-Object -Property "Pos", "Player" | Where-Object {$_.Player -eq $Player.Name}).Pos | Get-Unique
        $Player.Team = ($ExposureCsv | Select-Object -Property "Team", "Player" | Where-Object {$_.Player -eq $Player.Name}).Team | Get-Unique
    }
    return $PlayerCounts | Select-Object -Property Name,Exposure
}
Function Add-Files {
    Param(
        [CmdletBinding()]
        [Parameter(Mandatory=$False)]$DKExposure,
        [Parameter(Mandatory=$False)]$UDExposure
    )
    $ExcelFile = "BestBallBuddy.xlsx"
    $hashTable = @{
        "Best-Ball---DK-Ranks.csv" = "DK_ADP"
        "Best-Ball---UD-Ranks.csv" = "UD_ADP"
    }
    foreach ($key in $hashTable.GetEnumerator()) {
        $data = Import-Csv -Path $key.Name | Select-Object -Property *,"Exposure"
        if ($key.Name -match "DK") {
            foreach ($Player in $data) {
                $lookup = $DKExposure | Where-Object {$_.Name -eq $Player.Name}
                if ($lookup) {
                    $Player.Exposure = $lookup.Exposure
                }
                else {
                    $Player.Exposure = "0%"
                }
            }
        }
        elseif ($key.Name -Match "UD") {
            foreach ($Player in $data) {
                $lookup = $UDExposure | Where-Object {$_.Name -eq $Player.Name}
                if ($lookup) {
                    $Player.Exposure = $lookup.Exposure
                }
                else {
                    $Player.Exposure = "0%"
                }
            }
        }
        $data | Export-Excel -Path $ExcelFile -WorksheetName $key.Value
    }
}
Function Get-NewDKDraft {
    $NewDKDraft = Import-Excel -Path $ExcelFile -WorksheetName 'DK_Draft' | Select-Object Round, Player, Pos, Team, Wk17, Pick, ADP, 'ADP Value'
    $ExposureCSV = Import-Csv -path $DK_csv
    $LastDKDraft = ($ExposureCsv[-20..-1]).Player
    $CompareDrafts = Compare-Object -ReferenceObject $LastDKDraft -DifferenceObject ($NewDKDraft).Player
    if ($CompareDrafts.count -gt 0) {
        $ExposureCSV += $NewDKDraft
        $ExposureCSV | Export-Csv -Path $DK_csv -NoTypeInformation -Force
    }
}
Push-Location -Path $BBDir
Get-NewDKDraft
$UDExposure = Get-UDExposure -UD_csv $UD_csv
$DKExposure = Get-DKExposure -DK_csv $DK_csv
Add-Files -DKExposure $DKExposure -UDExposure $UDExposure
Pop-Location