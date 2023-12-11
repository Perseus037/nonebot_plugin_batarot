<div align="center">
  <img src="https://github.com/Perseus037/nonebot_plugin_batarot/blob/main/Alice%20tarot%20picture.jpg" alt="碧蓝档案塔罗牌占卜图标" >

# nonebot-plugin-batarot

_🔮 一个可以进行测运势，魔法占卜与解读的碧蓝档案塔罗牌nonebot2插件🔮 _

<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">
<a href="https://pdm.fming.dev">
  <img src="https://img.shields.io/badge/pdm-managed-blueviolet" alt="pdm-managed">
</a>
<!-- <a href="https://wakatime.com/badge/user/b61b0f9a-f40b-4c82-bc51-0a75c67bfccf/project/f4778875-45a4-4688-8e1b-b8c844440abb">
  <img src="https://wakatime.com/badge/user/b61b0f9a-f40b-4c82-bc51-0a75c67bfccf/project/f4778875-45a4-4688-8e1b-b8c844440abb.svg" alt="wakatime">
</a> -->

<br />

<a href="./LICENSE">
  <img src="https://img.shields.io/github/license/lgc-NB2Dev/nonebot-plugin-uma.svg" alt="license">
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

"许多人都会选择在塔罗牌的指引下探索未知：宇宙的秘密、月亮的暗面、星辰的指引、潜意识的呢喃、命运的征兆、时间的涟漪、以及自我真实的倒影。"

by 伦道夫·卡特

## 📖 介绍

一个可以进行测运势，魔法占卜与解读的碧蓝档案塔罗牌nonebot2插件

目前暂时有4个功能：ba塔罗牌，ba运势，ba占卜和ba塔罗牌解读，使用详见下方指令

自己推的国内仓库，无需担心从github下载图片的一次次报错和网络加载失败等问题

ps：有任何问题或建议可以直接提issue或者发email到qq邮箱，我会尽快解决/实现。

## 💿 安装

</details>
<summary>使用 nb-cli 安装（推荐）</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-batarot

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot-plugin-batarot[all]

</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-batarot[all]

</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-batarot[all]

</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-batarot[all]

</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_batarot"]

</details>

## ⚙️ 配置

无需配置，开箱即用。

## 🎉 使用

现有指令列表：

ba塔罗牌：随机发送一张ba塔罗牌以及正逆位含义

ba占卜：默认以合并转发的方式随机发送一个牌阵进行占卜（私聊时发送的是消息段）

ba运势：随机发送一张ba塔罗牌以及对应的运势分数和对应运势评价

ba塔罗牌解读：发送一张ba塔罗牌以及塔罗牌原画师的解读，支持如：ba塔罗牌解读 21 或 ba塔罗牌解读 世界的命令，实现指定塔罗牌解读。

## 💡 Q/A

-  Q1: 如果出现运行插件报错ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED]该如何解决(ssl证书验证报错）

   A1: 先使用pip install --upgrade certifi指令尝试更新python的证书库，
       你的梯子配置的是system proxy也可能会导致该报错，改为tun模式使用虚拟网卡就可以通过ssl验证了。
       如果使用上述方法都没有解决问题
       将utils.py中，async with session.get(url) as response:
       加参数改为async with session.get(url, ssl=False) as response 就可以避免报错（缺点是有一定安全风险，非必要不建议）

## 📞 制作者

### 黑纸折扇 [Perseus037] (https://github.com/Perseus037)

QQ：1209228678

## 🙏 感谢

在此感谢以下开发者(项目)对本项目做出的贡献：

-  [shi0n_krbn](twitter@shi0n_krbn) 提供的超好看ba塔罗牌原画和专业的解读

-  [CedarLullaby](https://space.bilibili.com/2910913) 提供的解读翻译

-  [student_2333](https://github.com/lgc2333) 对于我学习编写插件和配置qqbot等过程中的无私帮助

-  [nonebot_plugin_tarot](https://github.com/MinatoAquaCrews/nonebot_plugin_tarot) 提供的代码参考（~~直接开抄~~) 

## 📝 更新日志

### 0.2.0.post2
- 修复ba占卜功能在私聊时无法发送的问题
- 修改部分运势描述语句中的错误描述

### 0.2.0.post1
- 修改了全部的运势描述语句，加入了大量对国内外电影，诗歌，小说中的引用，来让描述变得更优美
- 结合现实生活中的塔罗牌占卜，增加了六个新的占卜牌阵
  
### 0.2.0
- 修复塔罗牌图片在pc端老版本qq上无法显示的问题
- 使用塔罗牌原图，提高了图像的清晰度

### 0.1.0 - 0.1.0.post4

- 修复各种bug
- 重构代码，对原有代码进行模块化拆分便于维护

