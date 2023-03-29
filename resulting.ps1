Param(
    [Parameter(Mandatory=$False)]$DfsDir = "",
    [Parameter(Mandatory=$False)]$Week = "",
    [Parameter(Mandatory=$False)]$MyUser = ""
)
Function Get-OpponentCsv {
    $OppCsv = "Week$Week"+"Results.csv"
    $ResultsDir = "$FullDir\Results\"
    Set-Location -Path $ResultsDir
    Get-ChildItem -Path $ResultsDir -Filter *.zip -Name | Expand-Archive -DestinationPath $ResultsDir
    $csvs = Get-ChildItem -Path $ResultsDir -Filter contest*.csv -Name
    foreach ($csv in $csvs) {    
        Import-Csv -Path $csv | Select-Object -Property 'EntryName','Lineup','Points' `
            | Where-Object {$_.EntryName -notmatch $MyUser} `
            | Export-Csv $OppCsv -Append -NoTypeInformation
        Remove-Item $csv
    }
    Return $OppCsv
}
Function Get-Lineups ($OpponentCsv) {
    $Positions = @("QB", "RB1", "RB2", "WR1", "WR2", "WR3", "TE", "FLEX", "DST")
    $csv = Import-Csv -Path $OpponentCsv | Select-Object *,"QB","RB1","RB2","WR1","WR2","WR3","TE","FLEX","DST" 
    $lineups = ($csv).Lineup
    for ($i=0;$i -lt $lineups.Count;$i++) {
        $array = $lineups[$i].split(" ")
        $Rb1Pos = $array.IndexOf("RB")
        $array[$Rb1Pos] = "RB1"
        $Rb2Pos = $array.IndexOf("RB")
        $array[$Rb2Pos] = "RB2"
        $Wr1Pos = $array.IndexOf("WR")
        $array[$Wr1Pos] = "WR1"
        $Wr2Pos = $array.IndexOf("WR")
        $array[$Wr2Pos] = "WR2"
        $Wr3Pos = $array.IndexOf("WR")
        $array[$Wr3Pos] = "WR3"
        foreach ($Position in $Positions) {
            $pos = $array.indexof($Position)
            $name = $array[$pos+1] + " " + $array[$pos+2]
            $csv[$i].$Position = $name
        }
    }
    $csv | export-csv -Path $OpponentCsv -NoTypeInformation -Force
}
$FullDir = $DfsDir+"\Week$Week"
$OpponentCsv = Get-OpponentCsv ($MyUser, $FullDir)
Get-Lineups $OpponentCsv
