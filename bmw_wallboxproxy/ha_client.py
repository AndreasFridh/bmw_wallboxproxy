import time
from typing import Optional

import requests
import urllib3
from requests.adapters import HTTPAdapter

import config
from state import (
    get_ha_data_age_seconds,
    latest_values,
    log_net,
    mark_ha_update,
    set_ha_data_stale,
    state_lock,
    stats,
    stats_lock,
    stop_event,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Home Assistant states that carry no numeric value. They are normal (an entity
# restarting, a sensor briefly offline) and must not be logged as read errors,
# otherwise the real failures drown in noise.
NON_NUMERIC_STATES = {"unavailable", "unknown", "none", "null", ""}

BOOL_STATES = {"on": 1.0, "true": 1.0, "off": 0.0, "false": 0.0}

# One pooled session for every entity read. Without it each poll cycle opened a
# fresh TCP connection per entity — at one cycle per second that is well over a
# million short-lived sockets a day, all sitting in TIME_WAIT.
_session = requests.Session()
_session.mount("http://", HTTPAdapter(pool_connections=2, pool_maxsize=4))
_session.mount("https://", HTTPAdapter(pool_connections=2, pool_maxsize=4))


def read_ha_state(entity_id: str) -> Optional[float]:
    if not entity_id:
        return None

    auth_token = config.get_ha_auth_token()
    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
    url = f"{config.get_ha_api_base_url()}/states/{entity_id}"
    try:
        r = _session.get(
            url,
            headers=headers,
            timeout=config.HA_REQUEST_TIMEOUT_SECONDS,
            verify=config.get_ha_verify_tls(),
        )
        r.raise_for_status()
        raw = r.json().get("state", "")
    except Exception as e:
        with stats_lock:
            stats["ha_reads_fail"] += 1
        log_net(f"HA read error: {entity_id} -> {e}")
        return None

    if str(raw).strip().lower() in NON_NUMERIC_STATES:
        with stats_lock:
            stats["ha_entities_unavailable"] += 1
        return None

    text = str(raw).strip().lower()
    if text in BOOL_STATES:
        with stats_lock:
            stats["ha_reads_ok"] += 1
        return BOOL_STATES[text]

    try:
        value = float(raw)
    except (TypeError, ValueError):
        with stats_lock:
            stats["ha_reads_fail"] += 1
        log_net(f"HA read error: {entity_id} -> non-numeric state {raw!r}")
        return None

    with stats_lock:
        stats["ha_reads_ok"] += 1
    return value


def _publish_data_age(previously_stale: bool) -> bool:
    """Refresh the exposed data age and log stale/recovered transitions once."""
    age = get_ha_data_age_seconds()
    with stats_lock:
        stats["ha_data_age_seconds"] = None if age is None else round(age, 1)

    limit = config.HA_STALE_AFTER_SECONDS
    if limit <= 0:
        return False

    stale = age is None or age >= limit
    if stale and not previously_stale:
        set_ha_data_stale(True)
        log_net(
            "HA live data is STALE: the charger is being served the last known "
            f"values, unrefreshed for {'ever' if age is None else f'{age:.0f}s'}"
        )
    elif not stale and previously_stale:
        set_ha_data_stale(False)
        log_net("HA live data recovered, values are fresh again")
    return stale


def ha_poller() -> None:
    log_net(
        "HA poller starting "
        f"url={config.get_ha_api_base_url()} "
        f"tls_verify={config.get_ha_verify_tls()} "
        f"auth_mode={config.get_ha_auth_mode()} "
        f"request_timeout={config.HA_REQUEST_TIMEOUT_SECONDS}s "
        f"stale_after={config.HA_STALE_AFTER_SECONDS}s"
    )

    if not config.has_ha_auth():
        log_net("HA startup error: no Home Assistant authentication is available")
        raise RuntimeError("No Home Assistant authentication is available.")

    stale = False

    while not stop_event.is_set():
        cycle_started = time.monotonic()
        updates = {}
        for key, entity in config.get_ha_entities().items():
            if stop_event.is_set():
                return
            if not entity:
                continue
            value = read_ha_state(entity)
            if value is not None:
                updates[key] = value

        cycle_seconds = time.monotonic() - cycle_started

        if updates:
            with state_lock:
                latest_values.update(updates)
            mark_ha_update(cycle_seconds)
        else:
            with stats_lock:
                stats["ha_poll_cycle_seconds"] = round(cycle_seconds, 3)

        stale = _publish_data_age(stale)

        # Keep a fixed cadence instead of adding a full interval on top of a
        # slow cycle, so a sluggish Home Assistant does not silently stretch
        # the refresh rate the charger depends on.
        stop_event.wait(max(0.0, config.HA_POLL_SECONDS - cycle_seconds))
