Param(
    [CmdletBinding()]
    [Parameter(Mandatory=$False)][String]$DfsDir = "", #G:\My Drive\Fantasy Football\DFS\2022\
    [Parameter(Mandatory=$False)][int]$Week = ""
    [Parameter(Mandatory=$False)][String]$MyUser = ""
)
Function Get-OpponentCsv {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][int]$Week,
        [Parameter(Mandatory=$true)][string]$FullDir, 
        [Parameter(Mandatory=$true)][string]$MyUser
    )
    $FileName = "Week$Week" + "_Results.csv"
    $OppCsv = Join-Path -Path $FullDir -ChildPath $FileName
    $ResultsDir = Join-Path -Path $FullDir -ChildPath "Results"
    try {
        Push-Location -Path $ResultsDir
        Get-ChildItem -Path $ResultsDir -Filter *.zip -Name | Expand-Archive -DestinationPath $ResultsDir -ErrorAction SilentlyContinue
    }
    catch {
        Write-Error "Error expanding zip file: $($_.Exception.Message)"
        return
    }
    $csvs = Get-ChildItem -Path $ResultsDir -Filter contest*.csv -Name
    foreach ($csv in $csvs) {    
        try {
            Import-Csv -Path $csv | Select-Object -Property 'EntryName','Lineup','Points' `
                | Where-Object {$_.EntryName -notmatch $MyUser} `
                | Export-Csv $OppCsv -Append -NoTypeInformation
            Remove-Item $csv -Force
        }
        catch {
            Write-Error "Error importing CSV file '$csv': $($_.Exception.Message)"
        }
    }
    Pop-Location
    Return $OppCsv
}
Function Get-Lineups {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][String]$OpponentCsv
    )
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
    $csv | Export-Csv -Path $OpponentCsv -NoTypeInformation -Force
}
Function Get-Points () {
    
}

$FullDir = Join-Path -Path $DfsDir -ChildPath "Week$Week"
$OpponentCsv = Get-OpponentCsv -Week $Week -FullDir $FullDir -MyUser $MyUser
Get-Lineups -OpponentCsv $OpponentCsv
