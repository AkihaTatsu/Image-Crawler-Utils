import dataclasses
from typing import Optional, Union
import traceback

from urllib import parse
import nodriver

from image_crawler_utils import Cookies, KeywordParser, CrawlerSettings, ImageInfo, update_nodriver_browser_cookies
from image_crawler_utils.keyword import KeywordLogicTree
from image_crawler_utils.progress_bar import CustomProgress, ProgressGroup
from image_crawler_utils.utils import set_up_nodriver_browser

from .search_settings import TwitterSearchSettings
from .search_status_analyzer import scrolling_to_find_status
from .status_classes import TwitterStatus



##### Twitter Keyword Parser


class TwitterKeywordMediaParser(KeywordParser):
    """
    Keyword Parser for Twitter. Will fetch all media images from the searching result of certain keywords.

    Args:
        crawler_settings (image_crawler_utils.CrawlerSettings): The CrawlerSettings used in this Parser.
        station_url (str): The URL of the main page of a website.

            + This parameter works when several websites use the same structure. For example, https://yande.re/ and https://konachan.com/ both use Moebooru to build their websites, and this parameter must be filled to deal with these sites respectively.
            + For websites like https://www.pixiv.net/, as no other website uses its structure, this parameter has already been initialized and do not need to be filled.

        standard_keyword_string (str): Query keyword string using standard syntax. Refer to the documentation for detailed instructions.
        keyword_string (str, None): If you want to directly specify the keywords used in searching, set ``keyword_string`` to a custom non-empty string. It will OVERWRITE ``standard_keyword_string``.

            + For example, set ``keyword_string`` to ``"kuon_(utawarerumono) rating:safe"`` in DanbooruKeywordParser means searching directly with this string in Danbooru, and its standard keyword string equivalent is ``"kuon_(utawarerumono) AND rating:safe"``.

        cookies (image_crawler_utils.Cookies, str, dict, list, None): Cookies containing logging information.
        twitter_search_settings (image_crawler_utils.stations.twitter.TwitterSearchSettings): A TwitterSearchSettings class that contains extra options when searching.
        reload_times (int): Reload the page for ``reload_times`` times. May be useful when there are status (tweets) not detected.
        error_retry_delay (float): When Twitter / X returns an error, the Parser will retry after ``error_retry_delay`` seconds.
        headless (bool): Do not display browsers window when a browser is started. Set to :py:data:`False` will pop up browser windows.
    """

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


    def run(self) -> list[ImageInfo]:
        """
        The main function that runs the Parser and returns a list of :class:`image_crawler_utils.ImageInfo`.
        """
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

        self.crawler_settings.log.info(f'Loading searching page using query string "{query_string}" and URL [repr.url]{search_status_url}[reset] ...', extra={"markup": True})
        
        flag_success = False
        for i in range(self.crawler_settings.download_config.retry_times):
            with CustomProgress(has_spinner=True, transient=True) as progress:
                try:
                    task = progress.add_task(total=3, description='Loading browser components...')
                    
                    # Connect once to get cookies
                    try:
                        self.crawler_settings.log.debug(f"Connecting to twitter searching result: [repr.url]{search_status_url}[reset]", extra={"markup": True})
                        browser = await set_up_nodriver_browser(
                            proxies=self.crawler_settings.download_config.result_proxies,
                            headless=self.headless,
                            no_image_stylesheet=True,
                        )

                        progress.update(task, advance=1, description="Requesting searching result once...")

                        tab = await browser.get(search_status_url)
                        result = await tab.select('div[id="react-root"]')
                        if result is None:
                            raise ModuleNotFoundError('Element div[id="react-root"] not found')
                    except Exception as e:
                        browser.stop()
                        raise ConnectionError(f"{e}")

                    # Replace cookies
                    await update_nodriver_browser_cookies(browser, self.cookies)

                    # Connect twice to get page
                    try:
                        progress.update(task, advance=1, description="Requesting searching result again with cookies...")

                        await tab.get(search_status_url)  # Do not reload directly! It may be the login page.
                    except Exception as e:
                        browser.stop()
                        raise ConnectionError(f"{e}")
                    flag_success = True
                    
                    progress.update(task, advance=1, description="[green]Requesting successfully finished!")

                    break
                except Exception as e:
                    self.crawler_settings.log.warning(f"Loading Twitter / X searching result page failed at attempt {i + 1} because {e}")
                    error_msg = e
        if not flag_success:
            output_msg_base = f"Loading Twitter / X searching result page [repr.url]{search_status_url}[reset] failed"
            self.crawler_settings.log.critical(f"{output_msg_base}.\n{traceback.format_exc()}", output_msg=f"{output_msg_base} because {error_msg}", extra={"markup": True})
            raise ConnectionError(f"{error_msg}")

        self.crawler_settings.log.info("Scrolling to get status...")
        with ProgressGroup(panel_title="Scrolling to Find [yellow]Status[reset]") as progress_group:
            status_list, media_count = await scrolling_to_find_status(
                tab=tab, 
                tab_url=search_status_url,
                crawler_settings=self.crawler_settings,
                reload_times=self.reload_times,
                error_retry_delay=self.error_retry_delay,
                image_num_restriction=self.crawler_settings.capacity_count_config.image_num,
                progress_group=progress_group,
                transient=False,
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
