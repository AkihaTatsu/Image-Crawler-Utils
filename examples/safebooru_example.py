from image_crawler_utils import Downloader
from image_crawler_utils.stations.booru import SafebooruKeywordParser

parser = SafebooruKeywordParser(
    standard_keyword_string="kuon_(utawareru_mono)",
)
image_info_list = parser.run()
downloader = Downloader(
    store_path='Safebooru',
    image_info_list=image_info_list,
)
downloader.run()
