from image_crawler_utils import Downloader
from image_crawler_utils.stations.booru import MoebooruKeywordParser

# use_api is True, then image_num_per_gallery_page and image_num_per_json must be designated
from image_crawler_utils.stations.booru import (
    YANDERE_IMAGE_NUM_PER_GALLERY_PAGE,
    YANDERE_IMAGE_NUM_PER_JSON,
)

parser = MoebooruKeywordParser(
    station_url="https://yande.re/",
    standard_keyword_string="kuon_(utawarerumono) AND rating:safe",
    use_api=True,
    image_num_per_gallery_page=YANDERE_IMAGE_NUM_PER_GALLERY_PAGE,
    image_num_per_json=YANDERE_IMAGE_NUM_PER_JSON,
)
image_info_list = parser.run()
downloader = Downloader(
    store_path='Yandere',
    image_info_list=image_info_list,
)
downloader.run()
