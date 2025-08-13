from __future__ import annotations
import json
from typing import Any, Dict, Tuple, Union

# ---------- Flexible getter ----------
def _g(obj: Dict[str, Any], path: str, *, default: Any = None) -> Any:
    cur: Any = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur

# ---------- Field getters ----------
def _get_event_name(ev): return _g(ev, "detail.eventName") or ev.get("eventName")
def _get_console_login(ev): return _g(ev, "detail.responseElements.ConsoleLogin") or _g(ev, "responseElements.ConsoleLogin")
def _get_access_key_id(ev): return _g(ev, "detail.userIdentity.accessKeyId") or _g(ev, "userIdentity.accessKeyId")
def _get_account_id(ev): return _g(ev, "detail.userIdentity.accountId") or _g(ev, "userIdentity.accountId")
def _get_user_name(ev): return _g(ev, "detail.userIdentity.userName") or _g(ev, "userIdentity.userName")
def _get_user_type(ev): return _g(ev, "detail.userIdentity.type") or _g(ev, "userIdentity.type")
def _get_event_time(ev): return _g(ev, "detail.eventTime") or ev.get("eventTime") or ev.get("time")
def _get_event_source(ev): return _g(ev, "detail.eventSource") or ev.get("eventSource")
def _get_source_ip(ev): return _g(ev, "detail.sourceIPAddress") or ev.get("sourceIPAddress")
def _get_event_id(ev): return _g(ev, "detail.eventID") or ev.get("eventID")

# ---------- Validation ----------
def _require_strings(payload: Dict[str, Any], paths: Tuple[str, ...]) -> Tuple[bool, str]:
    missing = []
    wrong_type = []
    for p in paths:
        val = _g(payload, p)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            missing.append(p)
        elif not isinstance(val, str):
            wrong_type.append((p, type(val).__name__))
    if missing or wrong_type:
        parts = []
        if missing:
            parts.append(f"missing: {', '.join(missing)}")
        if wrong_type:
            parts.append("wrong types: " + ", ".join(f"{p}={t}" for p, t in wrong_type))
        return False, "; ".join(parts)
    return True, ""

# ---------- Builder detection ----------
def _detect_builder(ev: Dict[str, Any]) -> str:
    event_name = _get_event_name(ev)
    console_login = _get_console_login(ev)
    access_key_id = _get_access_key_id(ev)

    if event_name == "ConsoleLogin" and isinstance(console_login, str):
        return "password"
    if isinstance(access_key_id, str) and access_key_id.strip():
        return "access_key"
    raise ValueError("Unsupported event type for these builders")

# ---------- Mapping ----------
def map_event_to_java_source(event: Dict[str, Any]) -> Dict[str, Any]:
    builder_type = _detect_builder(event)

    mapped: Dict[str, Any] = {
        "eventTime": _get_event_time(event),
        "eventSource": _get_event_source(event),
        "eventName": _get_event_name(event),
        "sourceIPAddress": _get_source_ip(event),
        "eventID": _get_event_id(event),
        "userIdentity": {
            "type": _get_user_type(event),  # <-- added
            "accountId": _get_account_id(event),
            "userName": _get_user_name(event),
            "accessKeyId": _get_access_key_id(event),
        },
        "responseElements": {
            "ConsoleLogin": _get_console_login(event)
        },
    }

    # Remove fields based on builder type
    if builder_type == "access_key":
        mapped.pop("responseElements", None)
    else:
        if "userIdentity" in mapped and isinstance(mapped["userIdentity"], dict):
            mapped["userIdentity"].pop("accessKeyId", None)

    # Validation
    if builder_type == "access_key":
        ok, err = _require_strings(
            mapped,
            (
                "eventTime",
                "userIdentity.accountId",
                "userIdentity.accessKeyId",
                "userIdentity.userName",
                "userIdentity.type",  # validate type too
            ),
        )
    else:
        ok, err = _require_strings(
            mapped,
            (
                "eventTime",
                "userIdentity.accountId",
                "userIdentity.userName",
                "userIdentity.type",  # validate type too
                "eventName",
                "responseElements.ConsoleLogin",
            ),
        )
        if ok and mapped.get("eventName") != "ConsoleLogin":
            ok, err = False, "eventName must be 'ConsoleLogin' for the password builder"

    if not ok:
        raise ValueError(f"Mandatory field validation failed: {err}")

    return mapped

# ---------- Normalization entry point ----------
def normalize_aws_syslog(syslog: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(syslog, str):
        try:
            event = json.loads(syslog)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}") from e
    elif isinstance(syslog, dict):
        event = syslog
    else:
        raise ValueError("syslog must be a JSON string or dict")
    return map_event_to_java_source(event)
