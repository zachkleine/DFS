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
        $Count = $ExposureCsv."Name" | Where-Object {$_ -eq $Line."Name"} | Measure-Object | Select-Object -ExpandProperty Count
        $Exposure = (($Count/$DraftCount) * 100).ToString("N2") + "%"
        $Line."Exposure" = $Exposure
    }
    $ExposureCsv | Sort-Object -Property "Name" | Get-Unique
    Return $ExposureCsv
}
$Csv = Get-UDExposure