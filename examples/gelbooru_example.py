from image_crawler_utils import Downloader
from image_crawler_utils.stations.booru import GelbooruKeywordParser

parser = GelbooruKeywordParser(
    standard_keyword_string="kuon_(utawarerumono) AND rating:general",
)
image_info_list = parser.run()
downloader = Downloader(
    store_path='Gelbooru',
    image_info_list=image_info_list,
)
downloader.run()
