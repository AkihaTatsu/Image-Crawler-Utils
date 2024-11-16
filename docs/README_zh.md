<h1 align="center">
Image Crawler Utils
</h1>
<h4 align="center">
一个可自定义的多网站图像爬取框架
</h4>
<p align="center">
<a href="../README.md">English</a> | 简体中文
</p>

---

## 关于本项目

一个**相对可自定义**的图像爬取框架，允许使用多线程方法下载图像及其信息。

同时，此框架内包含数个有助于更好地构建自定义图像爬取程序的轮子。

**请遵循robots.txt所设定的爬取程序要求，并在爬取时自觉设置较低的线程数和较高的延迟时间。过于频繁的请求和巨大的下载流量可能会导致IP地址被封禁或账号被暂停。**

## 安装

建议通过以下命令安装：

```Default
pip install -i https://test.pypi.org/simple/ image-crawler-utils
```

+ 需要`Python >= 3.9`环境。

### 注意！

+ **[nodriver](https://github.com/ultrafunkamsterdam/nodriver)** 被此项目用于从部分网站上解析信息。建议提前安装 **最新版本的 [Google Chrome](https://www.google.com/chrome/)** 以保证爬取程序的正常运行。

## 功能（部分）

+ 当前支持的网站：
  + [Danbooru](https://danbooru.donmai.us/) - 支持的功能：
    + 下载根据关键词 / 标签搜索到的图片
  + [yande.re](https://yande.re/) / [konachan.com](https://konachan.com/) / [konachan.net](https://konachan.net/) - 支持的功能：
    + 下载根据关键词 / 标签搜索到的图片
  + [Gelbooru](https://gelbooru.com/) - 支持的功能：
    + 下载根据关键词 / 标签搜索到的图片
  + [Safebooru](https://safebooru.org/) - 支持的功能：
    + 下载根据关键词 / 标签搜索到的图片
  + [Pixiv](https://www.pixiv.net/) - 支持的功能：
    + 下载根据关键词 / 标签搜索到的图片
    + 下载某一成员（用户）上传的所有图片
  + [Twitter / X](https://x.com/) - 支持的功能：
    + 从搜索结果中下载所有的图片
    + 下载某一用户发布的所有图片
+ 日志记录爬取程序的操作到控制台以及（可选的）文件中。
+ 使用`tqdm`进度条表示爬取程序的进度。
+ 保存或加载爬取的设置。
+ 保存或加载所有图片的信息，以便于未来的爬取。
+ 数个用于设计自定义图片爬取程序的类和函数。

## 如何使用

完整信息请参考[教程](tutorials_zh.md)和[网站任务说明（English）](notes_for_tasks.md)。

### 快速开始

Image Crawler Utils提供了三个相互独立的模块以构建图片爬取程序：

+ **爬取程序设置（CrawlerSettings）：** 有关下载和调试爬取程序的基本配置。除站点链接（station_url）之外的每个参数均为可选项，并将在留空的情况下使用默认值（参见[教程](tutorials_zh.md)）。一个完整的爬取程序设置参数列表如下所示：

```Python
from image_crawler_utils import CrawlerSettings
from image_crawler_utils.configs import DebugConfig

crawler_settings = CrawlerSettings(
    # 限制下载数量和流量的配置
    image_num: int | None=None,
    capacity: float | None=None,
    page_num: int | None=None,
    # 下载参数的配置
    headers: dict | Callable | None=None,
    proxies: dict | Callable | None=None,
    thread_delay: float=5,
    fail_delay: float=3,
    randomize_delay: bool=True,
    thread_num: int=5,
    timeout: float | None=10,
    max_download_time: float | None=None,
    retry_times: int=5,
    overwrite_images: bool=True,
    # 控制在控制台上显示信息的配置
    debug_config=DebugConfig(
        show_debug: bool=False,
        show_info: bool=True,
        show_warning: bool=True,
        show_error: bool=True,
        show_critical: bool=True,
    ),
    # 自行使用时的额外参数
    extra_configs={
        "arg_name": "config", 
        "arg_name2": "config2", 
        ...
    },
)
```

+ **解析器（Parser）：** 解析参数，访问并爬取网站，最后返回一个包含图片URL和信息的列表。不同的任务需要不同的解析器。一个能正确运行的解析器应当遵循如下形式：

```Python
# import SomeParser from image_crawler_utils.stations.some_station

parser = SomeParser(crawler_settings, parser_args)
image_info_list = parser.run()


# 样例
from image_crawler_utils.stations.booru import DanbooruKeywordParser

parser = DanbooruKeywordParser(
    crawler_settings=crawler_settings,
    standard_keyword_string="kuon_(utawarerumono) AND rating:safe",
)
image_info_list = parser.run()
```

+ **下载器（Downloader）：** 下载使用image_filter参数筛选过后的、由解析器生成的图片列表。一个完整的下载器参数列表如下所示：

```Python
from image_crawler_utils import Downloader

downloader = Downloader(
    crawler_settings: CrawlerSettings=CrawlerSettings(),
    image_info_list: Iterable[ImageInfo],
    store_path: str | Iterable[str]='./',
    image_info_filter: Callable | bool=True,
    cookies: Cookies | list | dict | str | None=Cookies(),
)
total_size, succeeded_image_list, failed_image_list, skipped_image_list = downloader.run()
```

### 样例

运行此[样例](../examples/example.py)将会在[Danbooru](https://danbooru.donmai.us/)上搜索关键词 / 标签为`kuon_(utawarerumono)`和`rating:general`的图片，并将前20张图片下载到“Danbooru”文件夹中。图片信息将会存储在与你的程序同一目录下的`image_info_list.json`文件中。注意代理可能需要手动进行更改。

```Python
from image_crawler_utils import CrawlerSettings, Downloader, save_image_infos
from image_crawler_utils.stations.booru import DanbooruKeywordParser

crawler_settings = CrawlerSettings(
    image_num=20,
    # If you do not use system proxies, remove '#' and set this manually
    # proxies={"https": "socks5://127.0.0.1:7890"},
)

parser = DanbooruKeywordParser(
    crawler_settings=crawler_settings,
    standard_keyword_string="kuon_(utawarerumono) AND rating:general",
)
image_info_list = parser.run()
save_image_infos(image_info_list, "image_info_list")
downloader = Downloader(
    crawler_settings=crawler_settings,
    store_path='Danbooru',
    image_info_list=image_info_list,
)
downloader.run()
```

## 文档

+ [教程](tutorials_zh.md): 关于如何设置爬取程序参数，完成一个爬取程序程序，并从Danbooru上根据关键词 / 标签下载图片的详细教程。
+ [网站任务说明（English）](notes_for_tasks.md): 包含每个支持的网站和爬取任务的说明与样例。
+ [构建一个爬取程序（English）](building_a_crawler.md): 提供此项目内各结构、可用类及函数的信息。