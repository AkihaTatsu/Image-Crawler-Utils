import dataclasses
from typing import Optional, Union
import traceback

from urllib import parse
import nodriver

from image_crawler_utils import Cookies, KeywordParser, CrawlerSettings, ImageInfo, update_nodriver_browser_cookies
from image_crawler_utils.keyword import KeywordLogicTree
from image_crawler_utils.utils import custom_tqdm, set_up_nodriver_browser

from .search_settings import TwitterSearchSettings
from .search_status_analyzer import scrolling_to_find_status
from .status_classes import TwitterStatus



##### Twitter Keyword Parser


class TwitterKeywordMediaParser(KeywordParser):

    def __init__(
        self, 
        station_url: str="https://x.com/",
        crawler_settings: CrawlerSettings=CrawlerSettings(),
        standard_keyword_string: Optional[str]=None, 
        keyword_string: Optional[str]=None,
        cookies: Optional[Union[Cookies, list, dict, str]]=Cookies(),
        twitter_search_settings: TwitterSearchSettings=TwitterSearchSettings(),
        reload_times: int=1,
        error_retry_delay: float=200,
        headless: bool=True,
    ):
        """
        Parameters:
            crawler_settings (image_crawler_utils.CrawlerSettings): Crawler settings.
            station_url (str): URL of the website.
            standard_keyword_string (str): A keyword string using standard syntax.
            pixiv_search_settings (crawler_utils.stations.pixiv.PixivSearchSettings): Settings for Pixiv searching.
            keyword_string (str, optional): Specify the keyword string yourself. You can write functions to generate them from the keyword tree afterwards.
            cookies (crawler_utils.cookies.Cookies, str, dict or list, optional): Cookies containing logging information.
            reload_times (int): Time of reloading page in case some status are omitted.
            error_retry_delay (float): Pause error_retry_delay seconds if an error happened.
            headless (bool): Hide browser window when browser is loaded.
        """

        super().__init__(
            station_url=station_url,
            crawler_settings=crawler_settings, 
            standard_keyword_string=standard_keyword_string, 
            keyword_string=keyword_string,
            cookies=cookies,
            accept_empty=True,
        )
        self.twitter_search_settings = twitter_search_settings
        self.reload_times = reload_times
        self.error_retry_delay = error_retry_delay
        self.headless = headless


    def run(self):
        if self.cookies.is_none():
            raise ValueError('Cookies cannot be empty!')
        if self.keyword_string is None:
            self.generate_keyword_string()
        self.get_status()
        return self.parse_images_from_status()


    ##### Custom funcs

    
    # Generate keyword string from keyword tree
    def __build_keyword_str(self, tree: KeywordLogicTree) -> str:
        # Generate standard keyword string
        if isinstance(tree.lchild, str):
            res1 = tree.lchild
        else:
            res1 = self.__build_keyword_str(tree.lchild)
        if isinstance(tree.rchild, str):
            res2 = tree.rchild
        else:
            res2 = self.__build_keyword_str(tree.rchild)

        if tree.logic_operator == "AND":
            return f'({res1} {res2})'
        elif tree.logic_operator == "OR":
            return f'({res1} OR {res2})'
        elif tree.logic_operator == "NOT":
            return f'(-{res2})'
        elif tree.logic_operator == "SINGLE":
            return f'{res2}'


    # Basic keyword string
    def generate_keyword_string(self) -> str:            
        self.keyword_string = self.__build_keyword_str(self.keyword_tree)
        return self.keyword_string
    

    # Load browser and fetch images from status
    async def __get_status(self) -> list[TwitterStatus]:
        query_string = self.twitter_search_settings.build_search_appending_str(self.keyword_string)
        search_status_url = parse.quote(f'{self.station_url}search?q={query_string}&src=typed_query&f=live', safe='/:?=&')

        self.crawler_settings.log.info(f'Loading searching page using query string "{query_string}" ...')
        
        flag_success = False
        for i in range(self.crawler_settings.download_config.retry_times):
            try:
                with custom_tqdm.trange(
                    3,
                    desc=f'Loading browser components...',
                    leave=False,
                ) as pbar:
                    # Connect once to get cookies
                    try:
                        self.crawler_settings.log.debug(f"Connecting to twitter searching result: \"{search_status_url}\"")
                        browser = await set_up_nodriver_browser(
                            proxies=self.crawler_settings.download_config.result_proxies,
                            headless=self.headless,
                            no_image_stylesheet=True,
                        )

                        pbar.update()
                        pbar.set_description(f"Requesting searching result once...")

                        tab = await browser.get(search_status_url, new_tab=True)
                        await tab.find('div[id="react-root"]')
                    except Exception as e:
                        browser.stop()
                        raise ConnectionError(f"{e}")

                    # Replace cookies
                    await update_nodriver_browser_cookies(browser, self.cookies)

                    # Connect twice to get page
                    try:
                        pbar.update()
                        pbar.set_description(f"Requesting searching result again with cookies...")

                        await tab.get(search_status_url)  # Do not reload directly! It may be the login page.
                    except Exception as e:
                        browser.stop()
                        raise ConnectionError(f"{e}")
                    flag_success = True
                    pbar.update()  # Finish
                    break
            except Exception as e:
                self.crawler_settings.log.warning(f"Loading Twitter / X searching result page failed at attempt {i + 1} because {e}")
                error_msg = e
        if not flag_success:
            output_msg_base = f"Loading Twitter / X searching result page \"{search_status_url}\" failed"
            self.crawler_settings.log.critical(f"{output_msg_base}.\n{traceback.format_exc()}", output_msg=f"{output_msg_base} because {error_msg}")
            raise ConnectionError(f"{error_msg}")

        self.crawler_settings.log.info("Scrolling to get status...")
        status_list, media_count = await scrolling_to_find_status(
            tab=tab, 
            tab_url=search_status_url,
            crawler_settings=self.crawler_settings,
            reload_times=self.reload_times,
            error_retry_delay=self.error_retry_delay,
            image_num_restriction=self.crawler_settings.capacity_count_config.image_num,
            pbar_leave=True,
        )
        self.crawler_settings.log.info(f'Finished getting status. {len(status_list)} status & {media_count} {"images" if media_count > 1 else "image"} are collected.')
        browser.stop()
        self.status_list = status_list
        return self.status_list
        
        
    def get_status(self) -> list[TwitterStatus]:
        return nodriver.loop().run_until_complete(
            self.__get_status()
        )
    

    # Parse images from status
    def parse_images_from_status(self) -> list[ImageInfo]:
        self.crawler_settings.log.info("Parsing image info from collected status...")

        image_info_list = []
        for status in self.status_list:
            for image in status.media_list:
                image_info_list.append(ImageInfo(
                    url=image.image_source,
                    name=image.image_name,
                    info=dataclasses.asdict(status),
                ))

        if self.crawler_settings.capacity_count_config.image_num is not None:  # Get only image_num images
            image_info_list = image_info_list[:self.crawler_settings.capacity_count_config.image_num]
        self.crawler_settings.log.info(f"Image info parsed. {len(image_info_list)} {'images' if len(image_info_list) > 1 else 'image'} collected.")
        self.image_info_list = image_info_list
        return self.image_info_list
