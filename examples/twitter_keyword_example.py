from image_crawler_utils import Downloader
from image_crawler_utils.stations.twitter import TwitterKeywordMediaParser, TwitterSearchSettings, get_twitter_cookies

cookies = get_twitter_cookies(
    proxies={"https": "socks5://127.0.0.1:7890"}  # If you do not use system proxies, set the proxies manually.
)
cookies.save_to_json("Twitter_cookies.json")  # Save it to an JSON file for later use

parser = TwitterKeywordMediaParser(
    standard_keyword_string='#クオン AND #イラスト AND #うたわれるもの',
    twitter_search_settings=TwitterSearchSettings(
        only_media=True,
        ending_date='2024-01-01',
    ),
    cookies=cookies,
)
image_info_list = parser.run()
downloader = Downloader(
    store_path='Twitter',
    image_info_list=image_info_list,
)
downloader.run()
