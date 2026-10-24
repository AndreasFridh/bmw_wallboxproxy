import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


ENV_PATH = Path(os.environ.get("APP_ENV_FILE", Path(__file__).with_name(".env"))).expanduser()


def _load_dotenv() -> None:
    env_path = ENV_PATH
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _read_env_file_values() -> dict[str, str]:
    env_path = ENV_PATH
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_choice(name: str, default: str, allowed: set[str]) -> str:
    raw = os.environ.get(name)
    if raw is None:
        return default

    value = raw.strip().lower()
    if value in allowed:
        return value
    return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default

    try:
        value = int(raw.strip())
    except ValueError:
        return default

    if 1 <= value <= 65535:
        return value
    return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default

    try:
        value = float(raw.strip())
    except ValueError:
        return default

    if value >= 0:
        return value
    return default


def _env_float_any(name: str) -> Optional[float]:
    """Read an env var as a float, accepting any sign. Returns None if unset or unparseable."""
    raw = os.environ.get(name)
    if not raw or not raw.strip():
        return None
    try:
        return float(raw.strip())
    except ValueError:
        return None


def _env_str(name: str, default: str = "") -> str:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip()


def save_env_settings(settings: dict[str, str]) -> None:
    lines: list[str] = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

    remaining = dict(settings)
    for index, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, _value = stripped.split("=", 1)
        key = key.strip()
        if key in remaining:
            lines[index] = f"{key}={remaining.pop(key)}"

    for key, value in remaining.items():
        lines.append(f"{key}={value}")

    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for key, value in settings.items():
        os.environ[key] = value


def save_env_setting(name: str, value: str) -> None:
    save_env_settings({name: value})


_load_dotenv()

ENTITY_FIELDS = (
    ("u1", "Voltage L1", "Home Assistant entity for phase 1 voltage."),
    ("u2", "Voltage L2", "Home Assistant entity for phase 2 voltage."),
    ("u3", "Voltage L3", "Home Assistant entity for phase 3 voltage."),
    ("i1", "Current L1", "Home Assistant entity for phase 1 current."),
    ("i2", "Current L2", "Home Assistant entity for phase 2 current."),
    ("i3", "Current L3", "Home Assistant entity for phase 3 current."),
    ("p_total", "Total power", "Home Assistant entity for total active power."),
    ("freq", "Grid frequency", "Home Assistant entity for grid frequency."),
    ("p1", "Power L1", "Home Assistant entity for phase 1 active power."),
    ("p2", "Power L2", "Home Assistant entity for phase 2 active power."),
    ("p3", "Power L3", "Home Assistant entity for phase 3 active power."),
    ("e_import_total", "Imported energy", "Home Assistant entity for total imported energy."),
    ("e_export_total", "Exported energy", "Home Assistant entity for total exported energy."),
    ("pause", "Pause", "Home Assistant boolean entity (input_boolean, switch, binary_sensor). When on, all current and power values sent to the wallbox are forced to 0 so it neither charges nor discharges."),
    ("power_offset", "Power offset", "Home Assistant entity for power offset in watts (e.g. an input_number helper). Added to all power readings before they reach the charger. Negative = charger sees more export and ramps up. Leave empty to use the manual override in the dashboard instead."),
)

ENTITY_ENV_PREFIX = "HA_ENTITY_"
ENTITY_DEFAULTS = {
    "u1": "",
    "u2": "",
    "u3": "",
    "i1": "",
    "i2": "",
    "i3": "",
    "p_total": "",
    "freq": "",
    "p1": "",
    "p2": "",
    "p3": "",
    "e_import_total": "",
    "e_export_total": "",
    "pause": "",
    "power_offset": "",
}


def _entity_env_name(key: str) -> str:
    return f"{ENTITY_ENV_PREFIX}{key.upper()}"


def _load_entity_settings() -> dict[str, str]:
    return {
        key: _env_str(_entity_env_name(key), default)
        for key, default in ENTITY_DEFAULTS.items()
    }


def _is_valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and parsed.netloc)


HA_URL = _env_str("HA_URL", "")
HA_TOKEN = os.environ.get("HA_TOKEN", "")
SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")
HA_USE_SUPERVISOR = _env_bool("HA_USE_SUPERVISOR", bool(SUPERVISOR_TOKEN))

MODBUS_LISTEN_HOST = os.environ.get("MODBUS_LISTEN_HOST", "0.0.0.0")
MODBUS_LISTEN_PORT = _env_int("MODBUS_LISTEN_PORT", 502)
WEBAPP_HOST = _env_str("WEBAPP_HOST", "0.0.0.0")
WEBAPP_PORT = _env_int("WEBAPP_PORT", 8080)
WEBAPP_SSL_MODE = _env_choice(
    "WEBAPP_SSL_MODE",
    "off",
    {"off", "adhoc", "files"},
)
WEBAPP_SSL_CERT_FILE = _env_str("WEBAPP_SSL_CERT_FILE")
WEBAPP_SSL_KEY_FILE = _env_str("WEBAPP_SSL_KEY_FILE")

SLAVE_ID = 1

HA_POLL_SECONDS = 1.0
# Per-request timeout for a single Home Assistant state read. Every configured
# entity is fetched sequentially, so this bounds how long one slow or dead
# entity can delay the whole poll cycle.
HA_REQUEST_TIMEOUT_SECONDS = _env_float("HA_REQUEST_TIMEOUT_SECONDS", 3.0)
# How long live values may go without a successful refresh before the proxy
# flags them as stale. The charger load-balances on these numbers, so silently
# serving minute-old grid data is worse than saying so loudly.
HA_STALE_AFTER_SECONDS = _env_float("HA_STALE_AFTER_SECONDS", 30.0)
SOCKET_TIMEOUT = 2.0
MODBUS_IDLE_DISCONNECT_SECONDS = _env_float("MODBUS_IDLE_DISCONNECT_SECONDS", 10.0)
MODBUS_INITIAL_CONNECT_IDLE_SECONDS = _env_float("MODBUS_INITIAL_CONNECT_IDLE_SECONDS", 60.0)
POWER_OFFSET_WATTS: Optional[float] = _env_float_any("POWER_OFFSET_WATTS")
PHASE_ORDER = _env_str("PHASE_ORDER", "1,2,3")
MODBUS_TCP_KEEPALIVE_IDLE = _env_int("MODBUS_TCP_KEEPALIVE_IDLE", 5)
MODBUS_TCP_KEEPALIVE_INTERVAL = _env_int("MODBUS_TCP_KEEPALIVE_INTERVAL", 1)
MODBUS_TCP_KEEPALIVE_COUNT = _env_int("MODBUS_TCP_KEEPALIVE_COUNT", 3)
HA_VERIFY_TLS = _env_bool("HA_VERIFY_TLS", True)
MODBUS_TRANSPORT_MODE = _env_choice(
    "MODBUS_TRANSPORT_MODE",
    "modbus_tcp",
    {"rtu_over_tcp", "modbus_tcp"},
)
MODBUS_FLOAT_WORD_ORDER = _env_choice(
    "MODBUS_FLOAT_WORD_ORDER",
    "abcd",
    {"abcd", "cdab"},
)
MODBUS_REGISTER_ALIAS_MODE = _env_choice(
    "MODBUS_REGISTER_ALIAS_MODE",
    "exact",
    {"exact", "alias_minus_1", "alias_plus_1", "alias_both"},
)

ENTITIES = _load_entity_settings()


def get_ha_url() -> str:
    if HA_USE_SUPERVISOR and SUPERVISOR_TOKEN:
        return "http://supervisor/core/api"
    return HA_URL


def get_ha_api_base_url() -> str:
    base_url = get_ha_url().rstrip("/")
    if base_url.endswith("/api"):
        return base_url
    return f"{base_url}/api"


def get_ha_verify_tls() -> bool:
    if HA_USE_SUPERVISOR and SUPERVISOR_TOKEN:
        return False
    return HA_VERIFY_TLS


def get_ha_auth_token() -> str:
    if HA_USE_SUPERVISOR and SUPERVISOR_TOKEN:
        return SUPERVISOR_TOKEN
    return HA_TOKEN


def get_ha_auth_mode() -> str:
    if HA_USE_SUPERVISOR and SUPERVISOR_TOKEN:
        return "supervisor"
    if HA_TOKEN:
        return "manual_token"
    return "none"


def is_supervisor_ha_mode() -> bool:
    return get_ha_auth_mode() == "supervisor"


def has_ha_auth() -> bool:
    return bool(get_ha_auth_token())


def get_runtime_settings_store() -> str:
    return str(ENV_PATH)


def get_ha_entities() -> dict[str, str]:
    return ENTITIES.copy()


def get_ha_entity_fields() -> list[dict[str, str]]:
    return [
        {
            "key": key,
            "label": label,
            "help": help_text,
            "value": ENTITIES[key],
        }
        for key, label, help_text in ENTITY_FIELDS
    ]


def update_ha_live_data_settings(ha_url: str, verify_tls: bool, entities: dict[str, str]) -> bool:
    global HA_URL, HA_VERIFY_TLS

    if is_supervisor_ha_mode():
        normalized_url = HA_URL
        verify_tls = False
    else:
        normalized_url = ha_url.strip().rstrip("/")
        if not normalized_url or not _is_valid_url(normalized_url):
            raise ValueError("invalid Home Assistant URL")

    missing_keys = [key for key, _label, _help in ENTITY_FIELDS if key not in entities]
    if missing_keys:
        raise ValueError(f"missing entity keys: {', '.join(sorted(missing_keys))}")

    normalized_entities: dict[str, str] = {}
    for key, _label, _help in ENTITY_FIELDS:
        normalized_entities[key] = str(entities[key]).strip()

    changed = HA_URL != normalized_url or HA_VERIFY_TLS != verify_tls or any(
        ENTITIES.get(key) != value for key, value in normalized_entities.items()
    )

    HA_URL = normalized_url
    HA_VERIFY_TLS = verify_tls
    ENTITIES.clear()
    ENTITIES.update(normalized_entities)

    env_updates = {
        "HA_URL": HA_URL,
        "HA_VERIFY_TLS": "true" if HA_VERIFY_TLS else "false",
    }
    env_updates.update({
        _entity_env_name(key): value
        for key, value in normalized_entities.items()
    })
    save_env_settings(env_updates)
    return changed

DEFAULTS = {
    "u1": 230.0, "u2": 230.0, "u3": 230.0,
    "i1": 0.0, "i2": 0.0, "i3": 0.0,
    "p_total": 0.0, "freq": 50.0,
    "p1": 0.0, "p2": 0.0, "p3": 0.0,
    "e_import_total": 0.0, "e_export_total": 0.0,
    "power_offset": 0.0,
    "pause": 0.0,
}