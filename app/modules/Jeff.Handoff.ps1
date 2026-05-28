Set-StrictMode -Version Latest

. "C:\JeffLocal\app\modules\Jeff.StaffSummary.ps1"

function Get-JeffHandoffTaskText {
    param(
        [string]$RequestType,
        [string]$RequestSubtype,
        [string]$MedText,
        [string]$Pharmacy,
        [string]$CallbackText,
        [string]$UrgencyNote,
        [string]$CallerFor,
        [object]$PathwayResponses = $null,
        [string]$RawTranscript = "",
        [string]$TranscriptSummary = "",
        [string]$VerificationStatus = "",
        [string]$VerificationReason = "",
        [string]$Priority = "",
        $SafeToQueue = $true,
        $StaffReviewRequired = $false,
        $RedFlagsPresent = $false,
        [object]$NormalizedInput = $null,
        [array]$MedicationsRequested = @()
    )

    $summaryArgs = @{
        RequestType = $RequestType
        RequestSubtype = $RequestSubtype
        PathwayResponses = $PathwayResponses
        RawTranscript = $RawTranscript
        TranscriptSummary = $TranscriptSummary
        VerificationStatus = $VerificationStatus
        VerificationReason = $VerificationReason
        Priority = $Priority
        SafeToQueue = $SafeToQueue
        StaffReviewRequired = $StaffReviewRequired
        RedFlagsPresent = $RedFlagsPresent
        NormalizedInput = $NormalizedInput
        MedicationsRequested = $MedicationsRequested
        Pharmacy = $Pharmacy
        CallbackNumber = $CallbackText
    }

    return Get-JeffStaffTaskText @summaryArgs
}

function Get-JeffHandoffDisposition {
    param(
        [string]$RequestType,
        [string]$RequestSubtype,
        [string]$FlagPriority,
        [string]$VerificationStatus,
        [string]$CallbackNumber = "",
        $StaffReviewRequiredFromCall,
        $RedFlagsPresentFromCall
    )

    $staffReviewRequired = $false
    if ($StaffReviewRequiredFromCall -eq $true -or "$StaffReviewRequiredFromCall".ToLowerInvariant() -eq "true") {
        $staffReviewRequired = $true
    }

    $redFlagsPresent = $false
    if ($RedFlagsPresentFromCall -eq $true -or "$RedFlagsPresentFromCall".ToLowerInvariant() -eq "true") {
        $redFlagsPresent = $true
    }

    $identityReviewStatuses = @("possible_match", "possible_match_weak", "needs_review", "no_match", "insufficient_data")
    $hasIdentityUncertainty = $VerificationStatus -in $identityReviewStatuses
    $callbackMissing = [string]::IsNullOrWhiteSpace($CallbackNumber) -or $CallbackNumber -in @("not confirmed", "refused", "unknown", "uncertain")
    $urgentSubtype = $RequestSubtype -in @("urgent_repeat_prescription", "urgent_appointment_request", "red_flag_medication_request")

    if ($VerificationStatus -ne "matched") {
        $staffReviewRequired = $true
    }

    if ($callbackMissing) {
        $staffReviewRequired = $true
    }

    if (
        $RequestSubtype -in @("third_party_repeat_prescription", "sick_note_request", "referral_query", "test_results_query") -or
        $RequestType -in @("sick_note", "referral", "test_result", "appointment_redirect", "unknown", "needs_review")
    ) {
        $staffReviewRequired = $true
    }

    if ($urgentSubtype) {
        $staffReviewRequired = $true
    }

    $priority = $FlagPriority
    if ([string]::IsNullOrWhiteSpace($priority)) {
        $priority = "routine"
    }

    if ($redFlagsPresent) {
        $priority = "999 Emergency"
        $safeToQueue = $false
    }
    else {
        $safeToQueue = $true

        if ($urgentSubtype) {
            $priority = "urgent_review"
        }
        elseif ($hasIdentityUncertainty -or $callbackMissing) {
            $priority = "review_required"
        }
        elseif ($priority -eq "urgent_review" -and [string]::IsNullOrWhiteSpace($FlagPriority)) {
            $priority = "review_required"
        }
    }

    $actionNeeded = if ($staffReviewRequired) { "Staff review required" } else { "Process according to workflow" }

    return [pscustomobject]@{
        priority = $priority
        staff_review_required = $staffReviewRequired
        red_flags_present = $redFlagsPresent
        safe_to_queue = $safeToQueue
        action_needed = $actionNeeded
    }
}
