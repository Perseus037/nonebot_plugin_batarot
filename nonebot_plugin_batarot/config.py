try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
#
# 如果你使用 pydantic2 ：
# 1. 安装pydantic_settings包
# 2. 将第1行的pydantic修改为pydantic_settings
# 3. 删除第14行的井号
#

class Config(BaseSettings):
    forward_mode: bool = False  # 默认值为 False，如果未在 .env 文件中配置

    class Config:
        env_file = ".env.prod" 
        extra = "ignore"

config = Config()