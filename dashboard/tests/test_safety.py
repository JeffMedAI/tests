"""
TDD tests for the AI safety boundary module.

Core invariant: LLM output MUST NEVER set protected fields.
Protected fields are always set by deterministic code, never by the LLM.
"""
import pytest
from app.safety import (
    PROTECTED_FIELDS,
    SafetyViolation,
    validate_llm_output,
    sanitise_for_pipeline,
)


class TestProtectedFieldsList:
    def test_includes_verification_status(self):
        assert "verification_status" in PROTECTED_FIELDS

    def test_includes_safe_to_queue(self):
        assert "safe_to_queue" in PROTECTED_FIELDS

    def test_includes_priority(self):
        assert "priority" in PROTECTED_FIELDS

    def test_includes_matched_patient_name(self):
        assert "matched_patient_name" in PROTECTED_FIELDS

    def test_includes_nhs_number(self):
        assert "nhs_number" in PROTECTED_FIELDS

    def test_includes_emis_number(self):
        assert "emis_number" in PROTECTED_FIELDS

    def test_includes_date_of_birth(self):
        assert "date_of_birth" in PROTECTED_FIELDS

    def test_includes_clinical_urgency(self):
        assert "clinical_urgency" in PROTECTED_FIELDS

    def test_includes_patient_id(self):
        assert "patient_id" in PROTECTED_FIELDS

    def test_is_frozenset(self):
        assert isinstance(PROTECTED_FIELDS, frozenset)


class TestValidateLlmOutput:
    def test_passes_empty_dict(self):
        validate_llm_output({})  # must not raise

    def test_passes_safe_fields(self):
        validate_llm_output({
            "summary": "Patient wants appointment",
            "reason": "back pain",
            "urgency_indicator": "routine",
            "caller_type": "patient",
        })

    def test_raises_on_verification_status(self):
        with pytest.raises(SafetyViolation):
            validate_llm_output({"verification_status": "matched"})

    def test_raises_on_safe_to_queue(self):
        with pytest.raises(SafetyViolation):
            validate_llm_output({"safe_to_queue": True})

    def test_raises_on_priority(self):
        with pytest.raises(SafetyViolation):
            validate_llm_output({"priority": "urgent"})

    def test_raises_on_matched_patient_name(self):
        with pytest.raises(SafetyViolation):
            validate_llm_output({"matched_patient_name": "John Smith"})

    def test_raises_on_nhs_number(self):
        with pytest.raises(SafetyViolation):
            validate_llm_output({"nhs_number": "123 456 7890"})

    def test_raises_on_emis_number(self):
        with pytest.raises(SafetyViolation):
            validate_llm_output({"emis_number": "ABC123"})

    def test_raises_on_date_of_birth(self):
        with pytest.raises(SafetyViolation):
            validate_llm_output({"date_of_birth": "1980-01-01"})

    def test_raises_on_clinical_urgency(self):
        with pytest.raises(SafetyViolation):
            validate_llm_output({"clinical_urgency": "high"})

    def test_raises_on_patient_id(self):
        with pytest.raises(SafetyViolation):
            validate_llm_output({"patient_id": 42})

    def test_error_message_names_the_field(self):
        with pytest.raises(SafetyViolation, match="verification_status"):
            validate_llm_output({"verification_status": "matched"})

    def test_raises_on_multiple_violations_simultaneously(self):
        with pytest.raises(SafetyViolation):
            validate_llm_output({
                "verification_status": "matched",
                "priority": "urgent",
                "summary": "patient has pain",
            })

    def test_violation_reports_all_offending_fields(self):
        exc_info = pytest.raises(SafetyViolation, validate_llm_output, {
            "verification_status": "matched",
            "safe_to_queue": True,
        })
        msg = str(exc_info.value)
        assert "verification_status" in msg
        assert "safe_to_queue" in msg

    def test_value_of_none_still_triggers_violation(self):
        # LLM setting a field to None is still a violation — key presence matters
        with pytest.raises(SafetyViolation):
            validate_llm_output({"priority": None})


class TestSanitiseForPipeline:
    def test_passes_non_protected_fields_unchanged(self):
        raw = {"summary": "test", "reason": "pain", "caller_type": "patient"}
        result = sanitise_for_pipeline(raw)
        assert result == {"summary": "test", "reason": "pain", "caller_type": "patient"}

    def test_strips_verification_status(self):
        raw = {"summary": "test", "verification_status": "matched"}
        result = sanitise_for_pipeline(raw)
        assert "verification_status" not in result
        assert result["summary"] == "test"

    def test_strips_all_protected_fields(self):
        raw = {
            "summary": "test",
            "verification_status": "matched",
            "safe_to_queue": True,
            "priority": "urgent",
            "nhs_number": "123",
            "emis_number": "ABC",
            "date_of_birth": "1980-01-01",
            "clinical_urgency": "high",
            "matched_patient_name": "Jane",
        }
        result = sanitise_for_pipeline(raw)
        for field in PROTECTED_FIELDS:
            assert field not in result
        assert result["summary"] == "test"

    def test_does_not_mutate_original_dict(self):
        raw = {"verification_status": "matched", "summary": "test"}
        sanitise_for_pipeline(raw)
        assert "verification_status" in raw  # original must be untouched

    def test_empty_dict_returns_empty_dict(self):
        assert sanitise_for_pipeline({}) == {}

    def test_all_protected_dict_returns_empty(self):
        raw = {f: "x" for f in PROTECTED_FIELDS}
        assert sanitise_for_pipeline(raw) == {}

    def test_returns_dict_not_original_reference(self):
        raw = {"summary": "test"}
        result = sanitise_for_pipeline(raw)
        assert result is not raw
