import asyncio
import base64
import builtins
from contextlib import contextmanager
from copy import deepcopy
from io import BytesIO
import json
import os
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

import nonebot
from nonebot.adapters.onebot.v11 import Adapter, GroupMessageEvent, Message
from nonebot.exception import FinishedException
from PIL import Image

nonebot.init(_env_file=None, log_level="ERROR", batarot_llm_enabled=False)
nonebot.get_driver().register_adapter(Adapter)
assert nonebot.load_plugin("nonebot_plugin_batarot")
from nonebot_plugin_batarot import handler, llm, utils
from nonebot_plugin_batarot.config import Config, config


@contextmanager
def settings(**values):
    original = deepcopy(config.__dict__)
    config.__dict__.update(values)
    try:
        yield
    finally:
        config.__dict__.clear()
        config.__dict__.update(original)


def png(color="red"):
    buffer = BytesIO()
    with Image.new("RGB", (2, 2), color) as image:
        image.putpixel((0, 0), (0, 0, 255))
        image.save(buffer, "PNG")
    return buffer.getvalue()


def group_event():
    return GroupMessageEvent(time=0, self_id=10000, post_type="message",
        message_type="group", sub_type="normal", message_id=1, user_id=111,
        group_id=20000, message=Message("ba占卜"), raw_message="ba占卜", font=0,
        sender={"user_id":111, "nickname":"test"})


async def invoke(function, **kwargs):
    try:
        await function(**kwargs)
    except FinishedException:
        pass


class DataAndImageTests(unittest.TestCase):
    def setUp(self):
        utils._load_json.cache_clear()
        utils._read_image_cached.cache_clear()

    def test_static_json_read_once(self):
        with patch("builtins.open", wraps=builtins.open) as opened:
            for _ in range(3):
                utils.load_tarot_data()
                utils.load_spread_data()
                utils.load_fortune_descriptions()
        self.assertEqual(opened.call_count, 4)

    def test_english_name_with_question(self):
        cards, _ = utils.load_tarot_data()
        self.assertEqual(utils.parse_card_query(cards, "the FOOL 我的计划怎么样"), ("0", "我的计划怎么样"))

    def test_chinese_number_and_exact_name(self):
        cards, _ = utils.load_tarot_data()
        for text, expected in [("愚者\t我的计划", ("0", "我的计划")), ("0 问题", ("0", "问题")),
                               ("The Fool", ("0", "")), ("0bad", (None, "")), ("", (None, ""))]:
            with self.subTest(text=text):
                self.assertEqual(utils.parse_card_query(cards, text), expected)

    def test_longest_name_wins(self):
        cards = {"1":{"name_en":"The", "name_cn":"甲"}, "2":{"name_en":"The Fool", "name_cn":"乙"}}
        self.assertEqual(utils.parse_card_query(cards, "The Fool question"), ("2", "question"))

    def test_image_cache_returns_independent_streams(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(utils, "image_dir", folder):
            Path(folder, "card.png").write_bytes(png())
            first = utils.send_image_as_bytes("card.png")
            first.read()
            second = utils.send_image_as_bytes("card.png")
            self.assertEqual(second.tell(), 0)
            self.assertEqual(second.getvalue(), png())
            self.assertEqual(utils._read_image_cached.cache_info().hits, 1)

    def test_reversed_bytes_and_base64_match(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(utils, "image_dir", folder):
            Path(folder, "card.png").write_bytes(png())
            reversed_bytes = utils.send_image_as_bytes("card.png", True).getvalue()
            encoded = utils.send_image_as_base64("card.png", True)
            self.assertEqual(base64.b64decode(encoded[9:]), reversed_bytes)
            with Image.open(BytesIO(reversed_bytes)) as image:
                self.assertEqual(image.getpixel((1, 1)), (0, 0, 255))

    def test_changed_image_invalidates_cache(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(utils, "image_dir", folder):
            file = Path(folder, "card.png")
            file.write_bytes(png())
            original = utils.send_image_as_bytes("card.png").getvalue()
            stamp = file.stat().st_mtime_ns
            file.write_bytes(png("green"))
            os.utime(file, ns=(stamp + 1_000_000_000, stamp + 1_000_000_000))
            self.assertNotEqual(utils.send_image_as_bytes("card.png").getvalue(), original)

    def test_missing_and_corrupt_images_are_safe(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(utils, "image_dir", folder):
            file = Path(folder, "card.png")
            file.write_bytes(png())
            self.assertIsNotNone(utils.send_image_as_bytes("card.png"))
            file.unlink()
            self.assertIsNone(utils.send_image_as_bytes("card.png", True))
            file.write_bytes(b"broken image")
            self.assertIsNone(utils.send_image_as_bytes("card.png"))
            self.assertIsNone(utils.send_image_as_base64("card.png", True))

    def test_compressed_image_cache_is_bounded(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(utils, "image_dir", folder):
            for index in range(24):
                name = f"{index}.png"
                Path(folder, name).write_bytes(png())
                self.assertIsNotNone(utils.send_image_as_bytes(name))
            self.assertEqual(utils._read_image_cached.cache_info().currsize, 16)

    def test_all_bundled_cards_are_valid(self):
        cards, urls = utils.load_tarot_data()
        self.assertEqual(len(cards), 22)
        for filename in urls.values():
            with self.subTest(filename=filename):
                for reverse in (False, True):
                    with Image.open(utils.send_image_as_bytes(filename, reverse)) as image:
                        image.load()
                        self.assertGreater(image.width, 0)

    def test_invalid_limits_rejected(self):
        for kwargs in ({"batarot_llm_max_concurrency":0}, {"batarot_llm_timeout":0},
                       {"batarot_llm_max_question_chars":0}, {"batarot_llm_max_tokens":-1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Config(**kwargs)


class HandlerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        handler._llm_inflight.clear()
        handler._llm_last_used.clear()
        utils._image_slots = None
        self.folder = tempfile.TemporaryDirectory()
        self.options = settings(batarot_data_file=Path(self.folder.name) / "state.json",
                                batarot_llm_api_key="test-secret")
        self.options.__enter__()
        handler._state_store = None

    async def asyncTearDown(self):
        self.options.__exit__(None, None, None)
        self.folder.cleanup()

    async def test_image_work_runs_off_event_loop(self):
        main_thread = threading.get_ident()
        called = []
        def load(*args):
            called.append(threading.get_ident())
            return BytesIO(png())
        with patch.object(utils, "send_image_as_bytes", side_effect=load):
            await utils.load_image_as_bytes("card.png")
        self.assertNotEqual(called, [main_thread])
        self.assertEqual(len(called), 1)

    async def test_image_workers_limited(self):
        active = peak = 0
        lock = threading.Lock()
        def load(*args):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            time.sleep(0.02)
            with lock:
                active -= 1
            return BytesIO(png())
        with patch.object(utils, "send_image_as_bytes", side_effect=load):
            await asyncio.gather(*(utils.load_image_as_bytes("card.png") for _ in range(6)))
        self.assertEqual(peak, 2)

    async def test_missing_reversed_single_card_does_not_crash(self):
        with settings(batarot_llm_enabled=False), \
             patch.object(handler, "random_tarot_card", return_value=("愚者", "down", "牌义", "missing.png")), \
             patch.object(handler, "load_image_as_bytes", new=AsyncMock(return_value=None)) as image, \
             patch.object(handler.MessageFactory, "send", new=AsyncMock()) as send:
            await invoke(handler.handle_tarot, event=group_event(), args=Message(""))
        image.assert_awaited_once_with("missing.png", True)
        send.assert_awaited_once()

    async def test_cancelled_image_keeps_slot_until_worker_finishes(self):
        loop = asyncio.get_running_loop()
        started = asyncio.Event()
        release = threading.Event()
        active = peak = 0
        lock = threading.Lock()
        def load(*args):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            loop.call_soon_threadsafe(started.set)
            release.wait(1)
            with lock:
                active -= 1
            return BytesIO(png())
        with patch.object(utils, "send_image_as_bytes", side_effect=load):
            first = asyncio.create_task(utils.load_image_as_bytes("card.png"))
            await asyncio.wait_for(started.wait(), 1)
            first.cancel()
            following = [asyncio.create_task(utils.load_image_as_bytes("card.png")) for _ in range(2)]
            await asyncio.sleep(0.04)
            release.set()
            results = await asyncio.gather(first, *following, return_exceptions=True)
        self.assertIsInstance(results[0], asyncio.CancelledError)
        self.assertLessEqual(peak, 2)

    async def test_english_question_reaches_prompt(self):
        with patch.object(handler.MessageFactory, "send", new=AsyncMock()), \
             patch.object(handler, "load_image_as_bytes", new=AsyncMock(return_value=BytesIO(png()))), \
             patch.object(handler, "_request_ai_text", new=AsyncMock(return_value="")) as request:
            await invoke(handler.handle_tarot_reading, event=group_event(), args=Message("The Fool 我该怎样开始新计划"))
        self.assertIn("我该怎样开始新计划", request.call_args.args[1])
        self.assertIn("愚者", request.call_args.args[1])

    async def spread(self, forward_mode=False, fail=False, private=False):
        bot = SimpleNamespace(send_group_forward_msg=AsyncMock(side_effect=RuntimeError("test") if fail else None), send=AsyncMock())
        event = SimpleNamespace(self_id=10000, get_user_id=lambda:"111") if private else group_event()
        spread = {"formations":{"test":{"cards_num":3, "representations":[["过去", "现在", "未来"]]}}}
        with settings(forward_mode=forward_mode, batarot_llm_enabled=False), \
             patch.object(handler, "load_spread_data", return_value=spread), \
             patch.object(handler.random, "random", return_value=1), \
             patch.object(handler, "load_image_as_base64", new=AsyncMock(return_value="base64://" + base64.b64encode(png()).decode())) as images:
            await invoke(handler.handle_tarot_spread, bot=bot, event=event, args=Message(""))
        self.assertEqual(images.await_count, 3)
        self.assertTrue(all(call.args[1] is True for call in images.call_args_list))
        return bot

    async def test_group_forward_and_reverse_images(self):
        bot = await self.spread()
        bot.send_group_forward_msg.assert_awaited_once()
        bot.send.assert_not_awaited()

    async def test_long_message_mode(self):
        bot = await self.spread(forward_mode=True)
        bot.send_group_forward_msg.assert_not_awaited()
        bot.send.assert_awaited_once()
        self.assertEqual(sum(s.type == "image" for s in bot.send.call_args.args[1]), 3)

    async def test_forward_failure_falls_back_once(self):
        bot = await self.spread(fail=True)
        bot.send_group_forward_msg.assert_awaited_once()
        bot.send.assert_awaited_once()
        self.assertEqual(sum(s.type == "image" for s in bot.send.call_args.args[1]), 3)

    async def test_private_message(self):
        bot = await self.spread(private=True)
        bot.send_group_forward_msg.assert_not_awaited()
        bot.send.assert_awaited_once()

    async def test_disabled_ai_never_calls_provider(self):
        with settings(batarot_llm_enabled=False), patch.object(handler, "generate_reading", new=AsyncMock()) as generate:
            self.assertEqual(await handler._request_ai_text(group_event(), "prompt"), "")
        generate.assert_not_awaited()

    async def test_same_user_request_does_not_overlap_and_cancel_cleans_up(self):
        started = asyncio.Event()
        async def slow(*args):
            started.set()
            await asyncio.Event().wait()
        with settings(batarot_llm_enabled=True, batarot_llm_cooldown=0), \
             patch.object(handler, "generate_reading", new=AsyncMock(side_effect=slow)) as generate:
            task = asyncio.create_task(handler._request_ai_text(group_event(), "prompt"))
            await asyncio.wait_for(started.wait(), 1)
            self.assertIn("处理中", await handler._request_ai_text(group_event(), "second"))
            generate.assert_awaited_once()
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertEqual(handler._llm_inflight, set())

    async def test_cooldown_and_user_capacity(self):
        with settings(batarot_llm_enabled=True, batarot_llm_cooldown=10, batarot_llm_max_concurrency=2), \
             patch.object(handler, "generate_reading", new=AsyncMock(return_value="解读")) as generate:
            self.assertIn("解读", await handler._request_ai_text(group_event(), "first"))
            self.assertIn("冷却", await handler._request_ai_text(group_event(), "second"))
            handler._llm_inflight.update({"222", "333"})
            self.assertIn("较多", await handler._request_ai_text(SimpleNamespace(get_user_id=lambda:"444"), "third"))
            generate.assert_awaited_once()


class LLMTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.options = settings(batarot_llm_enabled=True, batarot_llm_api_key="test-secret",
            batarot_llm_api_base="https://api.siliconflow.cn/v1", batarot_llm_model="inclusionAI/Ling-mini-2.0",
            batarot_llm_thinking=False, batarot_llm_thinking_provider="auto", batarot_llm_max_concurrency=2,
            batarot_llm_input_price_per_million=0.5, batarot_llm_output_price_per_million=2,
            batarot_llm_max_tokens=600)
        self.options.__enter__()
        llm._active_requests = 0

    async def asyncTearDown(self):
        self.options.__exit__(None, None, None)
        await llm.shutdown()

    def response(self, usage=True):
        data = {"choices":[{"message":{"content":"可以从一个小目标开始。", "reasoning_content":"hidden"}}]}
        if usage:
            data["usage"] = {"prompt_tokens":1000, "completion_tokens":500, "total_tokens":1500,
                             "completion_tokens_details":{"reasoning_tokens":0}}
        return 200, json.dumps(data)

    async def test_siliconflow_supported_model_thinking_switch(self):
        for thinking in (False, True):
            with settings(batarot_llm_model="Qwen/Qwen3-14B", batarot_llm_thinking=thinking), \
                 patch.object(llm, "_post_json", new=AsyncMock(return_value=self.response())) as post:
                await llm.chat_completion([{"role":"user", "content":"test"}])
                self.assertIs(post.call_args.args[1]["enable_thinking"], thinking)
                self.assertEqual(post.call_args.args[1]["max_tokens"], 600)

    async def test_ling_and_instruct_omit_unsupported_parameter(self):
        for model in ("inclusionAI/Ling-mini-2.0", "Qwen/Qwen3-30B-A3B-Instruct-2507"):
            with settings(batarot_llm_model=model), patch.object(llm, "_post_json", new=AsyncMock(return_value=self.response())) as post:
                await llm.chat_completion([])
                self.assertNotIn("enable_thinking", post.call_args.args[1])

    async def test_deepseek_and_unknown_host(self):
        self.assertEqual(llm._thinking_options("https://api.deepseek.com/v1", "deepseek-chat"), {"thinking":{"type":"disabled"}})
        self.assertEqual(llm._thinking_options("https://api.siliconflow.cn.example/v1", "Qwen/Qwen3-14B"), {})
        with settings(batarot_llm_thinking_provider="siliconflow"):
            self.assertEqual(llm._thinking_options("https://gateway.example/v1", "custom"), {"enable_thinking":False})
        with settings(batarot_llm_thinking_provider="none"):
            self.assertEqual(llm._thinking_options("https://api.deepseek.com/v1", "deepseek-chat"), {})

    async def test_usage_and_cost_without_prompt_or_key(self):
        with patch.object(llm, "_post_json", new=AsyncMock(return_value=self.response())), patch.object(llm.logger, "info") as log:
            answer = await llm.chat_completion([{"role":"user", "content":"private-question"}])
        self.assertNotIn("hidden", answer)
        record = json.loads(log.call_args.args[1])
        self.assertEqual(record["estimated_cost_cny"], 0.0015)
        self.assertEqual(record["total_tokens"], 1500)
        self.assertEqual(record["reasoning_tokens"], 0)
        self.assertEqual(record["state"], "completed")
        self.assertNotIn("test-secret", json.dumps(record))
        self.assertNotIn("private-question", json.dumps(record))

    async def test_missing_usage_remains_unknown(self):
        with patch.object(llm, "_post_json", new=AsyncMock(return_value=self.response(False))), patch.object(llm.logger, "info") as log:
            await llm.chat_completion([])
        record = json.loads(log.call_args.args[1])
        self.assertIsNone(record["estimated_cost_cny"])
        self.assertIsNone(record["completion_tokens"])

    async def test_error_is_sanitized_and_not_retried(self):
        with patch.object(llm, "_post_json", new=AsyncMock(return_value=(401, "test-secret private-question"))) as post, \
             patch.object(llm.logger, "info") as log:
            with self.assertRaises(llm.LLMError) as error:
                await llm.chat_completion([])
        post.assert_awaited_once()
        self.assertNotIn("test-secret", str(error.exception))
        record = json.loads(log.call_args.args[1])
        self.assertEqual(record["state"], "failed")
        self.assertEqual(record["http_status"], 401)
        self.assertIsNone(record["estimated_cost_cny"])
        self.assertEqual(llm._active_requests, 0)

    async def test_timeout_releases_slot(self):
        with patch.object(llm, "_post_json", new=AsyncMock(side_effect=llm.LLMError("timeout"))) as post:
            with self.assertRaises(llm.LLMError):
                await llm.chat_completion([])
        post.assert_awaited_once()
        self.assertEqual(llm._active_requests, 0)

    async def test_global_concurrency_and_cancellation(self):
        started = asyncio.Event()
        count = 0
        async def slow(*args):
            nonlocal count
            count += 1
            if count == 2:
                started.set()
            await asyncio.Event().wait()
        with patch.object(llm, "_post_json", new=AsyncMock(side_effect=slow)) as post:
            tasks = [asyncio.create_task(llm.chat_completion([])) for _ in range(2)]
            await asyncio.wait_for(started.wait(), 1)
            with self.assertRaises(llm.LLMError):
                await llm.chat_completion([])
            self.assertEqual(post.await_count, 2)
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        self.assertEqual(llm._active_requests, 0)

    async def test_disabled_ai_does_not_record_billable_request(self):
        with settings(batarot_llm_enabled=False), patch.object(llm, "_post_json", new=AsyncMock()) as post, \
             patch.object(llm, "_write_usage") as usage:
            with self.assertRaises(llm.LLMError):
                await llm.chat_completion([])
        post.assert_not_awaited()
        usage.assert_not_called()

    async def test_question_length_bound(self):
        with settings(batarot_llm_max_question_chars=5):
            self.assertEqual(llm._question_line("123456789"), "老师提出的问题是：12345")


if __name__ == "__main__":
    unittest.main()
