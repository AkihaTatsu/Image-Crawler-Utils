from typing import Optional, Union

import time, random
import json
from collections import ChainMap
from collections.abc import Callable
import requests

from urllib import parse

from image_crawler_utils import Cookies, KeywordParser, ImageInfo, CrawlerSettings
from image_crawler_utils.keyword import KeywordLogicTree, min_len_keyword_group, construct_keyword_tree_from_list
from image_crawler_utils.user_agent import UserAgent
from image_crawler_utils.progress_bar import CustomProgress, ProgressGroup

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


    def run(self) -> list[ImageInfo]:
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
            self.get_json_page_num()
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
        if isinstance(tree.lchild, str):
            res1 = tree.lchild
            while '_' in res1 or '*' in res1:  # Pixiv does not support _ and *
                res1 = res1.replace("_", "").replace("*", "")
        else:
            res1 = self.__build_keyword_str(tree.lchild)
        if isinstance(tree.rchild, str):
            res2 = tree.rchild
            while '_' in res2 or '*' in res2:  # Pixiv does not support _ and *
                res2 = res2.replace("_", "").replace("*", "")
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


    # Keyword (include) string
    def generate_keyword_string_include(self) -> str:
        keyword_group = min_len_keyword_group(self.keyword_tree.keyword_include_group_list())
        keyword_strings = [self.__build_keyword_str(construct_keyword_tree_from_list(group, log=self.crawler_settings.log)) 
                           for group in keyword_group]
        min_image_num = None

        self.crawler_settings.log.info("Testing the image num of keyword (include) groups to find the one with fewest pages.")
        with CustomProgress(transient=True) as progress:
            task = progress.add_task(description="Requesting pages:", total=len(keyword_strings))
            for string in keyword_strings:
                self.crawler_settings.log.debug(f'Testing the image num of keyword string: {string}')
                self.keyword_string = string
                image_num = self.get_json_page_num()
                self.crawler_settings.log.debug(f'The image num of {string} is {image_num}.')
                if min_image_num is None or image_num < min_image_num:
                    min_image_num = image_num
                    min_string = string
                progress.update(task, advance=1)

            progress.update(task, description="[green]Requesting pages finished!")
                
        self.keyword_string = min_string
        self.crawler_settings.log.info(f'The keyword string the parser will use is "{self.keyword_string}" which has {min_image_num} {"images" if min_image_num > 1 else "image"}.')
        return self.keyword_string


    def get_json_page_num(self, session: requests.Session=None) -> int:
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)

        if self.crawler_settings.download_config.result_headers is None:  # Pixiv must have user-agents!
            json_search_page_headers = dict(ChainMap(UserAgent.random_agent_with_name("Chrome"), {"Referer": "www.pixiv.net"}))
        else:
            json_search_page_headers = dict(ChainMap(self.crawler_settings.download_config.result_headers, {"Referer": "www.pixiv.net"}))

        first_page_url = parse.quote(f"{self.station_url}{self.pixiv_search_settings.build_search_appending_str_json(self.keyword_string)}", safe='/:?=&')

        self.crawler_settings.log.info(f'Connecting to the first gallery page using URL "{first_page_url}" ...')
            
        content = self.request_page_content(first_page_url, session=session, headers=json_search_page_headers)

        if content is None:
            self.crawler_settings.log.critical(f"CANNOT connect to the first JSON page, URL: \"{first_page_url}\"")
            raise ConnectionError(f"CANNOT connect to the first JSON page, URL: \"{first_page_url}\"")
        else:
            self.crawler_settings.log.info(f'Successfully connected to the first JSON page.')

        parsed_content = json.loads(content)
        for image_list_type in ["illust", "illustManga", "manga"]:
            if image_list_type in parsed_content["body"].keys():
                self.artworks_num = int(parsed_content["body"][image_list_type]["total"])
                self.json_page_num = int(parsed_content["body"][image_list_type]["lastPage"])

        if self.json_page_num == 1000:
            self.crawler_settings.log.warning("Number of result pages has reached 1000. Due to Pixiv restrictions, result in pages exceeding 1000 cannot be fetched through JSON API directly.")
        
        self.crawler_settings.log.info(f"Number of artworks: {self.artworks_num}")
        return self.json_page_num
        

    # Get Pixiv ajax API json page URLs
    def get_json_page_urls(self) -> list[str]:
        self.json_page_urls = [parse.quote(f"{self.station_url}{self.pixiv_search_settings.build_search_appending_str_json(self.keyword_string)}&p={page_num}", safe='/:?=&')
                               for page_num in range(1, self.json_page_num + 1)]
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

        # Get pages until all pages are fetched
        empty_urls = self.json_page_urls.copy()
        json_basic_info = {}

        while len(empty_urls) > 0:
            download_urls = empty_urls.copy()
            empty_urls = []

            # Get and parse json page info
            json_page_contents = self.threading_request_page_content(
                download_urls, 
                restriction_num=self.crawler_settings.capacity_count_config.page_num, 
                session=session,
                headers=json_search_page_headers,
                # It seems that pixiv has less restrictions on crawling this type of pages, so no batch download is set.
            )

            # Get dict
            for i in range(len(download_urls)):
                parsed_content = json.loads(json_page_contents[i])
                for image_list_type in ["illust", "illustManga", "manga"]:
                    if image_list_type in parsed_content["body"].keys():
                        if len(parsed_content["body"][image_list_type]["data"]) > 0:
                            for image_data in parsed_content["body"][image_list_type]["data"]:
                                json_basic_info[image_data["id"]] = image_data
                        else:
                            empty_urls.append(download_urls[i])

            if len(empty_urls) > 0:
                self.crawler_settings.log.warning(f'{len(empty_urls)} {"pages are" if len(empty_urls) > 1 else "page is"} empty, possibly because requests were too frequent. Retrying to request pages in 1 to 2 minutes.')
                time.sleep(60 + random.random() * 60)

        # Sort with ID from large to small
        json_basic_info = {elem[0]: elem[1] for elem in sorted(json_basic_info.items(), key=lambda item: int(item[0]), reverse=True)}

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
            if content is None:  # Empty page!
                continue
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
        
        self.crawler_settings.log.info(f'Parsing image info...')
        image_info_list = []
        with ProgressGroup(panel_title="Parsing Image Info") as progress_group:
            progress = progress_group.main_count_bar
            task = progress.add_task(description="Parsing image info pages:", total=len(json_image_url_page_contents))
            for content in json_image_url_page_contents:
                if content is None:
                    continue  # Empty page!
                parsed_content = json.loads(content)
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
                progress.update(task, advance=1)
            
            progress.update(task, description="[green]Parsing image info pages finished!")

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

        self.crawler_settings.log.info(f'Parsing image info...')
        image_info_list = []
        with ProgressGroup(panel_title="Parsing Image Info") as progress_group:
            progress = progress_group.main_count_bar
            task = progress.add_task(description="Parsing image info pages:", total=len(json_image_url_page_contents))
            for content in json_image_url_page_contents:
                if content is None:
                    continue  # Empty page!
                parsed_content = json.loads(content)
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
                progress.update(task, advance=1)
            
            progress.update(task, description="[green]Parsing image info pages finished!")

        self.image_info_list = image_info_list
        return self.image_info_list
