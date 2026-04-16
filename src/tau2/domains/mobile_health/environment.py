from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.mobile_health.data_model import (
    MobileHealthDB,
    MonitoringConsentStatus,
    PairingTokenStatus,
    UploadRecord,
)
from tau2.domains.mobile_health.tools import MobileHealthTools
from tau2.domains.mobile_health.user_data_model import MobileHealthUserDB
from tau2.domains.mobile_health.user_tools import MobileHealthUserTools
from tau2.domains.mobile_health.utils import (
    MOBILE_HEALTH_DB_PATH,
    MOBILE_HEALTH_MAIN_POLICY_PATH,
    MOBILE_HEALTH_MAIN_POLICY_SOLO_PATH,
    MOBILE_HEALTH_SUPPORT_MANUAL_PATH,
    MOBILE_HEALTH_TASK_SET_PATH,
    MOBILE_HEALTH_TASK_SET_SMALL_PATH,
    MOBILE_HEALTH_USER_DB_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file


class MobileHealthEnvironment(Environment):
    tools: MobileHealthTools
    user_tools: MobileHealthUserTools

    def _get_current_patient_and_user(self):
        user = self.user_tools.db.user
        patient = self.tools._get_patient(user.patient_id)
        return patient, user

    def sync_tools(self):
        if self.tools is None or self.user_tools is None or not self.tools.db.patients:
            return

        patient, user = self._get_current_patient_and_user()

        user.consent_prompt_available = patient.consent_request_pending
        user.latest_pairing_code = patient.active_pairing_code
        user.monitoring_program = patient.monitoring_program.value
        user.assigned_device_id = patient.device_assignment.device_id

        if user.consent_accepted and patient.consent_request_pending:
            patient.consent_request_pending = False
            patient.monitoring_consent_status = MonitoringConsentStatus.ACTIVE
            user.consent_accepted = False
            user.consent_prompt_available = False

        patient.red_flag_event_open = (
            patient.red_flag_event_open or user.emergency_symptoms_present
        )

        if user.device_paired_to_phone:
            patient.device_assignment.paired_to_current_phone = True
            if patient.active_pairing_code is not None:
                patient.pairing_token_status = PairingTokenStatus.REDEEMED
        else:
            patient.device_assignment.paired_to_current_phone = False
            if patient.pairing_token_status == PairingTokenStatus.REDEEMED:
                patient.pairing_token_status = PairingTokenStatus.INVALID_AFTER_PHONE_CHANGE

        can_sync_upload = (
            patient.patient_record_exists
            and
            patient.monitoring_consent_status == MonitoringConsentStatus.ACTIVE
            and patient.program_status.value == "active"
            and patient.device_assignment.assigned
            and user.device_paired_to_phone
            and user.bluetooth_system_enabled
            and user.network_available
            and user.background_sync_enabled
            and user.cuff_battery_ok
            and user.bp_app_installed
            and user.bp_app_logged_in
            and user.bp_app_bluetooth_permission.value == "granted"
            and not patient.red_flag_event_open
        )
        if can_sync_upload and user.pending_upload_queue:
            pending = user.pending_upload_queue.pop(0)
            patient.last_successful_upload_at = pending.captured_at
            patient.upload_queue_visible = True
            patient.recent_uploads.append(
                UploadRecord(
                    metric=pending.metric,
                    captured_at=pending.captured_at,
                    source=pending.source,
                    quality=pending.quality,
                    visible_to_provider=True,
                    systolic=pending.systolic,
                    diastolic=pending.diastolic,
                    protocol=pending.protocol,
                )
            )
        else:
            patient.upload_queue_visible = bool(patient.recent_uploads) and not user.pending_upload_queue


def get_environment(
    db: Optional[MobileHealthDB] = None,
    user_db: Optional[MobileHealthUserDB] = None,
    solo_mode: bool = False,
) -> MobileHealthEnvironment:
    if db is None:
        db = MobileHealthDB.load(MOBILE_HEALTH_DB_PATH)
    tools = MobileHealthTools(db)
    if user_db is None:
        user_db = MobileHealthUserDB.load(MOBILE_HEALTH_USER_DB_PATH)
    user_tools = MobileHealthUserTools(user_db)
    policy_path = (
        MOBILE_HEALTH_MAIN_POLICY_SOLO_PATH if solo_mode else MOBILE_HEALTH_MAIN_POLICY_PATH
    )
    main_policy = load_file(policy_path)
    support_manual = load_file(MOBILE_HEALTH_SUPPORT_MANUAL_PATH)
    policy = (
        "<main_policy>\n"
        + main_policy
        + "\n</main_policy>\n"
        + "<support_manual>\n"
        + support_manual
        + "\n</support_manual>"
    )
    env = MobileHealthEnvironment(
        domain_name="mobile_health",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
    )
    if solo_mode:
        env.set_solo_mode(True)
    return env


def _load_tasks(path) -> list[Task]:
    tasks = load_file(path)
    if isinstance(tasks, dict) and "tasks" in tasks:
        tasks = tasks["tasks"]
    return [Task.model_validate(task) for task in tasks]


def get_tasks(task_split_name: Optional[str] = "base") -> list[Task]:
    if task_split_name == "small":
        return _load_tasks(MOBILE_HEALTH_TASK_SET_SMALL_PATH)
    if task_split_name in (None, "base", "full"):
        return _load_tasks(MOBILE_HEALTH_TASK_SET_PATH)
    raise ValueError(
        "Invalid task split name for mobile_health. Valid splits are: base, full, small"
    )


def get_tasks_split() -> dict[str, list[str]]:
    full_tasks = _load_tasks(MOBILE_HEALTH_TASK_SET_PATH)
    small_tasks = _load_tasks(MOBILE_HEALTH_TASK_SET_SMALL_PATH)
    return {
        "base": [task.id for task in full_tasks],
        "full": [task.id for task in full_tasks],
        "small": [task.id for task in small_tasks],
    }
