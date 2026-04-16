from tau2.domains.mobile_health.user_data_model import (
    AppPermissionStatus,
    LocalReading,
    MobileHealthUserDB,
    PendingUpload,
)
from tau2.domains.mobile_health.utils import get_now
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class MobileHealthUserTools(ToolKitBase):
    """Patient-side app and device tools for mobile RPM support."""

    db: MobileHealthUserDB

    @property
    def user(self):
        return self.db.user

    @is_tool(ToolType.WRITE)
    def accept_consent(self, app_name: str = "bp_app") -> str:
        """Accept a pending monitoring consent request in the RPM app."""
        if app_name != "bp_app":
            raise ValueError("Only the blood pressure app is supported.")
        if not self.user.bp_app_installed or not self.user.bp_app_logged_in:
            raise ValueError("The patient must be logged into the BP app to accept consent.")
        if not self.user.consent_prompt_available:
            raise ValueError("There is no pending consent request to accept.")
        self.user.consent_accepted = True
        self.user.consent_prompt_available = False
        return "Monitoring consent accepted in the BP app."

    @is_tool(ToolType.WRITE)
    def grant_app_permission(self, app_name: str, permission: str) -> str:
        """Grant a phone permission required by the RPM app."""
        if app_name != "bp_app":
            raise ValueError("Only the blood pressure app is supported.")
        if not self.user.bp_app_installed:
            raise ValueError("The BP app must be installed before changing permissions.")
        if permission.lower() != "bluetooth":
            raise ValueError("Only bluetooth permission is modeled in this domain.")
        self.user.bp_app_bluetooth_permission = AppPermissionStatus.GRANTED
        return "Bluetooth permission granted to the BP app."

    @is_tool(ToolType.WRITE)
    def pair_bp_monitor(self, app_name: str, code: str) -> str:
        """Pair the assigned blood pressure monitor with the phone using the current pairing code."""
        if app_name != "bp_app":
            raise ValueError("Only the blood pressure app is supported.")
        if not self.user.bp_app_installed or not self.user.bp_app_logged_in:
            raise ValueError("The BP app must be installed and logged in before pairing.")
        if not self.user.bluetooth_system_enabled:
            raise ValueError("Bluetooth must be enabled before pairing.")
        if self.user.bp_app_bluetooth_permission != AppPermissionStatus.GRANTED:
            raise ValueError("Bluetooth permission must be granted before pairing.")
        if self.user.latest_pairing_code is None:
            raise ValueError("No active pairing code is available.")
        if code != self.user.latest_pairing_code:
            raise ValueError("The pairing code is invalid.")
        self.user.device_paired_to_phone = True
        return "Blood pressure monitor paired successfully."

    @is_tool(ToolType.WRITE)
    def toggle_bluetooth(self) -> str:
        """Toggle the phone's Bluetooth setting on or off."""
        self.user.bluetooth_system_enabled = not self.user.bluetooth_system_enabled
        return (
            f"Bluetooth is now {'enabled' if self.user.bluetooth_system_enabled else 'disabled'}."
        )

    @is_tool(ToolType.WRITE)
    def take_bp_reading(self, protocol: str = "seated_rest_5min") -> str:
        """Take a fresh blood pressure reading using the paired home cuff."""
        if self.user.emergency_symptoms_present:
            raise ValueError(
                "Emergency symptoms are present. Stop troubleshooting and seek urgent care."
            )
        if not self.user.bp_app_installed or not self.user.bp_app_logged_in:
            raise ValueError("The BP app must be installed and logged in before taking a reading.")
        if not self.user.device_paired_to_phone:
            raise ValueError("The monitor must be paired before taking a reading.")
        if self.user.bp_app_bluetooth_permission != AppPermissionStatus.GRANTED:
            raise ValueError("Bluetooth permission must be granted before taking a reading.")
        if not self.user.bluetooth_system_enabled:
            raise ValueError("Bluetooth must be enabled before taking a reading.")
        if not self.user.cuff_battery_ok:
            raise ValueError("The cuff battery is too low to take a reading.")

        captured_at = get_now()
        reading = LocalReading(
            systolic=128,
            diastolic=82,
            captured_at=captured_at,
            protocol=protocol,
        )
        self.user.last_local_reading = reading
        self.user.pending_upload_queue.append(
            PendingUpload(
                metric="blood_pressure",
                captured_at=captured_at,
                source="device_auto",
                quality="acceptable",
                systolic=reading.systolic,
                diastolic=reading.diastolic,
                protocol=protocol,
            )
        )
        return "A fresh blood pressure reading was taken and queued for sync."

    @is_tool(ToolType.READ)
    def check_app_sync_status(self, app_name: str = "bp_app") -> dict:
        """Check whether the RPM app is ready to sync and whether queued readings are waiting to upload."""
        if app_name != "bp_app":
            raise ValueError("Only the blood pressure app is supported.")
        return {
            "bp_app_installed": self.user.bp_app_installed,
            "bp_app_logged_in": self.user.bp_app_logged_in,
            "background_sync_enabled": self.user.background_sync_enabled,
            "network_available": self.user.network_available,
            "pending_upload_queue_size": len(self.user.pending_upload_queue),
            "device_paired_to_phone": self.user.device_paired_to_phone,
            "bluetooth_permission": self.user.bp_app_bluetooth_permission.value,
        }

    def assert_bluetooth_permission(self, expected: str = "granted") -> bool:
        return self.user.bp_app_bluetooth_permission.value == expected

    def assert_device_paired(self, expected: bool = True) -> bool:
        return self.user.device_paired_to_phone == expected

    def assert_fresh_bp_reading_taken(self, expected: bool = True) -> bool:
        return (self.user.last_local_reading is not None) == expected

    def assert_app_ready_for_sync(self, expected: bool = True) -> bool:
        ready = (
            self.user.bp_app_installed
            and self.user.bp_app_logged_in
            and self.user.background_sync_enabled
            and self.user.network_available
        )
        return ready == expected
