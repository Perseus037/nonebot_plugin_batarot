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
from .config import Config
from . import handler as handler

__version__ = "0.3.0"
__plugin_meta__ = PluginMetadata(
    name="碧蓝档案塔罗牌",
    description="碧蓝档案塔罗牌，运势预测与魔法占卜🔮支持多适配器，可接入大模型（LLM）辅助解读",
    usage=(
        "使用命令：ba塔罗牌，ba占卜，ba运势，ba塔罗牌解读\n"
        "以上命令均可在后面追加自己的问题，例如：ba塔罗牌 我最近的工作会顺利吗\n"
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
