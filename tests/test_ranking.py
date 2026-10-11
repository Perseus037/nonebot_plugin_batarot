import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from test_batarot import group_event, invoke, settings
from nonebot_plugin_batarot import handler


class RankingHandlerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "state.json"
        self.options = settings(batarot_data_file=self.path, batarot_llm_enabled=True)
        self.options.__enter__()
        handler._state_store = None
        self.event = group_event()
        self.event.group_id = 123
        self.bot = SimpleNamespace(
            self_id=str(self.event.self_id),
            adapter=SimpleNamespace(get_name=lambda: "OneBot V11"),
            get_group_member_list=AsyncMock(return_value=[]),
        )
        self.bot_token = handler.current_bot.set(self.bot)
        self.scope = handler._scope_key(self.event)
        self.real_text = handler.Text
        self.real_factory = handler.MessageFactory
        self.patchers = [
            patch.object(self.real_factory, "send", new=AsyncMock()),
            patch.object(handler, "Text", side_effect=self.real_text),
            patch.object(handler, "MessageFactory", wraps=self.real_factory),
            patch.object(handler, "generate_reading", new=AsyncMock(side_effect=AssertionError("Ranking must not call AI"))),
            patch.object(handler.MessageSegment, "at", side_effect=AssertionError("Ranking must not mention members")),
        ]
        self.send, self.text, self.factory, self.generate, self.at = [p.start() for p in self.patchers]

    async def asyncTearDown(self):
        for patcher in reversed(self.patchers):
            patcher.stop()
        handler.current_bot.reset(self.bot_token)
        handler._state_store = None
        self.options.__exit__(None, None, None)
        self.temporary.cleanup()

    def write_users(self, users):
        self.path.write_text(json.dumps({"schema_version": 1, "users": users}), encoding="utf-8")

    async def ranking(self, event=None):
        await invoke(handler.handle_lucky_ranking, bot=self.bot, event=event or self.event)

    def shown(self):
        self.text.assert_called_once()
        return self.text.call_args.args[0]

    async def test_top_ten_current_group_and_bot_only_without_ai_or_writes(self):
        users = {self.scope + str(i): {"luck_total": i} for i in range(15)}
        users["OneBot V11:10000:group:1234:outside"] = {"luck_total": 999}
        users["OneBot V11:10001:group:123:otherbot"] = {"luck_total": 998}
        users["OneBot V12:10000:group:123:otheradapter"] = {"luck_total": 997}
        users[self.scope + "quotaonly"] = {"ai_usage": {"date": "2026-10-11", "used": 3}}
        self.write_users(users)
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        store = handler._store()
        with patch.object(store, "reserve_ai", new=AsyncMock(side_effect=AssertionError("No quota writes"))) as reserve:
            await self.ranking()
        lines = self.shown().splitlines()
        self.assertEqual(len(lines), 11)
        self.assertEqual(lines[1:], [f"{rank}. {score}：{score}" for rank, score in enumerate(range(14, 4, -1), 1)])
        self.bot.get_group_member_list.assert_awaited_once_with(group_id=123)
        reserve.assert_not_awaited()
        self.generate.assert_not_awaited()
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), digest)
        self.send.assert_awaited_once_with(reply=True)

    async def test_empty_group_does_not_query_member_api_or_create_file(self):
        await self.ranking()
        self.assertIn("本群还没有", self.shown())
        self.bot.get_group_member_list.assert_not_awaited()
        self.generate.assert_not_awaited()
        self.assertFalse(self.path.exists())

    async def test_private_message_does_not_read_store(self):
        private = SimpleNamespace(group_id=None, get_user_id=lambda: "111")
        with patch.object(handler, "_store", side_effect=AssertionError("Private ranking must not access state")):
            await self.ranking(private)
        self.assertIn("请在群聊", self.shown())
        self.bot.get_group_member_list.assert_not_awaited()

    async def test_group_card_then_nickname_then_number(self):
        self.write_users({self.scope + str(i): {"luck_total": 20 - i} for i in (1, 2, 3)})
        self.bot.get_group_member_list.return_value = [
            {"user_id": 1, "card": "群名片", "nickname": "不应优先的昵称"},
            {"user_id": 2, "card": "", "nickname": "用户昵称"},
            {"user_id": 3, "card": "", "nickname": ""},
        ]
        await self.ranking()
        text = self.shown()
        self.assertIn("1. 群名片（1）：19", text)
        self.assertNotIn("不应优先", text)
        self.assertIn("2. 用户昵称（2）：18", text)
        self.assertIn("3. 3：17", text)
        self.bot.get_group_member_list.assert_awaited_once_with(group_id=123)

    async def test_whitespace_only_card_falls_back_to_nickname(self):
        self.write_users({self.scope + "1": {"luck_total": 10}})
        self.bot.get_group_member_list.return_value = [{"user_id": 1, "card": " \t\n ", "nickname": "昵称"}]
        await self.ranking()
        self.assertIn("昵称（1）：10", self.shown())

    async def test_member_api_failure_falls_back_to_user_numbers(self):
        self.write_users({self.scope + "1": {"luck_total": 0}, self.scope + "2": {"luck_total": -3}})
        self.bot.get_group_member_list.side_effect = RuntimeError("API unavailable")
        await self.ranking()
        self.assertEqual(self.shown().splitlines()[1:], ["1. 1：0", "2. 2：-3"])
        self.send.assert_awaited_once_with(reply=True)

    async def test_invalid_member_list_or_entries_fall_back(self):
        self.write_users({self.scope + "1": {"luck_total": 10}})
        self.bot.get_group_member_list.return_value = {"unexpected": "response"}
        await self.ranking()
        self.assertIn("1. 1：10", self.shown())

    async def test_names_have_no_newlines_and_are_bounded(self):
        self.write_users({self.scope + "1": {"luck_total": 11}, self.scope + "2": {"luck_total": 10}})
        self.bot.get_group_member_list.return_value = [
            {"user_id": 1, "card": "  甲\n乙\t 丙 \r\n", "nickname": ""},
            {"user_id": 2, "card": "名" * 40, "nickname": ""},
            None,
        ]
        await self.ranking()
        lines = self.shown().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[1], "1. 甲 乙 丙（1）：11")
        self.assertEqual(lines[2], "2. " + "名" * 30 + "（2）：10")

    async def test_reply_contains_only_text_without_real_mentions(self):
        self.write_users({self.scope + "1": {"luck_total": 10}})
        self.bot.get_group_member_list.return_value = [{"user_id": 1, "card": "[CQ:at,qq=all]", "nickname": ""}]
        await self.ranking()
        self.factory.assert_called_once()
        self.assertIsInstance(self.factory.call_args.args[0], self.real_text)
        self.at.assert_not_called()
        self.generate.assert_not_awaited()

    async def test_broken_state_prompts_without_api_or_rewriting(self):
        self.path.write_bytes(b"{broken")
        await self.ranking()
        self.assertIn("存档暂时不可用", self.shown())
        self.assertEqual(self.path.read_bytes(), b"{broken")
        self.bot.get_group_member_list.assert_not_awaited()
        self.generate.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
