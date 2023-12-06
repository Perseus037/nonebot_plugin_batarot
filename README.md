<div align="center">
  <img src="https://github.com/Perseus037/nonebot_plugin_batarot/blob/main/Alice%20tarot%20picture.jpg" alt="碧蓝档案塔罗牌占卜" >

# NoneBot-Plugin-Batarot

_🔮 一个可以进行测运势，占卜的碧蓝档案塔罗牌nonebot2插件🔮 _

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

## 📖 介绍

一个可以进行测运势，魔法占卜与解读碧蓝档案塔罗牌nonebot2插件

目前暂时有4个功能：ba塔罗牌，ba运势，ba占卜和ba塔罗牌解读，使用详见下方指令

自己推的国内仓库，无需担心从github下载图片的一次次报错和网络加载失败等问题

有任何问题可以直接提issue或者发email到qq邮箱，我会尽快解决喵，如果愿意提供一些更优美的运势预测句子更好喵。

## 💿 安装

建议使用包管理器（nb plugin install nonebot_plugin_batarot）直接安装

如果使用gitclone安装的话，请将文件下载到site——package文件夹下，
然后打开 nonebot2 项目根目录下的 `pyproject.toml` 文件,在 `[tool.nonebot]` 部分的 `plugins` 项里追加写入nonebot_plugin_babattleline即可

<!--
<details open>
<summary>[推荐] 使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

```bash
nb plugin install nonebot_plugin_batarot
```
-->

</details>

<details open>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details open>
<summary>pip</summary>

```bash
pip install nonebot_plugin_batarot
```

</details>
<details>
<summary>pdm</summary>

```bash
pdm add nonebot_plugin_batarot
```

</details>
<details>
<summary>poetry</summary>

```bash
poetry add nonebot_plugin_batarot
```

</details>
<details>
<summary>conda</summary>

```bash
conda install nonebot_plugin_batarot
```

</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分的 `plugins` 项里追加写入

```toml
[tool.nonebot]
plugins = [
    # ...
    "nonebot_plugin_batarot"
]
```

</details>

## ⚙️ 配置

无需配置，开箱即用。

## 🎉 使用

现有指令列表：

ba塔罗牌：随机发送一张ba塔罗牌以及正逆位含义

ba占卜：以合并转发的方式发送一个牌阵进行占卜

ba运势：随机发送一张ba塔罗牌以及对应的运势分数和对应的运势评价

ba塔罗牌解读：发送一张ba塔罗牌以及塔罗牌原画师的解读，支持如：ba塔罗牌解读 21 或 ba塔罗牌解读 世界的命令，实现指定塔罗牌解读。

 
## 📞 制作者

### 黑纸折扇 [Perseus037] (https://github.com/Perseus037)

QQ：1209228678

## 🙏 感谢

### shi0n_krbn（twitter@shi0n_krbn)提供的超好看ba塔罗牌和专业的解读

### CedarLullaby（https://space.bilibili.com/2910913) 提供的翻译

### student_2333 (https://github.com/lgc2333) 对于我学习编写插件和配置qqbot等过程中的无私帮助

### KafCoppelia （https://github.com/KafCoppelia) 提供的思路借鉴（~~直接开抄~~) 

## 📝 更新日志

### 0.2.0.post1
- 修改了全部的运势描述语句，加入了大量对国内外电影，诗歌，小说中的引用，来让所有描述变得更优美
- 结合现实生活中的塔罗牌占卜，增加了六个新的占卜牌阵
  
### 0.2.0
- 修复塔罗牌图片在pc端老版本qq上无法显示的问题
- 使用塔罗牌原图，提高了图像的清晰度

### 0.1.0 - 0.1.0.post4

- 修复各种bug
- 重构代码，对原有代码进行模块化拆分便于维护

