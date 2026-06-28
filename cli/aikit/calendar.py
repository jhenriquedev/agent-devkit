"""Calendar MVP backed by local ICS files."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from cli.aikit.app_home import config_path, ensure_app_home
from cli.aikit.llm import load_config, save_config


DATE_COMPACT = "%Y%m%d"
DATETIME_COMPACT = "%Y%m%dT%H%M%S"


def configure_calendar(*, ics_path: str | None = None, timezone: str | None = None) -> dict[str, Any]:
    if not ics_path:
        return calendar_needs_input()
    path = Path(ics_path).expanduser().resolve()
    if not path.exists():
        raise ValueError(f"calendar ics file not found: {ics_path}")
    config = load_config()
    calendar = config.setdefault("calendar", {})
    calendar["provider"] = "ics"
    calendar["source_ref"] = str(path)
    if timezone:
        calendar["timezone"] = timezone
    written = save_config(config)
    return {
        "kind": "calendar-configure",
        "status": "configured",
        "provider": "ics",
        "source_ref": str(path),
        "timezone": timezone,
        "config_path": str(written),
        "stored_secret": False,
    }


def calendar_today() -> dict[str, Any]:
    today = date.today()
    return calendar_list(today.isoformat(), today.isoformat(), label="today")


def calendar_tomorrow() -> dict[str, Any]:
    tomorrow = date.today() + timedelta(days=1)
    return calendar_list(tomorrow.isoformat(), tomorrow.isoformat(), label="tomorrow")


def calendar_list(date_from: str | None, date_to: str | None, *, label: str | None = None) -> dict[str, Any]:
    config = load_config()
    calendar = config.get("calendar") if isinstance(config.get("calendar"), dict) else {}
    if calendar.get("provider") != "ics" or not calendar.get("source_ref"):
        return calendar_needs_input()
    start = parse_date(date_from) if date_from else date.today()
    end = parse_date(date_to) if date_to else start
    events = [
        event
        for event in parse_ics(Path(str(calendar["source_ref"])))
        if event_overlaps(event, start, end)
    ]
    events.sort(key=lambda item: item.get("start") or "")
    return {
        "kind": "calendar",
        "status": "ok",
        "label": label,
        "provider": "ics",
        "source_ref": str(calendar["source_ref"]),
        "from": start.isoformat(),
        "to": end.isoformat(),
        "events": events,
        "count": len(events),
        "sensitive": True,
        "llm_safe": False,
    }


def calendar_needs_input() -> dict[str, Any]:
    ensure_app_home()
    return {
        "kind": "calendar",
        "status": "needs-input",
        "ok": False,
        "requires_provider": True,
        "config_path": str(config_path()),
        "message": "Calendar provider is not configured.",
        "next_steps": [
            "Configure a local ICS file with `agent calendar configure --ics <path>`.",
            "Then run `agent calendar today` or ask `agent qual minha agenda de hoje?`.",
        ],
        "exit_code": 2,
    }


def parse_ics(path: Path) -> list[dict[str, Any]]:
    text = unfold_ics(path.read_text(encoding="utf-8"))
    events: list[dict[str, Any]] = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.DOTALL):
        fields: dict[str, str] = {}
        for raw_line in block.splitlines():
            if ":" not in raw_line:
                continue
            key, value = raw_line.split(":", 1)
            key = key.split(";", 1)[0].upper()
            fields[key] = value.strip()
        start = parse_ics_datetime(fields.get("DTSTART"))
        end = parse_ics_datetime(fields.get("DTEND"))
        events.append(
            {
                "uid": fields.get("UID"),
                "summary": fields.get("SUMMARY") or "(sem titulo)",
                "description": fields.get("DESCRIPTION"),
                "location": fields.get("LOCATION"),
                "start": start.isoformat() if start else None,
                "end": end.isoformat() if end else None,
                "all_day": bool(start and isinstance(start, date) and not isinstance(start, datetime)),
            }
        )
    return events


def unfold_ics(text: str) -> str:
    return re.sub(r"\r?\n[ \t]", "", text)


def parse_ics_datetime(value: str | None) -> date | datetime | None:
    if not value:
        return None
    value = value.rstrip("Z")
    for fmt in (DATETIME_COMPACT, DATE_COMPACT):
        try:
            parsed = datetime.strptime(value, fmt)
        except ValueError:
            continue
        return parsed.date() if fmt == DATE_COMPACT else parsed
    return None


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def event_overlaps(event: dict[str, Any], start: date, end: date) -> bool:
    raw_start = event.get("start")
    if not raw_start:
        return False
    event_date = datetime.fromisoformat(raw_start).date() if "T" in raw_start else date.fromisoformat(raw_start)
    return start <= event_date <= end


def calendar_summary(payload: dict[str, Any]) -> str:
    if payload.get("status") != "ok":
        return str(payload.get("message") or "")
    if not payload.get("events"):
        return "Nenhum compromisso encontrado no periodo."
    lines = []
    for item in payload["events"]:
        start = item.get("start") or "-"
        summary = item.get("summary") or "-"
        lines.append(f"- {start}: {summary}")
    return "\n".join(lines)
