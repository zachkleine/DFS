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
Function Get-FormattedLineup {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]$LineupArray
    )
    $RbCount = 0
    $WrCount = 0
    foreach ($pos in 0..($LineupArray.Length - 1)) {
        switch ($Lineup[$pos]) {
            "RB" {
                $RbCount++
                $LineupArray[$pos] = "RB$RbCount"
            }
            "WR" {
                $WrCount++
                $LineupArray[$pos] = "WR$WrCount"
            }
        }
    }
    Return $LineupArray
}
Function Get-ValidNames {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][String[]]$Positions,
        [Parameter(Mandatory=$true)]$NameList,
        [Parameter(Mandatory=$true)]$Names
    )
    foreach ($Position in $Positions) {
        $list += ($Names | Select-Object -Property $Position | Where-Object {$_.$Position -ne " "}).$Position | Sort-Object | Get-Unique
    }
    $ResultsList = $list | Sort-Object | Get-Unique
    foreach ($Result in $ResultsList) {
        if ($NameList -notcontains $Result) {
            $MissingList += $Result +" "
        }
    }
    Return $MissingList
}
Function Get-Lineups {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][String]$OpponentCsv,
        [Parameter(Mandatory=$true)][String[]]$Positions
    )
    $LineupCsv = Import-Csv -Path $OpponentCsv | Select-Object *,"QB","RB1","RB2","WR1","WR2","WR3","TE","FLEX","DST","Projection","Ownership","Ceiling"
    $FullLineup = ($LineupCsv).Lineup
    for ($i=0;$i -lt $FullLineup.Count;$i++) {
        $Lineup = $FullLineup[$i].split(" ")
        Get-FormattedLineup -LineupArray $Lineup
        foreach ($Position in $Positions) {
            $pos = $Lineup.indexof($Position)
            $Name = $Lineup[$pos+1] + " " + $Lineup[$pos+2]
            $LineupCsv[$i].$Position = $Name
        }
    }
    return $LineupCsv
}
Function Get-Totals {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][String]$LineupCsv,
        [Parameter(Mandatory=$true)][String[]]$Positions
    )
}
$Positions = @("QB", "RB1", "RB2", "WR1", "WR2", "WR3", "TE", "FLEX", "DST")
$FullDir = Join-Path -Path $DfsDir -ChildPath "Week$Week"
$Projections = $FullDir+"\ETRProj.csv"
$OpponentCsv = Get-OpponentCsv -Week $Week -FullDir $FullDir -MyUser $MyUser
$LineupCsv = Get-Lineups -OpponentCsv $OpponentCsv -Positions $Positions
$MissingNames = Get-ValidNames -Positions $Positions -NameList (Import-csv -path $Projections | Select-Object -Property Name).Name -Names ($LineupCsv | Select-Object -Property "QB","RB1","RB2","WR1","WR2","WR3","TE","FLEX","DST")
if (!$MissingNames){
    $LineupCsv `
        | Select-Object "EntryName","QB","RB1","RB2","WR1","WR2","WR3","TE","FLEX","DST","Points","Projection","Ownership","Ceiling" `
        | Export-Csv -Path $OpponentCsv -NoTypeInformation -Force
}
else {
    Remove-Item $OpponentCsv
    Out-File -FilePath $FullDir"\missingplayers.txt" -InputObject $MissingNames
}

#$ProjCsv = Import-Csv -Path $Projections | Select-Object "Name","DK Projection","DK Ownership","DK Ceiling"
<#    if (!$MissingPlayers) {
    }
    else {
        
        $Output = $MissingPlayers | Sort-Object | Get-Unique

    }#>

            #$ProjectionTotal = 0
        #$OwnershipTotal = 0
        #$CeilingTotal = 0
            #$ValidName = Get-ValidName -Name $Name -NameList $ProjCsv.Name
            #if ($ValidName) {    
            #    $LineupCsv[$i].$Position = $Name
            #    $Lookup = $ProjCsv `
            #        | Where-Object {$_.Name -eq $Name} `
            #        | Select-Object -Property "DK Projection","DK Ownership","DK Ceiling"
            #    $ProjectionTotal += $Lookup."DK Projection"
            #    $OwnershipTotal += $Lookup."DK Ownership"
            #    $CeilingTotal += $Lookup."DK Ceiling"
            #}
            #else {
            #    $MissingPlayers += $Name+" "
            #}
        #$LineupCsv[$i].'Projection' = $ProjectionTotal
        #$LineupCsv[$i].'Ownership' = $OwnershipTotal
        #$LineupCsv[$i].'Ceiling' = $CeilingTotal