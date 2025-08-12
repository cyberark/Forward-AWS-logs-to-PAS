import json
from typing import Any, Dict, Optional, Tuple


def _g(obj: Dict[str, Any], path: str, *, default: Any = None) -> Any:
    cur: Any = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def _pick_event_time(ev: Dict[str, Any]) -> Optional[str]:
    return _g(ev, "detail.eventTime") or ev.get("time")


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
            parts.append(
                "wrong types: " + ", ".join(f"{p}={t}" for p, t in wrong_type)
            )
        return False, "; ".join(parts)
    return True, ""


def _detect_builder(ev: Dict[str, Any]) -> str:
    event_name = _g(ev, "detail.eventName")
    console_login = _g(ev, "detail.responseElements.ConsoleLogin")
    access_key_id = _g(ev, "detail.userIdentity.accessKeyId")

    if event_name == "ConsoleLogin" and isinstance(console_login, str):
        return "password"
    if isinstance(access_key_id, str) and access_key_id.strip():
        return "access_key"
    raise ValueError("Unsupported event type for these builders")


def map_event_to_java_source(event: Dict[str, Any]) -> Dict[str, Any]:
    builder_type = _detect_builder(event)

    event_time = _pick_event_time(event)
    mapped: Dict[str, Any] = {
        "eventTime": event_time,
        "eventSource": _g(event, "detail.eventSource"),
        "eventName": _g(event, "detail.eventName"),
        "sourceIPAddress": _g(event, "detail.sourceIPAddress"),
        "eventID": _g(event, "detail.eventID"),
        "userIdentity": {
            "accountId": _g(event, "detail.userIdentity.accountId"),
            "userName": _g(event, "detail.userIdentity.userName"),
            "accessKeyId": _g(event, "detail.userIdentity.accessKeyId"),
        },
        "responseElements": {
            "ConsoleLogin": _g(event, "detail.responseElements.ConsoleLogin")
        },
    }

    if builder_type == "access_key":
        mapped.pop("responseElements", None)
    else:
        if "userIdentity" in mapped and isinstance(mapped["userIdentity"], dict):
            mapped["userIdentity"].pop("accessKeyId", None)

    if builder_type == "access_key":
        ok, err = _require_strings(
            mapped,
            (
                "eventTime",
                "userIdentity.accountId",
                "userIdentity.accessKeyId",
                "userIdentity.userName",
            ),
        )
    else:
        ok, err = _require_strings(
            mapped,
            (
                "eventTime",
                "userIdentity.accountId",
                "userIdentity.userName",
                "eventName",
                "responseElements.ConsoleLogin",
            ),
        )
        if ok and mapped.get("eventName") != "ConsoleLogin":
            ok, err = False, "eventName must be 'ConsoleLogin' for the password builder"

    if not ok:
        raise ValueError(f"Mandatory field validation failed: {err}")

    return mapped


def normalize_aws_syslog(syslog: str | Dict[str, Any]) -> Dict[str, Any]:
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
