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
- `ba运势` 现为每日幸运牌：每群每人每天首次抽牌，幸运值从 10 开始累计；重复查询展示已保存的牌面和解读，不再抽牌或调用 AI
- 0.3.0 起支持**大模型（AI）辅助占卜**：在 `.env` 里配置接口地址与密钥后，原指令会在本地结果之后追加一段由大模型生成的解读，配置方法见下方「配置」章节，可直接复制 [.env.example](./.env.example)
- 0.3.0 同时修复了 `ba占卜` 私聊发送失败、`ba塔罗牌解读` 参数解析报错两个问题，详见「更新日志」

有问题请先自行去 Q/A 查看，请下载最新的发版！！！

## 💿 安装

### 前置条件

| 依赖 | 说明 |
| --- | --- |
| `nonebot2 >= 2.1.1` | 插件运行环境 |
| `nonebot-plugin-send-anything-anywhere`（saa） | **必需前置**，插件加载时会 `require("nonebot_plugin_saa")`，没装会直接加载失败 |
| `pydantic >= 1.10.13, < 3` | 支持 Pydantic 1/2，配置由 NoneBot 统一读取 |

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

### 关于 Pydantic 兼容性

本插件支持 Pydantic 1/2，不要求为了 AI 功能升级到 Pydantic 2，也不直接依赖 `pydantic-settings`。配置只从 NoneBot 已加载的全局配置中读取，不自行读取 `.env.prod`。其他插件的版本约束仍需由你的机器人环境满足。

## ⚙️ 配置

所有配置项都写在 **nonebot2 项目根目录**的 `.env`（或 `.env.prod` / `.env.{ENVIRONMENT}`）文件里，变量名大小写不敏感，推荐全大写。插件仓库根目录提供了带注释的示例文件 [.env.example](./.env.example)，可按需复制。

### 牌阵发送配置

```dotenv
# false：OneBot v11 群聊合并转发；true：一条普通图文长消息
FORWARD_MODE=false
```

私聊及其他适配器使用普通图文消息；群聊合并转发失败时也回退为一条普通图文消息。

### 每日幸运牌与 AI 额度

| 配置项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `BATAROT_DATA_FILE` | path | `data/batarot/state.json` | 状态文件；相对路径以机器人工作目录为基准 |
| `BATAROT_INITIAL_LUCK` | int | `10` | 新用户在当前群的初始累计幸运值，不会覆盖已有累计值 |
| `BATAROT_LUCK_MIN` | int | `-5` | 逆位变化下限，可设为 `-5`～`0`；非零时在下限至 `-1` 中随机，设为 `0` 时逆位不扣分 |
| `BATAROT_LUCK_MAX` | int | `5` | 正位变化上限，可设为 `0`～`5`；非零时在 `1` 至上限中随机，设为 `0` 时正位不加分 |
| `BATAROT_LLM_DAILY_LIMIT` | int | `3` | 每群每人每日普通占卜 AI 请求上限；`0` 关闭这部分 AI，基础抽牌不受影响 |
| `BATAROT_DAY_UTC_OFFSET` | int | `8` | 每日重置所用 UTC 时差，整数 `-12`～`14`；默认北京时间零点日切 |

- `ba运势` 每天首次随机抽取一张幸运牌与正逆位，默认正位加 `1`～`5`、逆位减 `1`～`5`，累计值可以为负数。只在首次抽牌时加减一次。
- 当天再次发送 `ba运势`，先提示已经抽取，再展示当天的牌面、幸运变化、累计值与已保存解读。重复查询、更换问题和重启机器人都不会重新抽牌或请求 AI。
- `ba塔罗牌`、`ba占卜`、`ba塔罗牌解读` 共用普通 AI 日额度；幸运牌首次解读独立于这 3 次额度。关闭 AI 时仍可使用所有基础抽牌功能。
- 数据、日额度、冷却及同用户在途限制均按群和用户隔离，同一人在不同群独立使用。私聊独立保存；不同适配器和机器人账号也分别记录。
- 真正开始尝试的普通 AI 请求即占用一次额度；AI 关闭、配置不完整、冷却中、已有请求或全局并发已满时不扣额度。
- 幸运牌只在首次抽取时尝试 AI。已有同用户请求或全局并发已满时，最多等待 `BATAROT_LLM_TIMEOUT + 2` 秒获取名额，获取后再按原请求超时调用模型；等待时不占并发或普通日额度。等待耗尽、调用失败、中断或未开启 AI 时，当天均不补请求，已抽牌和幸运值仍保留。

状态文件保存每个群用户的累计值、最近一次幸运牌及 AI 解读、最近一天普通 AI 次数，不追加每日历史。首次 AI 请求前先保存牌面，再写回解读；同一进程内串行更新并原子替换文件。首次幸运牌会等待解读完成或失败后，一并发送牌面与解读。

机器人需要状态目录的读写权限。**同一数据文件仅供一个机器人进程使用**，多实例应配置不同路径。文件损坏或无法读写时停止对应的存档/额度操作，不自动清空或重置；请从备份恢复。该文件包含累计值和用户标识，不应当作临时缓存删除，也不要提交到公开仓库。

### 大模型（AI 解读）配置

开启后，普通占卜在本地结果后追加一条 AI 解读；每日幸运牌将首次 AI 解读与牌面一同保存、发送。关闭时不调用模型接口。

| 配置项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `BATAROT_LLM_ENABLED` | bool | `false` | **总开关**，是否开启大模型辅助解读（写 `true` / `True` / `1` 都可以） |
| `BATAROT_LLM_API_BASE` | str | `https://api.deepseek.com/v1` | **接口地址**，OpenAI 兼容，写到 `/v1` 即可，插件会自动补 `/chat/completions` |
| `BATAROT_LLM_API_KEY` | str | 空 | **接口密钥**，开启 AI 时填写；基础抽牌不需要 |
| `BATAROT_LLM_MODEL` | str | `deepseek-flash` | 模型名称，须与服务商当前提供的模型对应 |
| `BATAROT_LLM_THINKING` | bool | `false` | 对支持切换的接口/模型发送思考模式设置 |
| `BATAROT_LLM_THINKING_PROVIDER` | str | `auto` | `auto`、`deepseek`、`siliconflow`、`none`，见下方说明 |
| `BATAROT_LLM_SYSTEM_PROMPT` | str | 空 | 自定义占卜师人设，留空使用内置人设 |
| `BATAROT_LLM_TEMPERATURE` | float | `0.9` | 采样温度，越大越发散 |
| `BATAROT_LLM_MAX_TOKENS` | int | `800` | 单次解读最大长度，`0` 表示不发送该参数 |
| `BATAROT_LLM_TIMEOUT` | float | `60` | 单次请求超时（秒） |
| `BATAROT_LLM_COOLDOWN` | int | `10` | 同群同用户普通 AI 解读的最小间隔（秒），`0` 表示不限制；每日幸运牌首次解读不检查此间隔 |
| `BATAROT_LLM_MAX_CONCURRENCY` | int | `2` | 全插件最大同时 AI 请求数，可设为 `1`～`8` |
| `BATAROT_LLM_MAX_QUESTION_CHARS` | int | `1000` | 发送给模型的问题字符上限，可设为 `1`～`10000`，超出部分截断 |
| `BATAROT_LLM_INPUT_PRICE_PER_MILLION` | float | 空 | 每百万输入 token 价格，可选非负数；用于日志估算费用 |
| `BATAROT_LLM_OUTPUT_PRICE_PER_MILLION` | float | 空 | 每百万输出 token 价格，可选非负数；两项价格使用同一币种 |

`THINKING_PROVIDER=auto` 对 DeepSeek 官方地址发送 `thinking.type`，对硅基流动已识别的 Qwen3、DeepSeek-V3.1/V3.2、GLM-4.5/4.6 系列发送 `enable_thinking`，排除 Instruct、Embedding、Reranker 名称。其他模型（如 Ling）不盲目添加思考参数。自建网关可在确认兼容后显式选 `deepseek` 或 `siliconflow`；选 `none` 完全不发送思考参数。模型支持情况以服务商为准，这个开关不保证任意模型都能关闭思考。使用其它平台模型请务必自己核对参数。

最小可用配置示例（复制到 bot 根目录的 `.env` 并重启）：

```dotenv
BATAROT_LLM_ENABLED=true
BATAROT_LLM_API_BASE=https://api.deepseek.com/v1
BATAROT_LLM_API_KEY=
BATAROT_LLM_MODEL=deepseek-flash
```

示例密钥留空，请自行填写后再启用。

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

> DeepSeek 的旧模型名 `deepseek-chat` / `deepseek-reasoner` 已列入官方停用公告。此处按当前文档使用 `deepseek-flash`，并默认关闭思考模式。参见 [模型文档](https://api-docs.deepseek.com/quick_start/pricing/) 和 [思考模式](https://api-docs.deepseek.com/guides/thinking_mode/)。使用本地 Ollama 时，密钥可填占位值 `ollama`，模型名填写你已下载的模型。云接口消耗部署者自己的账户额度，插件不提供免费 Key。

### 自定义占卜师人设（可选）

`BATAROT_LLM_SYSTEM_PROMPT` 可以整体替换内置人设，注意**只能写在一行内**：

```dotenv
BATAROT_LLM_SYSTEM_PROMPT=你是《碧蓝档案》里阿罗娜风格的塔罗牌占卜师，语气活泼亲切，每次解读控制在 150 字以内，不使用任何 Markdown 标记。
```

### AI 解读与资源使用

- 普通占卜先发送基础结果，再单独发送 AI 解读；每日幸运牌等待首次解读后统一发送，后续直接复用存档
- 提示词里会带上牌名、正逆位、牌阵位置、牌义，以及你在指令后追加的问题
- 普通 AI 受每群每人日额度、冷却和全局并发保护，忙碌时立即提示；幸运牌首次解读会限时等待同用户在途与全局并发名额
- 接口超时、401、余额不足、网络异常等情况只回复固定分类提示；日志记录相同的安全提示或异常类型，不记录服务商原始报错正文、密钥或用户问题
- 请求不自动重试。`batarot_usage` 日志记录耗时、状态、服务商返回的 token 用量及可选估算费用；未返回的用量保留未知，估算不等于账户实际扣费
- 静态牌义 JSON 读取后复用；压缩图片使用最多 16 项内存缓存，图片处理最多 2 个后台任务，不另建图片磁盘缓存。原始牌图仍从插件资源目录读取
- AI 解读由大模型生成，仅作娱乐与自我反思的参考，不构成医疗、法律、投资建议；解读会消耗你的接口额度

## 🎉 使用

| 指令 | 别名 | 说明 |
| --- | --- | --- |
| `ba塔罗牌` | `batarot`、`tarot`、`塔罗牌` | 随机发送一张ba塔罗牌以及正逆位含义 |
| `ba占卜` | `divination`、`占卜` | 随机抽取塔罗牌牌阵，按 `FORWARD_MODE` 发送 |
| `ba运势` | `fortune`、`运势` | 每群每人每日一张幸运牌，累计幸运值，重复查询回显当天存档 |
| `ba塔罗牌解读 [牌名或编号] [问题]` | `reading`、`塔罗牌解读` | 发送一张ba塔罗牌以及来自塔罗牌原画师大人 shi0n_krbn 的解读；不带参数时随机选一张 |

命令前缀：nonebot 默认 `COMMAND_START={"/"}`，此时实际输入形如 `/ba塔罗牌`；如果你的 bot 把 `COMMAND_START` 配置成 `[""]`，就可以直接输入 `ba塔罗牌`。

追加问题：4 个指令都支持在末尾写自己的问题，例如

    /ba塔罗牌 我最近的工作会顺利吗
    /ba塔罗牌解读 愚者 这段感情该怎么处理
    /ba占卜 我该不该换一个城市生活

开启 AI 解读后，大模型会结合抽到的牌与你写的问题作答（`ba塔罗牌解读` 还支持英文牌名，如 `/ba塔罗牌解读 The Fool`）。

`ba运势` 仅使用首次抽取时的问题；重复发送不会用新问题重写解读。本次将原有 `ba运势` 改为幸运牌，没有另加一套“今日运势”命令。

## 💡 Q/A

- Q1:无法成功发送图片，输入指令后图片很久才响应，该如何解决？

  A1:这主要是图床的锅，使用魔法进行科学上网可以有效避免该问题。

     二编：已经改为从本地发送，第一次安装插件由于图片清晰度较高下载可能比较慢，建议使用魔法科学上网。

- Q2:出现插件无法正常加载相关报错该如何解决？

  A2:请先确认你已经安装了 nonebot-plugin-send-anything-anywhere（saa），并且是最新版本。

     如果没有安装请使用 pip install nonebot-plugin-send-anything-anywhere 在你机器人部署的虚拟环境中安装这个前置插件

     然后查看你的 pyproject 文件确保 nonebot_plugin_saa（nonebot-plugin-send-anything-anywhere）被正确写入并加载

- Q3：关于 Pydantic 版本

  A3:本插件兼容 Pydantic 1/2，无需手动修改 config.py，也无需为本插件单独安装 pydantic-settings。

- Q4:我还有其他问题/报错，没有出现在上面，我也不知道该如何解决.

  A4:出现如无法加载图片，插件报错，前置插件版本冲突等问题，欢迎提issue，我会尽快解决。本插件为一时兴起写着玩的，出现解决不了的问题请自行寻找其他方案。

     如果你想给这个插件增加新的功能/补充完善代码，欢迎提pr。

     关于bot的安装配置问题，请去nb官方群聊进行咨询，我不负责也没有义务解答。

- Q5:AI 解读没有出现 / 提示「AI 解读暂时不可用」，怎么办？

  A5:请按顺序检查：

    1. `.env` 里写了 `BATAROT_LLM_ENABLED=true`（写 `True`、`1` 也可以），并且**重启了机器人**；
    2. `BATAROT_LLM_API_KEY` 已填写且没有多余空格；
    3. `BATAROT_LLM_API_BASE` 与 `BATAROT_LLM_MODEL` 是否属于同一家服务商（例如 DeepSeek 的 key 配 DeepSeek 的地址与 `deepseek-flash`）；
    4. 根据安全分类提示（如鉴权失败、余额不足、超时）检查配置或服务商控制台；插件不透传接口原始报错；
    5. 提示「AI 解读冷却中」是正常现象；普通 AI 当日额度用完后需等日切。幸运牌当天首次未生成解读时不会补请求，重新查询只展示存档。

- Q6:输入 `ba塔罗牌` 没反应，但输入 `/ba塔罗牌` 有反应？

  A6:这是 nonebot 的命令前缀设置（`COMMAND_START`）导致的，默认必须带 `/`。

     想让机器人不带前缀也能识别，在 `.env` 里加一行 `COMMAND_START=[""]` 即可（把空字符串也加入允许的前缀列表，
     注意不要写成 `COMMAND_START=[]`，那样命令会完全无法触发）。

- Q7:AI 解读会花钱吗？牌面信息会被上传吗？

  A7:会消耗你自己配置的那家服务商的额度；`BATAROT_LLM_DAILY_LIMIT`、冷却及最大生成长度可控制调用量，实际 token 用量以服务商返回值为准。

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

### 0.5.0

- `ba运势` 改为每群每人每日幸运牌：初始幸运值 10，默认正位 `+1`～`+5`、逆位 `-5`～`-1`，支持累计负值及配置范围；默认北京时间零点刷新，可配置时差。
- JSON 保存累计值、当天牌面和首次 AI 解读；重复查询回显，不重抽、不重复加减或调用 AI。原子写入、并发去重、重启复用，损坏存档不自动重置。
- 其他三条命令共用每群每人每日 AI 额度，默认 3 次；幸运牌独立。补充全局并发、问题长度、请求用量及可选费用估算。
- 思考参数兼容 DeepSeek 与硅基流动已识别模型，支持手动选择接口格式；不向未识别模型盲发参数。
- 缓存静态数据和压缩图片，将图像处理移至后台；修复取消时后台 HTTP/图像线程仍运行却提前释放并发名额的问题。
- 修复牌阵逆位图片、缺图坏图降级、多词英文牌名带问题解析及 `FORWARD_MODE`；合并转发失败只回退一条图文消息，兼容 Pillow 9.0 旋转常量。
- 移除未使用的 htmlrender、apscheduler 依赖；增加离线回归测试与 Python/Pydantic 兼容性 CI，不调用真实模型或发送聊天消息。

本地运行测试：

```shell
python -m unittest discover -s tests -v
```

### 0.3.0

- 修复通用命令参数绑定 OneBot v11 消息类型的问题；`ba占卜` 原有的转发实现仍仅支持 OneBot v11
- 配置只读取 NoneBot 当前环境，支持 Pydantic 1/2；API 报错不再透传原文
- 牌阵一次选择一套位置并按牌序对应；维持原有抽牌数量，时间之流牌阵使用过去、现在、未来三个位置，未实现的额外切牌位置不参与解读
- 更新 DeepSeek 默认模型及示例，并为官方接口增加思考模式开关
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
