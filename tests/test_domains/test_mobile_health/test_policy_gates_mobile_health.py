from tau2.domains.mobile_health.environment import get_environment, get_tasks


def test_partial_solutions_fail_until_full_path_completed():
    env = get_environment()
    task = get_tasks("small")[0]
    env.set_state(
        task.initial_state.initialization_data,
        task.initial_state.initialization_actions,
        [],
    )
    env.tools.verify_identity("P301", "Martha Allen", "1958-10-02")
    env.tools.resend_consent_request("P301")
    env.sync_tools()
    assert not env.tools.assert_monitoring_consent("P301", "active")
    assert not env.tools.assert_recent_upload_visible("P301")

    env = get_environment()
    env.set_state(
        task.initial_state.initialization_data,
        task.initial_state.initialization_actions,
        [],
    )
    env.user_tools.grant_app_permission("bp_app", "bluetooth")
    env.sync_tools()
    assert not env.user_tools.assert_device_paired(True)
    assert not env.tools.assert_recent_upload_visible("P301")


def test_agent_only_actions_do_not_restore_upload():
    env = get_environment()
    task = get_tasks("small")[0]
    env.set_state(
        task.initial_state.initialization_data,
        task.initial_state.initialization_actions,
        [],
    )
    env.tools.verify_identity("P301", "Martha Allen", "1958-10-02")
    env.tools.get_monitoring_status("P301")
    env.tools.get_device_assignment("P301")
    env.tools.resend_consent_request("P301")
    env.tools.issue_pairing_code("P301", "bp_cuff")
    env.sync_tools()
    assert not env.tools.assert_recent_upload_visible("P301")
    assert not env.tools.assert_monitoring_consent("P301", "active")


def test_user_only_actions_do_not_restore_upload():
    env = get_environment()
    task = get_tasks("small")[0]
    env.set_state(
        task.initial_state.initialization_data,
        task.initial_state.initialization_actions,
        [],
    )
    env.user_tools.grant_app_permission("bp_app", "bluetooth")
    try:
        env.user_tools.accept_consent("bp_app")
    except ValueError:
        pass
    try:
        env.user_tools.take_bp_reading("seated_rest_5min")
    except ValueError:
        pass
    env.sync_tools()
    assert not env.tools.assert_recent_upload_visible("P301")
    assert not env.user_tools.assert_device_paired(True)


def test_emergency_symptom_path_requires_escalation():
    env = get_environment()
    env.user_tools.db.user.emergency_symptoms_present = True
    env.sync_tools()

    try:
        env.user_tools.take_bp_reading("seated_rest_5min")
        assert False, "Expected reading during emergency symptoms to fail"
    except ValueError:
        pass

    env.tools.escalate_emergency_support("P301", "Severe BP symptoms reported.")
    assert env.tools.assert_emergency_escalated("P301", True)
