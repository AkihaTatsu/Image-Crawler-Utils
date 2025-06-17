from image_crawler_utils import Downloader
from image_crawler_utils.stations.pixiv import PixivKeywordParser, PixivSearchSettings, get_pixiv_cookies

cookies = get_pixiv_cookies(
    proxies={"https": "socks5://127.0.0.1:7890"}  # If you do not use system proxies, set the proxies manually.
)
cookies.save_to_json("Pixiv_cookies.json")  # Save it to an JSON file for later use

parser = PixivKeywordParser(
    standard_keyword_string="クオン AND うたわれるもの1000users入り",
    cookies=cookies,
    pixiv_search_settings=PixivSearchSettings(
        age_rating="safe",
        target_manga=False,
        display_ai=False,
    ),
    quick_mode=True,
)
image_info_list = parser.run()
downloader = Downloader(
    store_path='Pixiv',
    image_info_list=image_info_list,
)
downloader.run()
