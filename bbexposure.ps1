Param(
    [CmdletBinding()]
    [Parameter(Mandatory=$False)][String]$BBDir = "G:\My Drive\Fantasy Football\BestBall",
    [Parameter(Mandatory=$False)][String]$UD_csv = "UD_Exposure_Raw.csv",
    [Parameter(Mandatory=$False)][String]$DK_csv = "DK_Exposure_Raw.csv"
)
Import-Module -Name ImportExcel
Function Get-UDExposure {
    Param(
        [CmdletBinding()]
        [Parameter(Mandatory=$False)][String]$BBDir,
        [Parameter(Mandatory=$False)][String]$UD_csv
    )
    Push-Location -Path $BBDir
    $FilePath = Join-Path -Path $BBDir -ChildPath $UD_csv
    $ExposureCsv = Import-Csv -Path $FilePath | Select-Object -Property "First Name", "Last Name", "Draft", "Name"
    $DraftCount = ($ExposureCsv.Draft | Get-Unique).Count
    foreach ($Line in $ExposureCsv) {
        $Line."Name" = $Line."First Name"+" "+$Line."Last Name"
    }
    $PlayerCounts = $ExposureCsv."Name" | Group-Object | Select-Object Name, Count, Exposure
    foreach ($Player in $PlayerCounts) {
        $Exposure = (($Player.Count/$DraftCount) * 100).ToString("N2") + "%"
        $Player.Exposure = $Exposure
    }
    $PlayerCounts | Select-Object -Property Name,Team,Pos,Exposure | Export-Csv -Path "UD_Exposure.csv" -NoTypeInformation -Force
    Pop-Location
}
Function Get-DKExposure {
    Param(
        [CmdletBinding()]
        [Parameter(Mandatory=$False)][String]$BBDir,
        [Parameter(Mandatory=$False)][String]$DK_csv
    )
    Push-Location -Path $BBDir
    $FilePath = Join-Path -Path $BBDir -ChildPath $DK_csv
    $ExposureCsv = Import-Csv -Path $FilePath | Select-Object -Property "Player", "Round"
    $DraftCount = ($ExposureCsv.Round | Where-Object {$_ -eq "1"}).Count
    $PlayerCounts = $ExposureCsv.Player | Group-Object | Select-Object -Property "Name", "Count", "Exposure"
    foreach ($Player in $PlayerCounts) {
        $Exposure = (($Player.Count/$DraftCount) * 100).ToString("N2") + "%"
        $Player.Exposure = $Exposure
    }
    $PlayerCounts | Select-Object -Property Name,Exposure | Export-Csv -Path "DK_Exposure.csv" -NoTypeInformation -Force
    Pop-Location
}
Function Add-Files {
    Param(
        [CmdletBinding()]
        [Parameter(Mandatory=$False)][String]$BBDir
    )
    $ExcelFile = "BestBallBuddy.xlsx"
    Push-Location -Path $BBDir
    $hashTable = @{
        "Best-Ball---DK-Ranks.csv" = "DK_ADP"
        "Best-Ball---UD-Ranks.csv" = "UD_ADP"
        "UD_Exposure.csv" = "UD_Exposure"
        "DK_Exposure.csv" = "DK_Exposure"
    }
    foreach ($key in $hashTable.GetEnumerator()) {
        $data = Import-Csv -Path $key.Name
        $data | Export-Excel -Path $ExcelFile -WorksheetName $key.Value
    }
    Pop-Location
}
Get-UDExposure -BBDir $BBDir -UD_csv $UD_csv
Get-DKExposure -BBDir $BBDir -DK_csv $DK_csv
Add-Files -BBDir $BBDir