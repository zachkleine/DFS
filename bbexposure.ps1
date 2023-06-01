Function Get-UDExposure {
    Param(
        [CmdletBinding()]
        [Parameter(Mandatory=$False)][String]$BBDir = "G:\My Drive\Fantasy Football\BestBall",
        [Parameter(Mandatory=$False)][String]$UD_csv = "UD_Exposure.csv"
    )
    $FilePath = Join-Path -Path $BBDir -ChildPath $UD_csv
    $ExposureCsv = Import-Csv -Path $FilePath | Select-Object -Property "First Name", "Last Name", "Draft", "Name", "Exposure"
    $DraftCount = ($ExposureCsv.Draft | Get-Unique).Count
    foreach ($Line in $ExposureCsv) {
        $Line."Name" = $Line."First Name"+" "+$Line."Last Name"
    }
    $PlayerList = $ExposureCsv."Name" | Sort-Object | Get-Unique
    foreach ($Player in $PlayerList) {
        $Count = $ExposureCsv."Name" | Where-Object {$_ -eq $Player} | Measure-Object | Select-Object -ExpandProperty Count
        $Exposure = (($Count/$DraftCount) * 100).ToString("N2") + "%"
        #Write $exposure to exposure column
        
    }
    Return $ExposureCsv
}
$Csv = Get-UDExposure
#export Csv 