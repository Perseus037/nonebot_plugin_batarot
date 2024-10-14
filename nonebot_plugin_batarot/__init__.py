from nonebot import require
from nonebot.plugin import PluginMetadata

"""
加载saa插件 提供多适配器支持
:::notice 请勿重复加载saa
"""
require("nonebot_plugin_saa")

from nonebot_plugin_saa import __plugin_meta__ as saa_plugin_meta

from . import handler as handler

__version__ = "0.2.2.post3"
__plugin_meta__ = PluginMetadata(
    name="碧蓝档案塔罗牌",
    description="碧蓝档案塔罗牌，运势预测与魔法占卜🔮支持多适配器",
    usage="使用命令：ba塔罗牌，ba占卜，ba运势，ba塔罗牌解读",
    homepage="https://github.com/Perseus037/nonebot_plugin_batarot",
    type="application",
    config=None,
    supported_adapters=saa_plugin_meta.supported_adapters,
)
