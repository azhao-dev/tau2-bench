from tau2.domains.mobile_health.environment import get_environment, get_tasks


def test_mobile_health_task_set_loads():
    tasks = get_tasks()
    assert len(tasks) == 10
    assert tasks[0].id.startswith("[bp_sync_issue]")
    assert get_tasks("small")[0].id == "[bp_sync_issue]phone_upgrade_consent_expired_bt_denied"


def test_variant_tasks_cover_requested_mix():
    task_ids = {task.id for task in get_tasks()}
    assert "[bp_sync_issue]phone_upgrade_pairing_only[PERSONA:None]" in task_ids
    assert "[bp_sync_issue]consent_expired_only[PERSONA:None]" in task_ids
    assert "[bp_sync_issue]bt_permission_denied_only[PERSONA:None]" in task_ids
    assert "[bp_sync_issue]consent_plus_pairing[PERSONA:None]" in task_ids
    assert "[bp_sync_issue]pairing_plus_permission[PERSONA:None]" in task_ids
    assert "[bp_sync_issue]consent_plus_pairing_plus_permission[PERSONA:None]" in task_ids
    assert "[bp_sync_issue]phone_upgrade_consent_expired_bt_denied[PERSONA:None]" in task_ids
    assert "[bp_sync_issue]phone_upgrade_consent_expired_bt_denied[PERSONA:Easy]" in task_ids
    assert "[bp_sync_issue]phone_upgrade_consent_expired_bt_denied[PERSONA:Hard]" in task_ids


def test_full_correct_path_produces_provider_visible_upload():
    env = get_environment()
    task = get_tasks()[0]
    env.set_state(
        task.initial_state.initialization_data,
        task.initial_state.initialization_actions,
        [],
    )

    env.tools.verify_identity("P301", "Martha Allen", "1958-10-02")
    env.tools.resend_consent_request("P301")
    env.user_tools.grant_app_permission("bp_app", "bluetooth")
    env.tools.issue_pairing_code("P301", "bp_cuff")
    env.sync_tools()
    env.user_tools.accept_consent("bp_app")
    env.sync_tools()
    env.user_tools.pair_bp_monitor("bp_app", "PAIR-D440-BP-CUFF")
    env.sync_tools()
    env.user_tools.take_bp_reading("seated_rest_5min")
    env.sync_tools()

    assert env.tools.assert_program_status("P301", "active")
    assert env.tools.assert_device_assignment_present("P301", True)
    assert env.tools.assert_monitoring_consent("P301", "active")
    assert env.user_tools.assert_bluetooth_permission("granted")
    assert env.user_tools.assert_device_paired(True)
    assert env.tools.assert_pairing_token_status("P301", "redeemed")
    assert env.tools.assert_recent_upload_visible("P301")
