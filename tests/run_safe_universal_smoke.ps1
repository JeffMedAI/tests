Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. "C:\JeffLocal\app\modules\Jeff.Common.ps1"
. "C:\JeffLocal\app\modules\Jeff.PatientMatch.ps1"

function Assert-True {
    param(
        [string]$Name,
        [bool]$Condition
    )

    if (-not $Condition) {
        throw "$Name expected true"
    }
}

function Assert-False {
    param(
        [string]$Name,
        [bool]$Condition
    )

    if ($Condition) {
        throw "$Name expected false"
    }
}

function Assert-HasProperty {
    param(
        [string]$Name,
        [object]$Object,
        [string]$PropertyName
    )

    Assert-True -Name $Name -Condition ($null -ne $Object.PSObject.Properties[$PropertyName])
}

$schema = Get-Content -LiteralPath "C:\JeffLocal\config\output_schema.json" -Raw | ConvertFrom-Json
$schemaBlocks = @(
    "practice",
    "call",
    "caller",
    "patient",
    "identity",
    "request",
    "pathway_responses",
    "operational_flags",
    "routing",
    "outputs",
    "meta"
)

foreach ($block in $schemaBlocks) {
    Assert-HasProperty -Name "schema block $block" -Object $schema.properties -PropertyName $block
}

$criticalFields = @($schema.staff_critical_fields)
foreach ($field in @(
    "verification_status",
    "verification_reason",
    "matched_patient_ref",
    "matched_patient_name",
    "matched_nhs_number",
    "candidate_matches",
    "top_candidate_ref",
    "top_candidate_name",
    "top_candidate_score",
    "transcript_summary",
    "transcript_quality_flag",
    "uncertain_fields",
    "missing_fields",
    "task_title",
    "task_body",
    "priority",
    "safe_to_queue",
    "request_type",
    "selected_pathway"
)) {
    Assert-True -Name "staff critical field $field" -Condition ($criticalFields -contains $field)
}

$pathwayConfig = Get-Content -LiteralPath "C:\JeffLocal\config\pathways.json" -Raw | ConvertFrom-Json
foreach ($pathway in @(
    "prescription",
    "sick_note",
    "referral",
    "test_result",
    "admin"
)) {
    Assert-HasProperty -Name "pathway $pathway present" -Object $pathwayConfig.pathways -PropertyName $pathway
    $entry = $pathwayConfig.pathways.PSObject.Properties[$pathway].Value
    Assert-True -Name "pathway $pathway enabled" -Condition ($entry.enabled -eq $true)
    Assert-HasProperty -Name "pathway $pathway canonical" -Object $entry -PropertyName "canonical_name"
    Assert-HasProperty -Name "pathway $pathway routing label" -Object $entry -PropertyName "staff_routing_label"
    Assert-HasProperty -Name "pathway $pathway priority" -Object $entry -PropertyName "default_priority"
    Assert-HasProperty -Name "pathway $pathway safety notes" -Object $entry -PropertyName "safety_notes"
}

Assert-False -Name "deadletter manifest ignored" -Condition (Test-JeffQueuePayloadFileName "RX-1.json.deadletter.json")
Assert-False -Name "manifest ignored" -Condition (Test-JeffQueuePayloadFileName "RX-1.manifest.json")
Assert-False -Name "backup ignored" -Condition (Test-JeffQueuePayloadFileName "RX-1.backup.json")
Assert-False -Name "temp ignored" -Condition (Test-JeffQueuePayloadFileName "RX-1.tmp.json")
Assert-True -Name "normal queue payload accepted" -Condition (Test-JeffQueuePayloadFileName "RX-1.json")

$matchCommand = Get-Command Get-JeffPatientMatch
Assert-False -Name "patient match has no callback parameter" -Condition ($matchCommand.Parameters.ContainsKey("CallbackNumber"))

$callOllamaText = Get-Content -LiteralPath "C:\JeffLocal\app\call_ollama.ps1" -Raw
Assert-True -Name "ollama prompt is universal" -Condition ($callOllamaText -match "GP surgery phone call transcript")
Assert-True -Name "ollama prompt includes pathway_responses" -Condition ($callOllamaText -match '"pathway_responses"')
Assert-True -Name "ollama prompt keeps deterministic verification" -Condition ($callOllamaText -match "deterministic local code makes final routing")
Assert-False -Name "ollama prompt not prescription-only" -Condition ($callOllamaText -match "GP prescription request call")

Write-Output "Safe universal smoke tests passed."
