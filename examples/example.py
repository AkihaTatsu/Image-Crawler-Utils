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
    store_path='Danbooru',
    image_info_list=image_info_list,
    crawler_settings=crawler_settings,
)
downloader.run()
