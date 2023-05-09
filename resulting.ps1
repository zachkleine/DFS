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
Function Get-Lineups {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][String]$OpponentCsv,
        [Parameter(Mandatory=$true)][String]$Projections,
        [Parameter(Mandatory=$true)][String]$FullDir
    )
    $Positions = @("DST", "FLEX", "QB", "RB1", "RB2", "TE", "WR1", "WR2", "WR3")
    $LineupCsv = Import-Csv -Path $OpponentCsv | Select-Object *,"QB","RB1","RB2","WR1","WR2","WR3","TE","FLEX","DST","Projection","Ownership","Ceiling"        
    $ProjCsv = Import-Csv -Path $Projections | Select-Object "Name","DK Projection","DK Ownership","DK Ceiling"
    $FullLineup = ($LineupCsv).Lineup
    for ($i=0;$i -lt $FullLineup.Count;$i++) {
        $Lineup = $FullLineup[$i].split(" ")
        $FormattedLineup = Get-FormattedLineup -LineupArray $Lineup
        $Roster = Get-Roster -positions $Positions -rosterString $FormattedLineup
        foreach ($Position in $Positions) {
            $Name = $($Roster[$Position]).Trim($Position)
            $NameFinal = $Name.Trim(" ")
            if ($Position -eq "DST") {
                $NameFinal = $NameFinal+" "
            }
            $LineupCsv[$i].$Position = $NameFinal
        }
    }
    $MissingPlayers = Get-ValidateNames -Names ($LineupCsv | Select-Object -Property "QB","RB1","RB2","WR1","WR2","WR3","TE","FLEX","DST") -Projections ($ProjCsv).Name -Positions $Positions
    If (!$MissingPlayers) {
        #if valid do the calculations and output csv
        foreach ($Lineup in $LineupCsv) {
            $ProjectionTotal = @()
            $OwnershipTotal = @()
            $CeilingTotal = @()
            foreach ($Position in $Positions) {
                $Lookup = $ProjCsv `
                    | Where-Object {$_.Name -eq $Lineup.$Position} `
                    | Select-Object -Property "DK Projection","DK Ownership","DK Ceiling"
                $ProjectionTotal += $Lookup."DK Projection"
                $OwnershipTotal += $Lookup."DK Ownership"
                $CeilingTotal += $Lookup."DK Ceiling"
                write-host $OwnershipTotal.Count
            }
            $Lineup.'Projection' = ($ProjectionTotal | Measure-Object -Sum).Sum
            if ($OwnershipTotal.Count -ge 1) {
                $Lineup.'Ownership' = Get-ProductOwnership -OwnershipTotal $OwnershipTotal
            }
            else {
                $Lineup.'Ownership' = 0
            }
            $Lineup.'Ceiling' = ($CeilingTotal | Measure-Object -Sum).Sum
        } 
        $LineupCsv `
            | Select-Object "EntryName","QB","RB1","RB2","WR1","WR2","WR3","TE","FLEX","DST","Points","Projection","Ownership","Ceiling" `
            | Export-Csv -Path $OpponentCsv -NoTypeInformation -Force
    }
    else {
        $MissingPlayers | Out-File -FilePath $FullDir"\MissingPlayers.txt" -Force
        Remove-Item $OpponentCsv
    }
}
Function Get-FormattedLineup {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][System.Object]$LineupArray
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
Function Get-Roster {
    param (
        [string]$rosterString,
        [string[]]$positions
    )
    $roster = @{}
    $rosterString = $rosterString -split '\s+'
    for ($i = 0; $i -lt $positions.Length; $i++) {
        $pos = $positions[$i]
        $nextPos = $positions[$i+1]
        $startIndex = $rosterString.IndexOf($pos)
        $endIndex = $rosterString.IndexOf($nextPos)
        if ($endIndex -eq -1) {
            $endIndex = $rosterString.Length
        }
        $text = $rosterString[$startIndex..($endIndex-1)] -join ''
        $roster[$pos] = $text
    }
    return $roster
}
Function Get-ValidateNames {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][System.Object]$Names,
        [Parameter(Mandatory=$true)][System.Object]$Projections,
        [Parameter(Mandatory=$true)][String[]]$Positions
    )
    foreach ($Position in $Positions) {
        $list += ($Names | Select-Object -Property $Position | Where-Object {$_.$Position -ne " "}).$Position | Sort-Object | Get-Unique
    }
    $ResultsList = $list | Sort-Object | Get-Unique
    foreach ($Result in $ResultsList) {
        if ($Projections -notcontains $Result) {
            $MissingPlayers += $Result
        }
    }
    return $MissingPlayers
}
Function Get-ProductOwnership {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string[]]$OwnershipTotal
    )
    $product = 1
    foreach ($value in $OwnershipTotal) {
        if ($value -ne 0) {
            $product *= $value
        }
    }
    $total = $product / 1000
    return $total
}
$FullDir = Join-Path -Path $DfsDir -ChildPath "Week$Week"
$Projections = $FullDir+"\ETRProj.csv"
$OpponentCsv = Get-OpponentCsv -Week $Week -FullDir $FullDir -MyUser $MyUser
$LineupCsv = Get-Lineups -OpponentCsv $OpponentCsv -Projections $Projections -FullDir $FullDir