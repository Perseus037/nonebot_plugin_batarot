<div align="center">
  <img src="https://github.com/Perseus037/nonebot_plugin_batarot/blob/main/Alice%20tarot%20picture.jpg" alt="碧蓝档案塔罗牌占卜图标" >

# nonebot-plugin-batarot

_🔮 一个可以进行测运势，魔法占卜与解读，并支持大模型辅助解读的碧蓝档案塔罗牌nonebot2插件🔮 _

<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">
<a href="https://pdm.fming.dev">
  <img src="https://img.shields.io/badge/pdm-managed-blueviolet" alt="pdm-managed">
</a>
<!-- <a href="https://wakatime.com/badge/user/b61b0f9a-f40b-4c82-bc51-0a75c67bfccf/project/f4778875-45a4-4688-8e1b-b8c844440abb">
  <img src="https://wakatime.com/badge/user/b61b0f9a-f40b-4c82-bc51-0a75c67bfccf/project/f4778875-45a4-4688-8e1b-b8c844440abb.svg" alt="wakatime">
</a> -->

<br />

<a href="./LICENSE">
  <img src="https://img.shields.io/github/license/Perseus037/nonebot_plugin_batarot.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-batarot">
  <img src="https://img.shields.io/pypi/v/nonebot-plugin-batarot.svg" alt="pypi">
</a>
<a href="https://pypi.org/project/nonebot-plugin-batarot/">
  <img src="https://img.shields.io/pypi/dm/nonebot-plugin-batarot.svg" alt="pypi download">
</a>

</div>

<div align="left">

## 💬 前言

若我超脱自然，便将绝不再用，任何自然物化作身躯之外形。

而只求古希腊金匠人用鎏金，和镀金锤铸的绝美造型。

以使昏昏欲睡的帝王清醒，或停留在金色枝头声声歌唱。

把过往，今日，或明朝之事，唱给拜占庭的贵妇王公们听。

——威廉·巴特勒·叶芝《驶向拜占庭》

## 📖 介绍

一个可以进行测运势，魔法占卜与解读的碧蓝档案塔罗牌nonebot2插件。

- 从本地读取图片并发送，使用 nonebot_plugin_send_anything_anywhere 实现多适配器支持（onebot.v11, onebot.v12, qqguild, kaiheila, telegram, feishu, red）
- 目前提供 4 个指令：`ba塔罗牌`、`ba运势`、`ba占卜`、`ba塔罗牌解读`，每个指令都可以在末尾追加自己的问题
- 0.3.0 起支持**大模型（AI）辅助占卜**：在 `.env` 里配置接口地址与密钥后，原指令会在本地结果之后追加一段由大模型生成的解读，配置方法见下方「配置」章节，可直接复制 [.env.example](./.env.example)
- 0.3.0 同时修复了 `ba占卜` 私聊发送失败、`ba塔罗牌解读` 参数解析报错两个问题，详见「更新日志」

有问题请先自行去 Q/A 查看，请下载最新的发版！！！

## 💿 安装

### 前置条件

| 依赖 | 说明 |
| --- | --- |
| `nonebot2 >= 2.1.1` | 插件运行环境 |
| `nonebot-plugin-send-anything-anywhere`（saa） | **必需前置**，插件加载时会 `require("nonebot_plugin_saa")`，没装会直接加载失败 |
| `pydantic-settings` | pydantic v2 环境下读取配置用，已写入插件依赖，安装插件时会自动带上 |

<details>
<summary>使用 nb-cli 安装（推荐）</summary>

在 nonebot2 项目的根目录下打开命令行，输入以下指令即可安装

    nb plugin install nonebot-plugin-batarot

</details>

<details>
<summary>使用包管理器安装</summary>

在 nonebot2 项目的根目录下打开命令行，根据你使用的包管理器输入相应命令

<details>
<summary>pip</summary>

    pip install nonebot-plugin-batarot

</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-batarot

</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-batarot

</details>
<details>
<summary>conda</summary>

conda 上没有这个包，请在 conda 虚拟环境里用 pip 安装

    pip install nonebot-plugin-batarot

</details>

</details>

### 安装前置插件 saa

若上面安装插件时没有自动带上 saa，请在机器人所在虚拟环境中手动安装

    pip install nonebot-plugin-send-anything-anywhere

### 安装后注册插件

在 nonebot2 项目根目录的 `pyproject.toml` 中写入。nonebot 2.5 及以上使用新的 `[tool.nonebot.plugins]` 表：

```toml
[tool.nonebot.plugins]
nonebot-plugin-batarot = ["nonebot_plugin_batarot"]
```

较早的 nonebot / nb-cli 版本使用旧写法，写在 `[tool.nonebot]` 下：

```toml
[tool.nonebot]
plugins = ["nonebot_plugin_batarot"]
```

> 如果你是把插件源码直接放进 bot 的本地插件目录（即 `pyproject.toml` 里 `plugin_dirs` 指向的目录），nonebot 会自动加载它，**不需要**再手动注册，但该目录必须在 bot 项目目录内（nonebot 会解析真实路径，放在项目外的软链接/联接会报 `ValueError` 导致启动失败）。

### 关于 pydantic / pydantic-settings

插件通过 `pydantic-settings` 读取配置，它已经写在插件依赖里，`pip install` / `nb plugin install` 会自动安装。如果你的环境里缺失它，手动补装即可：

    pip install pydantic-settings

插件代码里**不需要**修改任何 import，直接安装依赖后重启机器人即可。

## ⚙️ 配置

所有配置项都写在 **nonebot2 项目根目录**的 `.env`（或 `.env.prod` / `.env.{ENVIRONMENT}`）文件里，变量名大小写不敏感，推荐全大写。插件仓库根目录提供了带注释的示例文件 [.env.example](./.env.example)，可按需复制。

### 原有配置

```dotenv
# 牌阵占卜是否以长消息形式发出，默认为否（合并转发），建议不更改
FORWARD_MODE=false
```

> 说明：`FORWARD_MODE` 是早期预留的开关，**当前版本代码里尚未实际生效** —— `ba占卜` 在群聊固定使用合并转发，私聊则合并成一条消息发送。保留该配置项仅为兼容旧配置。

### 大模型（AI 解读）配置

开启后，`ba塔罗牌`、`ba占卜`、`ba运势`、`ba塔罗牌解读` 会在发送本地结果后，**再追加一条大模型生成的解读消息**；关闭时插件行为与本功能加入前完全一致。

| 配置项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `BATAROT_LLM_ENABLED` | bool | `false` | **总开关**，是否开启大模型辅助解读（写 `true` / `True` / `1` 都可以） |
| `BATAROT_LLM_API_BASE` | str | `https://api.deepseek.com/v1` | **接口地址**，OpenAI 兼容，写到 `/v1` 即可，插件会自动补 `/chat/completions` |
| `BATAROT_LLM_API_KEY` | str | 空 | **接口密钥**，形如 `sk-xxxx`，必填 |
| `BATAROT_LLM_MODEL` | str | `deepseek-chat` | 模型名称 |
| `BATAROT_LLM_SYSTEM_PROMPT` | str | 空 | 自定义占卜师人设，留空使用内置人设 |
| `BATAROT_LLM_TEMPERATURE` | float | `0.9` | 采样温度，越大越发散 |
| `BATAROT_LLM_MAX_TOKENS` | int | `800` | 单次解读最大长度，`0` 表示不发送该参数 |
| `BATAROT_LLM_TIMEOUT` | float | `60` | 单次请求超时（秒） |
| `BATAROT_LLM_COOLDOWN` | int | `10` | 同一用户两次 AI 解读的最小间隔（秒），`0` 表示不限制 |

最小可用配置示例（复制到 bot 根目录的 `.env` 并重启）：

```dotenv
BATAROT_LLM_ENABLED=true
BATAROT_LLM_API_BASE=https://api.deepseek.com/v1
BATAROT_LLM_API_KEY=sk-你的密钥
BATAROT_LLM_MODEL=deepseek-chat
```

常见服务商的 `BATAROT_LLM_API_BASE`：

| 服务商 | 接口地址 |
| --- | --- |
| DeepSeek | `https://api.deepseek.com/v1` |
| OpenAI | `https://api.openai.com/v1` |
| 月之暗面 Kimi | `https://api.moonshot.cn/v1` |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` |
| 阿里通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| SiliconFlow | `https://api.siliconflow.cn/v1` |
| 本地 Ollama | `http://127.0.0.1:11434/v1` |

> 只要服务商兼容 OpenAI 的 `/chat/completions` 协议即可直接填写使用；接口路径特殊的网关，也可以把完整地址（形如 `https://xxx/v1/chat/completions`）直接写进 `BATAROT_LLM_API_BASE`。
>
> 该功能无需额外安装依赖：请求优先使用插件已声明的 `aiohttp`，如果运行环境里没有 `aiohttp`，会自动回退到 Python 标准库，不会因为缺少 HTTP 库导致插件加载失败。

### 自定义占卜师人设（可选）

`BATAROT_LLM_SYSTEM_PROMPT` 可以整体替换内置人设，注意**只能写在一行内**：

```dotenv
BATAROT_LLM_SYSTEM_PROMPT=你是《碧蓝档案》里阿罗娜风格的塔罗牌占卜师，语气活泼亲切，每次解读控制在 150 字以内，不使用任何 Markdown 标记。
```

### AI 解读的行为说明

- AI 解读是**单独一条消息**，不会和原本的牌面图片挤在一起；本地占卜结果永远先发出，接口慢也不会影响它
- 提示词里会带上牌名、正逆位、牌阵位置、牌义，以及你在指令后追加的问题
- 同一用户连续使用受 `BATAROT_LLM_COOLDOWN` 限制，冷却中只回复一句提示，不会消耗 tokens
- 接口超时、401、余额不足、网络异常等情况只回复一句简短提示，并在机器人日志里记录详细原因，本地占卜流程不受影响
- AI 解读由大模型生成，仅作娱乐与自我反思的参考，不构成医疗、法律、投资建议；解读会消耗你的接口额度

## 🎉 使用

| 指令 | 别名 | 说明 |
| --- | --- | --- |
| `ba塔罗牌` | `batarot`、`tarot`、`塔罗牌` | 随机发送一张ba塔罗牌以及正逆位含义 |
| `ba占卜` | `divination`、`占卜` | 随机抽取一个塔罗牌牌阵占卜，群聊以合并转发发送，私聊合并成一条消息发送 |
| `ba运势` | `fortune`、`运势` | 随机发送一张ba塔罗牌以及对应的运势分数和运势评价 |
| `ba塔罗牌解读 [牌名或编号] [问题]` | `reading`、`塔罗牌解读` | 发送一张ba塔罗牌以及来自塔罗牌原画师大人 shi0n_krbn 的解读；不带参数时随机选一张 |

命令前缀：nonebot 默认 `COMMAND_START={"/"}`，此时实际输入形如 `/ba塔罗牌`；如果你的 bot 把 `COMMAND_START` 配置成 `[""]`，就可以直接输入 `ba塔罗牌`。

追加问题：4 个指令都支持在末尾写自己的问题，例如

    /ba塔罗牌 我最近的工作会顺利吗
    /ba塔罗牌解读 愚者 这段感情该怎么处理
    /ba占卜 我该不该换一个城市生活

开启 AI 解读后，大模型会结合抽到的牌与你写的问题作答（`ba塔罗牌解读` 还支持英文牌名，如 `/ba塔罗牌解读 The Fool`）。

## 💡 Q/A

- Q1:无法成功发送图片，输入指令后图片很久才响应，该如何解决？

  A1:这主要是图床的锅，使用魔法进行科学上网可以有效避免该问题。

     二编：已经改为从本地发送，第一次安装插件由于图片清晰度较高下载可能比较慢，建议使用魔法科学上网。

- Q2:出现插件无法正常加载相关报错该如何解决？

  A2:请先确认你已经安装了 nonebot-plugin-send-anything-anywhere（saa），并且是最新版本。

     如果没有安装请使用 pip install nonebot-plugin-send-anything-anywhere 在你机器人部署的虚拟环境中安装这个前置插件

     然后查看你的 pyproject 文件确保 nonebot_plugin_saa（nonebot-plugin-send-anything-anywhere）被正确写入并加载

- Q3：关于 pydantic / pydantic-settings

  A3:插件依赖 pydantic v2 + pydantic-settings，安装插件时会自动带上，不需要手动改 config.py。

     如果启动时报 No module named 'pydantic_settings'，在机器人虚拟环境里补装即可：

         pip install pydantic-settings

- Q4:我还有其他问题/报错，没有出现在上面，我也不知道该如何解决.

  A4:出现如无法加载图片，插件报错，前置插件版本冲突等问题，欢迎提issue，我会尽快解决。本插件为一时兴起写着玩的，出现解决不了的问题请自行寻找其他方案。

     如果你想给这个插件增加新的功能/补充完善代码，欢迎提pr。

     关于bot的安装配置问题，请去nb官方群聊进行咨询，我不负责也没有义务解答。

- Q5:AI 解读没有出现 / 提示「AI 解读暂时不可用」，怎么办？

  A5:请按顺序检查：

    1. `.env` 里写了 `BATAROT_LLM_ENABLED=true`（写 `True`、`1` 也可以），并且**重启了机器人**；
    2. `BATAROT_LLM_API_KEY` 已填写且没有多余空格；
    3. `BATAROT_LLM_API_BASE` 与 `BATAROT_LLM_MODEL` 是否属于同一家服务商（例如 DeepSeek 的 key 配 DeepSeek 的地址与 `deepseek-chat`）；
    4. 提示里会带上具体原因（如 `接口返回 401`、`请求超时`、`网络请求失败`），按提示排查网络或余额问题，机器人日志里也有更详细的记录；
    5. 提示「AI 解读冷却中」是正常现象，等待提示的秒数后再试即可，也可把 `BATAROT_LLM_COOLDOWN` 设为 `0` 关闭限制。

- Q6:输入 `ba塔罗牌` 没反应，但输入 `/ba塔罗牌` 有反应？

  A6:这是 nonebot 的命令前缀设置（`COMMAND_START`）导致的，默认必须带 `/`。

     想让机器人不带前缀也能识别，在 `.env` 里加一行 `COMMAND_START=[""]` 即可（把空字符串也加入允许的前缀列表，
     注意不要写成 `COMMAND_START=[]`，那样命令会完全无法触发）。

- Q7:AI 解读会花钱吗？牌面信息会被上传吗？

  A7:会消耗你自己配置的那家服务商的额度，每次大约几百 tokens；`BATAROT_LLM_COOLDOWN` 可以限制每人调用频率。

     请求内容只包含牌名、正逆位、牌义（`ba塔罗牌解读` 会额外带上原画师的解读文本）以及你写的问题，
     发送到你在 `BATAROT_LLM_API_BASE` 里填写的那个接口，插件本身不收集也不中转任何数据。

## 📞 制作者

### 黑纸折扇 [Perseus037] (https://github.com/Perseus037)

EMAIL：1209228678@qq.com

## 🙏 感谢

在此感谢以下开发者(项目)对本项目做出的贡献：

-  [shi0n_krbn](twitter@shi0n_krbn) Twitter塔罗牌原画作者，以及专业的解读

-  [CedarLullaby](https://space.bilibili.com/2910913) 提供的解读翻译

-  [student_2333](https://github.com/lgc2333) 的无私帮助

-  [Nicr0n](https://github.com/Nicr0n)  使插件实现多适配器支持

-  [nonebot_plugin_tarot](https://github.com/MinatoAquaCrews/nonebot_plugin_tarot) 提供的代码参考（~~直接开抄~~)

-  [nonebot-plugin-send-anything-anywhere](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere) 处理不同 adapter 消息的适配和发送

## 📝 更新日志

### 0.3.0

- 新增大模型（AI）辅助占卜：在 `.env` 中配置 `BATAROT_LLM_ENABLED` / `BATAROT_LLM_API_BASE` / `BATAROT_LLM_API_KEY` 等即可开启，兼容 OpenAI 风格的 `/chat/completions` 接口（DeepSeek、OpenAI、Kimi、智谱、通义、SiliconFlow、本地 Ollama 等）
- `ba塔罗牌`、`ba占卜`、`ba运势`、`ba塔罗牌解读` 均可在指令后追加自己的问题，AI 解读会结合问题作答
- 新增同一用户 AI 解读冷却时间、超时时间、生成长度与占卜师人设等可选项，接口异常时只发送简短提示，不影响本地占卜流程
- 配置项改为通过 nonebot 全局配置读取，`.env` / `.env.prod` / `.env.{ENVIRONMENT}` 均可生效，并新增带注释的 `.env.example`
- `ba塔罗牌解读` 的牌名匹配改用参数解析，修复了省略空格的写法会导致报错的问题，并支持英文牌名
- 修复 `ba占卜` 在私聊时拼接图片消息报 `ValueError: Unexpected type` 导致占卜失败的问题

### 0.2.2.post1-post4
- 将图片发送改为从本地读取，优化牌阵指令部分代码
- 优化关于合并转发部分的代码逻辑

### 0.2.1.post2-post3
- 更换图床来提高响应速度
- 修复塔罗牌图片错位问题

### 0.2.1.post1
- 使用nonebot_plugin_saa实现多适配器支持

### 0.2.0.post2-post3
- 修复ba占卜功能在私聊时无法发送的问题
- 修改部分运势描述语句中的错误描述

### 0.2.0.post1
- 修改了全部的运势描述语句，加入了大量对国内外电影，诗歌，小说中的引用，来让描述变得更优美
- 结合现实生活中的塔罗牌占卜，增加了六个新的占卜牌阵
  
### 0.2.0
- 改为使用base64发送图片，修复塔罗牌图片在pc端老版本qq上无法显示的问题
- 使用塔罗牌原图，提高了图像的清晰度

### 0.1.0 - 0.1.0.post4
- 修复各种bug
- 重构代码，对原有代码进行模块化拆分便于维护

</div>
