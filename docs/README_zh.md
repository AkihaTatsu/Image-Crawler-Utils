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

一个**相对可自定义**的图像爬取框架，允许使用多线程方法下载图像及其信息。如下GIF为一个爬取样例程序在控制台上得到的结果：

![](example.gif)

同时，此框架内包含数个有助于更好地构建自定义图像爬取程序的[类与函数（English）](classes_and_functions.md)。

**请遵循robots.txt所设定的爬取程序要求，并在爬取时自觉设置较低的线程数和较高的延迟时间。过于频繁的请求和巨大的下载流量可能会导致IP地址被封禁或账号被暂停。**

## 安装

建议通过以下命令安装：

```Default
pip install image-crawler-utils
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
+ 使用`rich`进度条和日志信息显示爬取程序的进度（包含对Jupyter Notebook的支持）。
+ 保存或读取爬取的设置与配置。
+ 保存或读取所有图片的信息，以便于未来的爬取。
+ 获取及管理部分网站的cookies，包括对其进行保存与读取。
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
    # 日志设置
    detailed_console_log: bool=False,
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

在保存的`image_info_list.json`中，一张图片的信息如下所示：

<details>
<summary><b>ImageInfo Structure in JSON</b></summary>

```json
{
    "url": "https://cdn.donmai.us/original/cd/91/cd91f0000b9574bf142d125a1e886e5c.png",
    "name": "Danbooru 4994142 cd91f0000b9574bf142d125a1e886e5c.png",
    "info": {
        "info": {
            "id": 4994142,
            "created_at": "2021-12-21T08:02:13.706-05:00",
            "uploader_id": 772564,
            "score": 10,
            "source": "https://i.pximg.net/img-original/img/2020/08/11/12/41/43/83599609_p0.png",
            "md5": "cd91f0000b9574bf142d125a1e886e5c",
            "last_comment_bumped_at": null,
            "rating": "s",
            "image_width": 2000,
            "image_height": 2828,
            "tag_string": "1girl absurdres animal_ears black_eyes black_hair coat grabbing_own_breast hair_ornament hairband highres holding holding_mask japanese_clothes kuon_(utawarerumono) long_hair looking_at_viewer mask ponytail shirokuro_neko_(ouma_haruka) smile solo utawarerumono utawarerumono:_itsuwari_no_kamen",
            "fav_count": 10,
            "file_ext": "png",
            "last_noted_at": null,
            "parent_id": null,
            "has_children": false,
            "approver_id": null,
            "tag_count_general": 17,
            "tag_count_artist": 1,
            "tag_count_character": 1,
            "tag_count_copyright": 2,
            "file_size": 4527472,
            "up_score": 10,
            "down_score": 0,
            "is_pending": false,
            "is_flagged": false,
            "is_deleted": false,
            "tag_count": 23,
            "updated_at": "2024-07-10T12:21:31.782-04:00",
            "is_banned": false,
            "pixiv_id": 83599609,
            "last_commented_at": null,
            "has_active_children": false,
            "bit_flags": 0,
            "tag_count_meta": 2,
            "has_large": true,
            "has_visible_children": false,
            "media_asset": {
                "id": 5056745,
                "created_at": "2021-12-21T08:02:04.132-05:00",
                "updated_at": "2023-03-02T04:43:15.608-05:00",
                "md5": "cd91f0000b9574bf142d125a1e886e5c",
                "file_ext": "png",
                "file_size": 4527472,
                "image_width": 2000,
                "image_height": 2828,
                "duration": null,
                "status": "active",
                "file_key": "nxj2jBet8",
                "is_public": true,
                "pixel_hash": "5d34bcf53ddde76fd723f29aae5ebc53",
                "variants": [
                    {
                        "type": "180x180",
                        "url": "https://cdn.donmai.us/180x180/cd/91/cd91f0000b9574bf142d125a1e886e5c.jpg",
                        "width": 127,
                        "height": 180,
                        "file_ext": "jpg"
                    },
                    {
                        "type": "360x360",
                        "url": "https://cdn.donmai.us/360x360/cd/91/cd91f0000b9574bf142d125a1e886e5c.jpg",
                        "width": 255,
                        "height": 360,
                        "file_ext": "jpg"
                    },
                    {
                        "type": "720x720",
                        "url": "https://cdn.donmai.us/720x720/cd/91/cd91f0000b9574bf142d125a1e886e5c.webp",
                        "width": 509,
                        "height": 720,
                        "file_ext": "webp"
                    },
                    {
                        "type": "sample",
                        "url": "https://cdn.donmai.us/sample/cd/91/sample-cd91f0000b9574bf142d125a1e886e5c.jpg",
                        "width": 850,
                        "height": 1202,
                        "file_ext": "jpg"
                    },
                    {
                        "type": "original",
                        "url": "https://cdn.donmai.us/original/cd/91/cd91f0000b9574bf142d125a1e886e5c.png",
                        "width": 2000,
                        "height": 2828,
                        "file_ext": "png"
                    }
                ]
            },
            "tag_string_general": "1girl animal_ears black_eyes black_hair coat grabbing_own_breast hair_ornament hairband holding holding_mask japanese_clothes long_hair looking_at_viewer mask ponytail smile solo",
            "tag_string_character": "kuon_(utawarerumono)",
            "tag_string_copyright": "utawarerumono utawarerumono:_itsuwari_no_kamen",
            "tag_string_artist": "shirokuro_neko_(ouma_haruka)",
            "tag_string_meta": "absurdres highres",
            "file_url": "https://cdn.donmai.us/original/cd/91/cd91f0000b9574bf142d125a1e886e5c.png",
            "large_file_url": "https://cdn.donmai.us/sample/cd/91/sample-cd91f0000b9574bf142d125a1e886e5c.jpg",
            "preview_file_url": "https://cdn.donmai.us/180x180/cd/91/cd91f0000b9574bf142d125a1e886e5c.jpg"
        },
        "family_group": null,
        "tags": [
            "1girl",
            "absurdres",
            "animal_ears",
            "black_eyes",
            "black_hair",
            "coat",
            "grabbing_own_breast",
            "hair_ornament",
            "hairband",
            "highres",
            "holding",
            "holding_mask",
            "japanese_clothes",
            "kuon_(utawarerumono)",
            "long_hair",
            "looking_at_viewer",
            "mask",
            "ponytail",
            "shirokuro_neko_(ouma_haruka)",
            "smile",
            "solo",
            "utawarerumono",
            "utawarerumono:_itsuwari_no_kamen"
        ],
        "tags_class": {
            "1girl": "general",
            "animal_ears": "general",
            "black_eyes": "general",
            "black_hair": "general",
            "coat": "general",
            "grabbing_own_breast": "general",
            "hair_ornament": "general",
            "hairband": "general",
            "holding": "general",
            "holding_mask": "general",
            "japanese_clothes": "general",
            "long_hair": "general",
            "looking_at_viewer": "general",
            "mask": "general",
            "ponytail": "general",
            "smile": "general",
            "solo": "general",
            "kuon_(utawarerumono)": "character",
            "utawarerumono": "copyright",
            "utawarerumono:_itsuwari_no_kamen": "copyright",
            "shirokuro_neko_(ouma_haruka)": "artist",
            "absurdres": "meta",
            "highres": "meta"
        }
    },
    "backup_urls": [
        "https://i.pximg.net/img-original/img/2020/08/11/12/41/43/83599609_p0.png"
    ]
}
```

</details>

## 文档

+ [教程](tutorials_zh.md)：关于如何设置爬取程序参数，完成一个爬取程序程序，并从Danbooru上根据关键词 / 标签下载图片的详细教程。
+ [网站任务说明（English）](notes_for_tasks.md)：包含每个支持的网站和爬取任务的说明与样例。
+ [类与函数（English）](classes_and_functions.md)：提供此项目内各结构、可用类及函数的信息。
