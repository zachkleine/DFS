Function Get-UDExposure {
    Param(
        [CmdletBinding()]
        [Parameter(Mandatory=$False)][String]$BBDir = "G:\My Drive\Fantasy Football\BestBall",
        [Parameter(Mandatory=$False)][String]$UD_csv = "Underdog_Exposure.csv"
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
    $PlayerCounts | Select-Object -Property Name,Exposure | Export-Csv -Path "UD_Exposure.csv" -NoTypeInformation -Force
    Pop-Location
}
Get-UDExposure