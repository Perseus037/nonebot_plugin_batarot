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

若我超脱自然，便将绝不再用，任何自然物化作身躯之外形。

而只求古希腊金匠人用鎏金，和镀金锤铸的绝美造型。

以使昏昏欲睡的帝王清醒，或停留在金色枝头声声歌唱。

把过往，今日，或明朝之事，唱给拜占庭的贵妇王公们听。

——威廉·巴特勒·叶芝《驶向拜占庭》

## 📖 介绍

一个可以进行测运势，魔法占卜与解读的碧蓝档案塔罗牌nonebot2插件

从本地读取图片并发送，使用nonebot_plugin_send_anything_anywhere已实现多适配器支持(onebot.v11, onebot.v12, qqguild，kaiheila, telegram, feishu, red)

目前暂有4个功能：ba塔罗牌，ba运势，ba占卜和ba塔罗牌解读，使用详见下方指令

请下载最新的发版！！！

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

ba占卜：默认以合并转发的方式随机发送一个塔罗牌牌阵进行占卜（私聊时发送的是消息段）。

ba运势：随机发送一张ba塔罗牌以及对应的运势分数和对应运势评价

ba塔罗牌解读：发送一张ba塔罗牌以及来自塔罗牌原画师大人shi0n_krbn的解读。

## 💡 Q/A
- Q1:无法成功发送图片，输入指令后图片很久才响应，该如何解决？

  A1:这主要是图床的锅，使用魔法进行科学上网可以有效避免该问题。
  
     原来用的国内图床，结果有很多日本网友给我发邮件要求我使用日本ip可以访问的图床(?),所以有时候国内ip访问图床可能会抽风。

     二编：已经改为从本地发送，第一次安装插件由于图片清晰度较高下载可能比较慢，建议使用魔法科学上网。
  


- Q2:出现插件无法正常加载相关报错该如何解决？

  A2:请先确认你已经安装了nonebot-plugin-send-anything-anywhere，并且是最新版本
  
     如果没有安装请使用pip install nonebot-plugin-send-anything-anywhere在你机器人部署的虚拟环境中安装这个前置插件
  
     然后查看你的pyproject文件确保nonebot_plugin_saa（nonebot-plugin-send-anything-anywhere）被正确写入并加载

  

- Q3:我还有其他问题/报错，没有出现在上面，我也不知道该如何解决.

  A3:出现如无法加载图片，插件报错，前置插件版本冲突等问题，欢迎提issue或直接qq私信我，我会尽快解决。
     
     如果你想给这个插件增加新的功能/补充完善代码，欢迎提pull request，我把你拉进来方便你直接改源码。

     关于bot的安装配置问题，请去nb官方群聊进行咨询，我不负责也没有义务解答。

## 📞 制作者

### 黑纸折扇 [Perseus037] (https://github.com/Perseus037)

EMAIL：1209228678@qq.com

企鹅：1209228678

## 🙏 感谢

在此感谢以下开发者(项目)对本项目做出的贡献：

-  [shi0n_krbn](twitter@shi0n_krbn) Twitter塔罗牌原画作者，以及专业的解读

-  [CedarLullaby](https://space.bilibili.com/2910913) 提供的解读翻译

-  [student_2333](https://github.com/lgc2333) 的无私帮助

-  [Nicr0n](https://github.com/Nicr0n)  使插件实现多适配器支持

-  [nonebot_plugin_tarot](https://github.com/MinatoAquaCrews/nonebot_plugin_tarot) 提供的代码参考（~~直接开抄~~)

-  [nonebot-plugin-send-anything-anywhere](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere) 处理不同 adapter 消息的适配和发送

## 📝 更新日志
### 0.2.2.post1-post2
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

