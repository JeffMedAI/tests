Set-StrictMode -Version Latest

function Get-JeffMissingFields {
    param(
        [object]$NormalizedInput,
        [string]$RequestType
    )

    $missingFields = @()

    $patientName = ""
    $dob = ""
    $medicationsRequested = @()

    if ($null -ne $NormalizedInput) {
        if ($NormalizedInput.PSObject.Properties["patient_name"]) {
            $patientName = [string]$NormalizedInput.patient_name
        }

        if ($NormalizedInput.PSObject.Properties["dob"]) {
            $dob = [string]$NormalizedInput.dob
        }

        if ($NormalizedInput.PSObject.Properties["medications_requested"] -and $null -ne $NormalizedInput.medications_requested) {
            $medicationsRequested = @($NormalizedInput.medications_requested)
        }
    }

    if ([string]::IsNullOrWhiteSpace($patientName)) {
        $missingFields += "patient_name"
    }

    if ([string]::IsNullOrWhiteSpace($dob)) {
        $missingFields += "dob"
    }

    if ($RequestType -eq "prescription" -and $medicationsRequested.Count -eq 0) {
        $missingFields += "medications_requested"
    }

    return @($missingFields)
}
