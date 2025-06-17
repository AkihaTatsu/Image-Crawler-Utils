from bs4 import BeautifulSoup
from typing import Optional, Union

import re
import json
from urllib import parse
import requests

from image_crawler_utils import Cookies, KeywordParser, ImageInfo, CrawlerSettings
from image_crawler_utils.keyword import KeywordLogicTree, min_len_keyword_group, construct_keyword_tree_from_list
from image_crawler_utils.progress_bar import CustomProgress, ProgressGroup

from .constants import GELBOORU_IMAGE_NUM_PER_JSON, GELBOORU_IMAGE_NUM_PER_GALLERY_PAGE, MAX_GELBOORU_JSON_PAGE_NUM, SPECIAL_WEBSITES



##### Gelbooru Keyword Parser


class GelbooruKeywordParser(KeywordParser):
    """
    Args:
        crawler_settings (image_crawler_utils.CrawlerSettings): The CrawlerSettings used in this Parser.
        station_url (str): The URL of the main page of a website.

            + This parameter works when several websites use the same structure. For example, https://yande.re/ and https://konachan.com/ both use Moebooru to build their websites, and this parameter must be filled to deal with these sites respectively.
            + For websites like https://www.pixiv.net/, as no other website uses its structure, this parameter has already been initialized and do not need to be filled.

        standard_keyword_string (str): Query keyword string using standard syntax. Refer to the documentation for detailed instructions.
        cookies (image_crawler_utils.Cookies, list, dict, str, None): Cookies used in loading websites.

            + Can be one of :class:`image_crawler_utils.Cookies`, :py:class:`list`, :py:class:`dict`, :py:class:`str` or :py:data:`None`.
                + :py:data:`None` means no cookies and works the same as ``Cookies()``.
                + Leave this parameter blank works the same as :py:data:`None` / ``Cookies()``.

        keyword_string (str, None): If you want to directly specify the keywords used in searching, set ``keyword_string`` to a custom non-empty string. It will OVERWRITE ``standard_keyword_string``.

            + For example, set ``keyword_string`` to ``"kuon_(utawarerumono) rating:safe"`` in DanbooruKeywordParser means searching directly with this string in Danbooru, and its standard keyword string equivalent is ``"kuon_(utawarerumono) AND rating:safe"``.

        use_api (bool): Use Gelbooru API page, like https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&api_key=*********&user_id=*********.

            + Set to :py:data:`False` will parse image infos from directly visited gallery pages, like https://yande.re/.
            + For some websites like konachan.com, the API is protected, and you need to set this parameters to False to ensure that the Parser works correctly.

        replace_url_with_source_level (str, must be one of "All", "File", and "None"): A level controlling whether the Parser will try to download from the source URL of images instead of from the current website.

            + It has 3 available levels, and default is "None":
                + "All" or "all" (NOT SUGGESTED): As long as the image has a source URL, try to download from this URL first.
                + "File" or "file": If the source URL looks like a file (e.g. https://foo.bar/image.png) or it is one of several special websites (e.g. Pixiv or Twitter / X status), try to download from this URL first.
                + "None" or "none": Do not try to download from any source URL first.
            + Both source URLs and Danbooru URLs are stored in ImageInfo class and will be used when downloading. This parameters only controls the priority of URLs.
            + Set to a level other than "None" / "none" will reduce the pressure on Danbooru server but cost longer time (as source URLs may not be directly accessible, or they are absolutely unavailable).

        use_keyword_include (bool): If this parameter is set to :py:data:`True`, KeywordParser will try to find keyword / tag subgroups with lowest number of keywords / tags (or subgroups with number of keywords / tags lower than a threshold, like 2 in Danbooru for those without an account) that contain all searching results with the least page number.

            + Only works when ``standard_keyword_string`` is used. When ``keyword_string`` is specified, this parameter is omitted.
            + For example, if the ``standard_keyword_string`` is set to "kuon_(utawarerumono) AND rating:safe OR utawarerumono", then the Parser will check "kuon_(utawarerumono) OR utawarerumono" and "rating:safe OR utawarerumono" and select the group with the least page number of results as the keyword string in later queries.
            + If no subgroup with less than 2 keywords / tags exists (e.g. "kuon_(utawarerumono) OR rating:safe OR utawarerumono"), the Parser will try to find keyword / tag subgroups with the least keyword / tag number. This may often CAUSE ERRORS, so make a quick check of your keywords before setting this parameter to :py:data:`True`.

        api_key (str): The api_key used to access JSON-API. Can be acquired after logging in at https://gelbooru.com/index.php?page=account&s=options.
        user_id (str): The user_id used to access JSON-API. Can be acquired after logging in at https://gelbooru.com/index.php?page=account&s=options.
    """

    def __init__(
        self, 
        station_url: str="https://gelbooru.com/",
        crawler_settings: CrawlerSettings=CrawlerSettings(),
        standard_keyword_string: Optional[str]=None, 
        keyword_string: Optional[str]=None,
        cookies: Optional[Union[Cookies, list, dict, str]]=Cookies(),
        use_api: bool=False,
        replace_url_with_source_level: str="None",
        use_keyword_include: bool=False,
        api_key: str=None,
        user_id: str=None,
    ):

        super().__init__(
            station_url=station_url,
            crawler_settings=crawler_settings, 
            standard_keyword_string=standard_keyword_string, 
            keyword_string=keyword_string,
            cookies=cookies,
        )
        self.use_api = use_api
        self.replace_url_with_source_level = replace_url_with_source_level.lower()
        self.use_keyword_include = use_keyword_include
        self.api_key = api_key
        self.user_id = user_id
        if use_api and (api_key is None or user_id is None):
            self.crawler_settings.log.warning("api_key and user_id should not be empty! Otherwise, the API pages will be quite possibly inaccessible.")


    def run(self) -> list[ImageInfo]:
        """
        The main function that runs the Parser and returns a list of :class:`image_crawler_utils.ImageInfo`.
        """
        with requests.Session() as session:
            if not self.cookies.is_none():
                session.cookies.update(self.cookies.cookies_dict)

            if self.keyword_string is None:
                if self.use_keyword_include:
                    self.generate_keyword_string_include(session=session)
                else:
                    self.generate_keyword_string()

            if self.use_api:
                self.get_total_image_num_json(session=session)
                self.get_json_page_num()
                self.get_json_page_urls()
                self.get_image_info_from_json(session=session)
            else:
                self.get_total_image_num_gallery(session=session)
                self.get_gallery_page_urls()
                self.get_image_info_from_gallery(session=session)

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
            return f'{res1} {res2}'
        elif tree.logic_operator == "OR":
            self.crawler_settings.log.warning('"OR" is currently not supported in the standard_keyword_string of Gelbooru! An error is likely to happen. Please check out the cheatsheet of Gelbooru to construct the keyword_string manually.')
            return '{{{} ~ {}}}'.format(res1, res2)
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
            
        # In Danbooru, no more than 2 keywords can be applied at the same time when having no account.
        keyword_group = min_len_keyword_group(self.keyword_tree.keyword_include_group_list(), below=2)
        keyword_strings = [self.__build_keyword_str(construct_keyword_tree_from_list(group, log=self.crawler_settings.log)) 
                           for group in keyword_group]
        min_image_num = None

        self.crawler_settings.log.info("Testing the image num of keyword (include) groups to find the one with fewest images.")
        with CustomProgress(transient=True) as progress:
            task = progress.add_task(description="Requesting pages:", total=len(keyword_strings))
            for string in keyword_strings:
                self.crawler_settings.log.debug(f'Testing the image num of keyword string: {string}')
                self.keyword_string = string
                image_num = self.get_total_image_num_json(session=session)
                self.crawler_settings.log.debug(f'The image num of {string} is {image_num}.')
                if min_image_num is None or image_num < min_image_num:
                    min_image_num = image_num
                    min_string = string
                progress.update(task, advance=1)

            progress.update(task, description="[green]Requesting pages finished!")

        self.keyword_string = min_string
        self.crawler_settings.log.info(f'The keyword string the parser will use is "{self.keyword_string}" which has {min_image_num} {"images" if min_image_num > 1 else "image"}.')
        return self.keyword_string


    ##### Method I: Using API


    # Get total image num from JSON
    def get_total_image_num_json(self, session: requests.Session=None) -> int:
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)
            
        # Connect to the first JSON-API page
        self.crawler_settings.log.info(f'Connecting to the first JSON-API page using keyword string "{self.keyword_string}" ...')

        # Generate URL
        first_page_url = parse.quote(f"{self.station_url}index.php?page=dapi&s=post&q=index&json=1{f'&api_key={self.api_key}' if self.api_key is not None else ''}{f'&user_id={self.user_id}' if self.user_id is not None else ''}&tags={self.keyword_string}", safe='/:?=&')

        # Get content
        content = self.request_page_content(first_page_url, session=session)
        if content is None:
            self.crawler_settings.log.critical(f"CANNOT connect to the first JSON-API page, URL: [repr.url]{first_page_url}[reset]", extra={"markup": True})
            raise ConnectionError(f"CANNOT connect to the first JSON-API page, URL: {first_page_url}")
        else:
            self.crawler_settings.log.info(f'Successfully connected to the first JSON-API page.')

        self.total_image_num = json.loads(content)['@attributes']['count']
        return self.total_image_num
    

    # Get total json page num
    def get_json_page_num(self) -> int:
        last_json_page_num = self.total_image_num // GELBOORU_IMAGE_NUM_PER_JSON + 1

        if last_json_page_num > MAX_GELBOORU_JSON_PAGE_NUM:
            self.crawler_settings.log.warning(f"Currently do not accept queries for over {MAX_GELBOORU_JSON_PAGE_NUM} pages ({MAX_GELBOORU_JSON_PAGE_NUM * GELBOORU_IMAGE_NUM_PER_JSON} images)! Consider change your keywords / tags.")
            last_json_page_num = MAX_GELBOORU_JSON_PAGE_NUM  # Actually from 0 to MAX_GELBOORU_PAGE_NUM, i.e. MAX_GELBOORU_PAGE_NUM + 1 pages

        self.last_json_page_num = last_json_page_num
        return self.last_json_page_num
    

    # Get Booru API json page URLs
    def get_json_page_urls(self) -> list[str]:
        # Attention: Gelbooru page num starts from 0 (0, 1, 2, ...)
        # self.last_json_page_num = 3 means page num is (0, 1, 2)
        if self.crawler_settings.capacity_count_config.page_num is not None:
            total_page_num = min(self.last_json_page_num, self.crawler_settings.capacity_count_config.page_num)
        else:
            total_page_num = self.last_json_page_num

        page_numlist = [str(item) for item in range(0, total_page_num)]
        self.json_page_urls = [f"{self.station_url}index.php?page=dapi&s=post&q=index&json=1{f'&api_key={self.api_key}' if self.api_key is not None else ''}{f'&user_id={self.user_id}' if self.user_id is not None else ''}&tags={self.keyword_string}&pid={page_num}" for page_num in page_numlist]

        return self.json_page_urls
    

    # Get image info
    def get_image_info_from_json(self, session: requests.Session=None) -> list[ImageInfo]:
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)
            
        self.crawler_settings.log.info(f'Requesting JSON-API pages...')
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
                if "post" not in json.loads(content).keys():  # No result!
                    continue
                image_info_dict = json.loads(content)["post"]  # Gelbooru-style
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
                        image_name = f'Gelbooru {new_info["info"]["id"]} {image_name}'
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


    # Get total image num from JSON
    def get_total_image_num_gallery(self, session: requests.Session=None) -> int:
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
            self.crawler_settings.log.critical(f"CANNOT connect to the first gallery page, URL: [repr.url]{first_page_url}[reset]", extra={"markup": True})
            raise ConnectionError(f"CANNOT connect to the first gallery page, URL: {first_page_url}")
        else:
            self.crawler_settings.log.info(f'Successfully connected to the first gallery page.')

        # Parse page number
        soup = BeautifulSoup(content, 'lxml')
        last_page_url = soup.find('a', alt='last page')
        if last_page_url is not None:
            try:
                last_gallery_page_num = int(re.search(r"pid=.*?&", last_page_url['href']).group()[len("pid="):-1]) // GELBOORU_IMAGE_NUM_PER_GALLERY_PAGE + 1
            except:
                last_gallery_page_num = int(re.search(r"pid=.*", last_page_url['href']).group()[len("pid="):]) // GELBOORU_IMAGE_NUM_PER_GALLERY_PAGE + 1
        else:
            page_urls = soup.find('div', id='paginator')
            pages = page_urls.find_all("a")
            if len(page_urls) > 0:  # Multiple pages, but not much
                last_gallery_page_num = int(pages[-1].text)
            else:  # Only 1 page
                last_gallery_page_num = 1

        self.last_gallery_page_num = last_gallery_page_num
        return self.last_gallery_page_num


    # Get Booru API json page URLs
    def get_gallery_page_urls(self) -> list[str]:
        # Check if max page-starting pid exceeds 20000
        max_starting_pid = (MAX_GELBOORU_JSON_PAGE_NUM - 1) * GELBOORU_IMAGE_NUM_PER_JSON
        if (self.last_gallery_page_num - 1) * GELBOORU_IMAGE_NUM_PER_GALLERY_PAGE > max_starting_pid:
            self.crawler_settings.log.warning(f"Currently do not accept queries for gallery pages starting from the {(max_starting_pid // GELBOORU_IMAGE_NUM_PER_GALLERY_PAGE + 1) * GELBOORU_IMAGE_NUM_PER_GALLERY_PAGE}th image! Consider change your keywords / tags.")

            total_page_num = max_starting_pid // 42 + 1
            page_numlist = [item for item in range(0, total_page_num)]
            self.gallery_page_urls = [f"{self.station_url}index.php?page=post&s=list&tags={self.keyword_string}&pid={page_num * GELBOORU_IMAGE_NUM_PER_GALLERY_PAGE}" for page_num in page_numlist]
            self.gallery_page_urls.append(f"{self.station_url}index.php?page=post&s=list&tags={self.keyword_string}&pid={max_starting_pid}")  # Add the last page

            self.is_last_page_exceeded = True  # LAST PAGE EXCEEDED 20034!
        else:
            total_page_num = self.last_gallery_page_num
            page_numlist = [item for item in range(0, total_page_num)]
            self.gallery_page_urls = [f"{self.station_url}index.php?page=post&s=list&tags={self.keyword_string}&pid={page_num * GELBOORU_IMAGE_NUM_PER_GALLERY_PAGE}" for page_num in page_numlist]
            
            self.is_last_page_exceeded = False  # LAST PAGE EXCEEDED 20034!

        return self.gallery_page_urls


    # Get image info
    def get_image_info_from_gallery(self, session: requests.Session=None) -> list[ImageInfo]:
        if session is None:
            session = requests.Session()
            session.cookies.update(self.cookies.cookies_dict)
        
        # Getting gallery pages
        self.crawler_settings.log.info(f'Requesting gallery pages...')
        page_content_list = self.threading_request_page_content(
            self.gallery_page_urls,
            restriction_num=self.crawler_settings.capacity_count_config.page_num, 
            session=session, 
        )
        
        # Parsing gallery info
        self.crawler_settings.log.info(f'Parsing gallery pages...')
        image_page_urls = []
        with ProgressGroup(panel_title="Parsing Gallery Pages") as progress_group:
            progress = progress_group.main_count_bar
            task = progress.add_task(description="Parsing gallery pages:", total=len(page_content_list))

            for content in page_content_list:
                soup = BeautifulSoup(content, 'lxml')
                thumbnail_struct_list = soup.find_all("article", class_="thumbnail-preview")
                for thumbnail_struct in thumbnail_struct_list:
                    image_page_urls.append(thumbnail_struct.find("a")['href'])
                    
                progress.update(task, advance=1)

        # Getting image pages
        self.crawler_settings.log.info(f'Requesting detailed image pages...')
        page_content_list = self.threading_request_page_content(
            image_page_urls,
            restriction_num=self.crawler_settings.capacity_count_config.page_num, 
            session=session, 
        )
        
        # Parsing image info
        self.crawler_settings.log.info(f'Parsing detailed image pages...')
        image_info_list = []
        with ProgressGroup(panel_title="Parsing Image Pages") as progress_group:
            progress = progress_group.main_count_bar
            task = progress.add_task(description="Parsing image pages:", total=len(page_content_list))

            for content in page_content_list:
                soup = BeautifulSoup(content, 'lxml')

                # Deal with tags
                sidebar_html = soup.find("ul", class_="tag-list")
                sidebar_list = sidebar_html.find_all("li")
                tag_struct_list = [tag_struct for tag_struct in sidebar_list
                                   if 'class' in tag_struct.attrs.keys()]

                tags_list = [tag.find_all("a")[1].text for tag in tag_struct_list]
                tags_class_list = {}
                for i in range(len(tags_list)):
                    tags_list[i] = tags_list[i].replace('\n', '').replace(' ', '_').strip()
                    while '__' in tags_list[i]:
                        tags_list[i] = tags_list[i].replace('__', '_')
                    tags_class_list[tags_list[i]] = tag_struct_list[i].attrs['class'][0].replace('tag-type-', '')

                # Deal with statistics
                id = [int(elem.text.replace("Id: ", "")) for elem in sidebar_list
                    if "Id: " in elem.text][0]
                created_at = [' '.join(elem.text.strip().split(' ')[1:3])
                              for elem in sidebar_list 
                              if "Posted: " in elem.text][0]
                owner = [elem.find('a').text
                         for elem in sidebar_list
                         if "Posted: " in elem.text][0]
                creator_id = [elem.find('a')['href'][elem.find('a')['href'].find("id=") + len("id="):]
                              for elem in sidebar_list
                              if "Posted: " in elem.text][0]
                width_by_height = [elem.text.replace("Size: ", "")
                                   for elem in sidebar_list
                                   if "Size: " in elem.text][0]
                width, height = tuple(width_by_height.split('x'))
                width, height = int(width), int(height)
                source = [elem.find('a')
                          for elem in sidebar_list
                          if "Source: " in elem.text]
                if len(source) > 0:
                    source = source[0]
                    source = source['href'] if source is not None else source
                else:
                    source = None
                rating = [elem.text.replace("Rating: ", "").lower()
                          for elem in sidebar_list
                          if "Rating: " in elem.text][0]
                score = [int(elem.find('span').text)
                         for elem in sidebar_list
                         if "Score: " in elem.text][0]
                
                info_dict = {
                    "info": {
                        "id": id,
                        "created_at": created_at,
                        "owner": owner,
                        "creator_id": creator_id,
                        "width": width,
                        "height": height,
                        "source": source,
                        "rating": rating,
                        "score": score,
                    },
                    "tags": tags_list,
                    "tags_class": tags_class_list,
                }
                
                # Deal with other attributes

                url = None
                image_name = None
                source_url = source
                
                # Get image url & name
                url = soup.find('a', rel="noopener")['href']
                image_name = url.split('/')[-1]

                if url is None:
                    if source_url is None:
                        # No url exists!
                        self.crawler_settings.log.error(f"Image with ID: {info_dict['info']['id']} is inaccessible.")
                    else:
                        # Only source_url exists, move source url to first if original url does not exist
                        url = source_url
                        source_url = None

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
                    self.crawler_settings.log.error(f"Cannot parse image info for image ID: {info_dict['info']['id']}!")
                # Successfully parsed
                else:
                    image_name = f'Gelbooru {info_dict["info"]["id"]} {image_name}'
                    image_info_list.append(ImageInfo(
                        url=download_url,
                        backup_urls=[backup_url] if backup_url is not None else [],
                        name=parse.unquote(image_name),
                        info=info_dict,
                    ))

                progress.update(task, advance=1)
            
            progress.update(task, description="[green]Parsing image info pages finished!")
                
        self.image_info_list = image_info_list
        return self.image_info_list
    