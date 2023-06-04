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
    $PlayerCounts | Select-Object -Property Name,Exposure | Export-Csv -Path "UD_Exposure.csv" -NoTypeInformation -Force
    Pop-Location
}
Function Add-Files {
    Param(
        [CmdletBinding()]
        [Parameter(Mandatory=$False)][String]$BBDir
    )
    $ExcelFile = "BestBallBuddy.xlsx"
    $UDRankings = "Best-Ball---UD-Ranks.csv"
    $DKRankings = "Best-Ball---DK-Ranks.csv"
    #$DK_Exposure = "DK_Exposure.csv"
    $UD_Exposure = "UD_Exposure.csv"

    Push-Location -Path $BBDir
    $UD_ADPTab = "UD_ADP"
    $DK_ADPTab = "DK_ADP"
    #$DK_ExposureTab = "DK_Exposure"
    $UD_ExposureTab = "UD_Exposure"
    
    $UD_ADP_data = Import-Csv -Path $UDRankings
    $UD_ADP_data | Export-Excel -Path $ExcelFile -WorksheetName $UD_ADPTab
    
    $DK_ADP_data = Import-Csv -Path $DKRankings
    $DK_ADP_data | Export-Excel -Path $ExcelFile -WorksheetName $DK_ADPTab
    
    #$DK_Exposure_data = Import-Csv -Path $DK_Exposure
    #$DK_Exposure_data | Export-Excel -Path $ExcelFile -WorksheetName $DK_ExposureTab
    
    $UD_Exposure_data = Import-Csv -Path $UD_Exposure
    $UD_Exposure_data | Export-Excel -Path $ExcelFile -WorksheetName $UD_ExposureTab
    
    Pop-Location
}
$UD_Exposure = Get-UDExposure -BBDir $BBDir -UD_csv $UD_csv
#DK_Exposure = Get-DKExpsoure -BBDir $BBDir -DK_csv $DK_csv
Add-Files -BBDir $BBDir