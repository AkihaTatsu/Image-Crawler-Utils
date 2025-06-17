<h1 align="center">
Image Crawler Utils
</h1>
<h4 align="center">
A Customizable Multi-station Image Crawler Structure
</h4>
<p align="center">
English | <a href="README_zh.md">简体中文</a>
</p>

---

## [Click Here for Documentation](https://image-crawler-utils.readthedocs.io/)

## About

A **rather customizable** image crawler structure, designed to download images with their information using multi-threading method. This GIF depicts a sample run:

![](docs/example.gif)

Besides, several classes and functions have been implemented to help better build a custom image crawler for yourself.

**Please follow the rules of robots.txt, and set a low number of threads with high number of delay time when crawling images. Frequent requests and massive download traffic may result in IP addresses being banned or accounts being suspended.**

## Installing

It is recommended to install it by

```Default
pip install image-crawler-utils
```

+ Requires `Python >= 3.9`.

### Attentions!

+ **[nodriver](https://github.com/ultrafunkamsterdam/nodriver)** is used to parse information from certain websites. It is suggested to **install the latest version of [Google Chrome](https://www.google.com/chrome/)** first to ensure the crawler will be correctly running.

## Features

+ Currently supported websites:
  + [Danbooru](https://danbooru.donmai.us/) - features supported:
    + Downloading images searched by tags
  + [yande.re](https://yande.re/) / [konachan.com](https://konachan.com/) / [konachan.net](https://konachan.net/) - features supported:
    + Downloading images searched by tags
  + [Gelbooru](https://gelbooru.com/) - features supported:
    + Downloading images searched by tags
  + [Safebooru](https://safebooru.org/) - features supported:
    + Downloading images searched by tags
  + [Pixiv](https://www.pixiv.net/) - features supported:
    + Downloading images searched by tags
    + Downloading images uploaded by a certain member
  + [Twitter / X](https://x.com/) - features supported:
    + Downloading images from searching result
    + Downloading images uploaded by a certain user
+ Logging of crawler process onto the console and (optional) into a file.
+ Using `rich` bars and logging messages to denote the progress of crawler (Jupyter Notebook support is included).
+ Save or load the settings and configs of a crawler.
+ Save or load the information of images for future downloading.
+ Acquire and manage cookies of some websites, including saving and loading them.
+ Several classes and functions for custom image crawler designing.

## Example

Running this [example](examples/danbooru_example.py) will download the first 20 images from [Danbooru](https://danbooru.donmai.us/) with keyword / tag `kuon_(utawarerumono)` and `rating:general` into the "Danbooru" folder. Information of images will be stored in `image_info_list.json` at same the path of your program. Pay attention that the proxies may need to be changed manually.

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
