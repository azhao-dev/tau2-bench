from pathlib import Path

import pytest

from tau2.domains.mobile_health.data_model import MobileHealthDB
from tau2.domains.mobile_health.tools import MobileHealthTools

MOBILE_HEALTH_DB_PATH = (
    Path(__file__).parents[3]
    / "data"
    / "tau2"
    / "domains"
    / "mobile_health"
    / "db.toml"
)


@pytest.fixture
def tools() -> MobileHealthTools:
    db = MobileHealthDB.load(MOBILE_HEALTH_DB_PATH)
    return MobileHealthTools(db)


def test_cannot_inspect_protected_state_before_identity_verification(
    tools: MobileHealthTools,
):
    with pytest.raises(ValueError):
        tools.get_monitoring_status("P301")
    with pytest.raises(ValueError):
        tools.get_device_assignment("P301")
    with pytest.raises(ValueError):
        tools.check_recent_uploads("P301")
    with pytest.raises(ValueError):
        tools.check_red_flag_status("P301")
    with pytest.raises(ValueError):
        tools.resend_consent_request("P301")
    with pytest.raises(ValueError):
        tools.issue_pairing_code("P301", "bp_cuff")


def test_verify_identity_allows_backend_access(tools: MobileHealthTools):
    result = tools.verify_identity("P301", "Martha Allen", "1958-10-02")
    assert result["identity_verified"] is True
    status = tools.get_monitoring_status("P301")
    assert status["monitoring_program"] == "smbp_hypertension"


def test_resend_consent_only_changes_consent_to_pending(tools: MobileHealthTools):
    tools.verify_identity("P301", "Martha Allen", "1958-10-02")
    tools.resend_consent_request("P301")
    patient = tools._get_patient("P301")
    assert patient.monitoring_consent_status.value == "pending_user_acceptance"
    assert patient.last_successful_upload_at is not None


def test_issue_pairing_code_uses_device_identity(tools: MobileHealthTools):
    tools.verify_identity("P301", "Martha Allen", "1958-10-02")
    result = tools.issue_pairing_code("P301", "bp_cuff")
    assert result["pairing_code"] == "PAIR-D440-BP-CUFF"
    assert tools._get_patient("P301").pairing_token_status.value == "issued"
