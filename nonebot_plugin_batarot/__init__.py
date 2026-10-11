from nonebot import get_driver, require
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

"""
加载saa插件 提供多适配器支持
:::notice 请勿重复加载saa
"""
require("nonebot_plugin_saa")

from nonebot_plugin_saa import __plugin_meta__ as saa_plugin_meta

from . import llm as llm
from .config import Config, config
from . import handler as handler

__version__ = "0.3.0"
__plugin_meta__ = PluginMetadata(
    name="碧蓝档案塔罗牌",
    description="碧蓝档案塔罗牌，运势预测与魔法占卜🔮支持多适配器，可接入大模型（LLM）辅助解读",
    usage=(
        "使用命令：ba塔罗牌，ba占卜，ba运势，ba塔罗牌解读\n"
        "ba运势：每群每人每天一张幸运牌，重复查询展示当天结果\n"
        "其他占卜 AI 解读每群每人每天默认 3 次；可在命令后追加问题\n"
        "在 .env 中配置 BATAROT_LLM_ENABLED / BATAROT_LLM_API_BASE / BATAROT_LLM_API_KEY "
        "即可开启大模型辅助解读（详见插件 README 与 .env.example）"
    ),
    homepage="https://github.com/Perseus037/nonebot_plugin_batarot",
    type="application",
    config=Config,
    supported_adapters=saa_plugin_meta.supported_adapters,
)

try:
    # 机器人关闭时释放大模型请求所用的连接池
    get_driver().on_shutdown(llm.shutdown)
except Exception as e:  # pragma: no cover - 理论上不会发生
    logger.warning(f"batarot: 注册大模型连接池回收钩子失败：{e}")


@get_driver().on_startup
async def _log_settings():
    logger.info("batarot: AI={}, model={}, max_tokens={}, timeout={}, concurrency={}, cooldown={}, forward_mode={}, daily_limit={}, luck={}..{}, initial_luck={}, utc_offset={}",
                config.batarot_llm_enabled, config.batarot_llm_model, config.batarot_llm_max_tokens,
                config.batarot_llm_timeout, config.batarot_llm_max_concurrency,
                config.batarot_llm_cooldown, config.forward_mode, config.batarot_llm_daily_limit,
                config.batarot_luck_min, config.batarot_luck_max, config.batarot_initial_luck,
                config.batarot_day_utc_offset)
