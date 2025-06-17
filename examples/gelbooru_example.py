from image_crawler_utils import Downloader
from image_crawler_utils.stations.booru import GelbooruKeywordParser

parser = GelbooruKeywordParser(
    standard_keyword_string="kuon_(utawarerumono) AND rating:general",
    api_key='your_api_key',  # Must be replaced by your api_key
    user_id='your_user_id',  # Must be replaced by your user_id
)
image_info_list = parser.run()
downloader = Downloader(
    store_path='Gelbooru',
    image_info_list=image_info_list,
)
downloader.run()
