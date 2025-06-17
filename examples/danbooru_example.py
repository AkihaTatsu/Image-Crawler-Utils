from image_crawler_utils import CrawlerSettings, Downloader, save_image_infos
from image_crawler_utils.stations.booru import DanbooruKeywordParser

#======================================================================#
# This part prepares the settings for crawling and downloading images. #
#======================================================================#

crawler_settings = CrawlerSettings(
    image_num=20,
    # If you do not use system proxies, remove '#' and set the proxies manually.
    # proxies={"https": "socks5://127.0.0.1:7890"},
)

#==================================================================#
# This part gets the URLs and information of images from Danbooru. #
#==================================================================#

parser = DanbooruKeywordParser(
    crawler_settings=crawler_settings,
    standard_keyword_string="kuon_(utawarerumono) AND rating:general",
)
image_info_list = parser.run()
# The information will be saved at image_info_list.json
save_image_infos(image_info_list, "image_info_list")

#===================================================================#
# This part downloads the images according to the image information #
# just collected in the image_info_list.                            #
#===================================================================#

downloader = Downloader(
    store_path='Danbooru',
    image_info_list=image_info_list,
    crawler_settings=crawler_settings,
)
downloader.run()
