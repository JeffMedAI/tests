Set-StrictMode -Version Latest

function Get-JeffFlags {
    param(
        [string]$NormalizedRawTranscript,
        [object]$NormalizedInput
    )

    $transcriptQualityFlag = "ok"
    $uncertainFields = @()

    if (
        $NormalizedRawTranscript -match "Caller:\s*maso\." -or
        $NormalizedRawTranscript -match "Caller:\s*Description\." -or
        $NormalizedRawTranscript -match "CH439PT" -or
        $NormalizedRawTranscript -match "number ending in 204"
    ) {
        $transcriptQualityFlag = "review_needed"
    }

    if ($NormalizedRawTranscript -match "Caller:\s*maso\.") {
        $uncertainFields += "caller_relationship"
    }

    if ($NormalizedRawTranscript -match "Caller:\s*Description\.") {
        $uncertainFields += "request_type_initial_response"
    }

    if ([string]::IsNullOrWhiteSpace($NormalizedInput.callback_number)) {
        $transcriptQualityFlag = "review_needed"
        $uncertainFields += "callback_number"
    }

    $missingFields = @()
    if ([string]::IsNullOrWhiteSpace($NormalizedInput.patient_name)) { $missingFields += "patient_name" }
    if ([string]::IsNullOrWhiteSpace($NormalizedInput.dob)) { $missingFields += "dob" }
    if ($NormalizedInput.medications_requested.Count -eq 0) { $missingFields += "medications_requested" }

    $uncertainFields = @($uncertainFields + $missingFields | Select-Object -Unique)

    $priority = "routine"
    if ($NormalizedInput.urgency_note -match "run out|about to run out|ran out") {
        $priority = "urgent_review"
    }

    return [pscustomobject]@{
        transcript_quality_flag = $transcriptQualityFlag
        uncertain_fields = @($uncertainFields)
        missing_fields = @($missingFields)
        priority = $priority
    }
}