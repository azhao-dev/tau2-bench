from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import Field

from tau2.environment.db import DB
from tau2.utils.pydantic_utils import BaseModelNoExtra


class AppPermissionStatus(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"


class PendingUpload(BaseModelNoExtra):
    metric: str = Field(description="Metric awaiting upload.")
    captured_at: datetime = Field(description="When the reading was captured.")
    source: str = Field(description="How the reading was captured.")
    quality: str = Field(description="Quality label for the reading.")
    systolic: int = Field(description="Systolic value.")
    diastolic: int = Field(description="Diastolic value.")
    protocol: str = Field(description="Collection protocol.")


class LocalReading(BaseModelNoExtra):
    systolic: int = Field(description="Systolic blood pressure.")
    diastolic: int = Field(description="Diastolic blood pressure.")
    captured_at: datetime = Field(description="Capture timestamp.")
    protocol: str = Field(description="Collection protocol.")


class MobileHealthUserState(BaseModelNoExtra):
    patient_id: str = Field(description="Linked patient identifier.")
    full_name: str = Field(description="User full name.")
    date_of_birth: str = Field(description="User DOB in YYYY-MM-DD.")
    monitoring_program: str = Field(
        default="smbp_hypertension",
        description="Monitoring program shown in the user's app.",
    )
    assigned_device_id: str = Field(
        default="D440_bp_cuff",
        description="Assigned device identifier shown in the user's app.",
    )
    bp_app_installed: bool = Field(default=True, description="Whether app is installed.")
    bp_app_logged_in: bool = Field(default=True, description="Whether user is logged in.")
    bluetooth_system_enabled: bool = Field(
        default=True, description="Whether Bluetooth is enabled at the system level."
    )
    bp_app_bluetooth_permission: AppPermissionStatus = Field(
        default=AppPermissionStatus.GRANTED,
        description="Bluetooth permission for the BP app.",
    )
    device_paired_to_phone: bool = Field(
        default=False, description="Whether cuff is paired to the phone."
    )
    background_sync_enabled: bool = Field(
        default=True, description="Whether background sync is enabled."
    )
    network_available: bool = Field(
        default=True, description="Whether network connectivity is available."
    )
    cuff_battery_ok: bool = Field(
        default=True, description="Whether the cuff battery is usable."
    )
    latest_pairing_code: Optional[str] = Field(
        default=None, description="Pairing code currently shown to the user."
    )
    consent_prompt_available: bool = Field(
        default=False, description="Whether there is a consent prompt to accept."
    )
    consent_accepted: bool = Field(
        default=False, description="Whether the user accepted the pending consent."
    )
    last_local_reading: Optional[LocalReading] = Field(
        default=None, description="Most recent local reading."
    )
    pending_upload_queue: list[PendingUpload] = Field(
        default_factory=list, description="Uploads waiting to sync."
    )
    emergency_symptoms_present: bool = Field(
        default=False, description="Whether the user has emergency red-flag symptoms."
    )


class MobileHealthUserDB(DB):
    """User-side device and app state for mobile health."""

    user: MobileHealthUserState = Field(description="Current patient-side session.")
