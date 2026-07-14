"""
AI Safety Boundary module for Avamed / JeffLocal.

Enforces the core safety invariant: LLM output MUST NEVER set protected fields.
These fields are always determined by deterministic code — never by model output.

Fields protected by this module:
    verification_status, safe_to_queue, priority, matched_patient_name,
    nhs_number, emis_number, date_of_birth, clinical_urgency, patient_id

Usage:
    from app.safety import validate_llm_output, sanitise_for_pipeline

    raw = ollama_extract(transcript)      # LLM output
    validate_llm_output(raw)              # raises SafetyViolation if protected field present
    safe_raw = sanitise_for_pipeline(raw) # strip any protected fields, return clean dict
    # deterministic code now sets verification_status, priority, etc.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

PROTECTED_FIELDS: frozenset[str] = frozenset({
    "verification_status",
    "safe_to_queue",
    "priority",
    "matched_patient_name",
    "nhs_number",
    "emis_number",
    "date_of_birth",
    "clinical_urgency",
    "patient_id",
    "matched_dob",
    "matched_nhs",
    "matched_emis",
})


class SafetyViolation(Exception):
    """Raised when LLM output attempts to set a protected deterministic field."""


def validate_llm_output(raw: dict) -> None:
    """
    Raise SafetyViolation if raw LLM output contains any protected field.

    Call this immediately after receiving LLM output, before any pipeline stage
    that writes to the database or the handoff JSON.
    """
    violations = [field for field in PROTECTED_FIELDS if field in raw]
    if violations:
        log.critical(
            "SAFETY VIOLATION: LLM output attempted to set protected fields: %s — "
            "rejecting output. This is a critical bug if it appears in production.",
            violations,
        )
        raise SafetyViolation(
            f"LLM output attempted to set protected fields: {violations}. "
            "These fields must only be set by deterministic code."
        )


def sanitise_for_pipeline(raw: dict) -> dict:
    """
    Return a copy of raw with all protected fields removed.

    Logs a warning for each stripped field so violations are visible in audit
    logs even when the caller prefers silent stripping over rejection.
    """
    stripped: dict = {}
    for key, value in raw.items():
        if key in PROTECTED_FIELDS:
            log.warning(
                "sanitise_for_pipeline: stripped protected field '%s' from LLM output.",
                key,
            )
        else:
            stripped[key] = value
    return stripped
