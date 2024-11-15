from image_crawler_utils import Downloader
from image_crawler_utils.stations.booru import MoebooruKeywordParser

parser = MoebooruKeywordParser(
    station_url="https://konachan.com/",
    standard_keyword_string="kuon_(utawarerumono) AND rating:safe",
    use_api=False,
    has_cloudflare=True,
)
image_info_list = parser.run()
downloader = Downloader(
    store_path='Konachan_com',
    image_info_list=image_info_list,
)
downloader.run()
