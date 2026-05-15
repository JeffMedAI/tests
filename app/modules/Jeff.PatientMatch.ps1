Set-StrictMode -Version Latest

function Get-JeffSafePropertyValue {
    param(
        [object]$Object,
        [string]$Name,
        $Default = ""
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

function Get-JeffFirstNonBlank {
    param([array]$Values)

    foreach ($v in $Values) {
        $s = [string]$v
        if (-not [string]::IsNullOrWhiteSpace($s)) {
            return $s
        }
    }

    return ""
}

function Normalize-JeffHandoffName {
    param([string]$Name)

    $value = [string]$Name
    $value = $value.Trim()

    if ([string]::IsNullOrWhiteSpace($value)) {
        return ""
    }

    $value = $value -replace "\(.*?\)", ""
    $value = $value.Trim()

    if ($value -match ",") {
        $parts = $value.Split(",", 2)
        $value = "$($parts[1].Trim()) $($parts[0].Trim())"
    }

    $value = $value.ToUpperInvariant()
    $value = $value -replace "[^A-Z0-9 ]", " "
    $value = $value -replace "\s+", " "
    return $value.Trim()
}

function Get-JeffLastNameSafe {
    param([string]$Name)

    $n = Normalize-JeffHandoffName $Name
    if ([string]::IsNullOrWhiteSpace($n)) {
        return ""
    }

    $parts = @($n.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries))
    if ($parts.Count -eq 0) {
        return ""
    }

    return $parts[-1]
}

function Get-JeffFirstNameSafe {
    param([string]$Name)

    $n = Normalize-JeffHandoffName $Name
    if ([string]::IsNullOrWhiteSpace($n)) {
        return ""
    }

    $parts = @($n.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries))
    if ($parts.Count -eq 0) {
        return ""
    }

    return $parts[0]
}

function Get-JeffSimilarityScore {
    param(
        [string]$A,
        [string]$B
    )

    $aNorm = Normalize-JeffHandoffName $A
    $bNorm = Normalize-JeffHandoffName $B

    if ([string]::IsNullOrWhiteSpace($aNorm) -or [string]::IsNullOrWhiteSpace($bNorm)) {
        return 0
    }

    if ($aNorm -eq $bNorm) {
        return 100
    }

    $aLast = Get-JeffLastNameSafe $aNorm
    $bLast = Get-JeffLastNameSafe $bNorm
    $aFirst = Get-JeffFirstNameSafe $aNorm
    $bFirst = Get-JeffFirstNameSafe $bNorm

    $score = 0

    if ($aLast -eq $bLast) {
        $score += 50
    }
    elseif ($aLast.Length -ge 3 -and $bLast.Length -ge 3 -and $aLast.Substring(0, 3) -eq $bLast.Substring(0, 3)) {
        $score += 30
    }

    if ($aFirst -eq $bFirst) {
        $score += 40
    }
    elseif ($aFirst.Length -ge 3 -and $bFirst.Length -ge 3 -and $aFirst.Substring(0, 3) -eq $bFirst.Substring(0, 3)) {
        $score += 20
    }

    return $score
}

function Get-JeffPatientMatch {
    param(
        [string]$PatientName,
        [string]$Dob,
        [array]$NormalizedPatients,
        [array]$FlagMissingFields = @()
    )

    $verificationStatus = "no_match"
    $verificationReason = "No matching patient found in lookup."
    $matchedPatientRef = ""
    $matchedPatientName = ""
    $matchedNhsNumber = ""
    $matchedAge = ""
    $matchedGender = ""
    $candidateMatches = @()
    $topCandidateRef = ""
    $topCandidateName = ""
    $topCandidateScore = 0

    if ([string]::IsNullOrWhiteSpace($PatientName) -or [string]::IsNullOrWhiteSpace($Dob)) {
        $verificationStatus = "insufficient_data"
        $verificationReason = "Required identity details missing for safe patient matching."
    }
    else {
        $scoredCandidates = @()

        foreach ($patient in @($NormalizedPatients)) {
            if ($null -eq $patient) {
                continue
            }

            $candidateDob = Get-JeffSafePropertyValue -Object $patient -Name "dob" -Default ""
            $candidateName = Get-JeffSafePropertyValue -Object $patient -Name "full_name" -Default ""
            $candidateNameNorm = Get-JeffFirstNonBlank @(
                (Get-JeffSafePropertyValue -Object $patient -Name "full_name_normalized"),
                (Normalize-JeffHandoffName $candidateName)
            )

            if ([string]::IsNullOrWhiteSpace($candidateDob) -or [string]::IsNullOrWhiteSpace($candidateNameNorm)) {
                continue
            }

            $sameDob = $candidateDob -eq $Dob
            $nameScore = Get-JeffSimilarityScore -A $PatientName -B $candidateName

            if ($sameDob -or $nameScore -ge 50) {
                $score = $nameScore
                if ($sameDob) {
                    $score += 100
                }

                $candidateRef = Get-JeffFirstNonBlank @(
                    (Get-JeffSafePropertyValue -Object $patient -Name "emis_number"),
                    (Get-JeffSafePropertyValue -Object $patient -Name "patient_ref"),
                    (Get-JeffSafePropertyValue -Object $patient -Name "matched_patient_ref"),
                    (Get-JeffSafePropertyValue -Object $patient -Name "ref")
                )

                $candidateNhs = Get-JeffFirstNonBlank @(
                    (Get-JeffSafePropertyValue -Object $patient -Name "nhs_number"),
                    (Get-JeffSafePropertyValue -Object $patient -Name "nhs")
                )

                $candidateAge = Get-JeffSafePropertyValue -Object $patient -Name "age" -Default ""
                $candidateGender = Get-JeffSafePropertyValue -Object $patient -Name "gender" -Default ""

                $scoredCandidates += [pscustomobject]@{
                    ref = $candidateRef
                    name = $candidateName
                    dob = $candidateDob
                    nhs_number = $candidateNhs
                    age = $candidateAge
                    gender = $candidateGender
                    score = $score
                    same_dob = $sameDob
                    name_score = $nameScore
                }
            }
        }

        $scoredCandidates = @($scoredCandidates | Sort-Object score -Descending)

        if ($scoredCandidates.Count -gt 0) {
            $top = $scoredCandidates[0]
            $topCandidateRef = [string]$top.ref
            $topCandidateName = [string]$top.name
            $topCandidateScore = [int]$top.score
            $candidateMatches = @($scoredCandidates | Select-Object -First 5)
        }

        $exactMatches = @(
            $scoredCandidates | Where-Object {
                $_.same_dob -eq $true -and $_.name_score -ge 95
            }
        )

        if ($exactMatches.Count -eq 1) {
            $match = $exactMatches[0]
            $verificationStatus = "matched"
            $verificationReason = "Exact normalized name and DOB match found in patient lookup."
            $matchedPatientRef = [string]$match.ref
            $matchedPatientName = [string]$match.name
            $matchedNhsNumber = [string]$match.nhs_number
            $matchedAge = [string]$match.age
            $matchedGender = [string]$match.gender
        }
        elseif ($exactMatches.Count -gt 1) {
            $verificationStatus = "needs_review"
            $verificationReason = "Multiple exact name and DOB matches found. Staff review required."
        }
        elseif ($scoredCandidates.Count -gt 0 -and $scoredCandidates[0].same_dob -eq $true -and $scoredCandidates[0].score -ge 130) {
            $match = $scoredCandidates[0]
            $verificationStatus = "possible_match"
            $verificationReason = "DOB matched and patient name was similar, but not exact. Staff review required."
            $matchedPatientRef = [string]$match.ref
            $matchedPatientName = [string]$match.name
            $matchedNhsNumber = [string]$match.nhs_number
            $matchedAge = [string]$match.age
            $matchedGender = [string]$match.gender
        }
        elseif ($scoredCandidates.Count -gt 0) {
            $verificationStatus = "needs_review"
            $verificationReason = "A possible candidate was found, but identity details were not strong enough for automatic match."
        }
    }

    if ($FlagMissingFields.Count -gt 0 -and $verificationStatus -eq "matched") {
        $verificationStatus = "needs_review"
        $verificationReason = "Matched patient, but required request details are missing: $($FlagMissingFields -join ', ')."
    }

    return [pscustomobject]@{
        verification_status = $verificationStatus
        verification_reason = $verificationReason
        matched_patient_ref = $matchedPatientRef
        matched_patient_name = $matchedPatientName
        matched_nhs_number = $matchedNhsNumber
        matched_age = $matchedAge
        matched_gender = $matchedGender
        candidate_matches = @($candidateMatches)
        top_candidate_ref = $topCandidateRef
        top_candidate_name = $topCandidateName
        top_candidate_score = $topCandidateScore
    }
}
