Set-StrictMode -Version Latest

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Normalize-Whitespace {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return "" }
    return (($Text -replace '\s+', ' ').Trim())
}

function To-TitleCaseSafe {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) { return "" }

    $words = Normalize-Whitespace $Text -split ' '
    $fixed = foreach ($w in $words) {
        if ($w.Length -le 1) {
            $w.ToUpper()
        } else {
            $w.Substring(0,1).ToUpper() + $w.Substring(1).ToLower()
        }
    }
    return ($fixed -join ' ')
}

function Normalize-Name {
    param([string]$Name)
    if ([string]::IsNullOrWhiteSpace($Name)) { return "" }
    return (Normalize-Whitespace $Name).ToUpper()
}

function Normalize-DateString {
    param([string]$DateText)
    if ([string]::IsNullOrWhiteSpace($DateText)) { return "" }

    $text = $DateText.Trim()
    $text = $text -replace '\b(\d{1,2})(st|nd|rd|th)\b', '$1'
    $text = $text -replace '\bof\b', ''
    $text = $text -replace ',', ''
    $text = Normalize-Whitespace $text

    $formats = @(
        "yyyy-MM-dd",
        "dd/MM/yyyy",
        "d/M/yyyy",
        "dd-MM-yyyy",
        "d-M-yyyy",
        "dd MMMM yyyy",
        "d MMMM yyyy",
        "dd MMM yyyy",
        "d MMM yyyy",
        "d MMM yy",
        "dd MMM yy",
        "d MMMM yy",
        "dd MMMM yy",
        "dd-MMM-yyyy",
        "d-MMM-yyyy",
        "dd-MMM-yy",
        "d-MMM-yy"
    )

    foreach ($fmt in $formats) {
        try {
            $dt = [datetime]::ParseExact($text, $fmt, $null)

            if ($dt.Year -gt (Get-Date).Year) {
                $dt = $dt.AddYears(-100)
            }

            return $dt.ToString("yyyy-MM-dd")
        } catch {}
    }

    try {
        $dt = [datetime]::Parse($text)
        if ($dt.Year -gt (Get-Date).Year) {
            $dt = $dt.AddYears(-100)
        }
        return $dt.ToString("yyyy-MM-dd")
    } catch {
        return ""
    }
}

function Normalize-Phone {
    param([string]$Phone)
    if ([string]::IsNullOrWhiteSpace($Phone)) { return "" }
    $digits = ($Phone -replace '[^\d]', '').Trim()
    if ($digits.Length -lt 10) { return "" }
    return $digits
}

function Get-LastName {
    param([string]$FullName)
    if ([string]::IsNullOrWhiteSpace($FullName)) { return "" }
    $parts = (Normalize-Whitespace $FullName) -split '\s+'
    return $parts[-1].ToUpper()
}

function Get-FirstName {
    param([string]$FullName)
    if ([string]::IsNullOrWhiteSpace($FullName)) { return "" }
    $parts = (Normalize-Whitespace $FullName) -split '\s+'
    return $parts[0].ToUpper()
}

function Test-First3LettersMatch {
    param(
        [string]$InputName,
        [string]$CandidateName
    )

    $a = Get-FirstName $InputName
    $b = Get-FirstName $CandidateName

    if ($a.Length -lt 3 -or $b.Length -lt 3) {
        return $false
    }

    return ($a.Substring(0,3) -eq $b.Substring(0,3))
}

function Test-SameSurname {
    param(
        [string]$InputName,
        [string]$CandidateName
    )
    $a = Get-LastName $InputName
    $b = Get-LastName $CandidateName
    return ($a -ne "" -and $b -ne "" -and $a -eq $b)
}

function Test-ExactFirstNameMatch {
    param(
        [string]$InputName,
        [string]$CandidateName
    )

    $a = Get-FirstName $InputName
    $b = Get-FirstName $CandidateName

    return ($a -ne "" -and $b -ne "" -and $a -eq $b)
}

function Convert-MedsToArray {
    param([object]$Value)

    if ($null -eq $Value) { return @() }

    if ($Value -is [System.Array]) {
        return @($Value | ForEach-Object { Normalize-Whitespace "$_" } | Where-Object { $_ -ne "" })
    }

    $text = Normalize-Whitespace "$Value"
    if ($text -eq "") { return @() }

    $parts = $text -split ',|;|\band\b'
    return @($parts | ForEach-Object { Normalize-Whitespace $_ } | Where-Object { $_ -ne "" })
}

function Normalize-TranscriptText {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) { return "" }

    $t = $Text
    $t = $t.Replace([char]0x2018, "'")
    $t = $t.Replace([char]0x2019, "'")
    $t = $t.Replace([char]0x201C, '"')
    $t = $t.Replace([char]0x201D, '"')
    $t = $t.Replace([char]0x2013, '-')
    $t = $t.Replace([char]0x2014, '-')

    return $t
}

function Convert-LookupNameToDisplay {
    param([string]$LookupName)

    if ([string]::IsNullOrWhiteSpace($LookupName)) { return "" }

    $name = Normalize-Whitespace $LookupName
    $name = $name -replace '\s*\((Mr|Mrs|Miss|Ms)\)\s*', ''

    if ($name -match '^\s*([^,]+)\s*,\s*(.+?)\s*$') {
        $surname = To-TitleCaseSafe $matches[1]
        $firstPart = To-TitleCaseSafe $matches[2]
        return Normalize-Whitespace "$firstPart $surname"
    }

    return To-TitleCaseSafe $name
}

function Get-LevenshteinDistance {
    param(
        [string]$A,
        [string]$B
    )

    if ($null -eq $A) { $A = "" }
    if ($null -eq $B) { $B = "" }

    $A = $A.ToUpper()
    $B = $B.ToUpper()

    $n = $A.Length
    $m = $B.Length

    if ($n -eq 0) { return $m }
    if ($m -eq 0) { return $n }

    $d = New-Object 'int[,]' ($n + 1), ($m + 1)

    for ($i = 0; $i -le $n; $i++) {
        $d[$i, 0] = $i
    }

    for ($j = 0; $j -le $m; $j++) {
        $d[0, $j] = $j
    }

    for ($i = 1; $i -le $n; $i++) {
        for ($j = 1; $j -le $m; $j++) {

            $cost = if ($A[$i - 1] -eq $B[$j - 1]) { 0 } else { 1 }

            $delete = $d[($i - 1), $j] + 1
            $insert = $d[$i, ($j - 1)] + 1
            $substitute = $d[($i - 1), ($j - 1)] + $cost

            $min1 = [Math]::Min($delete, $insert)
            $d[$i, $j] = [Math]::Min($min1, $substitute)
        }
    }

    return $d[$n, $m]
}

function Get-SurnameSimilarityScore {
    param(
        [string]$InputName,
        [string]$CandidateName
    )

    $a = Get-LastName $InputName
    $b = Get-LastName $CandidateName

    if ([string]::IsNullOrWhiteSpace($a) -or [string]::IsNullOrWhiteSpace($b)) {
        return 0
    }

    if ($a -eq $b) {
        return 100
    }

    $distance = Get-LevenshteinDistance -A $a -B $b
    $maxLen = [Math]::Max($a.Length, $b.Length)

    if ($maxLen -eq 0) {
        return 0
    }

    $score = [Math]::Round((1 - ($distance / $maxLen)) * 100, 0)

    if ($score -lt 0) { $score = 0 }
    if ($score -gt 100) { $score = 100 }

    return [int]$score
}