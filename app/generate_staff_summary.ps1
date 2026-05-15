Set-StrictMode -Version Latest

function New-JeffTranscriptSummary {
    param(
        [object]$NormalizedInput
    )

    $medText = if ($NormalizedInput.medications_requested.Count -gt 0) {
        $NormalizedInput.medications_requested -join ", "
    } else {
        "medication not clearly captured"
    }

    $summaryParts = @()
    $summaryParts += "Caller requested a prescription for $medText."

    if (-not [string]::IsNullOrWhiteSpace($NormalizedInput.urgency_note)) {
        $summaryParts += "Urgency noted: $($NormalizedInput.urgency_note)."
    }

    if (-not [string]::IsNullOrWhiteSpace($NormalizedInput.pharmacy) -and $NormalizedInput.pharmacy -ne "unclear") {
        $summaryParts += "Pharmacy given as $($NormalizedInput.pharmacy)."
    }

    if (-not [string]::IsNullOrWhiteSpace($NormalizedInput.callback_number)) {
        $summaryParts += "Callback number captured."
    } else {
        $summaryParts += "Callback number not confirmed."
    }

    if (-not [string]::IsNullOrWhiteSpace($NormalizedInput.caller_for)) {
        $summaryParts += "Caller is speaking for $($NormalizedInput.caller_for)."
    }

    return ($summaryParts -join " ")
}