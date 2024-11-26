from bs4 import BeautifulSoup
from typing import Optional, Union

import re, json
from urllib import parse
import requests

from image_crawler_utils import Cookies, KeywordParser, ImageInfo, CrawlerSettings
from image_crawler_utils.keyword import KeywordLogicTree, min_len_keyword_group, construct_keyword_tree_from_list
from image_crawler_utils.utils import custom_tqdm

from .constants import GELBOORU_IMAGE_NUM_PER_GALLERY_PAGE, GELBOORU_IMAGE_NUM_PER_JSON, MAX_SAFEBOORU_JSON_PAGE_NUM, SPECIAL_WEBSITES



##### Safebooru Keyword Parser


class SafebooruKeywordParser(KeywordParser):

    def __init__(
        self, 
        station_url: str="https://safebooru.org/",
        crawler_settings: CrawlerSettings=CrawlerSettings(),
        standard_keyword_string: Optional[str]=None, 
        keyword_string: Optional[str]=None,
        cookies: Optional[Union[Cookies, list, dict, str]]=Cookies(),
        replace_url_with_source_level: str="None",
        use_keyword_include: bool=False,
    ):
        """
        Parameters:
            crawler_settings (image_crawler_utils.CrawlerSettings): Crawler settings.
            station_url (str): URL of the website.
            standard_keyword_string (str): A keyword string using standard syntax.
            cookies (Cookies, list, dict, str or None): Cookies used in loading websites.
            keyword_string (str, optional): Specify the keyword string yourself. You can write functions to generate them from the keyword tree afterwards.
            replace_url_with_source_level (str, must be one of "All", "File", and "None"):
                - "All" means while the source of image exists, use the downloading URL with the one from source first.
                - "File" means if the source of image is a file or some special websites, use the source downloading URL first.
                - "None" means as long as the original URL exists, do not use source URL first.
            use_keyword_include (bool): Using a new keyword string whose searching results can contain all images belong to the original keyword string result. Default set to False.
                - Example: search "A" can contain all results by "A and B"
        """

        super().__init__(
            station_url=station_url,
            crawler_settings=crawler_settings, 
            standard_keyword_string=standard_keyword_string, 
            keyword_string=keyword_string,
            cookies=cookies,
        )
        self.replace_url_with_source_level = replace_url_with_source_level.lower()
        self.use_keyword_include = use_keyword_include


    def run(self):
        with requests.Session() as session:
            if not self.cookies.is_none():
                session.cookies.update(self.cookies.cookies_dict)

            if self.keyword_string is None:
                if self.use_keyword_include:
                    self.generate_keyword_string_include(session=session)
                else:
                    self.generate_keyword_string()

            self.get_total_image_num(session=session)
            self.get_json_page_num(session=session)
            self.get_json_page_urls()
            self.get_image_info_from_json(session=session)
            return self.image_info_list


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
            return f'( {res1} {res2} )'
        elif tree.logic_operator == "OR":
            return f'( {res1} ~ {res2} )'
        elif tree.logic_operator == "NOT":
            return f'-( {res2} )'
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
            
        # In Danbooru, no more than 2 keywords can be applied at the same time when having no account.
        keyword_group = min_len_keyword_group(self.keyword_tree.keyword_include_group_list(), below=2)
        keyword_strings = [self.__build_keyword_str(construct_keyword_tree_from_list(group, log=self.crawler_settings.log)) 
                           for group in keyword_group]
        min_page_num = None

        self.crawler_settings.log.info("Testing the page num of keyword (include) groups to find the one with fewest pages.")
        with custom_tqdm.trange(
            len(keyword_strings),
            desc="Requesting pages",
        ) as pbar:
            for string in keyword_strings:
                self.crawler_settings.log.debug(f'Testing the page num of keyword string: {string}')
                self.keyword_string = string
                page_num = self.get_json_page_num(session=session)
                self.crawler_settings.log.debug(f'The page num of {string} is {page_num}.')
                if min_page_num is None or page_num < min_page_num:
                    min_page_num = page_num
                    min_string = string
                pbar.update()
                
        self.keyword_string = min_string
        self.crawler_settings.log.info(f'The keyword string the parser will use is "{self.keyword_string}" which has {min_page_num} {"pages" if min_page_num > 1 else "page"}.')
        return self.keyword_string


    # Get total image num
    def get_total_image_num(self, session: requests.Session=None) -> int:
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)
            
        # Connect to the first gallery page
        self.crawler_settings.log.info(f'Connecting to the first gallery page using keyword string "{self.keyword_string}" ...')

        # Generate URL
        first_page_url = parse.quote(f"{self.station_url}index.php?page=post&s=list&tags={self.keyword_string}", safe='/:?=&')

        # Get content
        content = self.request_page_content(first_page_url, session=session)
        if content is None:
            self.crawler_settings.log.critical(f"CANNOT connect to the first gallery page, URL: \"{first_page_url}\"")
            raise ConnectionError(f"CANNOT connect to the first gallery page, URL: \"{first_page_url}\"")
        else:
            self.crawler_settings.log.info(f'Successfully connected to the first gallery page.')

        # Parse page num
        soup = BeautifulSoup(content, 'lxml')
        last_page_url = soup.find('a', alt="last page").get("href")
        try:
            last_page_start_id = re.search(r"pid=.*", last_page_url).group()[len('pid='):]
        except:
            last_page_start_id = re.search(r"pid=.*;", last_page_url).group()[len('pid='):len(';')]

        self.total_image_num = int(last_page_start_id)  # It is actually the starting image num of the last gallery page
        return self.total_image_num
    

    # Get total json page num
    def get_json_page_num(self, session: requests.Session=None) -> int:
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)
            
        last_json_page_num = (self.total_image_num + GELBOORU_IMAGE_NUM_PER_GALLERY_PAGE) // GELBOORU_IMAGE_NUM_PER_JSON + 1

        if last_json_page_num > MAX_SAFEBOORU_JSON_PAGE_NUM:
            self.crawler_settings.log.warning(f"Currently do not accept queries for over {MAX_SAFEBOORU_JSON_PAGE_NUM} pages ({MAX_SAFEBOORU_JSON_PAGE_NUM * GELBOORU_IMAGE_NUM_PER_JSON} images)! Consider change your keywords / tags.")
            last_json_page_num = MAX_SAFEBOORU_JSON_PAGE_NUM  # Actually from 0 to MAX_SAFEBOORU_JSON_PAGE_NUM, i.e. MAX_SAFEBOORU_JSON_PAGE_NUM + 1 pages

        self.crawler_settings.log.info("Determining the last json page num...")
        with custom_tqdm.tqdm(
            bar_format=r'{desc}',
            leave=False,
        ) as pbar:
            while True:
                pbar.set_description_str(f"Current total json page num: {last_json_page_num}, Current last json page pid: {last_json_page_num - 1}")
                last_json_page_url = parse.quote(f"{self.station_url}index.php?page=dapi&s=post&q=index&json=1&tags={self.keyword_string}&pid={last_json_page_num - 1}", safe='/:?=&')
                content = self.request_page_content(last_json_page_url, session=session)
                if 'id' not in content:  # Last page does not exist
                    last_json_page_num -= 1
                else:
                    break

        self.last_json_page_num = last_json_page_num
        return self.last_json_page_num
    

    # Get Danbooru API json page URLs
    def get_json_page_urls(self) -> list[str]:
        # Attention: Gelbooru page num starts from 0 (0, 1, 2, ...)
        # self.last_json_page_num = 3 means page num is (0, 1, 2)
        if self.crawler_settings.capacity_count_config.page_num is not None:
            total_page_num = min(self.last_json_page_num, self.crawler_settings.capacity_count_config.page_num)
        else:
            total_page_num = self.last_json_page_num

        page_numlist = [str(item) for item in range(0, total_page_num)]
        self.json_page_urls = [f"{self.station_url}index.php?page=dapi&s=post&q=index&json=1&tags={self.keyword_string}&pid={page_num}" for page_num in page_numlist]

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
        with custom_tqdm.trange(
            len(page_content_list),
            desc="Parsing image info pages",
        ) as pbar:
            for content in page_content_list:
                image_info_dict = json.loads(content)  # Safebooru style
                for info in image_info_dict:
                    new_info = {"info": info, "family_group": None}

                    # Deal with tags
                    new_info["tags"] = info["tags"].split(" ")

                    # Add to image_group solving waitlist
                    if "has_children" in info.keys() and info["has_children"] is True:
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
                        image_name = f'Safebooru {new_info["info"]["id"]} {image_name}'
                        image_info_list.append(ImageInfo(
                            url=download_url,
                            backup_urls=[backup_url] if backup_url is not None else [],
                            name=parse.unquote(image_name),
                            info=new_info,
                        ))
               
                pbar.update()
                
        self.parent_id_list = list(set(parent_id_list))
        self.image_info_list = image_info_list
        return self.image_info_list
