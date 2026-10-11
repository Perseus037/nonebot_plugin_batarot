import asyncio
from copy import deepcopy
import json
import threading
import unittest
from unittest.mock import patch

import nonebot
from nonebot.adapters.onebot.v11 import Adapter

try:
    nonebot.get_driver()
except ValueError:
    nonebot.init(_env_file=None, log_level="ERROR", batarot_llm_enabled=False)
    nonebot.get_driver().register_adapter(Adapter)
if nonebot.get_plugin("nonebot_plugin_batarot") is None:
    assert nonebot.load_plugin("nonebot_plugin_batarot")

from nonebot_plugin_batarot import llm
from nonebot_plugin_batarot.config import config


class UrllibCancellationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.original_config = deepcopy(config.__dict__)
        config.__dict__.update(
            batarot_llm_enabled=True,
            batarot_llm_api_base="https://example.invalid/v1",
            batarot_llm_api_key="test-secret",
            batarot_llm_model="test-model",
            batarot_llm_max_concurrency=1,
            batarot_llm_thinking_provider="none",
        )
        self.backend = llm._backend
        llm._backend = "urllib"
        llm._active_requests = 0

    async def asyncTearDown(self):
        config.__dict__.clear()
        config.__dict__.update(self.original_config)
        llm._backend = self.backend
        await llm.shutdown()

    async def check_cancellation(self, worker_error=False):
        started = asyncio.Event()
        release = threading.Event()
        loop = asyncio.get_running_loop()

        def blocking_post(*args):
            loop.call_soon_threadsafe(started.set)
            if not release.wait(3):
                raise TimeoutError("test worker was not released")
            if worker_error:
                raise RuntimeError("test-secret private-question")
            return 200, json.dumps({"choices": [{"message": {"content": "解读"}}]})

        with patch.object(llm, "_blocking_urllib_post", side_effect=blocking_post) as post, \
                patch.object(llm, "_write_usage") as usage:
            task = asyncio.create_task(llm.chat_completion([]))
            try:
                await asyncio.wait_for(started.wait(), 1)
                task.cancel()
                await asyncio.sleep(0)
                task.cancel()
                await asyncio.sleep(0)
                self.assertFalse(task.done())
                self.assertEqual(llm._active_requests, 1)
                with self.assertRaises(llm.LLMError):
                    await llm.chat_completion([])
                post.assert_called_once()
                release.set()
                with self.assertRaises(asyncio.CancelledError):
                    await asyncio.wait_for(task, 1)
            finally:
                release.set()
                await asyncio.gather(task, return_exceptions=True)
        self.assertEqual(llm._active_requests, 0)
        usage.assert_called_once()
        self.assertEqual(usage.call_args.args[0]["state"], "cancelled")
        self.assertNotIn("test-secret", json.dumps(usage.call_args.args[0]))
        self.assertNotIn("private-question", json.dumps(usage.call_args.args[0]))

    async def test_repeated_cancellation_holds_slot_until_thread_returns(self):
        await self.check_cancellation()

    async def test_worker_failure_during_cancellation_stays_cancelled(self):
        await self.check_cancellation(worker_error=True)

    async def test_successful_urllib_request_releases_slot(self):
        response = (200, json.dumps({"choices": [{"message": {"content": "正常解读"}}]}))
        with patch.object(llm, "_blocking_urllib_post", return_value=response) as post, \
                patch.object(llm, "_write_usage") as usage:
            self.assertEqual(await llm.chat_completion([]), "正常解读")
        post.assert_called_once()
        self.assertEqual(llm._active_requests, 0)
        self.assertEqual(usage.call_args.args[0]["state"], "completed")

    async def test_urllib_failure_is_sanitized_and_releases_slot(self):
        with patch.object(llm, "_blocking_urllib_post", side_effect=RuntimeError("test-secret private-question")), \
                patch.object(llm, "_write_usage"):
            with self.assertRaises(llm.LLMError) as error:
                await llm.chat_completion([])
        self.assertNotIn("test-secret", str(error.exception))
        self.assertNotIn("private-question", str(error.exception))
        self.assertEqual(llm._active_requests, 0)


if __name__ == "__main__":
    unittest.main()
