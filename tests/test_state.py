import asyncio
import importlib.util
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "nonebot_plugin_batarot" / "state.py"
SPEC = importlib.util.spec_from_file_location("batarot_state_test", MODULE_PATH)
state_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(state_module)
StateStore = state_module.StateStore
StateError = state_module.StateError


def draw(delta=3, status="pending"):
    return {
        "card_key": "0",
        "name": "愚者",
        "en_name": "The Fool",
        "position": "逆位" if isinstance(delta, (int, float)) and delta < 0 else "正位",
        "meaning": "新的起点",
        "image": "image/0.png",
        "delta": delta,
        "ai_status": status,
        "ai_text": "",
    }


class StateTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "nested" / "state.json"
        self.store = StateStore(self.path)
        self.day = "2026-10-11"

    async def test_concurrent_draw_is_recorded_once(self):
        calls = []

        def counted():
            calls.append(True)
            return draw()

        results = await asyncio.gather(*[
            self.store.get_or_draw("u", self.day, counted, 10) for _ in range(30)
        ])
        self.assertEqual(len(calls), 1)
        self.assertEqual(sum(fresh for _, fresh in results), 1)
        self.assertTrue(all(record["total"] == 13 for record, _ in results))

    async def test_restart_reuses_record_and_interpretation(self):
        await self.store.get_or_draw("u", self.day, draw, 10)
        self.assertTrue(await self.store.complete_daily("u", self.day, "今天适合迈出第一步。", "completed"))
        store = StateStore(self.path)
        with patch.object(store, "_save", side_effect=AssertionError("Unexpected save")):
            record, fresh = await store.get_or_draw("u", self.day, lambda: self.fail("Unexpected draw"), 99)
        self.assertFalse(fresh)
        self.assertEqual(record["total"], 13)
        self.assertEqual(record["ai_text"], "今天适合迈出第一步。")

    async def test_many_users_do_not_overwrite_each_other(self):
        await asyncio.gather(*[
            self.store.get_or_draw(str(i), self.day, draw, 10) for i in range(50)
        ])
        users = json.loads(self.path.read_text(encoding="utf-8"))["users"]
        self.assertEqual(len(users), 50)
        self.assertTrue(all(user["luck_total"] == 13 for user in users.values()))

    async def test_day_change_accumulates_and_replaces_record(self):
        await self.store.get_or_draw("u", self.day, lambda: draw(-5), 10)
        record, fresh = await self.store.get_or_draw("u", "2026-10-12", lambda: draw(-5), 999)
        self.assertTrue(fresh)
        self.assertEqual(record["total"], 0)
        self.assertIsNone(await self.store.get_daily("u", self.day))
        record, _ = await self.store.get_or_draw("u", "2026-10-13", lambda: draw(-3), 10)
        self.assertEqual(record["total"], -3)
        user = json.loads(self.path.read_text(encoding="utf-8"))["users"]["u"]
        self.assertEqual(set(user), {"luck_total", "fortune"})
        self.assertEqual(user["fortune"]["date"], "2026-10-13")

    async def test_quota_fourth_request_denied_and_day_reset(self):
        results = [await self.store.reserve_ai("u", self.day, 3) for _ in range(4)]
        self.assertEqual(results, [True, True, True, False])
        self.assertFalse(await StateStore(self.path).reserve_ai("u", self.day, 3))
        self.assertTrue(await self.store.reserve_ai("u", "2026-10-12", 3))
        user = json.loads(self.path.read_text(encoding="utf-8"))["users"]["u"]
        self.assertEqual(user["ai_usage"], {"date": "2026-10-12", "used": 1})
        self.assertNotIn("luck_total", user)

    async def test_concurrent_quota_reservations_are_atomic(self):
        results = await asyncio.gather(*[
            self.store.reserve_ai("u", self.day, 3) for _ in range(30)
        ])
        self.assertEqual(sum(results), 3)

    async def test_same_user_in_two_groups_has_independent_state(self):
        first = "group:111:user:999"
        second = "group:222:user:999"
        a, _ = await self.store.get_or_draw(first, self.day, lambda: draw(5), 10)
        b, fresh = await self.store.get_or_draw(second, self.day, lambda: draw(-5), 10)
        self.assertTrue(fresh)
        self.assertEqual((a["total"], b["total"]), (15, 5))
        for _ in range(3):
            self.assertTrue(await self.store.reserve_ai(first, self.day, 3))
        self.assertFalse(await self.store.reserve_ai(first, self.day, 3))
        self.assertTrue(await self.store.reserve_ai(second, self.day, 3))
        await self.store.complete_daily(first, self.day, "甲群解读", "completed")
        self.assertEqual((await self.store.get_daily(second, self.day))["ai_text"], "")

    async def test_zero_quota_does_not_create_file(self):
        self.assertFalse(await self.store.reserve_ai("u", self.day, 0))
        self.assertFalse(self.path.exists())

    async def test_ai_only_user_takes_initial_luck_on_first_draw(self):
        await self.store.reserve_ai("u", self.day, 3)
        record, _ = await self.store.get_or_draw("u", self.day, draw, 25)
        self.assertEqual(record["total"], 28)
        user = json.loads(self.path.read_text(encoding="utf-8"))["users"]["u"]
        self.assertEqual(user["ai_usage"]["used"], 1)

    async def test_daily_draw_does_not_consume_divination_quota(self):
        await self.store.get_or_draw("u", self.day, draw, 10)
        await self.store.complete_daily("u", self.day, "解读", "completed")
        for _ in range(3):
            self.assertTrue(await self.store.reserve_ai("u", self.day, 3))
        self.assertFalse(await self.store.reserve_ai("u", self.day, 3))
        self.assertEqual((await self.store.get_daily("u", self.day))["ai_text"], "解读")

    async def test_old_completion_cannot_overwrite_new_day(self):
        await self.store.get_or_draw("u", self.day, draw, 10)
        await self.store.get_or_draw("u", "2026-10-12", lambda: draw(-2), 10)
        self.assertFalse(await self.store.complete_daily("u", self.day, "旧解读", "completed"))
        record = await self.store.get_daily("u", "2026-10-12")
        self.assertEqual(record["ai_text"], "")
        self.assertEqual(record["total"], 11)
        self.assertTrue(await self.store.complete_daily("u", "2026-10-12", "新解读", "completed"))
        self.assertFalse(await self.store.complete_daily("u", "2026-10-12", "覆盖解读", "completed"))
        self.assertEqual((await self.store.get_daily("u", "2026-10-12"))["ai_text"], "新解读")

    async def test_missing_daily_read_does_not_create_file(self):
        self.assertIsNone(await self.store.get_daily("u", self.day))
        self.assertFalse(await self.store.complete_daily("u", self.day, "解释", "completed"))
        self.assertFalse(self.path.exists())

    async def test_invalid_files_fail_closed(self):
        self.path.parent.mkdir()
        for content in (
            "{broken",
            '{"schema_version":2,"users":{}}',
            '{"schema_version":true,"users":{}}',
            '{"schema_version":1,"users":[]}',
            '{"schema_version":1,"schema_version":1,"users":{}}',
            '{"schema_version":1,"users":{"u":{"luck_total":NaN}}}',
            '{"schema_version":1,"users":{"u":{"ai_usage":{"date":"today","used":2}}}}',
        ):
            with self.subTest(content=content):
                self.path.write_text(content, encoding="utf-8")
                before = self.path.read_bytes()
                with self.assertRaises(StateError):
                    await self.store.get_or_draw("u", self.day, draw, 10)
                with self.assertRaises(StateError):
                    await self.store.reserve_ai("u", self.day, 3)
                self.assertEqual(self.path.read_bytes(), before)

    async def test_atomic_replace_failure_keeps_original(self):
        await self.store.get_or_draw("u", self.day, draw, 10)
        before = self.path.read_bytes()
        with patch.object(state_module.os, "replace", side_effect=OSError("denied")):
            with self.assertRaises(StateError):
                await self.store.get_or_draw("u", "2026-10-12", draw, 10)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])
        record, fresh = await self.store.get_or_draw("u", "2026-10-12", draw, 10)
        self.assertTrue(fresh)
        self.assertEqual(record["total"], 16)

    async def test_fsync_failure_keeps_original(self):
        await self.store.get_or_draw("u", self.day, draw, 10)
        before = self.path.read_bytes()
        with patch.object(state_module.os, "fsync", side_effect=OSError("disk full")):
            with self.assertRaises(StateError):
                await self.store.reserve_ai("u", self.day, 3)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    async def test_invalid_draws_do_not_write(self):
        for delta in (-6, 6, True, 2.5, "2"):
            with self.subTest(delta=delta), self.assertRaises(StateError):
                await self.store.get_or_draw("u", self.day, lambda: draw(delta), 10)
        with self.assertRaises(StateError):
            await self.store.get_or_draw("u", self.day, lambda: {}, 10)
        self.assertFalse(self.path.exists())

    async def test_delta_boundaries_and_zero(self):
        for delta in (-5, 0, 5):
            record, _ = await self.store.get_or_draw(str(delta), self.day, lambda: draw(delta), 10)
            self.assertEqual(record["delta"], delta)
            self.assertEqual(record["total"], 10 + delta)

    async def test_returned_records_cannot_mutate_saved_state(self):
        record, _ = await self.store.get_or_draw("u", self.day, draw, 10)
        record["total"] = -999
        self.assertEqual((await self.store.get_daily("u", self.day))["total"], 13)

    async def test_cancellation_holds_lock_until_write_finishes(self):
        started = threading.Event()
        release = threading.Event()
        self.addCleanup(release.set)
        calls = []

        def delayed():
            calls.append(True)
            started.set()
            if not release.wait(5):
                raise RuntimeError("Test release timed out")
            return draw()

        first = asyncio.create_task(self.store.get_or_draw("u", self.day, delayed, 10))
        while not started.is_set():
            await asyncio.sleep(0.001)
        first.cancel()
        await asyncio.sleep(0)
        second = asyncio.create_task(self.store.get_or_draw("u", self.day, draw, 10))
        first.cancel()
        await asyncio.sleep(0.03)
        self.assertFalse(first.done())
        self.assertFalse(second.done())
        release.set()
        with self.assertRaises(asyncio.CancelledError):
            await first
        record, fresh = await second
        self.assertFalse(fresh)
        self.assertEqual(record["total"], 13)
        self.assertEqual(len(calls), 1)

    async def test_bad_parameters_are_rejected(self):
        for key, day in (("", self.day), ("u", "2026-02-30"), ("u", "20261011")):
            with self.subTest(key=key, day=day), self.assertRaises(StateError):
                await self.store.get_daily(key, day)
        for limit in (-1, True, 1.5):
            with self.subTest(limit=limit), self.assertRaises(StateError):
                await self.store.reserve_ai("u", self.day, limit)
        with self.assertRaises(StateError):
            await self.store.complete_daily("u", self.day, "", "pending")


if __name__ == "__main__":
    unittest.main()
