Set-StrictMode -Version Latest

function Normalize-JeffRequestType {
    param([AllowNull()][string]$Value)

    $v = ([string]$Value).Trim().ToLowerInvariant()
    $v = $v -replace "[_\-]+", " "

    switch -Regex ($v) {
        "prescription|repeat|medication|medicine|inhaler|pharmacy|drug|tablet|cream|gel|capsule|dose" { return "prescription" }
        "sick\s*note|fit\s*note|fitnote|med3|med\s*3|doctor'?s\s*note|gp\s*note|certificate|signed\s*off|sign\s*off" { return "sick_note" }
        "referral|hospital|consultant|clinic|chase\s*referral|referred|choose\s*and\s*book|e-?rs|ers" { return "referral" }
        "test|result|blood|xray|x-ray|scan|mri|\bct\b|urine|swab|sample|specimen|ultrasound" { return "test_result" }
        "appointment|book|booking|see\s*a\s*doctor|see\s*gp|see\s*nurse|same\s*day\s*appointment" { return "appointment_redirect" }
        "admin|reception|letter|records|address|registration|register|form|email|online\s*access|medical\s*record|copy\s*of|complaint" { return "admin" }
        default { return "admin" }
    }
}
