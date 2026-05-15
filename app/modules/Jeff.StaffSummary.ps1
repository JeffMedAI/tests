Set-StrictMode -Version Latest

function Get-JeffStaffValue {
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

function Get-JeffStaffFirstText {
    param([object[]]$Values)

    foreach ($value in $Values) {
        if ($null -eq $value) {
            continue
        }

        if ($value -is [System.Array]) {
            $parts = @(
                $value |
                    ForEach-Object { [string]$_ } |
                    Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
            )

            if ($parts.Count -gt 0) {
                return ($parts -join ", ")
            }

            continue
        }

        $text = ([string]$value).Trim()
        if (-not [string]::IsNullOrWhiteSpace($text)) {
            return $text
        }
    }

    return ""
}

function Convert-JeffStaffBool {
    param($Value)

    return ($Value -eq $true -or "$Value".ToLowerInvariant() -eq "true")
}

function Get-JeffTranscriptSpeakerSegments {
    param(
        [string]$Transcript
    )

    $text = [string]$Transcript
    if ([string]::IsNullOrWhiteSpace($text)) {
        return @()
    }

    $pattern = '(?is)(?<speaker>\b(?:caller|patient|user|self|agent|jeff|assistant|receptionist)\b)\s*:\s*'
    $matches = [regex]::Matches($text, $pattern)

    if ($matches.Count -eq 0) {
        return @([pscustomobject]@{
            speaker = ""
            text = $text.Trim()
        })
    }

    $segments = @()
    for ($i = 0; $i -lt $matches.Count; $i++) {
        $match = $matches[$i]
        $speaker = [string]$match.Groups["speaker"].Value
        $start = $match.Index + $match.Length
        $end = if ($i + 1 -lt $matches.Count) { $matches[$i + 1].Index } else { $text.Length }
        $segmentText = $text.Substring($start, [Math]::Max(0, $end - $start)).Trim()
        if (-not [string]::IsNullOrWhiteSpace($segmentText)) {
            $segments += [pscustomobject]@{
                speaker = $speaker
                text = $segmentText
            }
        }
    }

    return @($segments)
}

function Test-JeffCallerSymptomAffirmed {
    param(
        [string]$LineText
    )

    $text = ([string]$LineText).ToLowerInvariant()
    if ([string]::IsNullOrWhiteSpace($text)) {
        return @()
    }

    $symptomChecks = @(
        @{
            Regex = '\bchest\s*(pain|tightness)\b|\btight\s*chest\b'
            Text = 'chest pain'
            Denials = @(
                '\b(no|not|denies?|denied|without)\b.{0,20}\b(chest\s*(pain|tightness)|tight\s*chest)\b'
            )
        },
        @{
            Regex = '\bsevere difficulty breathing\b|\bstruggling to breathe\b|\bcannot breathe\b|\bgasping\b|\bshortness of breath\b|\bbreathless(ness)?\b'
            Text = 'breathlessness'
            Denials = @(
                '\b(no|not|denies?|denied|without)\b.{0,20}\b(breathless(ness)?|shortness of breath|struggling to breathe|cannot breathe|severe difficulty breathing|gasping)\b'
            )
        },
        @{
            Regex = '\bsweat(y|ing)?\b'
            Text = 'sweating'
            Denials = @(
                '\b(no|not|denies?|denied|without)\b.{0,20}\b(sweat(y|ing)?)\b'
            )
        },
        @{
            Regex = '\bfaint(ing)?\b|\bcollapse(d)?\b|\bcollapsing\b|\bunresponsive\b|\bhard to wake\b'
            Text = 'fainting'
            Denials = @(
                '\b(no|not|denies?|denied|without)\b.{0,20}\b(faint(ing)?|collapse(d)?|collapsing|unresponsive|hard to wake)\b'
            )
        },
        @{
            Regex = '\bsuicide\b|\bsuicidal\b|\bself harm\b|\bharm myself\b|\bharm themselves\b|\bunable to cope\b'
            Text = 'self harm'
            Denials = @(
                '\b(no|not|denies?|denied|without)\b.{0,20}\b(suicide|suicidal|self harm|harm myself|harm themselves|unable to cope)\b'
            )
        },
        @{
            Regex = '\bstroke\b|\bface droop\b|\bslurred speech\b|\bweakness on one side\b|\bsudden weakness\b|\bsudden numbness\b'
            Text = 'stroke symptoms'
            Denials = @(
                '\b(no|not|denies?|denied|without)\b.{0,20}\b(stroke|face droop|slurred speech|weakness on one side|sudden weakness|sudden numbness)\b'
            )
        },
        @{
            Regex = '\banaphylaxis\b|\bswelling of lips\b|\bswelling of tongue\b|\bswelling of throat\b'
            Text = 'allergic reaction'
            Denials = @(
                '\b(no|not|denies?|denied|without)\b.{0,20}\b(anaphylaxis|swelling of lips|swelling of tongue|swelling of throat)\b'
            )
        }
    )

    foreach ($pattern in $symptomChecks) {
        if ($text -notmatch $pattern.Regex) {
            continue
        }

        $denied = $text -match '\bnothing like that\b'
        foreach ($deny in @($pattern.Denials)) {
            if ($text -match $deny) {
                $denied = $true
                break
            }
        }

        if (-not $denied) {
            return @([string]$pattern.Text)
        }
    }

    return @()
}

function Get-JeffEmergencyEvidence {
    param(
        [object]$PathwayResponses,
        [string]$RawTranscript,
        [string]$TranscriptSummary
    )

    $urgency = Get-JeffStaffValue -Object $PathwayResponses -Name "urgency_assessment" -Default $null
    $structuredRedFlags = @(
        @(Get-JeffStaffValue -Object $urgency -Name "red_flags_mentioned" -Default @()) |
            ForEach-Object { ([string]$_).Trim() } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )
    $structuredUrgencyLevel = ([string](Get-JeffStaffValue -Object $urgency -Name "urgency_level" -Default "")).Trim()
    $structuredAdviceGiven = Convert-JeffStaffBool (Get-JeffStaffValue -Object $urgency -Name "emergency_advice_given" -Default $false)
    $appointmentRedirected = Convert-JeffStaffBool (Get-JeffStaffValue -Object $PathwayResponses -Name "appointment_redirected" -Default $false)

    if (@($structuredRedFlags).Count -gt 0) {
        return [pscustomobject]@{
            has_red_flag = $true
            symptoms = @($structuredRedFlags | Select-Object -First 4)
            source = "structured_red_flags_mentioned"
            emergency_advice_given = $structuredAdviceGiven
            urgency_level = $structuredUrgencyLevel
        }
    }

    if ($structuredAdviceGiven -or $structuredUrgencyLevel -eq "999 Emergency" -or $structuredUrgencyLevel -match "(?i)\b(emergency|urgent)\b") {
        $symptoms = @()
        if ($structuredUrgencyLevel -eq "999 Emergency") {
            $symptoms += "urgent symptoms"
        }
        elseif (-not [string]::IsNullOrWhiteSpace($TranscriptSummary)) {
            $symptoms += [string]$TranscriptSummary
        }

        if ($appointmentRedirected -and $structuredUrgencyLevel -match "(?i)\b(emergency|urgent)\b") {
            $symptoms += "urgent appointment redirect"
        }

        $symptoms = @($symptoms | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 4)
        if (@($symptoms).Count -eq 0) {
            $symptoms = @("urgent symptoms")
        }

        return [pscustomobject]@{
            has_red_flag = $true
            symptoms = $symptoms
            source = "structured_urgency_assessment"
            emergency_advice_given = $structuredAdviceGiven
            urgency_level = $structuredUrgencyLevel
        }
    }

    $segments = @(Get-JeffTranscriptSpeakerSegments -Transcript $RawTranscript)
    $callerLines = @(
        $segments |
            Where-Object {
                [string]::IsNullOrWhiteSpace([string]$_.speaker) -or $_.speaker -match '^(caller|patient|user|self)$'
            }
    )

    $evidence = @()
    foreach ($line in $callerLines) {
        $affirmed = @(Test-JeffCallerSymptomAffirmed -LineText $line.text)
        if ($affirmed.Count -gt 0) {
            $evidence += $affirmed
        }
    }

    $evidence = @($evidence | Select-Object -Unique | Select-Object -First 4)

    if (@($evidence).Count -gt 0) {
        return [pscustomobject]@{
            has_red_flag = $true
            symptoms = $evidence
            source = "caller_transcript"
            emergency_advice_given = $false
            urgency_level = ""
        }
    }

    if ([string]::IsNullOrWhiteSpace($RawTranscript) -and -not [string]::IsNullOrWhiteSpace($TranscriptSummary)) {
        $summaryText = $TranscriptSummary.ToLowerInvariant()
        if ($summaryText -match '\b(chest\s*(pain|tightness)|breathless(ness)?|shortness of breath|sweat(y|ing)?|faint(ing)?)\b') {
            return [pscustomobject]@{
                has_red_flag = $true
                symptoms = @("urgent symptoms")
                source = "summary_fallback"
                emergency_advice_given = $false
                urgency_level = ""
            }
        }
    }

    return [pscustomobject]@{
        has_red_flag = $false
        symptoms = @()
        source = "none"
        emergency_advice_given = $structuredAdviceGiven
        urgency_level = $structuredUrgencyLevel
    }
}

function Get-JeffStaffRedFlagText {
    param(
        [object]$PathwayResponses,
        [string]$RawTranscript,
        [string]$TranscriptSummary
    )

    $evidence = Get-JeffEmergencyEvidence -PathwayResponses $PathwayResponses -RawTranscript $RawTranscript -TranscriptSummary $TranscriptSummary
    $mentioned = @($evidence.symptoms)
    $parts = @(
        $mentioned |
            ForEach-Object { ([string]$_).Trim() } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )

    if ($parts.Count -gt 0) {
        return ($parts | Select-Object -First 4) -join ", "
    }

    $text = "$RawTranscript $TranscriptSummary".ToLowerInvariant()
    $detected = @()

    foreach ($pattern in @(
        @{ Regex = "\bchest\s*tightness\b"; Text = "chest tightness" },
        @{ Regex = "\bchest\s*pain\b"; Text = "chest pain" },
        @{ Regex = "\bsweat(y|ing)?\b"; Text = "sweating" },
        @{ Regex = "\bbreathless(ness)?\b"; Text = "breathlessness" },
        @{ Regex = "\bshortness of breath\b"; Text = "shortness of breath" },
        @{ Regex = "\bstruggling to breathe\b"; Text = "struggling to breathe" }
    )) {
        if ($text -match $pattern.Regex) {
            $detected += $pattern.Text
        }
    }

    $detected = @($detected | Select-Object -Unique)
    if ($detected.Count -gt 0) {
        return (($detected | Select-Object -First 4) -join ", ")
    }

    return "red-flag symptoms"
}

function Test-JeffEmergencyAdviceGiven {
    param(
        [object]$PathwayResponses,
        [string]$RawTranscript
    )

    $urgency = Get-JeffStaffValue -Object $PathwayResponses -Name "urgency_assessment" -Default $null
    $adviceGiven = Get-JeffStaffValue -Object $urgency -Name "emergency_advice_given" -Default $false

    if (Convert-JeffStaffBool $adviceGiven) {
        return $true
    }

    $segments = @(Get-JeffTranscriptSpeakerSegments -Transcript $RawTranscript)
    foreach ($line in $segments) {
        $speaker = ([string]$line.speaker).ToLowerInvariant()
        $text = ([string]$line.text).ToLowerInvariant()
        if ($speaker -notmatch '^(agent|jeff|assistant|receptionist)$') {
            continue
        }

        if ($text -match '(dial|call|ring)\s*(nine[- ]?nine[- ]?nine|999)|a\s*and\s*e|urgent care now|seek urgent care') {
            return $true
        }
    }

    return $false
}

function Join-JeffStaffSentences {
    param([string[]]$Sentences)

    $clean = @(
        $Sentences |
            ForEach-Object { ([string]$_).Trim() } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )

    return ($clean -join " ")
}

function Limit-JeffStaffWords {
    param(
        [string]$Text,
        [int]$MaxWords
    )

    $clean = ([string]$Text).Trim() -replace "\s+", " "
    if ([string]::IsNullOrWhiteSpace($clean) -or $MaxWords -le 0) {
        return ""
    }

    $words = @($clean.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries))
    if ($words.Count -le $MaxWords) {
        return $clean
    }

    return (($words | Select-Object -First $MaxWords) -join " ").TrimEnd(" ,;:") + "."
}

function Get-JeffRequestLabel {
    param([string]$RequestType)

    switch ($RequestType) {
        "prescription" { return "Prescription" }
        "sick_note" { return "Sick note" }
        "referral" { return "Referral" }
        "test_result" { return "Test result" }
        "appointment_redirect" { return "Appointment" }
        "admin" { return "Admin" }
        default { return "Request" }
    }
}

function Get-JeffRequestDetail {
    param(
        [string]$RequestType,
        [object]$PathwayResponses,
        [array]$MedicationsRequested = @()
    )

    $prescription = Get-JeffStaffValue -Object $PathwayResponses -Name "prescription" -Default $null
    $sickNote = Get-JeffStaffValue -Object $PathwayResponses -Name "sick_note" -Default $null
    $referral = Get-JeffStaffValue -Object $PathwayResponses -Name "referral" -Default $null
    $testResult = Get-JeffStaffValue -Object $PathwayResponses -Name "test_result" -Default $null
    $appointment = Get-JeffStaffValue -Object $PathwayResponses -Name "appointment_redirect" -Default $null
    $admin = Get-JeffStaffValue -Object $PathwayResponses -Name "admin" -Default $null

    switch ($RequestType) {
        "prescription" {
            return Get-JeffStaffFirstText @(
                $MedicationsRequested,
                (Get-JeffStaffValue -Object $prescription -Name "medications_requested" -Default @()),
                "medication unclear"
            )
        }
        "sick_note" {
            return Get-JeffStaffFirstText @(
                (Get-JeffStaffValue -Object $sickNote -Name "purpose"),
                (Get-JeffStaffValue -Object $sickNote -Name "reason"),
                "fit note"
            )
        }
        "referral" {
            return Get-JeffStaffFirstText @(
                (Get-JeffStaffValue -Object $referral -Name "hospital_name"),
                (Get-JeffStaffValue -Object $referral -Name "specialty"),
                (Get-JeffStaffValue -Object $referral -Name "referral_type"),
                "referral details unclear"
            )
        }
        "test_result" {
            return Get-JeffStaffFirstText @(
                (Get-JeffStaffValue -Object $testResult -Name "test_type"),
                "test details unclear"
            )
        }
        "appointment_redirect" {
            return Get-JeffStaffFirstText @(
                (Get-JeffStaffValue -Object $appointment -Name "appointment_reason"),
                "appointment reason unclear"
            )
        }
        default {
            return Get-JeffStaffFirstText @(
                (Get-JeffStaffValue -Object $admin -Name "admin_reason"),
                "admin details unclear"
            )
        }
    }
}

function Get-JeffIdentifierText {
    param(
        [string]$Emis,
        [string]$Nhs
    )

    $parts = @()
    if (-not [string]::IsNullOrWhiteSpace($Emis)) {
        $parts += "EMIS $Emis"
    }
    if (-not [string]::IsNullOrWhiteSpace($Nhs)) {
        $parts += "NHS $Nhs"
    }
    if ($parts.Count -eq 0) {
        return ""
    }
    return ($parts -join " / ")
}

function Get-JeffCallbackSentence {
    param([string]$CallbackNumber)

    $callback = ([string]$CallbackNumber).Trim()
    if ([string]::IsNullOrWhiteSpace($callback)) {
        return "Callback missing."
    }
    if ($callback -match "(?i)not confirmed|unconfirmed|refused|unknown|uncertain") {
        return "Callback not confirmed."
    }
    return "Callback provided."
}

function Test-JeffCallerForPatient {
    param([string]$CallerFor)

    $value = ([string]$CallerFor).Trim().ToLowerInvariant()
    return (-not [string]::IsNullOrWhiteSpace($value) -and $value -notin @("self", "patient", "myself", "caller", ""))
}

function Get-JeffCandidateNhsNumber {
    param(
        [array]$CandidateMatches,
        [string]$TopCandidateRef
    )

    foreach ($candidate in @($CandidateMatches)) {
        $candidateRef = Get-JeffStaffFirstText @(
            (Get-JeffStaffValue -Object $candidate -Name "ref"),
            (Get-JeffStaffValue -Object $candidate -Name "patient_ref")
        )
        if ($candidateRef -eq $TopCandidateRef) {
            return Get-JeffStaffFirstText @(
                (Get-JeffStaffValue -Object $candidate -Name "nhs_number"),
                (Get-JeffStaffValue -Object $candidate -Name "nhs")
            )
        }
    }

    return ""
}

function Get-JeffVerifiedStaffFacingText {
    param(
        [string]$RequestType,
        [object]$PathwayResponses,
        [string]$DraftTranscriptSummary = "",
        [string]$DraftTaskTitle = "",
        [string]$DraftTaskBody = "",
        [string]$VerificationStatus = "",
        [string]$VerificationReason = "",
        [string]$MatchedPatientRef = "",
        [string]$MatchedNhsNumber = "",
        [string]$MatchedPatientName = "",
        [string]$TopCandidateRef = "",
        [string]$TopCandidateName = "",
        [array]$CandidateMatches = @(),
        [object]$NormalizedInput = $null,
        $SafeToQueue = $true,
        $StaffReviewRequired = $false,
        [string]$CallbackNumber = "",
        [string]$CallerFor = "",
        [array]$MedicationsRequested = @()
    )

    # Ollama may draft text, but verified identifiers and safety/review wording are finalized here after deterministic matching.
    $requestLabel = Get-JeffRequestLabel -RequestType $RequestType
    $detail = Get-JeffRequestDetail -RequestType $RequestType -PathwayResponses $PathwayResponses -MedicationsRequested $MedicationsRequested
    $callbackSentence = Get-JeffCallbackSentence -CallbackNumber $CallbackNumber
    $callbackPhrase = $callbackSentence.TrimEnd(".").ToLowerInvariant()
    $callerForPatient = Test-JeffCallerForPatient -CallerFor $CallerFor
    $safe = Convert-JeffStaffBool $SafeToQueue
    $review = Convert-JeffStaffBool $StaffReviewRequired
    $status = ([string]$VerificationStatus).Trim()
    $patientName = Get-JeffStaffValue -Object $NormalizedInput -Name "patient_name" -Default ""
    $dob = Get-JeffStaffValue -Object $NormalizedInput -Name "dob" -Default ""

    $summary = ""
    $title = ""
    $bodySentences = @()

    if ($status -eq "matched") {
        $identifier = Get-JeffIdentifierText -Emis $MatchedPatientRef -Nhs $MatchedNhsNumber
        if ([string]::IsNullOrWhiteSpace($identifier)) {
            $identifier = Get-JeffStaffFirstText @($MatchedPatientName, "verified patient")
        }
        $summary = "$requestLabel requested for $identifier; $detail, $callbackPhrase."
        $titleId = Get-JeffStaffFirstText @(
            ($(if (-not [string]::IsNullOrWhiteSpace($MatchedPatientRef)) { "EMIS $MatchedPatientRef" } else { "" })),
            ($(if (-not [string]::IsNullOrWhiteSpace($MatchedNhsNumber)) { "NHS $MatchedNhsNumber" } else { "" })),
            "Matched patient"
        )
        $title = "$requestLabel - $titleId - Matched"
        $bodySentences += "$requestLabel requested for $detail."
        $bodySentences += "Verified patient: $identifier."
        if (-not [string]::IsNullOrWhiteSpace($MatchedPatientName)) {
            $bodySentences += "Display name: $MatchedPatientName."
        }
    }
    elseif ($status -in @("possible_match", "possible_match_weak", "needs_review")) {
        $candidateNhs = Get-JeffCandidateNhsNumber -CandidateMatches $CandidateMatches -TopCandidateRef $TopCandidateRef
        $candidateIdentifier = Get-JeffIdentifierText -Emis $TopCandidateRef -Nhs $candidateNhs
        if ([string]::IsNullOrWhiteSpace($candidateIdentifier)) {
            $candidateIdentifier = "record not confirmed"
        }
        $stated = Get-JeffStaffFirstText @($patientName, "Unknown patient")
        $summary = "$requestLabel for possible match $candidateIdentifier; $detail, staff identity review required."
        $titleId = if (-not [string]::IsNullOrWhiteSpace($TopCandidateRef)) { "Possible EMIS $TopCandidateRef" } else { "Possible Match" }
        $title = "$requestLabel - $titleId - Review"
        $bodySentences += "$requestLabel requested for $detail."
        $bodySentences += "Caller stated name sounds like $stated."
        $bodySentences += "Possible match: $candidateIdentifier."
        $bodySentences += "Staff identity review before processing."
    }
    else {
        $missing = @()
        if ([string]::IsNullOrWhiteSpace($patientName)) { $missing += "name missing" }
        if ([string]::IsNullOrWhiteSpace($dob)) { $missing += "DOB missing" }
        if ($callbackSentence -ne "Callback provided.") { $missing += $callbackSentence.TrimEnd(".").ToLowerInvariant() }
        if ($missing.Count -eq 0 -and -not [string]::IsNullOrWhiteSpace($VerificationReason)) { $missing += $VerificationReason }
        if ($missing.Count -eq 0) { $missing += $status }
        $missingText = ($missing | Select-Object -First 3) -join ", "
        $summary = "$requestLabel for Unknown patient; $detail, $missingText."
        $titleStatus = if ($status -eq "insufficient_data") { "Missing DOB" } elseif ($status -eq "no_match") { "No Match" } else { "Review" }
        $title = "$requestLabel - Unknown Patient - $titleStatus"
        $bodySentences += "$requestLabel requested for $detail."
        if (-not [string]::IsNullOrWhiteSpace($patientName)) {
            $bodySentences += "Caller-stated patient: $patientName."
        }
        $bodySentences += "No verified EMIS/NHS match."
        $bodySentences += ($missingText.Substring(0, 1).ToUpperInvariant() + $missingText.Substring(1) + ".")
    }

    $bodySentences += $callbackSentence
    if ($callerForPatient) {
        $bodySentences += "Caller acting for patient."
    }
    if ($review -or -not $safe -or $status -ne "matched") {
        $bodySentences += "Staff review required."
    }

    return [pscustomobject]@{
        transcript_summary = Limit-JeffStaffWords -Text $summary -MaxWords 22
        task_title = Limit-JeffStaffWords -Text $title -MaxWords 12
        task_body = Limit-JeffStaffWords -Text (Join-JeffStaffSentences $bodySentences) -MaxWords 45
    }
}

function Get-JeffStaffTaskText {
    param(
        [string]$RequestType,
        [string]$RequestSubtype,
        [object]$PathwayResponses,
        [string]$RawTranscript,
        [string]$TranscriptSummary,
        [string]$VerificationStatus,
        [string]$VerificationReason,
        [string]$Priority,
        $SafeToQueue,
        $StaffReviewRequired,
        $RedFlagsPresent,
        [object]$NormalizedInput,
        [array]$MedicationsRequested = @(),
        [string]$Pharmacy = "",
        [string]$CallbackNumber = ""
    )

    $redFlag = Convert-JeffStaffBool $RedFlagsPresent
    $safe = Convert-JeffStaffBool $SafeToQueue
    $staffReview = Convert-JeffStaffBool $StaffReviewRequired

    $prescription = Get-JeffStaffValue -Object $PathwayResponses -Name "prescription" -Default $null
    $sickNote = Get-JeffStaffValue -Object $PathwayResponses -Name "sick_note" -Default $null
    $referral = Get-JeffStaffValue -Object $PathwayResponses -Name "referral" -Default $null
    $testResult = Get-JeffStaffValue -Object $PathwayResponses -Name "test_result" -Default $null
    $admin = Get-JeffStaffValue -Object $PathwayResponses -Name "admin" -Default $null
    $urgency = Get-JeffStaffValue -Object $PathwayResponses -Name "urgency_assessment" -Default $null

    $callbackText = if (-not [string]::IsNullOrWhiteSpace($CallbackNumber)) { "Callback: $CallbackNumber." } else { "Callback not confirmed." }
    $verificationText = if ($VerificationStatus -eq "matched") {
        "Patient verification: matched."
    }
    else {
        "Patient verification: $VerificationStatus. $VerificationReason".Trim()
    }

    if ($redFlag -or $Priority -eq "999 Emergency") {
        $symptoms = Get-JeffStaffRedFlagText -PathwayResponses $PathwayResponses -RawTranscript $RawTranscript -TranscriptSummary $TranscriptSummary
        $adviceText = if (Test-JeffEmergencyAdviceGiven -PathwayResponses $PathwayResponses -RawTranscript $RawTranscript) {
            "Transcript/pathway indicates urgent care or 999/A&E advice was given."
        }
        else {
            "No confirmed 999/A&E advice found in the extracted pathway data."
        }

        return [pscustomobject]@{
            task_title = "POSSIBLE EMERGENCY - $symptoms"
            task_body = Join-JeffStaffSentences @(
                "Caller reported: $symptoms.",
                "Priority: 999 Emergency.",
                "Safe to queue: false.",
                $adviceText,
                $callbackText,
                $verificationText
            )
        }
    }

    switch ($RequestType) {
        "prescription" {
            $medText = Get-JeffStaffFirstText @(
                $MedicationsRequested,
                (Get-JeffStaffValue -Object $prescription -Name "medications_requested" -Default @()),
                "medication not clearly captured"
            )
            $prescriptionType = Get-JeffStaffFirstText @(
                (Get-JeffStaffValue -Object $prescription -Name "prescription_type"),
                ($(if ($RequestSubtype -match "repeat") { "repeat" } else { "" }))
            )
            $runOut = Get-JeffStaffValue -Object $prescription -Name "run_out_status" -Default ""
            $titlePrefix = if ($prescriptionType -eq "repeat") { "Repeat prescription request" } else { "Prescription request" }
            $title = "$titlePrefix - $medText"
            $body = Join-JeffStaffSentences @(
                "Caller requested prescription support for: $medText.",
                ($(if (-not [string]::IsNullOrWhiteSpace($Pharmacy)) { "Pharmacy: $Pharmacy." } else { "" })),
                ($(if (-not [string]::IsNullOrWhiteSpace($runOut)) { "Run-out status stated by caller: $runOut." } else { "" })),
                $callbackText,
                $verificationText
            )
        }
        "sick_note" {
            $noteType = Get-JeffStaffValue -Object $sickNote -Name "request_type" -Default ""
            $purpose = Get-JeffStaffValue -Object $sickNote -Name "purpose" -Default ""
            $startDate = Get-JeffStaffValue -Object $sickNote -Name "start_date" -Default ""
            $duration = Get-JeffStaffValue -Object $sickNote -Name "requested_duration" -Default ""
            $reason = Get-JeffStaffValue -Object $sickNote -Name "reason" -Default ""
            $detail = Get-JeffStaffFirstText @(
                ($(if (-not [string]::IsNullOrWhiteSpace($noteType) -and -not [string]::IsNullOrWhiteSpace($purpose)) { "$noteType fit note for $purpose" } else { "" })),
                ($(if (-not [string]::IsNullOrWhiteSpace($noteType)) { "$noteType fit note" } else { "" })),
                "fit note"
            )
            $title = "Sick note request - $detail"
            $body = Join-JeffStaffSentences @(
                "Caller requested a sick note/fit note.",
                ($(if (-not [string]::IsNullOrWhiteSpace($purpose)) { "Purpose stated: $purpose." } else { "" })),
                ($(if (-not [string]::IsNullOrWhiteSpace($startDate)) { "Requested start date: $startDate." } else { "" })),
                ($(if (-not [string]::IsNullOrWhiteSpace($duration)) { "Requested duration: $duration." } else { "" })),
                ($(if (-not [string]::IsNullOrWhiteSpace($reason)) { "Reason stated by caller: $reason." } else { "" })),
                $callbackText,
                $verificationText
            )
        }
        "referral" {
            $referralType = Get-JeffStaffValue -Object $referral -Name "referral_type" -Default ""
            $hospital = Get-JeffStaffValue -Object $referral -Name "hospital_name" -Default ""
            $submitted = Get-JeffStaffValue -Object $referral -Name "approx_submission_date" -Default ""
            $titleLead = if ($referralType -match "chas") { "Referral chase" } else { "Referral query" }
            $title = Get-JeffStaffFirstText @(
                ($(if (-not [string]::IsNullOrWhiteSpace($hospital)) { "$titleLead - $hospital" } else { "" })),
                $titleLead
            )
            $body = Join-JeffStaffSentences @(
                "Caller asked about a referral.",
                ($(if (-not [string]::IsNullOrWhiteSpace($hospital)) { "Hospital/service stated: $hospital." } else { "" })),
                ($(if (-not [string]::IsNullOrWhiteSpace($submitted)) { "Approximate submission timing stated: $submitted." } else { "" })),
                $callbackText,
                $verificationText
            )
        }
        "test_result" {
            $testType = Get-JeffStaffValue -Object $testResult -Name "test_type" -Default ""
            $testDate = Get-JeffStaffValue -Object $testResult -Name "approx_test_date" -Default ""
            $reference = Get-JeffStaffValue -Object $testResult -Name "reference_number" -Default ""
            $title = Get-JeffStaffFirstText @(
                ($(if (-not [string]::IsNullOrWhiteSpace($testType)) { "Test results query - $testType" } else { "" })),
                "Test results query"
            )
            $body = Join-JeffStaffSentences @(
                "Caller asked about test results.",
                ($(if (-not [string]::IsNullOrWhiteSpace($testType)) { "Test type stated: $testType." } else { "" })),
                ($(if (-not [string]::IsNullOrWhiteSpace($testDate)) { "Approximate test date stated: $testDate." } else { "" })),
                ($(if (-not [string]::IsNullOrWhiteSpace($reference)) { "Reference number stated: $reference." } else { "" })),
                $callbackText,
                $verificationText
            )
        }
        "appointment_redirect" {
            $urgencyLevel = Get-JeffStaffValue -Object $urgency -Name "urgency_level" -Default ""
            $title = "Appointment request"
            $body = Join-JeffStaffSentences @(
                "Caller requested appointment support.",
                ($(if (-not [string]::IsNullOrWhiteSpace($urgencyLevel)) { "Pathway urgency stated: $urgencyLevel." } else { "" })),
                $callbackText,
                $verificationText
            )
        }
        default {
            $adminReason = Get-JeffStaffValue -Object $admin -Name "admin_reason" -Default ""
            $category = if ($adminReason -match "record") {
                "records"
            }
            elseif ($adminReason -match "letter") {
                "letter"
            }
            elseif ($adminReason -match "address") {
                "address"
            }
            elseif ($adminReason -match "registration|register") {
                "registration"
            }
            else {
                "admin"
            }
            $title = "Admin query - $category"
            $body = Join-JeffStaffSentences @(
                "Caller requested admin support.",
                ($(if (-not [string]::IsNullOrWhiteSpace($adminReason)) { "Reason stated: $adminReason." } else { "" })),
                $callbackText,
                $verificationText
            )
        }
    }

    if ($staffReview) {
        $body = Join-JeffStaffSentences @($body, "Staff review required.")
    }

    if (-not $safe) {
        $body = Join-JeffStaffSentences @($body, "Safe to queue: false.")
    }

    return [pscustomobject]@{
        task_title = $title
        task_body = $body
    }
}
