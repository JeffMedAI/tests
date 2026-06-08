Set-StrictMode -Version Latest

. "C:\JeffLocal\app\modules\Jeff.RequestType.ps1"
. "C:\JeffLocal\app\modules\Jeff.PatientMatch.ps1"
. "C:\JeffLocal\app\modules\Jeff.Handoff.ps1"

function New-JeffHandoffObject {
    param(
        [object]$Call,
        [object]$NormalizedInput,
        [array]$NormalizedPatients,
        [object]$Flags,
        [string]$TranscriptSummary,
        [string]$NormalizedRawTranscript
    )

    function Get-SafePropertyValue {
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

    function Ensure-SafeNoteProperty {
        param(
            [object]$Object,
            [string]$Name,
            $Value = ""
        )

        if ($null -eq $Object) {
            return
        }

        if ($Object -is [System.Collections.IDictionary]) {
            if (-not $Object.Contains($Name)) {
                $Object[$Name] = $Value
            }
            return
        }

        $member = Get-Member -InputObject $Object -Name $Name -ErrorAction SilentlyContinue
        if ($null -eq $member) {
            $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
        }
    }

    function Normalize-HandoffName {
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

    function Get-LastNameSafe {
        param([string]$Name)

        $n = Normalize-HandoffName $Name
        if ([string]::IsNullOrWhiteSpace($n)) {
            return ""
        }

        $parts = @($n.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries))
        if ($parts.Count -eq 0) {
            return ""
        }

        return $parts[-1]
    }

    function Get-FirstNameSafe {
        param([string]$Name)

        $n = Normalize-HandoffName $Name
        if ([string]::IsNullOrWhiteSpace($n)) {
            return ""
        }

        $parts = @($n.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries))
        if ($parts.Count -eq 0) {
            return ""
        }

        return $parts[0]
    }

    function Get-SimilarityScore {
        param(
            [string]$A,
            [string]$B
        )

        $aNorm = Normalize-HandoffName $A
        $bNorm = Normalize-HandoffName $B

        if ([string]::IsNullOrWhiteSpace($aNorm) -or [string]::IsNullOrWhiteSpace($bNorm)) {
            return 0
        }

        if ($aNorm -eq $bNorm) {
            return 100
        }

        $aLast = Get-LastNameSafe $aNorm
        $bLast = Get-LastNameSafe $bNorm
        $aFirst = Get-FirstNameSafe $aNorm
        $bFirst = Get-FirstNameSafe $bNorm

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

    function Get-FirstNonBlank {
        param([array]$Values)

        foreach ($v in $Values) {
            $s = [string]$v
            if (-not [string]::IsNullOrWhiteSpace($s)) {
                return $s
            }
        }

        return ""
    }

    $callNormalizedInput = Get-SafePropertyValue -Object $Call -Name "normalized_input" -Default $null
    $voiceAgent = Get-SafePropertyValue -Object $Call -Name "voice_agent" -Default $null
    $pathwayResponses = Get-SafePropertyValue -Object $Call -Name "pathway_responses" -Default $null
    $identityResponses = Get-SafePropertyValue -Object $pathwayResponses -Name "identity" -Default $null
    $qualityFields = Get-SafePropertyValue -Object $Call -Name "quality" -Default $null

    $patientName = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $NormalizedInput -Name "patient_name"),
        (Get-SafePropertyValue -Object $Call -Name "patient_name"),
        (Get-SafePropertyValue -Object $Call -Name "patient_name_raw"),
        (Get-SafePropertyValue -Object $callNormalizedInput -Name "patient_name"),
        (Get-SafePropertyValue -Object $identityResponses -Name "patient_name")
    )

    $dob = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $NormalizedInput -Name "dob"),
        (Get-SafePropertyValue -Object $Call -Name "dob"),
        (Get-SafePropertyValue -Object $Call -Name "dob_raw"),
        (Get-SafePropertyValue -Object $callNormalizedInput -Name "dob"),
        (Get-SafePropertyValue -Object $identityResponses -Name "dob")
    )

    $postcode = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $NormalizedInput -Name "postcode"),
        (Get-SafePropertyValue -Object $Call -Name "postcode"),
        (Get-SafePropertyValue -Object $Call -Name "postcode_raw"),
        (Get-SafePropertyValue -Object $callNormalizedInput -Name "postcode"),
        (Get-SafePropertyValue -Object $identityResponses -Name "postcode")
    )

    $callbackNumber = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $NormalizedInput -Name "callback_number"),
        (Get-SafePropertyValue -Object $NormalizedInput -Name "callback_number_raw"),
        (Get-SafePropertyValue -Object $Call -Name "callback_number"),
        (Get-SafePropertyValue -Object $Call -Name "callback_number_raw"),
        (Get-SafePropertyValue -Object $callNormalizedInput -Name "callback_number"),
        (Get-SafePropertyValue -Object $identityResponses -Name "callback_number"),
        (Get-SafePropertyValue -Object $identityResponses -Name "callback_number_from_caller_id")
    )

    $callerFor = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $NormalizedInput -Name "caller_for"),
        (Get-SafePropertyValue -Object $Call -Name "caller_for"),
        (Get-SafePropertyValue -Object $callNormalizedInput -Name "caller_for"),
        "self"
    )

    $urgencyNote = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $NormalizedInput -Name "urgency_note"),
        (Get-SafePropertyValue -Object $Call -Name "urgency_note"),
        (Get-SafePropertyValue -Object $Call -Name "urgency_note_raw"),
        (Get-SafePropertyValue -Object $callNormalizedInput -Name "urgency_note")
    )

    $pharmacy = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $NormalizedInput -Name "pharmacy"),
        (Get-SafePropertyValue -Object $Call -Name "pharmacy"),
        (Get-SafePropertyValue -Object $Call -Name "pharmacy_raw"),
        (Get-SafePropertyValue -Object $callNormalizedInput -Name "pharmacy")
    )

    $suppliedNhsNumber = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $NormalizedInput -Name "supplied_nhs_number"),
        (Get-SafePropertyValue -Object $Call -Name "supplied_nhs_number"),
        (Get-SafePropertyValue -Object $callNormalizedInput -Name "supplied_nhs_number")
    )

    $medicationsRequested = @()

    foreach ($candidate in @(
        (Get-SafePropertyValue -Object $NormalizedInput -Name "medications_requested" -Default @()),
        (Get-SafePropertyValue -Object $Call -Name "medications_requested" -Default @()),
        (Get-SafePropertyValue -Object $callNormalizedInput -Name "medications_requested" -Default @())
    )) {
        if ($candidate -is [array]) {
            foreach ($m in $candidate) {
                if (-not [string]::IsNullOrWhiteSpace([string]$m)) {
                    $medicationsRequested += [string]$m
                }
            }
        }
        elseif (-not [string]::IsNullOrWhiteSpace([string]$candidate)) {
            $medicationsRequested += [string]$candidate
        }
    }

    $medicationsRequested = @($medicationsRequested | Select-Object -Unique)

    Ensure-SafeNoteProperty -Object $NormalizedInput -Name "patient_name" -Value $patientName
    Ensure-SafeNoteProperty -Object $NormalizedInput -Name "dob" -Value $dob
    Ensure-SafeNoteProperty -Object $NormalizedInput -Name "postcode" -Value $postcode
    Ensure-SafeNoteProperty -Object $NormalizedInput -Name "callback_number" -Value $callbackNumber
    Ensure-SafeNoteProperty -Object $NormalizedInput -Name "callback_number_raw" -Value $callbackNumber
    Ensure-SafeNoteProperty -Object $NormalizedInput -Name "medications_requested" -Value $medicationsRequested
    Ensure-SafeNoteProperty -Object $NormalizedInput -Name "urgency_note" -Value $urgencyNote
    Ensure-SafeNoteProperty -Object $NormalizedInput -Name "pharmacy" -Value $pharmacy
    Ensure-SafeNoteProperty -Object $NormalizedInput -Name "caller_for" -Value $callerFor
    Ensure-SafeNoteProperty -Object $NormalizedInput -Name "supplied_nhs_number" -Value $suppliedNhsNumber

    $callId = Get-SafePropertyValue -Object $Call -Name "call_id" -Default ""
    $callTimestamp = Get-SafePropertyValue -Object $Call -Name "call_timestamp" -Default ""
    $workflow = Get-SafePropertyValue -Object $Call -Name "workflow" -Default "unknown"
    $requestTypeRaw = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $Call -Name "request_type"),
        (Get-SafePropertyValue -Object $callNormalizedInput -Name "request_type"),
        (Get-SafePropertyValue -Object $pathwayResponses -Name "selected_pathway"),
        "admin"
    )
    $requestType = Normalize-JeffRequestType $requestTypeRaw
    $requestSubtype = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $Call -Name "request_subtype"),
        (Get-SafePropertyValue -Object $callNormalizedInput -Name "request_subtype"),
        $requestTypeRaw,
        $requestType
    )
    $source = Get-SafePropertyValue -Object $Call -Name "source" -Default "voice_agent"

    $callDurationSeconds = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $Call -Name "call_duration_seconds"),
        (Get-SafePropertyValue -Object $voiceAgent -Name "call_duration_seconds"),
        (Get-SafePropertyValue -Object $qualityFields -Name "call_duration_seconds")
    )

    $callerSentiment = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $Call -Name "caller_sentiment"),
        (Get-SafePropertyValue -Object $voiceAgent -Name "caller_sentiment"),
        (Get-SafePropertyValue -Object $qualityFields -Name "caller_sentiment")
    )

    $callerDifficulty = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $Call -Name "caller_difficulty"),
        (Get-SafePropertyValue -Object $voiceAgent -Name "caller_difficulty"),
        (Get-SafePropertyValue -Object $qualityFields -Name "caller_difficulty")
    )

    $transcriptQuality = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $Call -Name "transcript_quality"),
        (Get-SafePropertyValue -Object $voiceAgent -Name "transcript_quality"),
        (Get-SafePropertyValue -Object $qualityFields -Name "transcript_quality"),
        (Get-SafePropertyValue -Object $Flags -Name "transcript_quality_flag")
    )

    $handoffConfidence = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $Call -Name "handoff_confidence"),
        (Get-SafePropertyValue -Object $qualityFields -Name "handoff_confidence"),
        "0.80"
    )

    $extractionConfidenceValue = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $Call -Name "extraction_confidence" -Default $null),
        (Get-SafePropertyValue -Object $qualityFields -Name "extraction_confidence" -Default $null)
    )
    $extractionConfidenceOverall = ""

    if ($null -ne $extractionConfidenceValue) {
        if ($extractionConfidenceValue -is [double] -or $extractionConfidenceValue -is [decimal] -or $extractionConfidenceValue -is [int]) {
            $extractionConfidenceOverall = [string]$extractionConfidenceValue
        }
        else {
            $extractionConfidenceOverall = Get-SafePropertyValue -Object $extractionConfidenceValue -Name "overall" -Default ""
        }
    }

    if ([string]::IsNullOrWhiteSpace($extractionConfidenceOverall)) {
        $extractionConfidenceOverall = "0.80"
    }

    $staffReviewRequiredFromCall = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $Call -Name "staff_review_required" -Default $null),
        (Get-SafePropertyValue -Object $qualityFields -Name "staff_review_required" -Default $null),
        $false
    )
    $redFlagsPresentFromCall = Get-FirstNonBlank @(
        (Get-SafePropertyValue -Object $Call -Name "red_flags_present" -Default $null),
        (Get-SafePropertyValue -Object $qualityFields -Name "red_flags_present" -Default $null),
        $false
    )

    $flagMissingFields = @(Get-SafePropertyValue -Object $Flags -Name "missing_fields" -Default @())
    $flagPriority = Get-SafePropertyValue -Object $Flags -Name "priority" -Default "routine"
    $flagTranscriptQuality = Get-SafePropertyValue -Object $Flags -Name "transcript_quality_flag" -Default ""

    $patientMatchArgs = @{
        PatientName = $patientName
        Dob = $dob
        NormalizedPatients = $NormalizedPatients
        FlagMissingFields = $flagMissingFields
    }
    $patientMatch = Get-JeffPatientMatch @patientMatchArgs

    $verificationStatus = $patientMatch.verification_status
    $verificationReason = $patientMatch.verification_reason
    $matchedPatientRef = $patientMatch.matched_patient_ref
    $matchedPatientName = $patientMatch.matched_patient_name
    $matchedNhsNumber = $patientMatch.matched_nhs_number
    $matchedAge = $patientMatch.matched_age
    $matchedGender = $patientMatch.matched_gender
    $candidateMatches = @($patientMatch.candidate_matches)
    $topCandidateRef = $patientMatch.top_candidate_ref
    $topCandidateName = $patientMatch.top_candidate_name
    $topCandidateScore = $patientMatch.top_candidate_score

    $medText = if ($medicationsRequested.Count -gt 0) {
        $medicationsRequested -join ", "
    }
    else {
        "medication not clearly captured"
    }

    $callbackText = if (-not [string]::IsNullOrWhiteSpace($callbackNumber)) {
        $callbackNumber
    }
    else {
        "not confirmed"
    }

    $safeToQueueFromCall = Get-SafePropertyValue -Object $Call -Name "safe_to_queue" -Default $null

    $dispositionArgs = @{
        RequestType = $requestType
        RequestSubtype = $requestSubtype
        FlagPriority = $flagPriority
        VerificationStatus = $verificationStatus
        CallbackNumber = $callbackNumber
        StaffReviewRequiredFromCall = $staffReviewRequiredFromCall
        RedFlagsPresentFromCall = $redFlagsPresentFromCall
        SafeToQueueOverride = $safeToQueueFromCall
    }
    $disposition = Get-JeffHandoffDisposition @dispositionArgs
    $priority = $disposition.priority
    $staffReviewRequired = $disposition.staff_review_required
    $redFlagsPresent = $disposition.red_flags_present
    $safeToQueue = $disposition.safe_to_queue
    $actionNeeded = $disposition.action_needed

    $taskTextArgs = @{
        RequestType = $requestType
        RequestSubtype = $requestSubtype
        MedText = $medText
        Pharmacy = $pharmacy
        CallbackText = $callbackText
        UrgencyNote = $urgencyNote
        CallerFor = $callerFor
        PathwayResponses = $pathwayResponses
        RawTranscript = $NormalizedRawTranscript
        TranscriptSummary = $TranscriptSummary
        VerificationStatus = $verificationStatus
        VerificationReason = $verificationReason
        Priority = $priority
        SafeToQueue = $safeToQueue
        StaffReviewRequired = $staffReviewRequired
        RedFlagsPresent = $redFlagsPresent
        NormalizedInput = $NormalizedInput
        MedicationsRequested = @($medicationsRequested)
    }
    $taskText = Get-JeffHandoffTaskText @taskTextArgs
    # Final staff-facing wording is generated after deterministic matching so verified lookup identifiers override transcript/LLM guesses.
    $finalStaffText = Get-JeffVerifiedStaffFacingText `
        -RequestType $requestType `
        -PathwayResponses $pathwayResponses `
        -DraftTranscriptSummary $TranscriptSummary `
        -DraftTaskTitle $taskText.task_title `
        -DraftTaskBody $taskText.task_body `
        -VerificationStatus $verificationStatus `
        -VerificationReason $verificationReason `
        -MatchedPatientRef $matchedPatientRef `
        -MatchedNhsNumber $matchedNhsNumber `
        -MatchedPatientName $matchedPatientName `
        -TopCandidateRef $topCandidateRef `
        -TopCandidateName $topCandidateName `
        -CandidateMatches @($candidateMatches) `
        -NormalizedInput $NormalizedInput `
        -SafeToQueue $safeToQueue `
        -StaffReviewRequired $staffReviewRequired `
        -CallbackNumber $callbackNumber `
        -CallerFor $callerFor `
        -MedicationsRequested @($medicationsRequested)
    $taskTitle = $finalStaffText.task_title
    $taskBody = $finalStaffText.task_body
    $finalTranscriptSummary = $finalStaffText.transcript_summary
    $displayPatientName = if ($verificationStatus -eq "matched" -and -not [string]::IsNullOrWhiteSpace($matchedPatientName)) {
        $matchedPatientName
    }
    else {
        $patientName
    }

    $callSummary = if (-not [string]::IsNullOrWhiteSpace($finalTranscriptSummary)) {
        $finalTranscriptSummary
    }
    else {
        "$requestType received for $displayPatientName. Verification status: $verificationStatus."
    }

    $handoff = [ordered]@{
        call_id = $callId
        call_timestamp = $callTimestamp
        workflow = $workflow
        request_type = $requestType
        request_subtype = $requestSubtype
        source = $source

        normalized_input = [ordered]@{
            patient_name = $displayPatientName
            dob = $dob
            postcode = $postcode
            callback_number = $callbackNumber
            medications_requested = @($medicationsRequested)
            urgency_note = $urgencyNote
            pharmacy = $pharmacy
            caller_for = $callerFor
            supplied_nhs_number = $suppliedNhsNumber
            request_type = $requestType
            request_subtype = $requestSubtype
        }

        pathway_responses = $pathwayResponses
        voice_agent = $voiceAgent
        quality = $qualityFields

        raw_transcript = $NormalizedRawTranscript
        transcript_summary = $finalTranscriptSummary
        transcript_quality_flag = $flagTranscriptQuality

        missing_fields = @($flagMissingFields)

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

        task_title = $taskTitle
        task_body = $taskBody
        priority = $priority
        safe_to_queue = $safeToQueue
        action_needed = $actionNeeded
        call_summary = $callSummary

        call_duration_seconds = $callDurationSeconds
        caller_sentiment = $callerSentiment
        caller_difficulty = $callerDifficulty
        transcript_quality = $transcriptQuality
        handoff_confidence = $handoffConfidence
        extraction_confidence = $extractionConfidenceOverall
        staff_review_required = $staffReviewRequired
        red_flags_present = $redFlagsPresent

        assigned_to = ""
        outcome_notes = ""
        staff_action = ""
        resolved_at = ""
        resolved_by = ""
        last_edited_at = ""
        last_edited_by = ""
        turnaround_minutes = ""
    }

    return [pscustomobject]$handoff
}

