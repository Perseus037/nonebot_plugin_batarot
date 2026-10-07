"""nonebot-plugin-batarot 配置项。

所有配置项都可以写进 nonebot 项目根目录下的 ``.env`` / ``.env.prod`` 文件
（变量名大小写不敏感，推荐全大写写法），也可以在启动前设置为系统环境变量。

大模型（AI 解读）相关配置项见下方 ``batarot_llm_*`` 字段，
示例文件请参考插件仓库根目录的 ``.env.example``。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, validator

from nonebot import get_driver


class Config(BaseModel):
    """插件配置。"""

    forward_mode: bool = False
    """牌阵占卜是否以长消息形式发出，默认为否（合并转发）。"""

    # ------------------------------------------------------------------
    # 大模型（AI 解读）配置
    # ------------------------------------------------------------------
    batarot_llm_enabled: bool = False
    """是否开启大模型辅助解读。默认关闭，关闭时不请求模型接口。"""

    batarot_llm_api_base: str = "https://api.deepseek.com/v1"
    """大模型接口地址（OpenAI 兼容），可只写到 ``/v1``，插件会自动补 ``/chat/completions``。"""

    batarot_llm_api_key: str = ""
    """大模型接口密钥，形如 ``sk-xxxx``。"""

    batarot_llm_model: str = "deepseek-flash"
    """使用的模型名称，必须与服务商当前提供的模型对应。"""

    batarot_llm_thinking: bool = False
    """DeepSeek 官方接口的思考模式，短篇解读默认关闭；其他服务商不发送此参数。"""

    batarot_llm_system_prompt: str = ""
    """自定义占卜师人设（system 提示词），留空则使用插件内置人设。"""

    batarot_llm_temperature: float = 0.9
    """采样温度，越大越发散，建议 0.7 ~ 1.2。"""

    batarot_llm_max_tokens: int = 800
    """单次解读的最大生成长度，设为 0 表示不发送该参数。"""

    batarot_llm_timeout: float = 60.0
    """单次请求超时时间（秒）。"""

    batarot_llm_cooldown: int = 10
    """同一用户两次 AI 解读的最小间隔（秒），设为 0 表示不限制。"""

    @validator(
        "batarot_llm_api_base",
        "batarot_llm_api_key",
        "batarot_llm_model",
        "batarot_llm_system_prompt",
        pre=True,
    )
    def _coerce_to_str(cls, value: Any) -> Any:
        """兼容 .env 中纯数字等被 json 解析成非字符串的取值。"""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, bool)):
            return str(value)
        return ""


def _load_config() -> Config:
    """只读取 NoneBot 已选择的环境，兼容 NoneBot 2.1.1 和 Pydantic 1/2。"""
    global_config = get_driver().config
    if hasattr(global_config, "model_dump"):
        values = global_config.model_dump()
    else:
        values = global_config.dict()
    return Config(**values)


config = _load_config()

__all__ = ["Config", "config"]
