import pytest

from tau2.domains.mobile_health.user_data_model import (
    AppPermissionStatus,
    MobileHealthUserDB,
    MobileHealthUserState,
)
from tau2.domains.mobile_health.user_tools import MobileHealthUserTools


def make_user_tools() -> MobileHealthUserTools:
    db = MobileHealthUserDB(
        user=MobileHealthUserState(
            patient_id="P301",
            full_name="Martha Allen",
            date_of_birth="1958-10-02",
            monitoring_program="smbp_hypertension",
            assigned_device_id="D440_bp_cuff",
            bp_app_installed=True,
            bp_app_logged_in=True,
            bluetooth_system_enabled=True,
            bp_app_bluetooth_permission=AppPermissionStatus.DENIED,
            device_paired_to_phone=False,
            background_sync_enabled=True,
            network_available=True,
            cuff_battery_ok=True,
        )
    )
    return MobileHealthUserTools(db)


def test_permission_repair_alone_does_not_pair_device():
    tools = make_user_tools()
    tools.grant_app_permission("bp_app", "bluetooth")
    assert tools.assert_bluetooth_permission("granted")
    assert tools.assert_device_paired(False)


def test_pair_requires_permission_and_code():
    tools = make_user_tools()
    with pytest.raises(ValueError):
        tools.pair_bp_monitor("bp_app", "PAIR-D440-BP-CUFF")

    tools.grant_app_permission("bp_app", "bluetooth")
    tools.db.user.latest_pairing_code = "PAIR-D440-BP-CUFF"
    msg = tools.pair_bp_monitor("bp_app", "PAIR-D440-BP-CUFF")
    assert "paired successfully" in msg.lower()
    assert tools.assert_device_paired(True)


def test_take_reading_requires_app_ready_and_pairing():
    tools = make_user_tools()
    with pytest.raises(ValueError):
        tools.take_bp_reading("seated_rest_5min")

    tools.grant_app_permission("bp_app", "bluetooth")
    tools.db.user.latest_pairing_code = "PAIR-D440-BP-CUFF"
    tools.pair_bp_monitor("bp_app", "PAIR-D440-BP-CUFF")
    msg = tools.take_bp_reading("seated_rest_5min")
    assert "queued for sync" in msg.lower()
    assert tools.assert_fresh_bp_reading_taken(True)
