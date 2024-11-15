from typing import Optional, Union
from collections.abc import Callable

import json
from collections import ChainMap
import requests

from image_crawler_utils import Cookies, Parser, ImageInfo, CrawlerSettings
from image_crawler_utils.user_agent import UserAgent



##### Pixiv User Parser


class PixivUserParser(Parser):

    def __init__(
        self,
        member_id: str,
        station_url: str="https://www.pixiv.net/",
        crawler_settings: CrawlerSettings=CrawlerSettings(),
        cookies: Optional[Union[Cookies, list, dict, str]]=Cookies(),
        thread_delay: Union[float, Callable]=0,
        quick_mode: bool=False,
        info_page_batch_num: Optional[int]=100,
        info_page_batch_delay: Union[float, Callable]=300,
    ):
        """
        Parameters:
            crawler_settings (image_crawler_utils.CrawlerSettings): Crawler settings.
            member_id: Pixiv ID of the user.
            station_url (str): URL of the website.
            use_keyword_include (bool): Using a new keyword string whose searching results can contain all images belong to the original keyword string result. Default set to False.
                - Example: search "A" can contain all results by "A and B"
            cookies (crawler_utils.cookies.Cookies, str, dict or list, optional): Cookies containing logging information.
            quick_mode: DO NOT DOWNLOAD any image info. Will increase speed of downloading.
        """

        super().__init__(
            station_url=station_url,
            crawler_settings=crawler_settings, 
            cookies=cookies,
        )
        self.member_id = member_id
        self.thread_delay = thread_delay
        self.quick_mode = quick_mode
        self.info_page_batch_num = info_page_batch_num
        self.info_page_batch_delay = info_page_batch_delay


    def run(self):
        if self.thread_delay == 0:  # Pixiv do not accept frequent requests!
            self.thread_delay = self.crawler_settings.download_config.thread_num * 1.0  # Set the delay to 1.0 * thread num

        with requests.Session() as session:
            if not self.cookies.is_none():
                session.cookies.update(self.cookies.cookies_dict)
            else:
                raise ValueError('Cookies cannot be empty!')
            self.get_image_ids(session=session)
            if self.quick_mode:
                return self.get_image_info_quick(session=session)
            else:
                return self.get_image_info_full(session=session)


    ##### Custom funcs
    

    # Get Pixiv ajax API image IDs
    def get_image_ids(self, session: requests.Session=None) -> list[str]:
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)
            
        self.crawler_settings.log.info(f"Downloading info of images uploaded by Pixiv member ID: {self.member_id} ...")

        # Update headers for json download
        if self.crawler_settings.download_config.result_headers is None:  # Pixiv must have user-agents!
            json_user_page_headers = dict(ChainMap(UserAgent.random_agent_with_name("Chrome"), {"Referer": "www.pixiv.net"}))
        else:
            json_user_page_headers = dict(ChainMap(self.crawler_settings.download_config.result_headers, {"Referer": "www.pixiv.net"}))

        # Get and parse json page info
        user_page_json_content = self.request_page_content(
            url=f"{self.station_url}ajax/user/{self.member_id}/works/latest",
            session=session,
            headers=json_user_page_headers,
        )
        
        # Sort from newest to oldest
        self.image_ids = sorted(list(json.loads(user_page_json_content)["body"]["illusts"].keys()), key=lambda x: int(x), reverse=True)
        return self.image_ids
    

    # Get image info: full
    def get_image_info_full(self, session: requests.Session=None) -> list[ImageInfo]:
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)
            
        # Update headers for illust detection
        if self.crawler_settings.download_config.result_headers is None:  # Pixiv must have user-agents!
            json_image_url_page_headers = [dict(ChainMap(UserAgent.random_agent_with_name("Chrome"), {"Referer": f"www.pixiv.net/artworks/{artwork_id}"}))
                                           for artwork_id in self.image_ids]
        else:
            json_image_url_page_headers = [dict(ChainMap(self.crawler_settings.download_config.result_headers, {"Referer": f"www.pixiv.net/artworks/{artwork_id}"}))
                                           for artwork_id in self.image_ids]
        
        # Get and parse json page info 
        self.crawler_settings.log.info("Downloading image info for every Pixiv ID...")
        json_image_info_urls = [f'{self.station_url}ajax/illust/{artwork_id}'
                                for artwork_id in self.image_ids]
        json_image_url_page_contents = self.threading_request_page_content(
            json_image_info_urls, 
            restriction_num=self.crawler_settings.capacity_count_config.image_num, 
            session=session,
            headers=json_image_url_page_headers,
            thread_delay=1.0 * self.crawler_settings.download_config.thread_num,
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
                                    for artwork_id in self.image_ids]
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


    # Get image info: full
    def get_image_info_quick(self, session: requests.Session=None) -> list[ImageInfo]:
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)
            
        # Update headers for illust detection
        if self.crawler_settings.download_config.result_headers is None:  # Pixiv must have user-agents!
            json_image_url_page_headers = [dict(ChainMap(UserAgent.random_agent_with_name("Chrome"), {"Referer": f"www.pixiv.net/artworks/{artwork_id}"}))
                                           for artwork_id in self.image_ids]
        else:
            json_image_url_page_headers = [dict(ChainMap(self.crawler_settings.download_config.result_headers, {"Referer": f"www.pixiv.net/artworks/{artwork_id}"}))
                                           for artwork_id in self.image_ids]
            
        # Get and parse json page info 
        self.crawler_settings.log.info("Downloading image URLs for every Pixiv ID...")
        json_image_download_urls = [f'{self.station_url}ajax/illust/{artwork_id}/pages'
                                    for artwork_id in self.image_ids]
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
                image_info_list.append(ImageInfo(
                    url=image_url_size["urls"]["original"],
                    name=image_url_size["urls"]["original"].split('/')[-1],
                    info={
                        "id": image_id,
                        "width": image_url_size["width"],
                        "height": image_url_size["height"],
                    },
                ))

        self.image_info_list = image_info_list
        return self.image_info_list
