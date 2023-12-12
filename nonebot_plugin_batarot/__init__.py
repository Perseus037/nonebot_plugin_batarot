from nonebot import on_command
from nonebot.plugin import PluginMetadata
from .commands import handle_tarot, handle_tarot_spread, handle_daily_fortune, handle_tarot_reading

__version__ = "0.2.0.post3"
__plugin_meta__ = PluginMetadata(
    name="碧蓝档案塔罗牌",
    description="碧蓝档案塔罗牌，运势预测与魔法占卜🔮",
    usage="使用命令：ba塔罗牌，ba占卜，ba运势，ba塔罗牌解读",
    homepage="https://github.com/Perseus037/nonebot_plugin_batarot",
    type="application",
    config=None,
    supported_adapters={"~onebot.v11"},
)


tarot = on_command("batarot", aliases={"ba塔罗牌"})
tarot_spread = on_command("divination", aliases={"ba占卜"})
tarot_fortune = on_command("fortune", aliases={"ba运势"})
tarot_reading = on_command("reading", aliases={"ba塔罗牌解读"})

tarot.handle()(handle_tarot)
tarot_spread.handle()(handle_tarot_spread)
tarot_fortune.handle()(handle_daily_fortune)
tarot_reading.handle()(handle_tarot_reading)
