from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import Field

from tau2.environment.db import DB
from tau2.utils.pydantic_utils import BaseModelNoExtra


class ProgramStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    INACTIVE = "inactive"


class MonitoringConsentStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING_USER_ACCEPTANCE = "pending_user_acceptance"


class PairingTokenStatus(str, Enum):
    VALID = "valid"
    INVALID_AFTER_PHONE_CHANGE = "invalid_after_phone_change"
    ISSUED = "issued"
    REDEEMED = "redeemed"


class MonitoringProgram(str, Enum):
    SMBP_HYPERTENSION = "smbp_hypertension"


class DeviceAssignment(BaseModelNoExtra):
    device_id: str = Field(description="Assigned device identifier.")
    device_type: str = Field(description="Assigned device type.")
    assigned: bool = Field(default=True, description="Whether a device is assigned.")
    paired_to_current_phone: bool = Field(
        default=False,
        description="Whether the assigned device is paired to the current phone.",
    )


class UploadRecord(BaseModelNoExtra):
    metric: str = Field(description="Uploaded metric name.")
    captured_at: datetime = Field(description="When the reading was captured.")
    source: str = Field(description="How the reading entered the system.")
    quality: str = Field(description="Quality label for the reading.")
    visible_to_provider: bool = Field(
        default=True, description="Whether the provider can see the upload."
    )
    systolic: int = Field(description="Systolic value.")
    diastolic: int = Field(description="Diastolic value.")
    protocol: str = Field(description="Collection protocol.")


class PatientRecord(BaseModelNoExtra):
    patient_id: str = Field(description="Unique patient identifier.")
    full_name: str = Field(description="Patient full name.")
    date_of_birth: str = Field(description="Patient date of birth in YYYY-MM-DD.")
    patient_record_exists: bool = Field(
        default=True, description="Whether the patient record exists."
    )
    identity_verified: bool = Field(
        default=False, description="Whether the patient identity is verified."
    )
    monitoring_program: MonitoringProgram = Field(
        default=MonitoringProgram.SMBP_HYPERTENSION,
        description="Active monitoring program.",
    )
    program_status: ProgramStatus = Field(
        default=ProgramStatus.ACTIVE,
        description="Current program status.",
    )
    monitoring_consent_status: MonitoringConsentStatus = Field(
        default=MonitoringConsentStatus.ACTIVE,
        description="Consent status for monitoring.",
    )
    consent_request_pending: bool = Field(
        default=False, description="Whether a consent request is awaiting user action."
    )
    device_assignment: DeviceAssignment = Field(
        description="Assigned monitoring device."
    )
    pairing_token_status: PairingTokenStatus = Field(
        default=PairingTokenStatus.VALID,
        description="Current pairing token state.",
    )
    active_pairing_code: Optional[str] = Field(
        default=None, description="Most recent active pairing code."
    )
    last_successful_upload_at: Optional[datetime] = Field(
        default=None, description="Most recent provider-visible upload timestamp."
    )
    upload_queue_visible: bool = Field(
        default=False, description="Whether an upload is currently visible to staff."
    )
    red_flag_event_open: bool = Field(
        default=False, description="Whether emergency escalation is required."
    )
    escalation_initiated: bool = Field(
        default=False, description="Whether the case has been escalated."
    )
    recent_uploads: list[UploadRecord] = Field(
        default_factory=list,
        description="Recent provider-visible uploads for the patient.",
    )

    @property
    def upload_visible_count(self) -> int:
        return sum(1 for upload in self.recent_uploads if upload.visible_to_provider)


class MobileHealthDB(DB):
    """Backend state for the mobile health domain."""

    patients: list[PatientRecord] = Field(
        default_factory=list, description="Available patient records."
    )

    def get_statistics(self) -> dict[str, Any]:
        return {"num_patients": len(self.patients)}
