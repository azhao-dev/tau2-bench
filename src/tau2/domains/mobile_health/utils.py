from datetime import datetime

from tau2.utils.utils import DATA_DIR

MOBILE_HEALTH_DATA_DIR = DATA_DIR / "tau2" / "domains" / "mobile_health"
MOBILE_HEALTH_DB_PATH = MOBILE_HEALTH_DATA_DIR / "db.toml"
MOBILE_HEALTH_USER_DB_PATH = MOBILE_HEALTH_DATA_DIR / "user_db.toml"
MOBILE_HEALTH_MAIN_POLICY_PATH = MOBILE_HEALTH_DATA_DIR / "main_policy.md"
MOBILE_HEALTH_MAIN_POLICY_SOLO_PATH = MOBILE_HEALTH_DATA_DIR / "main_policy_solo.md"
MOBILE_HEALTH_SUPPORT_MANUAL_PATH = MOBILE_HEALTH_DATA_DIR / "support_manual.md"
MOBILE_HEALTH_TASK_SET_PATH = MOBILE_HEALTH_DATA_DIR / "tasks.json"
MOBILE_HEALTH_TASK_SET_SMALL_PATH = MOBILE_HEALTH_DATA_DIR / "tasks_small.json"


def get_now() -> datetime:
    """Return a fixed timestamp for deterministic task evaluation."""
    return datetime(2025, 3, 3, 9, 30, 0)
