from datetime import timedelta
from typing import Any

from tau2.domains.mobile_health.data_model import (
    MobileHealthDB,
    MonitoringConsentStatus,
    PairingTokenStatus,
    PatientRecord,
)
from tau2.domains.mobile_health.utils import get_now
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class MobileHealthTools(ToolKitBase):
    """Provider-side tools for mobile RPM support."""

    db: MobileHealthDB

    def _get_patient(self, patient_id: str) -> PatientRecord:
        for patient in self.db.patients:
            if patient.patient_id == patient_id:
                return patient
        raise ValueError(f"Patient {patient_id} not found")

    def _require_verified_identity(self, patient_id: str) -> PatientRecord:
        patient = self._get_patient(patient_id)
        if not patient.identity_verified:
            raise ValueError(
                "Identity must be verified before discussing monitoring details."
            )
        return patient

    @is_tool(ToolType.WRITE)
    def verify_identity(
        self, patient_id: str, full_name: str, date_of_birth: str
    ) -> dict[str, Any]:
        """Verify patient identity before accessing protected monitoring details."""
        patient = self._get_patient(patient_id)
        verified = (
            patient.patient_record_exists
            and patient.full_name.lower() == full_name.lower()
            and patient.date_of_birth == date_of_birth
        )
        patient.identity_verified = verified
        return {
            "identity_verified": verified,
            "message": (
                "Identity verified." if verified else "Identity could not be verified."
            ),
        }

    @is_tool(ToolType.READ)
    def get_monitoring_status(self, patient_id: str) -> dict[str, Any]:
        """Get the patient's monitoring program, program status, consent state, and latest upload timestamp."""
        patient = self._require_verified_identity(patient_id)
        return {
            "monitoring_program": patient.monitoring_program.value,
            "program_status": patient.program_status.value,
            "monitoring_consent_status": patient.monitoring_consent_status.value,
            "last_successful_upload_at": patient.last_successful_upload_at,
        }

    @is_tool(ToolType.READ)
    def get_device_assignment(self, patient_id: str) -> dict[str, Any]:
        """Get minimum-necessary device assignment details for the current monitoring program."""
        patient = self._require_verified_identity(patient_id)
        return {
            "device_id": patient.device_assignment.device_id,
            "device_type": patient.device_assignment.device_type,
            "paired_to_current_phone": patient.device_assignment.paired_to_current_phone,
            "pairing_token_status": patient.pairing_token_status.value,
        }

    @is_tool(ToolType.WRITE)
    def resend_consent_request(self, patient_id: str) -> str:
        """Re-send a monitoring consent request to the patient's app."""
        patient = self._require_verified_identity(patient_id)
        if patient.program_status.value != "active":
            raise ValueError("Monitoring program must be active to resend consent.")
        patient.consent_request_pending = True
        patient.monitoring_consent_status = (
            MonitoringConsentStatus.PENDING_USER_ACCEPTANCE
        )
        return "A new monitoring consent request was sent to the patient's app."

    @is_tool(ToolType.WRITE)
    def issue_pairing_code(self, patient_id: str, device_type: str) -> dict[str, str]:
        """Issue a new pairing code for a supported monitoring device."""
        patient = self._require_verified_identity(patient_id)
        if not patient.device_assignment.assigned:
            raise ValueError("No device is currently assigned to this patient.")
        if patient.device_assignment.device_type != device_type:
            raise ValueError("Requested device type does not match the assigned device.")
        device_token = patient.device_assignment.device_id.replace("_", "-").upper()
        pairing_code = f"PAIR-{device_token}"
        patient.active_pairing_code = pairing_code
        patient.pairing_token_status = PairingTokenStatus.ISSUED
        return {"pairing_code": pairing_code, "device_id": patient.device_assignment.device_id}

    @is_tool(ToolType.READ)
    def check_recent_uploads(self, patient_id: str) -> dict[str, Any]:
        """Check whether recent blood pressure uploads are visible to the care team."""
        patient = self._require_verified_identity(patient_id)
        latest = patient.recent_uploads[-1] if patient.recent_uploads else None
        return {
            "upload_queue_visible": patient.upload_queue_visible,
            "last_successful_upload_at": patient.last_successful_upload_at,
            "latest_upload": latest,
        }

    @is_tool(ToolType.READ)
    def check_red_flag_status(self, patient_id: str) -> dict[str, bool]:
        """Check whether the case currently requires emergency escalation."""
        patient = self._require_verified_identity(patient_id)
        return {
            "red_flag_event_open": patient.red_flag_event_open,
            "escalation_initiated": patient.escalation_initiated,
        }

    @is_tool(ToolType.WRITE)
    def escalate_emergency_support(self, patient_id: str, summary: str) -> str:
        """Escalate a red-flag monitoring issue for urgent clinical follow-up."""
        patient = self._get_patient(patient_id)
        patient.escalation_initiated = True
        patient.red_flag_event_open = True
        return f"Emergency escalation initiated: {summary}"

    def assert_monitoring_consent(
        self, patient_id: str, expected: str = "active"
    ) -> bool:
        patient = self._get_patient(patient_id)
        return patient.monitoring_consent_status.value == expected

    def assert_program_status(self, patient_id: str, expected: str = "active") -> bool:
        patient = self._get_patient(patient_id)
        return patient.program_status.value == expected

    def assert_device_assignment_present(
        self, patient_id: str, expected: bool = True
    ) -> bool:
        patient = self._get_patient(patient_id)
        return patient.device_assignment.assigned == expected

    def assert_pairing_token_status(
        self, patient_id: str, expected: str = "redeemed"
    ) -> bool:
        patient = self._get_patient(patient_id)
        return patient.pairing_token_status.value == expected

    def assert_red_flag_status(self, patient_id: str, expected: bool = False) -> bool:
        patient = self._get_patient(patient_id)
        return patient.red_flag_event_open == expected

    def assert_recent_upload_visible(
        self,
        patient_id: str,
        metric: str = "blood_pressure",
        source: str = "device_auto",
        max_age_minutes: int = 5,
        quality: str = "acceptable",
    ) -> bool:
        patient = self._get_patient(patient_id)
        if not patient.recent_uploads or patient.last_successful_upload_at is None:
            return False
        latest = patient.recent_uploads[-1]
        if latest.metric != metric or latest.source != source or latest.quality != quality:
            return False
        age = get_now() - patient.last_successful_upload_at
        return (
            age <= timedelta(minutes=max_age_minutes)
            and latest.visible_to_provider
            and patient.upload_queue_visible
        )

    def assert_device_paired(self, patient_id: str, expected: bool = True) -> bool:
        patient = self._get_patient(patient_id)
        return patient.device_assignment.paired_to_current_phone == expected

    def assert_identity_verified(self, patient_id: str, expected: bool = True) -> bool:
        patient = self._get_patient(patient_id)
        return patient.identity_verified == expected

    def assert_emergency_escalated(self, patient_id: str, expected: bool = True) -> bool:
        patient = self._get_patient(patient_id)
        return patient.escalation_initiated == expected
