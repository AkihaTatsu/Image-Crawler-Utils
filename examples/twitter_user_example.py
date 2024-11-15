from image_crawler_utils import Downloader
from image_crawler_utils.stations.twitter import TwitterUserMediaParser, get_twitter_cookies

cookies = get_twitter_cookies(
    proxies={"https": "socks5://127.0.0.1:7890"}  # If you do not use system proxies, set this manually
)
cookies.save_to_json("Twitter_cookies.json")  # Save it to an JSON file for later use

parser = TwitterUserMediaParser(
    user_id="idonum",
    cookies=cookies,
    starting_date='2023-1-1',
    ending_date='2024-1-1',
)
image_info_list = parser.run()
downloader = Downloader(
    store_path='Twitter_user_idonum',
    image_info_list=image_info_list,
)
downloader.run()
