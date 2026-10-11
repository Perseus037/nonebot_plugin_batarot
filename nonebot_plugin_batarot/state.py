from __future__ import annotations

import asyncio
import copy
import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Callable, Optional, TypeVar


class StateError(Exception):
    pass


_T = TypeVar("_T")
_MAX_INT = 2**63 - 1
_AI_STATUSES = {"pending", "completed", "failed", "disabled", "skipped"}
_TEXT_LIMITS = {
    "card_key": 128,
    "name": 256,
    "en_name": 256,
    "position": 64,
    "meaning": 16000,
    "image": 4096,
    "ai_status": 64,
    "ai_text": 32000,
}


def _integer(value: object, minimum: int, maximum: int) -> bool:
    return type(value) is int and minimum <= value <= maximum


def _day(value: object) -> None:
    try:
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
            raise ValueError
    except ValueError as exc:
        raise StateError("Invalid state date") from exc


def _user_key(value: object) -> None:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise StateError("Invalid user key")


def _record(value: object) -> None:
    if not isinstance(value, dict):
        raise StateError("Invalid fortune record")
    _day(value.get("date"))
    for key, limit in _TEXT_LIMITS.items():
        text = value.get(key)
        if not isinstance(text, str) or len(text) > limit:
            raise StateError("Invalid fortune field: " + key)
    if not value["card_key"] or not value["name"] or value["ai_status"] not in _AI_STATUSES:
        raise StateError("Incomplete fortune record")
    if not _integer(value.get("delta"), -5, 5):
        raise StateError("Lucky change must be an integer between -5 and 5")
    if not _integer(value.get("total"), -_MAX_INT, _MAX_INT):
        raise StateError("Invalid lucky total")


def _validate(state: object) -> None:
    if not isinstance(state, dict) or type(state.get("schema_version")) is not int:
        raise StateError("Invalid state schema")
    if state["schema_version"] != 1 or not isinstance(state.get("users"), dict):
        raise StateError("Unsupported state schema")
    for key, user in state["users"].items():
        _user_key(key)
        if not isinstance(user, dict):
            raise StateError("Invalid user state")
        if "luck_total" in user and not _integer(user["luck_total"], -_MAX_INT, _MAX_INT):
            raise StateError("Invalid lucky total")
        if "fortune" in user:
            _record(user["fortune"])
            if user.get("luck_total") != user["fortune"]["total"]:
                raise StateError("Inconsistent lucky total")
        if "ai_usage" in user:
            usage = user["ai_usage"]
            if not isinstance(usage, dict) or not _integer(usage.get("used"), 0, _MAX_INT):
                raise StateError("Invalid AI usage")
            _day(usage.get("date"))


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise StateError("Duplicate state field")
        result[key] = value
    return result


def _invalid_constant(value):
    raise StateError("Invalid JSON constant")


class StateStore:
    def __init__(self, path):
        self.path = Path(path)
        self._lock = asyncio.Lock()

    def _load(self) -> dict:
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                state = json.load(handle, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
        except FileNotFoundError:
            return {"schema_version": 1, "users": {}}
        except (OSError, ValueError, UnicodeError, RecursionError) as exc:
            raise StateError("Cannot read lucky-card state") from exc
        _validate(state)
        return state

    def _save(self, state: dict) -> None:
        _validate(state)
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary = tempfile.mkstemp(prefix=self.path.name + ".", suffix=".tmp", dir=self.path.parent)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(state, handle, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except (OSError, ValueError, TypeError) as exc:
            raise StateError("Cannot save lucky-card state") from exc
        finally:
            if temporary is not None:
                try:
                    os.unlink(temporary)
                except FileNotFoundError:
                    pass
                except OSError:
                    pass

    async def _transaction(self, action: Callable[[], _T]) -> _T:
        async with self._lock:
            task = asyncio.get_running_loop().run_in_executor(None, action)
            try:
                return await asyncio.shield(task)
            except asyncio.CancelledError:
                while not task.done():
                    try:
                        await asyncio.shield(task)
                    except asyncio.CancelledError:
                        continue
                    except Exception:
                        break
                if task.done() and not task.cancelled():
                    task.exception()
                raise

    async def get_or_draw(self, user_key: str, day: str, draw: Callable[[], dict], initial_luck: int) -> tuple[dict, bool]:
        _user_key(user_key)
        _day(day)
        if not _integer(initial_luck, -_MAX_INT, _MAX_INT):
            raise StateError("Invalid initial luck")

        def action():
            state = self._load()
            user = state["users"].setdefault(user_key, {})
            previous = user.get("fortune")
            if previous is not None and previous["date"] == day:
                return copy.deepcopy(previous), False
            record = copy.deepcopy(draw())
            if not isinstance(record, dict) or not _integer(record.get("delta"), -5, 5):
                raise StateError("Invalid fortune draw")
            record["date"] = day
            record["total"] = user.get("luck_total", initial_luck) + record["delta"]
            _record(record)
            user["luck_total"] = record["total"]
            user["fortune"] = record
            self._save(state)
            return copy.deepcopy(record), True

        return await self._transaction(action)

    async def complete_daily(self, user_key: str, day: str, ai_text: str, status: str) -> bool:
        _user_key(user_key)
        _day(day)
        if not isinstance(ai_text, str) or len(ai_text) > _TEXT_LIMITS["ai_text"]:
            raise StateError("Invalid AI interpretation")
        if not isinstance(status, str) or status not in _AI_STATUSES - {"pending"}:
            raise StateError("Invalid completed AI status")

        def action():
            state = self._load()
            record = state["users"].get(user_key, {}).get("fortune")
            if record is None or record["date"] != day or record["ai_status"] != "pending":
                return False
            record["ai_text"] = ai_text
            record["ai_status"] = status
            self._save(state)
            return True

        return await self._transaction(action)

    async def reserve_ai(self, user_key: str, day: str, limit: int) -> bool:
        _user_key(user_key)
        _day(day)
        if not _integer(limit, 0, _MAX_INT):
            raise StateError("Invalid daily AI limit")

        def action():
            state = self._load()
            user = state["users"].setdefault(user_key, {})
            usage = user.get("ai_usage", {})
            used = usage.get("used", 0) if usage.get("date") == day else 0
            if used >= limit:
                return False
            user["ai_usage"] = {"date": day, "used": used + 1}
            self._save(state)
            return True

        return await self._transaction(action)

    async def get_daily(self, user_key: str, day: str) -> Optional[dict]:
        _user_key(user_key)
        _day(day)

        def action():
            record = self._load()["users"].get(user_key, {}).get("fortune")
            if record is None or record["date"] != day:
                return None
            return copy.deepcopy(record)

        return await self._transaction(action)
