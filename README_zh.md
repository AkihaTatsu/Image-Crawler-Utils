<h1 align="center">
Image Crawler Utils
</h1>
<h4 align="center">
一个可自定义的多网站图像爬取框架
</h4>
<p align="center">
<a href="README.md">English</a> | 简体中文
</p>

---

## 关于本项目

一个**相对可自定义**的图像爬取框架，允许使用多线程方法下载图像及其信息。如下GIF为一个爬取样例程序在控制台上得到的结果：

![](docs/example.gif)

同时，此框架内包含数个有助于更好地构建自定义图像爬取程序的类与函数。

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

## 样例程序

运行此[样例](examples/danbooru_example.py)将会在[Danbooru](https://danbooru.donmai.us/)上搜索关键词 / 标签为`kuon_(utawarerumono)`和`rating:general`的图片，并将前20张图片下载到“Danbooru”文件夹中。图片信息将会存储在与你的程序同一目录下的`image_info_list.json`文件中。注意代理可能需要手动进行更改。

```Python
from image_crawler_utils import CrawlerSettings, Downloader, save_image_infos
from image_crawler_utils.stations.booru import DanbooruKeywordParser

#======================================================================#
# This part prepares the settings for crawling and downloading images. #
#======================================================================#

crawler_settings = CrawlerSettings(
    image_num=20,
    # If you do not use system proxies, remove '#' and set the proxies manually.
    # proxies={"https": "socks5://127.0.0.1:7890"},
)

#==================================================================#
# This part gets the URLs and information of images from Danbooru. #
#==================================================================#

parser = DanbooruKeywordParser(
    crawler_settings=crawler_settings,
    standard_keyword_string="kuon_(utawarerumono) AND rating:general",
)
image_info_list = parser.run()
# The information will be saved at image_info_list.json
save_image_infos(image_info_list, "image_info_list")

#===================================================================#
# This part downloads the images according to the image information #
# just collected in the image_info_list.                            #
#===================================================================#

downloader = Downloader(
    store_path='Danbooru',
    image_info_list=image_info_list,
    crawler_settings=crawler_settings,
)
downloader.run()
```
