Param(
    [CmdletBinding()]
    [Parameter(Mandatory=$False)][String]$DfsDir = "C:\Users\zachk\Downloads", #G:\My Drive\Fantasy Football\DFS\2022\
    [Parameter(Mandatory=$False)][int]$Week = "13", #14
    [Parameter(Mandatory=$False)][String]$MyUser = "ZachKleine"
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
    $LineupCsv = Import-Csv -Path $OpponentCsv | Select-Object *,"QB","RB1","RB2","WR1","WR2","WR3","TE","FLEX","DST" 
    $FullLineup = ($LineupCsv).Lineup
    for ($i=0;$i -lt $FullLineup.Count;$i++) {
        $Lineup = $FullLineup[$i].split(" ")
        $RbCount = 0
        $WrCount = 0
        foreach ($pos in 0..($Lineup.Length - 1)) {
            switch ($Lineup[$pos]) {
                "RB" {
                    $RbCount++
                    $Lineup[$pos] = "RB$RbCount"
                }
                "WR" {
                    $WrCount++
                    $Lineup[$pos] = "WR$WrCount"
                }
            }
        }
        foreach ($Position in $Positions) {
            $pos = $Lineup.indexof($Position)
            $name = $Lineup[$pos+1] + " " + $Lineup[$pos+2]
            $LineupCsv[$i].$Position = $name
        }
    }
    $LineupCsv | Export-Csv -Path $OpponentCsv -NoTypeInformation -Force

}
Function Get-Points () {
    C:\Users\zachk\Downloads\Week13\Week13_Results.csv   
}

$FullDir = Join-Path -Path $DfsDir -ChildPath "Week$Week"
$OpponentCsv = Get-OpponentCsv -Week $Week -FullDir $FullDir -MyUser $MyUser
$LineupCsv = Get-Lineups -OpponentCsv $OpponentCsv
Write-Host $LineupCsv