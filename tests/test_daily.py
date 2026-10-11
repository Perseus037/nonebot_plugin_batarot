import asyncio
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from test_batarot import Message, group_event, invoke, settings
from nonebot_plugin_batarot import handler, llm
from nonebot_plugin_batarot.config import Config, config


class DailyFortuneTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name, "state.json")
        self.options = settings(
            batarot_data_file=self.path,
            batarot_llm_enabled=True,
            batarot_llm_api_key="test-only-key",
            batarot_llm_model="test-model",
            batarot_llm_cooldown=0,
            batarot_llm_max_concurrency=2,
            batarot_llm_daily_limit=3,
            batarot_initial_luck=10,
            batarot_luck_min=-5,
            batarot_luck_max=5,
        )
        self.options.__enter__()
        handler._state_store = None
        handler._fortune_tasks.clear()
        handler._llm_inflight.clear()
        handler._llm_last_used.clear()
        self.real_draw = handler._draw_lucky_card
        self.real_text = handler.Text
        self.patchers = [
            patch.object(handler, "_today", return_value="2026-10-11"),
            patch.object(handler, "_draw_lucky_card", side_effect=self.record),
            patch.object(handler, "generate_reading", new=AsyncMock(return_value="固定的首次解读")),
            patch.object(handler.MessageFactory, "send", new=AsyncMock()),
            patch.object(handler, "load_image_as_bytes", new=AsyncMock(return_value=None)),
            patch.object(handler, "Text", side_effect=self.real_text),
        ]
        (self.today, self.draw, self.generate, self.send,
         self.image, self.text) = [patcher.start() for patcher in self.patchers]

    async def asyncTearDown(self):
        tasks = list(handler._fortune_tasks.values())
        for task in tasks:
            if not task.done():
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        handler._fortune_tasks.clear()
        handler._llm_inflight.clear()
        handler._llm_last_used.clear()
        handler._state_store = None
        for patcher in reversed(self.patchers):
            patcher.stop()
        self.options.__exit__(None, None, None)
        self.temporary.cleanup()

    def record(self, delta=2, position="up"):
        return {
            "card_key": "0", "name": "愚者", "en_name": "The Fool",
            "position": position, "meaning": "勇于开始", "image": "",
            "delta": delta, "ai_status": "pending" if config.batarot_llm_enabled else "disabled",
            "ai_text": "",
        }

    def event(self, group_id=12345, user_id=111):
        event = group_event()
        event.group_id = group_id
        event.user_id = user_id
        return event

    async def fortune(self, event=None, question=""):
        await invoke(handler.handle_daily_fortune, event=event or self.event(), args=Message(question))

    def user_state(self, event=None):
        if not self.path.exists():
            return {}
        state = json.loads(self.path.read_text(encoding="utf-8"))
        return state["users"].get(handler._user_key(event or self.event()), {})

    async def test_repeated_daily_queries_draw_add_luck_and_call_ai_once(self):
        for question in ("最初的问题", "另一个问题", "再次查询"):
            await self.fortune(question=question)
        self.draw.assert_called_once()
        self.generate.assert_awaited_once()
        self.assertEqual(self.send.await_count, 3)
        record = self.user_state()["fortune"]
        self.assertEqual((record["delta"], record["total"]), (2, 12))
        self.assertEqual(record["ai_status"], "completed")
        self.assertIn("固定的首次解读", record["ai_text"])
        self.assertIn("最初的问题", self.generate.call_args.args[0])
        self.assertNotIn("另一个问题", self.generate.call_args.args[0])
        shown = [call.args[0] for call in self.text.call_args_list]
        self.assertEqual(sum("今天已经抽取过" in text for text in shown), 2)
        self.assertEqual(sum("固定的首次解读" in text for text in shown), 3)

    async def test_same_user_in_different_groups_has_independent_first_draws(self):
        first, second = self.event(12345), self.event(67890)
        await self.fortune(first)
        await self.fortune(second)
        self.assertNotEqual(handler._user_key(first), handler._user_key(second))
        self.assertEqual(self.generate.await_count, 2)
        self.assertEqual(self.draw.call_count, 2)
        self.assertEqual(self.user_state(first)["luck_total"], 12)
        self.assertEqual(self.user_state(second)["luck_total"], 12)

    async def test_next_day_adds_to_total_and_can_generate_again(self):
        await self.fortune()
        self.today.return_value = "2026-10-12"
        self.draw.side_effect = lambda: self.record(delta=-3, position="down")
        await self.fortune()
        state = self.user_state()
        self.assertEqual(state["luck_total"], 9)
        self.assertEqual(state["fortune"]["date"], "2026-10-12")
        self.assertEqual(state["fortune"]["delta"], -3)
        self.assertEqual(self.generate.await_count, 2)

    async def test_new_state_object_reuses_file_without_drawing_or_requesting_ai(self):
        await self.fortune()
        original = self.user_state()
        handler._state_store = None
        handler._llm_last_used.clear()
        handler._fortune_tasks.clear()
        await self.fortune()
        self.assertEqual(self.user_state(), original)
        self.draw.assert_called_once()
        self.generate.assert_awaited_once()

    async def test_simultaneous_daily_queries_share_one_task(self):
        started, release = asyncio.Event(), asyncio.Event()

        async def slow(*args):
            started.set()
            await release.wait()
            return "并发共享解读"

        self.generate.side_effect = slow
        first = asyncio.create_task(self.fortune())
        followers = []
        try:
            await asyncio.wait_for(started.wait(), 1)
            followers = [asyncio.create_task(self.fortune()) for _ in range(2)]
            await asyncio.sleep(0)
            self.assertEqual(len(handler._fortune_tasks), 1)
            release.set()
            await asyncio.gather(first, *followers)
        finally:
            release.set()
            await asyncio.gather(first, *followers, return_exceptions=True)
        self.draw.assert_called_once()
        self.generate.assert_awaited_once()
        self.assertEqual(self.send.await_count, 3)
        self.assertEqual(self.user_state()["luck_total"], 12)

    async def test_send_failure_keeps_complete_record_for_retry(self):
        self.send.side_effect = [RuntimeError("simulated send failure"), None]
        with self.assertRaises(RuntimeError):
            await self.fortune()
        await self.fortune()
        self.draw.assert_called_once()
        self.generate.assert_awaited_once()
        self.assertEqual(self.user_state()["fortune"]["ai_status"], "completed")

    async def test_model_failure_is_saved_and_not_retried(self):
        self.generate.side_effect = llm.LLMError("simulated failure")
        await self.fortune()
        await self.fortune()
        self.generate.assert_awaited_once()
        self.draw.assert_called_once()
        record = self.user_state()["fortune"]
        self.assertEqual(record["ai_status"], "failed")
        self.assertIn("simulated failure", record["ai_text"])
        self.assertEqual(record["total"], 12)

    async def test_cancelled_handler_does_not_cancel_shared_generation(self):
        started, release = asyncio.Event(), asyncio.Event()

        async def slow(*args):
            started.set()
            await release.wait()
            return "取消后仍保存"

        self.generate.side_effect = slow
        first = asyncio.create_task(self.fortune())
        try:
            await asyncio.wait_for(started.wait(), 1)
            background = next(iter(handler._fortune_tasks.values()))
            first.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await first
            self.assertFalse(background.done())
            release.set()
            await asyncio.wait_for(background, 1)
            await self.fortune()
        finally:
            release.set()
            await asyncio.gather(first, return_exceptions=True)
        self.generate.assert_awaited_once()
        self.assertEqual(self.user_state()["fortune"]["ai_status"], "completed")
        self.assertIn("取消后仍保存", self.user_state()["fortune"]["ai_text"])

    async def test_cancelled_background_generation_preserves_card_and_failure(self):
        started = asyncio.Event()

        async def slow(*args):
            started.set()
            await asyncio.Event().wait()

        self.generate.side_effect = slow
        first = asyncio.create_task(self.fortune())
        try:
            await asyncio.wait_for(started.wait(), 1)
            background = next(iter(handler._fortune_tasks.values()))
            background.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await first
            await self.fortune()
        finally:
            if not first.done():
                first.cancel()
            await asyncio.gather(first, return_exceptions=True)
        self.generate.assert_awaited_once()
        self.assertEqual(self.user_state()["fortune"]["ai_status"], "failed")
        self.assertEqual(self.user_state()["luck_total"], 12)

    async def test_daily_ai_does_not_spend_regular_quota(self):
        await self.fortune()
        self.assertNotIn("ai_usage", self.user_state())
        for _ in range(3):
            self.assertIn("固定的首次解读", await handler._request_ai_text(self.event(), "ordinary"))
        self.assertIn("额度已用完", await handler._request_ai_text(self.event(), "fourth"))
        self.assertEqual(self.generate.await_count, 4)
        self.assertEqual(self.user_state()["ai_usage"]["used"], 3)

    async def test_regular_quota_is_independent_per_group(self):
        for group in (12345, 67890):
            for _ in range(3):
                self.assertIn("固定的首次解读", await handler._request_ai_text(self.event(group), "ordinary"))
            self.assertIn("额度已用完", await handler._request_ai_text(self.event(group), "fourth"))
            self.assertEqual(self.user_state(self.event(group))["ai_usage"]["used"], 3)
        self.assertEqual(self.generate.await_count, 6)

    async def test_regular_quota_survives_restart_and_resets_next_day(self):
        for _ in range(3):
            await handler._request_ai_text(self.event(), "ordinary")
        handler._state_store = None
        self.assertIn("额度已用完", await handler._request_ai_text(self.event(), "after restart"))
        self.today.return_value = "2026-10-12"
        self.assertIn("固定的首次解读", await handler._request_ai_text(self.event(), "tomorrow"))
        self.assertEqual(self.user_state()["ai_usage"], {"date": "2026-10-12", "used": 1})
        self.assertEqual(self.generate.await_count, 4)

    async def test_failed_regular_requests_spend_quota(self):
        self.generate.side_effect = llm.LLMError("simulated failure")
        for _ in range(3):
            self.assertIn("暂时不可用", await handler._request_ai_text(self.event(), "ordinary"))
        self.assertIn("额度已用完", await handler._request_ai_text(self.event(), "fourth"))
        self.assertEqual(self.generate.await_count, 3)
        self.assertEqual(self.user_state()["ai_usage"]["used"], 3)

    async def test_disabled_ai_does_not_spend_quota(self):
        with settings(batarot_llm_enabled=False):
            self.assertEqual(await handler._request_ai_text(self.event(), "ordinary"), "")
            await self.fortune()
        self.generate.assert_not_awaited()
        self.assertNotIn("ai_usage", self.user_state())
        self.assertEqual(self.user_state()["fortune"]["ai_status"], "disabled")

    async def test_cooldown_busy_and_same_user_inflight_do_not_spend_quota(self):
        key = handler._user_key(self.event())
        with settings(batarot_llm_cooldown=10):
            handler._llm_last_used[key] = time.monotonic()
            self.assertIn("冷却", await handler._request_ai_text(self.event(), "cooldown"))
        handler._llm_inflight.add(key)
        self.assertIn("处理中", await handler._request_ai_text(self.event(), "same user"))
        handler._llm_inflight.clear()
        handler._llm_inflight.update({"busy-1", "busy-2"})
        self.assertIn("较多", await handler._request_ai_text(self.event(), "busy"))
        self.generate.assert_not_awaited()
        self.assertNotIn("ai_usage", self.user_state())

    async def test_zero_quota_disables_only_regular_ai(self):
        with settings(batarot_llm_daily_limit=0):
            self.assertIn("额度已用完", await handler._request_ai_text(self.event(), "ordinary"))
            await self.fortune()
        self.generate.assert_awaited_once()
        self.assertNotIn("ai_usage", self.user_state())

    async def test_daily_waits_for_busy_capacity_then_generates_once(self):
        key = handler._user_key(self.event())
        handler._llm_inflight.update({key, "another-request"})
        waiting = asyncio.Event()
        release = asyncio.Event()

        async def wait_for_release(delay):
            waiting.set()
            await release.wait()

        proxy = SimpleNamespace(**dict(vars(asyncio), sleep=wait_for_release))
        with patch.object(handler, "asyncio", proxy):
            task = asyncio.create_task(self.fortune())
            try:
                await asyncio.wait_for(waiting.wait(), 1)
                self.generate.assert_not_awaited()
                self.assertEqual(handler._llm_inflight, {key, "another-request"})
                self.assertIn("较多", await handler._request_ai_text(self.event(67890), "ordinary"))
                handler._llm_inflight.clear()
                release.set()
                await asyncio.wait_for(task, 1)
                await self.fortune()
            finally:
                handler._llm_inflight.clear()
                release.set()
                if not task.done():
                    task.cancel()
                await asyncio.gather(task, return_exceptions=True)
        self.generate.assert_awaited_once()
        self.draw.assert_called_once()
        self.assertEqual(self.user_state()["fortune"]["ai_status"], "completed")
        self.assertNotIn("ai_usage", self.user_state())
        self.assertEqual(handler._llm_inflight, set())

    async def test_daily_capacity_wait_has_deadline_and_never_calls_model(self):
        handler._llm_inflight.update({"busy-1", "busy-2"})
        clock = [0.0]
        waits = []

        async def advance(delay):
            waits.append(delay)
            clock[0] += delay
            await asyncio.sleep(0)

        proxy = SimpleNamespace(**dict(vars(asyncio), sleep=advance))
        with settings(batarot_llm_timeout=0.5), \
                patch.object(handler, "time", SimpleNamespace(monotonic=lambda: clock[0])), \
                patch.object(handler, "asyncio", proxy):
            await self.fortune()
            await self.fortune()
        self.generate.assert_not_awaited()
        self.draw.assert_called_once()
        self.assertAlmostEqual(sum(waits), 2.5)
        self.assertTrue(all(0 < delay <= 0.05 for delay in waits))
        record = self.user_state()["fortune"]
        self.assertEqual(record["ai_status"], "skipped")
        self.assertIn("等待已有 AI 解读结束超时", record["ai_text"])
        self.assertEqual(record["total"], 12)
        self.assertNotIn("ai_usage", self.user_state())
        self.assertEqual(handler._llm_inflight, {"busy-1", "busy-2"})

    async def test_cancelling_daily_capacity_wait_does_not_leak_slot(self):
        handler._llm_inflight.update({"busy-1", "busy-2"})
        waiting = asyncio.Event()

        async def wait_forever(delay):
            waiting.set()
            await asyncio.Event().wait()

        proxy = SimpleNamespace(**dict(vars(asyncio), sleep=wait_forever))
        with patch.object(handler, "asyncio", proxy):
            task = asyncio.create_task(self.fortune())
            try:
                await asyncio.wait_for(waiting.wait(), 1)
                background = next(iter(handler._fortune_tasks.values()))
                background.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
            finally:
                if not task.done():
                    task.cancel()
                await asyncio.gather(task, return_exceptions=True)
        self.generate.assert_not_awaited()
        self.assertEqual(handler._llm_inflight, {"busy-1", "busy-2"})
        self.assertEqual(self.user_state()["fortune"]["ai_status"], "failed")
        self.assertNotIn("ai_usage", self.user_state())

    async def test_daily_prompt_contains_position_meaning_delta_and_total(self):
        with patch.object(handler, "build_fortune_prompt", wraps=llm.build_fortune_prompt) as prompt:
            await self.fortune(question="我该怎样开始")
        values = prompt.call_args.kwargs
        self.assertEqual((values["position"], values["meaning"], values["delta"], values["total"]),
                         ("正位", "勇于开始", 2, 12))
        self.assertEqual(values["question"], "我该怎样开始")
        content = self.generate.call_args.args[0]
        self.assertIn("+2", content)
        self.assertIn("累计幸运值：12", content)
        self.assertNotIn("/100", content)

    def test_lucky_delta_bounds_and_direction_signs(self):
        for position, delta, limits in (("up", 5, (1, 5)), ("down", -5, (-5, -1))):
            with self.subTest(position=position), \
                    patch.object(handler.random, "choice", side_effect=["0", position]), \
                    patch.object(handler.random, "randint", return_value=delta) as randint:
                result = self.real_draw()
            self.assertEqual(result["position"], position)
            self.assertEqual(result["delta"], delta)
            randint.assert_called_once_with(*limits)

    def test_zero_change_config_is_supported(self):
        with settings(batarot_luck_min=0, batarot_luck_max=0):
            for position in ("up", "down"):
                with patch.object(handler.random, "choice", side_effect=["0", position]), \
                        patch.object(handler.random, "randint") as randint:
                    self.assertEqual(self.real_draw()["delta"], 0)
                randint.assert_not_called()

    def test_invalid_luck_and_daily_limits_are_rejected(self):
        for values in ({"batarot_luck_min": -6}, {"batarot_luck_max": 6},
                       {"batarot_luck_min": 1}, {"batarot_luck_max": -1},
                       {"batarot_llm_daily_limit": -1}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                Config(**values)


if __name__ == "__main__":
    unittest.main()
