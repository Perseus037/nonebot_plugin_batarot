"""nonebot-plugin-batarot 配置项。

所有配置项都可以写进 nonebot 项目根目录下的 ``.env`` / ``.env.prod`` 文件
（变量名大小写不敏感，推荐全大写写法），也可以在启动前设置为系统环境变量。

大模型（AI 解读）相关配置项见下方 ``batarot_llm_*`` 字段，
示例文件请参考插件仓库根目录的 ``.env.example``。
"""

from __future__ import annotations

from typing import Any, Literal, Optional
from pathlib import Path

from pydantic import BaseModel, Field, validator

from nonebot import get_driver


class Config(BaseModel):
    """插件配置。"""

    forward_mode: bool = False
    """False 使用合并转发，True 使用一条普通图文长消息。"""

    batarot_data_file: Path = Path("data/batarot/state.json")
    batarot_initial_luck: int = 10
    batarot_luck_min: int = Field(-5, ge=-5, le=0)
    batarot_luck_max: int = Field(5, ge=0, le=5)
    batarot_llm_daily_limit: int = Field(3, ge=0)
    batarot_day_utc_offset: int = Field(8, ge=-12, le=14)

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
    """是否启用支持切换的模型的思考模式。"""

    batarot_llm_thinking_provider: Literal["auto", "deepseek", "siliconflow", "none"] = "auto"
    """auto 仅为已知支持的服务商和模型发送思考参数。"""

    batarot_llm_max_concurrency: int = Field(2, ge=1, le=8)
    batarot_llm_max_question_chars: int = Field(1000, ge=1, le=10000)
    batarot_llm_input_price_per_million: Optional[float] = Field(None, ge=0)
    batarot_llm_output_price_per_million: Optional[float] = Field(None, ge=0)

    batarot_llm_system_prompt: str = ""
    """自定义占卜师人设（system 提示词），留空则使用插件内置人设。"""

    batarot_llm_temperature: float = 0.9
    """采样温度，越大越发散，建议 0.7 ~ 1.2。"""

    batarot_llm_max_tokens: int = Field(800, ge=0)
    """单次解读的最大生成长度，设为 0 表示不发送该参数。"""

    batarot_llm_timeout: float = Field(60.0, gt=0)
    """单次请求超时时间（秒）。"""

    batarot_llm_cooldown: int = Field(10, ge=0)
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
