from image_crawler_utils import CrawlerSettings, Downloader
from image_crawler_utils.stations.pixiv import PixivUserParser, get_pixiv_cookies

crawler_settings = CrawlerSettings(
    image_num=30,
)

cookies = get_pixiv_cookies(
    proxies={"https": "socks5://127.0.0.1:7890"}  # If you do not use system proxies, set this manually
)
cookies.save_to_json("Pixiv_cookies.json")  # Save it to an JSON file for later use

parser = PixivUserParser(
    crawler_settings=crawler_settings,
    member_id="2175653",
    cookies=cookies,
)
image_info_list = parser.run()
downloader = Downloader(
    store_path='Pixiv_user_2175653',
    image_info_list=image_info_list,
    crawler_settings=crawler_settings,
)
downloader.run()
