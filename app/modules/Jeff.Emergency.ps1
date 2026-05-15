Set-StrictMode -Version Latest

. "C:\JeffLocal\app\modules\Jeff.StaffSummary.ps1"

function Set-JeffHandoffFieldSafe {
    param(
        [Parameter(Mandatory = $true)] $Object,
        [Parameter(Mandatory = $true)] [string]$Name,
        [Parameter(Mandatory = $true)] $Value
    )

    if ($Object.PSObject.Properties[$Name]) {
        $Object.PSObject.Properties[$Name].Value = $Value
    }
    else {
        $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
    }
}

function Invoke-JeffEmergencyOverride {
    param(
        [Parameter(Mandatory = $true)] $Handoff,
        [object[]]$ScanObjects = @()
    )

    $pathwayResponses = Get-JeffStaffValue -Object $Handoff -Name "pathway_responses" -Default $null
    $rawTranscript = [string](Get-JeffStaffValue -Object $Handoff -Name "raw_transcript" -Default "")
    $transcriptSummary = [string](Get-JeffStaffValue -Object $Handoff -Name "transcript_summary" -Default "")
    $evidence = Get-JeffEmergencyEvidence -PathwayResponses $pathwayResponses -RawTranscript $rawTranscript -TranscriptSummary $transcriptSummary

    if ($evidence.has_red_flag) {
        Set-JeffHandoffFieldSafe -Object $Handoff -Name "priority" -Value "999 Emergency"
        Set-JeffHandoffFieldSafe -Object $Handoff -Name "safe_to_queue" -Value $false
        Set-JeffHandoffFieldSafe -Object $Handoff -Name "staff_review_required" -Value $true
        Set-JeffHandoffFieldSafe -Object $Handoff -Name "red_flags_present" -Value $true

        $normalizedInput = Get-JeffStaffValue -Object $Handoff -Name "normalized_input" -Default $null
        $summaryArgs = @{
            RequestType = [string](Get-JeffStaffValue -Object $Handoff -Name "request_type" -Default "admin")
            RequestSubtype = [string](Get-JeffStaffValue -Object $Handoff -Name "request_subtype" -Default "")
            PathwayResponses = Get-JeffStaffValue -Object $Handoff -Name "pathway_responses" -Default $null
            RawTranscript = $rawTranscript
            TranscriptSummary = $transcriptSummary
            VerificationStatus = [string](Get-JeffStaffValue -Object $Handoff -Name "verification_status" -Default "")
            VerificationReason = [string](Get-JeffStaffValue -Object $Handoff -Name "verification_reason" -Default "")
            Priority = "999 Emergency"
            SafeToQueue = $false
            StaffReviewRequired = $true
            RedFlagsPresent = $true
            NormalizedInput = $normalizedInput
            MedicationsRequested = @(Get-JeffStaffValue -Object $normalizedInput -Name "medications_requested" -Default @())
            Pharmacy = [string](Get-JeffStaffValue -Object $normalizedInput -Name "pharmacy" -Default "")
            CallbackNumber = [string](Get-JeffStaffValue -Object $normalizedInput -Name "callback_number" -Default "")
        }
        $summary = Get-JeffStaffTaskText @summaryArgs

        Set-JeffHandoffFieldSafe -Object $Handoff -Name "task_title" -Value $summary.task_title
        Set-JeffHandoffFieldSafe -Object $Handoff -Name "task_body" -Value $summary.task_body
        Set-JeffHandoffFieldSafe -Object $Handoff -Name "call_summary" -Value "Possible emergency red-flag symptoms identified from caller report. Caller requires immediate urgent safety handling."
        Set-JeffHandoffFieldSafe -Object $Handoff -Name "urgency_level" -Value "999 Emergency"
    }

    return [bool]$evidence.has_red_flag
}
