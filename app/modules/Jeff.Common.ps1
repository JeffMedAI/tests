Set-StrictMode -Version Latest

function Ensure-Directory {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Get-FirstValue {
    param(
        [object]$Row,
        [string[]]$Names
    )

    foreach ($name in $Names) {
        $prop = $Row.PSObject.Properties[$name]
        if ($null -ne $prop) {
            $value = "$($prop.Value)".Trim()
            if (-not [string]::IsNullOrWhiteSpace($value)) {
                return $value
            }
        }
    }

    return ""
}

function Get-ObjectPropertyValue {
    param(
        [object]$Object,
        [string]$Name,
        $Default = $null
    )

    if ($null -eq $Object) {
        return $Default
    }

    if ($Object -is [System.Collections.IDictionary]) {
        if ($Object.Contains($Name)) {
            return $Object[$Name]
        }

        return $Default
    }

    $prop = $Object.PSObject.Properties[$Name]
    if ($null -ne $prop) {
        return $prop.Value
    }

    return $Default
}

function Set-ObjectPropertyValue {
    param(
        [object]$Object,
        [string]$Name,
        $Value
    )

    if ($null -eq $Object) {
        return
    }

    if ($Object -is [System.Collections.IDictionary]) {
        $Object[$Name] = $Value
        return
    }

    if ($Object.PSObject.Properties[$Name]) {
        $Object.PSObject.Properties[$Name].Value = $Value
    }
    else {
        $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
    }
}

function Get-FirstNonBlankValue {
    param([object[]]$Values)

    foreach ($value in $Values) {
        if ($null -eq $value) {
            continue
        }

        if ($value -is [System.Array]) {
            if (@($value).Count -gt 0) {
                return $value
            }

            continue
        }

        $text = [string]$value
        if (-not [string]::IsNullOrWhiteSpace($text)) {
            return $value
        }
    }

    return ""
}

function Test-JeffQueuePayloadFileName {
    param([string]$FileName)

    if ([string]::IsNullOrWhiteSpace($FileName)) {
        return $false
    }

    $name = [System.IO.Path]::GetFileName($FileName)

    if ($name -notmatch "\.json$") {
        return $false
    }

    if ($name -match "\.(deadletter|manifest|failed)\.json$") {
        return $false
    }

    if ($name -match "(^~|\.tmp\.json$|\.temp\.json$|\.bak\.json$|\.backup\.json$|\.before_|_backup)") {
        return $false
    }

    return $true
}
