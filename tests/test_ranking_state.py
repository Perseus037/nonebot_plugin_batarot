import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


MODULE_PATH = (Path(__file__).resolve().parents[1]
               / "nonebot_plugin_batarot" / "state.py")
SPEC = importlib.util.spec_from_file_location("batarot_ranking_state_test", MODULE_PATH)
state_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(state_module)
StateStore = state_module.StateStore
StateError = state_module.StateError


class RankingStateTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "nested" / "state.json"
        self.store = StateStore(self.path)
        self.scope = "OneBot V11:10000:group:123:"

    def write_users(self, users):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"schema_version": 1, "users": users}), encoding="utf-8")

    async def test_group_prefix_is_exact_not_partial(self):
        self.write_users({
            self.scope + "100": {"luck_total": 12},
            "OneBot V11:10000:group:1234:100": {"luck_total": 999},
            "OneBot V11:10000:group:12:100": {"luck_total": 998},
        })
        self.assertEqual(await self.store.leaderboard(self.scope), [{"user_id": "100", "total": 12}])

    async def test_other_bots_adapters_and_private_chats_are_excluded(self):
        self.write_users({
            self.scope + "100": {"luck_total": 12},
            "OneBot V11:100000:group:123:100": {"luck_total": 999},
            "OneBot V12:10000:group:123:100": {"luck_total": 998},
            "OneBot V11:10000:private:100": {"luck_total": 997},
            "OneBot V11:10000:group:456:100": {"luck_total": 996},
        })
        self.assertEqual(await self.store.leaderboard(self.scope), [{"user_id": "100", "total": 12}])

    async def test_zero_negative_and_positive_totals_are_sorted(self):
        self.write_users({
            self.scope + "negative": {"luck_total": -8},
            self.scope + "zero": {"luck_total": 0},
            self.scope + "positive": {"luck_total": 11},
            self.scope + "lower": {"luck_total": -50},
        })
        self.assertEqual(await self.store.leaderboard(self.scope), [
            {"user_id": "positive", "total": 11},
            {"user_id": "zero", "total": 0},
            {"user_id": "negative", "total": -8},
            {"user_id": "lower", "total": -50},
        ])

    async def test_quota_only_users_are_not_assigned_initial_points(self):
        self.write_users({
            self.scope + "quota": {"ai_usage": {"date": "2026-10-11", "used": 2}},
            self.scope + "empty": {},
            self.scope + "drawn": {"luck_total": -1},
        })
        self.assertEqual(await self.store.leaderboard(self.scope), [{"user_id": "drawn", "total": -1}])

    async def test_equal_totals_use_lexical_user_order(self):
        self.write_users({
            self.scope + user: {"luck_total": 10} for user in ("2", "11", "1", "a", "A")
        })
        result = await self.store.leaderboard(self.scope)
        self.assertEqual([row["user_id"] for row in result], ["1", "11", "2", "A", "a"])

    async def test_default_limit_returns_top_ten(self):
        self.write_users({self.scope + str(i): {"luck_total": i} for i in range(15)})
        result = await self.store.leaderboard(self.scope)
        self.assertEqual(len(result), 10)
        self.assertEqual([row["total"] for row in result], list(range(14, 4, -1)))

    async def test_limit_one_and_ten_boundaries(self):
        self.write_users({self.scope + str(i): {"luck_total": i} for i in range(12)})
        self.assertEqual(await self.store.leaderboard(self.scope, 1), [{"user_id": "11", "total": 11}])
        self.assertEqual(len(await self.store.leaderboard(self.scope, 10)), 10)

    async def test_invalid_limits_fail_closed(self):
        for limit in (0, -1, 11, True, False, 1.5, "3", None):
            with self.subTest(limit=limit), self.assertRaises(StateError):
                await self.store.leaderboard(self.scope, limit)
        self.assertFalse(self.path.exists())

    async def test_invalid_or_private_scopes_are_rejected(self):
        scopes = (None, "", "group:123:", "OneBot V11:10000:private:",
                  "OneBot V11:10000:group:123", "OneBot V11:10000:group::",
                  "OneBot V11:10000:group:123:100:", "OneBot V11::group:123:",
                  ":10000:group:123:")
        for scope in scopes:
            with self.subTest(scope=scope), self.assertRaises(StateError):
                await self.store.leaderboard(scope)
        self.assertFalse(self.path.exists())

    async def test_blank_store_does_not_create_file_or_parent(self):
        self.assertEqual(await self.store.leaderboard(self.scope), [])
        self.assertFalse(self.path.exists())
        self.assertFalse(self.path.parent.exists())

    async def test_read_does_not_change_file_or_return_private_fields(self):
        self.write_users({self.scope + "100": {"luck_total": 12,
            "ai_usage": {"date": "2026-10-11", "used": 2}}})
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        modified = self.path.stat().st_mtime_ns
        with patch.object(self.store, "_save", side_effect=AssertionError("Ranking must not write")):
            result = await self.store.leaderboard(self.scope)
        self.assertEqual(result, [{"user_id": "100", "total": 12}])
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), digest)
        self.assertEqual(self.path.stat().st_mtime_ns, modified)
        result[0]["total"] = 999
        self.assertEqual(await self.store.leaderboard(self.scope), [{"user_id": "100", "total": 12}])

    async def test_corrupt_or_unknown_schema_is_not_rewritten(self):
        self.path.parent.mkdir(parents=True)
        for content in (b"{broken", b'{"schema_version":2,"users":{}}',
                        b'{"schema_version":1,"users":{"u":{"luck_total":true}}}'):
            with self.subTest(content=content):
                self.path.write_bytes(content)
                with self.assertRaises(StateError):
                    await self.store.leaderboard(self.scope)
                self.assertEqual(self.path.read_bytes(), content)

    async def test_incomplete_or_nested_user_suffixes_are_not_ranked(self):
        self.write_users({
            self.scope: {"luck_total": 999},
            self.scope + "nested:100": {"luck_total": 998},
            self.scope + "100": {"luck_total": 12},
        })
        self.assertEqual(await self.store.leaderboard(self.scope), [{"user_id": "100", "total": 12}])


if __name__ == "__main__":
    unittest.main()
