Param(
    [CmdletBinding()]
    [Parameter(Mandatory=$False)][String]$DfsDir = "G:\My Drive\Fantasy Football\DFS\2022",
    [Parameter(Mandatory=$False)][int]$Week = "13",
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
Function Get-RBWR {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]$Lineup
    )
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
    Return $Lineup
}
Function Get-Lineups {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][String]$OpponentCsv,
        [Parameter(Mandatory=$true)]$ProjCsv
    )
    $Positions = @("QB", "RB1", "RB2", "WR1", "WR2", "WR3", "TE", "FLEX", "DST")
    $LineupCsv = Import-Csv -Path $OpponentCsv | Select-Object *,"QB","RB1","RB2","WR1","WR2","WR3","TE","FLEX","DST","Projection","Ownership","Ceiling"
    $ProjCsv = $ProjCsv | Select-Object "Name","DK Projection","DK Ownership","DK Ceiling"
    $FullLineup = ($LineupCsv).Lineup
    for ($i=0;$i -lt $FullLineup.Count;$i++) {
        $Lineup = $FullLineup[$i].split(" ")
        Get-RBWR -Lineup $Lineup
        $ProjectionTotal = 0
        $OwnershipTotal = 0
        $CeilingTotal = 0
        foreach ($Position in $Positions) {
            $pos = $Lineup.indexof($Position)
            $name = $Lineup[$pos+1] + " " + $Lineup[$pos+2]
            $LineupCsv[$i].$Position = $name
            $Lookup = $ProjCsv `
                | Where-Object {$_.Name -eq $name} `
                | Select-Object -Property "DK Projection","DK Ownership","DK Ceiling"
            $ProjectionTotal += $Lookup."DK Projection"
            $OwnershipTotal += $Lookup."DK Ownership"
            $CeilingTotal += $Lookup."DK Ceiling"
        }
        $LineupCsv[$i].'Projection' = $ProjectionTotal
        $LineupCsv[$i].'Ownership' = $OwnershipTotal
        $LineupCsv[$i].'Ceiling' = $CeilingTotal
    }
    $LineupCsv `
        | Select-Object "EntryName","QB","RB1","RB2","WR1","WR2","WR3","TE","FLEX","DST","Points","Projection","Ownership","Ceiling" `
        | Export-Csv -Path $OpponentCsv -NoTypeInformation -Force
}
$FullDir = Join-Path -Path $DfsDir -ChildPath "Week$Week"
$ProjCsv = Import-Csv -Path $FullDir"\ETRProj.csv"
$OpponentCsv = Get-OpponentCsv -Week $Week -FullDir $FullDir -MyUser $MyUser
$LineupCsv = Get-Lineups -OpponentCsv $OpponentCsv -ProjCsv $ProjCsv