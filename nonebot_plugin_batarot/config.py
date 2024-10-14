from pydantic import BaseSettings

class Config(BaseSettings):
    forward_mode: bool = False  # 默认值为 False，如果未在 .env 文件中配置

    model_config = {
        "env_file": ".env.prod",  
    }

config = Config()
