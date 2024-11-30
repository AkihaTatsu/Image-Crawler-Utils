from bs4 import BeautifulSoup
from typing import Optional, Union

import re
import json
from urllib import parse
import requests

from image_crawler_utils import Cookies, KeywordParser, ImageInfo, CrawlerSettings
from image_crawler_utils.keyword import KeywordLogicTree, min_len_keyword_group, construct_keyword_tree_from_list
from image_crawler_utils.progress_bar import CustomProgress, ProgressGroup

from .constants import SPECIAL_WEBSITES



##### Moebooru Keyword Parser


class MoebooruKeywordParser(KeywordParser):

    def __init__(
        self, 
        station_url: str,
        crawler_settings: CrawlerSettings=CrawlerSettings(),
        standard_keyword_string: Optional[str]=None, 
        keyword_string: Optional[str]=None,
        cookies: Optional[Union[Cookies, list, dict, str]]=Cookies(),
        use_api=True,
        image_num_per_gallery_page: int=1,
        image_num_per_json: int=10, 
        replace_url_with_source_level: str="None",
        use_keyword_include: bool=False,
        has_cloudflare: bool=False,
    ):
        """
        Parameters:
            crawler_settings (image_crawler_utils.CrawlerSettings): Crawler settings.
            station_url (str): URL of the website.
            standard_keyword_string (str): A keyword string using standard syntax.
            cookies (Cookies, list, dict, str or None): Cookies used in loading websites.
            use_api (bool): Use Moebooru API. Default set to True.
                - Set to False will parse image infos from directly visited gallery pages.
                - For some websites like konachan.com, the API is protected, and you need to set this parameters to False to ensure that the Parser works correctly.
            image_num_per_gallery_page (int): Number of images on a gallery page. Default set to 1. Values for particular websites can be found in constants.py.
            image_num_per_json (int): Number of images on a json page. Default set to 1. Values for particular websites can be found in constants.py.
            keyword_string (str, optional): Specify the keyword string yourself. You can write functions to generate them from the keyword tree afterwards.
            replace_url_with_source_level (str, must be one of "All", "File", and "None"):
                - "All" means while the source of image exists, use the downloading URL with the one from source first.
                - "File" means if the source of image is a file or some special websites, use the source downloading URL first.
                - "None" means as long as the original URL exists, do not use source URL first.
            use_keyword_include (bool): Using a new keyword string whose searching results can contain all images belong to the original keyword string result. Default set to False.
                - Example: search "A" can contain all results by "A and B"
            has_cloudflare (bool): Denoting whether current website has a cloudflare protection.
        """

        super().__init__(
            station_url=station_url,
            crawler_settings=crawler_settings, 
            standard_keyword_string=standard_keyword_string, 
            keyword_string=keyword_string,
            cookies=cookies,
        )
        self.use_api = use_api
        self.image_num_per_gallery_page = image_num_per_gallery_page
        self.image_num_per_json = image_num_per_json
        self.replace_url_with_source_level = replace_url_with_source_level.lower()
        self.use_keyword_include = use_keyword_include
        self.has_cloudflare = has_cloudflare


    def run(self) -> list[ImageInfo]:
        if self.has_cloudflare:
            self.get_cloudflare_cookies()
        with requests.Session() as session:
            if not self.cookies.is_none():
                session.cookies.update(self.cookies.cookies_dict)
                
            if self.keyword_string is None:
                if self.use_keyword_include:
                    self.generate_keyword_string_include(session=session)
                else:
                    self.generate_keyword_string()

            self.get_gallery_page_num(session=session)
            if self.use_api:
                self.get_json_page_num(session=session)
                self.get_json_page_urls()
                self.get_image_info_from_json(session=session)
            else:
                self.get_gallery_page_urls()
                self.get_image_info_from_gallery_pages(session=session)
            return self.image_info_list


    ##### Custom funcs

    
    # Generate keyword string from keyword tree
    def __build_keyword_str(self, tree: KeywordLogicTree) -> str:
        """
        WARNING: Moebooru(Moebooru) does not support brackets yet!
        Due to such reason, it is NOT SUGGESTED to directly use such string
        """

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
            return f'{res1} {res2}'
        elif tree.logic_operator == "OR":
            return f'~{res1} ~{res2}'.replace('~~', '~')
        elif tree.logic_operator == "NOT":
            return f'-{res2}'
        elif tree.logic_operator == "SINGLE":
            return f'{res2}'


    # Basic keyword string
    def generate_keyword_string(self) -> str:            
        self.keyword_string = self.__build_keyword_str(self.keyword_tree)
        return self.keyword_string


    # Keyword (include) string
    def generate_keyword_string_include(self, session: requests.Session=None) -> str:
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)
            
        keyword_group = min_len_keyword_group(self.keyword_tree.keyword_include_group_list())
        keyword_strings = [self.__build_keyword_str(construct_keyword_tree_from_list(group, log=self.crawler_settings.log)) 
                           for group in keyword_group]
        min_page_num = None

        self.crawler_settings.log.info("Testing the page num of keyword (include) groups to find the one with fewest pages.")
        with CustomProgress(transient=True) as progress:
            task = progress.add_task(description="Requesting pages:", total=len(keyword_strings))
            for string in keyword_strings:
                self.crawler_settings.log.debug(f'Testing the page num of keyword string: {string}')
                self.keyword_string = string
                page_num = self.get_gallery_page_num(session=session)
                self.crawler_settings.log.debug(f'The page num of {string} is {page_num}.')
                if min_page_num is None or page_num < min_page_num:
                    min_page_num = page_num
                    min_string = string
                progress.update(task, advance=1)

            progress.update(task, description="[green]Requesting pages finished!")

        self.keyword_string = min_string
        self.crawler_settings.log.info(f'The keyword string the parser will use is "{self.keyword_string}" which has {min_page_num} {"pages" if min_page_num > 1 else "page"}.')
        return self.keyword_string
    

    # Get total gallery page num
    def get_gallery_page_num(self, session: requests.Session=None) -> int:
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)
            
        # Connect to the first gallery page
        self.crawler_settings.log.info(f'Connecting to the first gallery page using keyword string "{self.keyword_string}" ...')

        # Generate URL
        first_page_url = parse.quote(f"{self.station_url}post?tags={self.keyword_string}", safe='/:?=&')

        # Get content
        content = self.request_page_content(first_page_url, session=session)
        if content is None:
            self.crawler_settings.log.critical(f"CANNOT connect to the first gallery page, URL: \"{first_page_url}\"")
            raise ConnectionError(f"CANNOT connect to the first gallery page, URL: \"{first_page_url}\"")
        else:
            self.crawler_settings.log.info(f'Successfully connected to the first gallery page.')

        # Parse page num
        soup = BeautifulSoup(content, 'lxml')
        last_page_url = soup.find('link', title='Last Page')
        if last_page_url is not None:
            try:
                last_page_num = int(re.search(r"page=.*?&", last_page_url['href']).group()[len("page="):-1])
            except:
                last_page_num = int(re.search(r"page=.*", last_page_url['href']).group()[len("page="):])
        else:  # Only 1 page
            last_page_num = 1

        self.last_gallery_page_num = last_page_num
        return self.last_gallery_page_num


    ##### Method I: Using API


    # Get total json page num
    def get_json_page_num(self, session: requests.Session=None) -> int:
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)
            
        # Moebooru may have images not displayed in gallery but can be found by json API.
        # We will determine such number of "hidden pages".
        self.crawler_settings.log.info(f'Moebooru may have images not displayed in gallery yet but can be found by its API. We will determine the number of such "hidden pages".')
        last_json_page_num = self.last_gallery_page_num * self.image_num_per_gallery_page // self.image_num_per_json
        extra_page_num = 0

        with ProgressGroup(panel_title="Detecting Hidden [yellow]Webpages[reset]") as progress_group:
            progress = progress_group.main_no_total_count_bar
            task = progress.add_task(description=f"Preparing for detection...")
            # Preparations
            content = self.request_page_content(
                f"{self.station_url}post.json?api_version=2&limit={self.image_num_per_json}&tags={self.keyword_string}&page={last_json_page_num}",
                session=session,
            )
            content_dict = json.loads(content)["posts"]

            # Start detecting
            while len(content_dict) > 0:
                last_json_page_num += 1
                extra_page_num += 1
                content = self.request_page_content(
                    f"{self.station_url}post.json?api_version=2&limit={self.image_num_per_json}&tags={self.keyword_string}&page={last_json_page_num}",
                    session=session,
                )
                content_dict = json.loads(content)["posts"]

                progress.update(task, advance=1, description=f"Detected page number (with about [repr.number]{extra_page_num * self.image_num_per_json}[reset] {'images' if extra_page_num > 0 else 'image'}):")
            
            progress.update(task, description=f"[green]Detection finished![reset] Number of pages (with about [repr.number]{extra_page_num * self.image_num_per_json}[reset] {'images' if extra_page_num > 0 else 'image'}) detected:")

        self.last_json_page_num = last_json_page_num - 1 if last_json_page_num >= 1 else 0

        return self.last_json_page_num
    

    # Get Moebooru API json page URLs
    def get_json_page_urls(self) -> list[str]:
        if self.crawler_settings.capacity_count_config.page_num is not None:
            total_page_num = min(self.last_json_page_num, self.crawler_settings.capacity_count_config.page_num)
        else:
            total_page_num = self.last_json_page_num

        self.json_page_urls = [f"{self.station_url}post.json?api_version=2&limit={self.image_num_per_json}&tags={self.keyword_string}&page={page_num}" for page_num in range(1, total_page_num + 1)]
        return self.json_page_urls
    

    # Get image info
    def get_image_info_from_json(self, session: requests.Session=None) -> list[ImageInfo]:
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)
            
        page_content_list = self.threading_request_page_content(
            self.json_page_urls,
            restriction_num=self.crawler_settings.capacity_count_config.page_num, 
            session=session, 
        )
        
        # Parsing basic info
        self.crawler_settings.log.info(f'Parsing image info...')
        image_info_list = []
        parent_id_list = []
        with ProgressGroup(panel_title="Parsing Image Info") as progress_group:
            progress = progress_group.main_count_bar
            task = progress.add_task(description="Parsing image info pages:", total=len(page_content_list))

            for content in page_content_list:
                image_info_dict = json.loads(content)["posts"]
                for info in image_info_dict:
                    new_info = {"info": info, "family_group": None}

                    # Deal with tags
                    new_info["tags"] = info["tags"].split(" ")

                    # Add to image_group solving waitlist
                    if info["has_children"] is True:
                        parent_id_list.append(info["id"])
                    elif info["parent_id"] is not None:
                        parent_id_list.append(info["parent_id"])

                    url = None
                    image_name = None
                    source_url = None

                    # Get image url
                    if "file_url" in info.keys() and info["file_url"] is not None and len(info["file_url"]) > 0:
                        url = info["file_url"]
                        image_name = url.split('/')[-1]

                    # Get source url; must be a file or a URL in special sites
                    if info["source"] is not None and '/' in info["source"]:
                        if info["source"].split('/')[-1].count('.') == 1:
                            source_url = info["source"]
                        for special_site in SPECIAL_WEBSITES:
                            if info["source"] is not None and special_site in info["source"]:
                                source_url = info["source"]
                        # Add image name
                        if image_name is None and source_url is not None:
                            image_name = source_url.split('/')[-1]

                    if url is None:
                        if source_url is None:
                            # No url exists!
                            self.crawler_settings.log.error(f"Image with ID: {info['id']} is inaccessible.")
                        else:
                            # Only source_url exists, move source url to first if original url does not exist
                            url = source_url
                            source_url = None

                    backup_url = None

                    # Move source_url to first as long as it exists
                    if self.replace_url_with_source_level == "all":
                        if source_url is not None:
                            download_url = source_url
                            backup_url = url
                        else:
                            download_url = url
                            backup_url = source_url
                    # Only files and special websites are moved to first
                    elif self.replace_url_with_source_level == "file":
                        download_url = url
                        backup_url = source_url
                        if source_url is not None and source_url.split('/')[-1].count('.') == 1:
                            download_url = source_url
                            backup_url = url
                        for special_site in SPECIAL_WEBSITES:
                            if source_url is not None and special_site in source_url:
                                download_url = source_url
                                backup_url = url
                    # Use source_url if orignal url is lost
                    elif self.replace_url_with_source_level == "none":
                        download_url = url
                        backup_url = source_url

                    if image_name is None:
                        self.crawler_settings.log.error(f"Cannot parse image info for image ID: {info['id']}!")
                    # Successfully parsed
                    else:
                        image_info_list.append(ImageInfo(
                            url=download_url,
                            backup_urls=[backup_url] if backup_url is not None else [],
                            name=parse.unquote(image_name),
                            info=new_info,
                        ))
               
                progress.update(task, advance=1)
            
            progress.update(task, description="[green]Parsing image info pages finished!")

        self.parent_id_list = list(set(parent_id_list))
        self.image_info_list = image_info_list
        return self.image_info_list


    ##### Method II: Using directly parsed webpages


    def get_gallery_page_urls(self) -> list[str]:
        if self.crawler_settings.capacity_count_config.page_num is not None:
            total_page_num = min(self.last_gallery_page_num, self.crawler_settings.capacity_count_config.page_num)
        else:
            total_page_num = self.last_gallery_page_num

        self.gallery_page_urls = [f"{self.station_url}post?page={page_num}&tags={self.keyword_string}" for page_num in range(1, total_page_num + 1)]
        return self.gallery_page_urls


    def get_image_info_from_gallery_pages(self, session: requests.Session=None):
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)
            
        page_content_list = self.threading_request_page_content(
            self.gallery_page_urls,
            restriction_num=self.crawler_settings.capacity_count_config.page_num, 
            session=session, 
        )
        
        # Parsing basic info
        self.crawler_settings.log.info(f'Parsing image info...')
        image_info_list = []
        parent_id_list = []
        with ProgressGroup(panel_title="Parsing Image Info") as progress_group:
            progress = progress_group.main_count_bar
            task = progress.add_task(description="Parsing image info pages:", total=len(page_content_list))

            for content in page_content_list:
                tag_dict = json.loads(re.search(r'Post.register_tags\(.*\)', content).group()[len('Post.register_tags('):-len(')')])
                image_info_dict = [json.loads(res[len('Post.register('):-len(')')]) for res in re.findall(r'Post.register\(.*\)', content)]
                for info in image_info_dict:
                    new_info = {"info": info, "family_group": None}

                    # Deal with tags
                    new_info["tags"] = info["tags"].split(" ")
                    new_info["tags_class"] = {}
                    for tag in new_info["tags"]:
                        if tag in tag_dict.keys():
                            new_info["tags_class"][tag] = tag_dict[tag]

                    # Add to image_group solving waitlist
                    if info["has_children"] is True:
                        parent_id_list.append(info["id"])
                    elif info["parent_id"] is not None:
                        parent_id_list.append(info["parent_id"])

                    url = None
                    image_name = None
                    source_url = None

                    # Get image url
                    if "file_url" in info.keys() and info["file_url"] is not None and len(info["file_url"]) > 0:
                        url = info["file_url"]
                        image_name = url.split('/')[-1]

                    # Get source url; must be a file or a URL in special sites
                    if info["source"] is not None and '/' in info["source"]:
                        if info["source"].split('/')[-1].count('.') == 1:
                            source_url = info["source"]
                        for special_site in SPECIAL_WEBSITES:
                            if info["source"] is not None and special_site in info["source"]:
                                source_url = info["source"]
                        # Add image name
                        if image_name is None and source_url is not None:
                            image_name = source_url.split('/')[-1]

                    if url is None:
                        if source_url is None:
                            # No url exists!
                            self.crawler_settings.log.error(f"Image with ID: {info['id']} is inaccessible.")
                        else:
                            # Only source_url exists, move source url to first if original url does not exist
                            url = source_url
                            source_url = None

                    backup_url = None

                    # Move source_url to first as long as it exists
                    if self.replace_url_with_source_level == "all":
                        if source_url is not None:
                            download_url = source_url
                            backup_url = url
                        else:
                            download_url = url
                            backup_url = source_url
                    # Only files and special websites are moved to first
                    elif self.replace_url_with_source_level == "file":
                        download_url = url
                        backup_url = source_url
                        if source_url is not None and source_url.split('/')[-1].count('.') == 1:
                            download_url = source_url
                            backup_url = url
                        for special_site in SPECIAL_WEBSITES:
                            if source_url is not None and special_site in source_url:
                                download_url = source_url
                                backup_url = url
                    # Use source_url if orignal url is lost
                    elif self.replace_url_with_source_level == "none":
                        download_url = url
                        backup_url = source_url

                    if image_name is None:
                        self.crawler_settings.log.error(f"Cannot parse image info for image ID: {info['id']}!")
                    # Successfully parsed
                    else:
                        image_info_list.append(ImageInfo(
                            url=download_url,
                            backup_urls=[backup_url] if backup_url is not None else [],
                            name=parse.unquote(image_name),
                            info=new_info,
                        ))
               
                progress.update(task, advance=1)
            
            progress.update(task, description="[green]Parsing image info pages finished!")

        self.parent_id_list = list(set(parent_id_list))
        self.image_info_list = image_info_list
        return self.image_info_list
    