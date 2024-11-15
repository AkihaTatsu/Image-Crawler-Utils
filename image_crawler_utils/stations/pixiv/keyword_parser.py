from typing import Optional, Union

import math
import json
from collections import ChainMap
from collections.abc import Callable
import requests
import traceback

from urllib import parse
import nodriver

from image_crawler_utils import Cookies, KeywordParser, ImageInfo, CrawlerSettings, update_nodriver_browser_cookies
from image_crawler_utils.keyword import KeywordLogicTree, min_len_keyword_group, keyword_list_tree
from image_crawler_utils.user_agent import UserAgent
from image_crawler_utils.utils import custom_tqdm, set_up_nodriver_browser

from .constants import PIXIV_IMAGE_NUM_PER_JSON, PIXIV_MAX_JSON_PAGE_NUM
from .search_settings import PixivSearchSettings



##### Pixiv Keyword Parser


class PixivKeywordParser(KeywordParser):

    def __init__(
        self, 
        station_url: str="https://www.pixiv.net/",
        crawler_settings: CrawlerSettings=CrawlerSettings(),
        standard_keyword_string: Optional[str]=None, 
        keyword_string: Optional[str]=None,
        cookies: Optional[Union[Cookies, list, dict, str]]=Cookies(),
        pixiv_search_settings: PixivSearchSettings=PixivSearchSettings(),
        use_keyword_include: bool=False,
        quick_mode: bool=False,
        info_page_batch_num: Optional[int]=100,
        info_page_batch_delay: Union[float, Callable]=300,
        headless: bool=True,
    ):
        """
        Parameters:
            crawler_settings (image_crawler_utils.CrawlerSettings): Crawler settings.
            station_url (str): URL of the website.
            standard_keyword_string (str): A keyword string using standard syntax.
            pixiv_search_settings (crawler_utils.stations.pixiv.PixivSearchSettings): Settings for Pixiv searching.
            keyword_string (str, optional): Specify the keyword string yourself. You can write functions to generate them from the keyword tree afterwards.
            use_keyword_include (bool): Using a new keyword string whose searching results can contain all images belong to the original keyword string result. Default set to False.
                - Example: search "A" can contain all results by "A and B"
            cookies (crawler_utils.cookies.Cookies, str, dict or list, optional): Cookies containing logging information.
            thread_delay (float or function, optional): As Pixiv restricts number of requests in a certain period, this argument defines the delay time (seconds) before every downloading thread of websites.
            quick_mode (bool): DO NOT DOWNLOAD any image info. Will increase speed of downloading.
            info_page_batch_num (int): Batch size of images. Finish downloading a batch will wait for a rather long time.
            info_page_batch_delay (float, optional): Delay time after each batch of images is downloaded.
            headless (bool): Hide browser window when browser is loaded.
        """

        super().__init__(
            station_url=station_url,
            crawler_settings=crawler_settings, 
            standard_keyword_string=standard_keyword_string, 
            keyword_string=keyword_string,
            cookies=cookies,
        )
        self.pixiv_search_settings = pixiv_search_settings
        self.use_keyword_include = use_keyword_include
        self.quick_mode = quick_mode
        self.info_page_batch_num = info_page_batch_num
        self.info_page_batch_delay = info_page_batch_delay
        self.headless = headless


    def run(self):
        if self.keyword_string is None:
            if self.use_keyword_include:
                self.generate_keyword_string_include()
            else:
                self.generate_keyword_string()

        with requests.Session() as session:
            if not self.cookies.is_none():
                session.cookies.update(self.cookies.cookies_dict)
            else:
                raise ValueError('Cookies cannot be empty!')
            self.get_image_num()
            self.get_json_page_urls()
            self.get_image_basic_info(session=session)
            if self.quick_mode:
                return self.get_image_info_quick(session=session)
            else:
                return self.get_image_info_full(session=session)


    ##### Custom funcs

    
    # Generate keyword string from keyword tree
    def __build_keyword_str(self, tree: KeywordLogicTree) -> str:
        # Generate standard keyword string
        if isinstance(tree.son1, str):
            res1 = tree.son1
            while '_' in res1 or '*' in res1:  # Pixiv does not support _ and *
                res1 = res1.replace("_", "").replace("*", "")
        else:
            res1 = self.__build_keyword_str(tree.son1)
        if isinstance(tree.son2, str):
            res2 = tree.son2
            while '_' in res2 or '*' in res2:  # Pixiv does not support _ and *
                res2 = res2.replace("_", "").replace("*", "")
        else:
            res2 = self.__build_keyword_str(tree.son2)

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


    # Keyword (include) string
    def generate_keyword_string_include(self) -> str:
        keyword_group = min_len_keyword_group(self.keyword_tree.keyword_include_group_list())
        keyword_strings = [self.__build_keyword_str(keyword_list_tree(group, log=self.crawler_settings.log)) 
                           for group in keyword_group]
        min_image_num = None

        self.crawler_settings.log.info("Testing the page num of keyword (include) groups to find the one with fewest pages.")
        with custom_tqdm.trange(
            len(keyword_strings),
            desc="Requesting pages",
        ) as pbar:
            for string in keyword_strings:
                self.crawler_settings.log.debug(f'Testing the image num of keyword string: {string}')
                self.keyword_string = string
                image_num = self.get_image_num()
                self.crawler_settings.log.debug(f'The image num of {string} is {image_num}.')
                if min_image_num is None or image_num < min_image_num:
                    min_image_num = image_num
                    min_string = string
                pbar.update()
        self.keyword_string = min_string
        return self.keyword_string


    # Get total image num
    async def __get_image_num(self) -> int:
        # Connect to the first gallery page
        for i in range(self.crawler_settings.download_config.retry_times):
            try:
                self.crawler_settings.log.info(f'Connecting to the first gallery page using keyword string "{self.keyword_string}" ...')
                first_page_url = parse.quote(f"{self.station_url}{self.pixiv_search_settings.build_search_appending_str_website(self.keyword_string)}", safe='/:?=&')

                with custom_tqdm.trange(
                    3,
                    desc=f'Loading browser components...',
                    leave=False,
                ) as pbar:
                    # Connect once to get cookies
                    try:
                        self.crawler_settings.log.debug(f"Parsing Pixiv page: \"{first_page_url}\"")
                        browser = await set_up_nodriver_browser(
                            proxies=self.crawler_settings.download_config.result_proxies,
                            headless=self.headless,
                        )

                        pbar.update()
                        pbar.set_description(f"Requesting page once...")

                        tab = await browser.get(first_page_url, new_tab=True)
                        await tab.find('img[alt="pixiv"]', timeout=30)
                    except Exception as e:
                        raise ConnectionError(f"{e}")

                    # Replace cookies
                    await update_nodriver_browser_cookies(browser, self.cookies)
                    
                    # Connect twice to get images
                    try:
                        pbar.update()
                        pbar.set_description(f"Requesting page again with cookies...")

                        await tab.get(first_page_url)
                        image_num_element = await tab.find('span[class="sc-1pt8s3a-10 bjcknB"]', timeout=30)
                        pbar.update()
                        browser.stop()
                    except Exception as e:
                        browser.stop()
                        raise ConnectionError(f"{e}")
                
                image_num_str = image_num_element.text.replace(',', '').strip()
                if len(image_num_str) == 0:
                    raise ValueError('Total image number is empty. Probably because the webpage element is not correctly loaded.')
                image_num = int(image_num_str)
                self.crawler_settings.log.info(f"{image_num} {'images' if image_num > 1 else 'image'} in total detected. Pay attention that not all images may be recorded and downloaded.")
                self.total_image_num = image_num
                return self.total_image_num
            except Exception as e:
                self.crawler_settings.log.warning(f"Parsing Pixiv first gallery page failed at attempt {i + 1} because {e}")
                error_msg = e
        output_msg_base = f"Parsing Pixiv first gallery page \"{first_page_url}\" failed"
        self.crawler_settings.log.critical(f"{output_msg_base}.\n{traceback.format_exc()}", output_msg=f"{output_msg_base} because {error_msg}")
        
        return 0
        

    def get_image_num(self) -> int:
        # Actually use this!
        return nodriver.loop().run_until_complete(
            self.__get_image_num()
        )
        

    # Get Pixiv ajax API json page URLs
    def get_json_page_urls(self) -> list[str]:
        self.last_page_num = math.ceil(self.total_image_num / PIXIV_IMAGE_NUM_PER_JSON)
        if self.last_page_num > PIXIV_MAX_JSON_PAGE_NUM:
            self.last_page_num = PIXIV_MAX_JSON_PAGE_NUM
        self.json_page_urls = [parse.quote(f"{self.station_url}{self.pixiv_search_settings.build_search_appending_str_json(self.keyword_string)}&p={page_num}", safe='/:?=&')
                               for page_num in range(1, self.last_page_num + 1)]
        return self.json_page_urls
    

    # Get image ID and basic info
    def get_image_basic_info(self, session: requests.Session=None) -> dict:            
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)

        self.crawler_settings.log.info("Downloading pages including Pixiv IDs...")
        # Update headers for json download
        if self.crawler_settings.download_config.result_headers is None:  # Pixiv must have user-agents!
            json_search_page_headers = dict(ChainMap(UserAgent.random_agent_with_name("Chrome"), {"Referer": "www.pixiv.net"}))
        else:
            json_search_page_headers = dict(ChainMap(self.crawler_settings.download_config.result_headers, {"Referer": "www.pixiv.net"}))

        # Get and parse json page info
        json_page_contents = self.threading_request_page_content(
            self.json_page_urls, 
            restriction_num=self.crawler_settings.capacity_count_config.page_num, 
            session=session,
            headers=json_search_page_headers,
            # It seems that pixiv has less restrictions on crawling this type of pages, so no batch download is set.
        )

        # Get dict
        json_basic_info = {}
        for content in json_page_contents:
            parsed_content = json.loads(content)
            for image_list_type in ["illust", "illustManga", "manga"]:
                if image_list_type in parsed_content["body"].keys():
                    for image_data in parsed_content["body"][image_list_type]["data"]:
                        json_basic_info[image_data["id"]] = image_data

        self.json_basic_info = json_basic_info
        return self.json_basic_info


    # Get image info: full
    def get_image_info_full(self, session: requests.Session=None) -> list[ImageInfo]:
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)
            
        # Update headers for illust detection
        if self.crawler_settings.download_config.result_headers is None:  # Pixiv must have user-agents!
            json_image_url_page_headers = [dict(ChainMap(UserAgent.random_agent_with_name("Chrome"), {"Referer": f"www.pixiv.net/artworks/{artwork_id}"}))
                                           for artwork_id in self.json_basic_info.keys()]
        else:
            json_image_url_page_headers = [dict(ChainMap(self.crawler_settings.download_config.result_headers, {"Referer": f"www.pixiv.net/artworks/{artwork_id}"}))
                                           for artwork_id in self.json_basic_info.keys()]
        
        # Get and parse json page info 
        self.crawler_settings.log.info("Downloading image info for every Pixiv ID...")
        json_image_info_urls = [f'{self.station_url}ajax/illust/{artwork_id}'
                                for artwork_id in self.json_basic_info.keys()]
        json_image_url_page_contents = self.threading_request_page_content(
            json_image_info_urls, 
            restriction_num=self.crawler_settings.capacity_count_config.image_num, 
            session=session,
            headers=json_image_url_page_headers,
            thread_delay=1.0 * self.crawler_settings.download_config.thread_num,  # Manually set thread_delay in case account get suspended because of too many requests
            batch_num=self.info_page_batch_num,
            batch_delay=self.info_page_batch_delay,
        )
        image_info_dict = {}
        for content in json_image_url_page_contents:
            parsed_content = json.loads(content)
            image_info_dict[parsed_content["body"]["id"]] = parsed_content["body"]

        # Get and parse json page info 
        self.crawler_settings.log.info("Downloading image URLs for every Pixiv ID...")
        json_image_download_urls = [f'{self.station_url}ajax/illust/{artwork_id}/pages'
                                    for artwork_id in self.json_basic_info.keys()]
        json_image_url_page_contents = self.threading_request_page_content(
            json_image_download_urls, 
            restriction_num=self.crawler_settings.capacity_count_config.image_num, 
            session=session,
            headers=json_image_url_page_headers,
            # It seems that pixiv has less restrictions on crawling this type of pages, so no batch download is set.
        )
        image_info_list = []
        for i in range(len(json_image_url_page_contents)):
            parsed_content = json.loads(json_image_url_page_contents[i])
            for image_url_size in parsed_content["body"]:
                image_id = image_url_size["urls"]["original"].split('/')[-1].split('_')[0]
                tags = [item["tag"] for item in image_info_dict[image_id]["tags"]["tags"]]
                image_info_list.append(ImageInfo(
                    url=image_url_size["urls"]["original"],
                    name=image_url_size["urls"]["original"].split('/')[-1],
                    info={
                        "id": image_id,
                        "width": image_url_size["width"],
                        "height": image_url_size["height"],
                        "tags": tags,
                        "info": image_info_dict[image_id],
                    },
                ))

        self.image_info_list = image_info_list
        return self.image_info_list


    # Get image info: quick
    def get_image_info_quick(self, session: requests.Session=None) -> list[ImageInfo]:
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)
            
        # Update headers for illust detection
        if self.crawler_settings.download_config.result_headers is None:  # Pixiv must have user-agents!
            json_image_url_page_headers = [dict(ChainMap(UserAgent.random_agent_with_name("Chrome"), {"Referer": f"www.pixiv.net/artworks/{artwork_id}"}))
                                           for artwork_id in self.json_basic_info.keys()]
        else:
            json_image_url_page_headers = [dict(ChainMap(self.crawler_settings.download_config.result_headers, {"Referer": f"www.pixiv.net/artworks/{artwork_id}"}))
                                           for artwork_id in self.json_basic_info.keys()]
            
        # Get and parse json page info 
        self.crawler_settings.log.info("Downloading image URLs for every Pixiv ID...")
        json_image_download_urls = [f'{self.station_url}ajax/illust/{artwork_id}/pages'
                                    for artwork_id in self.json_basic_info.keys()]
        json_image_url_page_contents = self.threading_request_page_content(
            json_image_download_urls, 
            restriction_num=self.crawler_settings.capacity_count_config.image_num, 
            session=session,
            headers=json_image_url_page_headers,
            # It seems that pixiv has less restrictions on crawling this type of pages, so no batch download is set.
        )
        image_info_list = []
        for i in range(len(json_image_url_page_contents)):
            parsed_content = json.loads(json_image_url_page_contents[i])
            for image_url_size in parsed_content["body"]:
                image_id = image_url_size["urls"]["original"].split('/')[-1].split('_')[0]
                tags = self.json_basic_info[image_id]["tags"]
                image_info_list.append(ImageInfo(
                    url=image_url_size["urls"]["original"],
                    name=image_url_size["urls"]["original"].split('/')[-1],
                    info={
                        "id": image_id,
                        "width": image_url_size["width"],
                        "height": image_url_size["height"],
                        "tags": tags,
                        "info": self.json_basic_info[image_id],
                    },
                ))
        
        self.image_info_list = image_info_list
        return self.image_info_list
