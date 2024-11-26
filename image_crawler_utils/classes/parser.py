from abc import ABC, abstractmethod

import requests
import traceback
import random
import time, datetime
from typing import Optional, Union
from collections.abc import Iterable, Callable
import os, dill
from pprint import pprint

from urllib import parse
from concurrent import futures

import nodriver

from image_crawler_utils import Cookies
from image_crawler_utils.keyword import KeywordLogicTree, construct_keyword_tree
from image_crawler_utils.log import print_logging_msg, Log
from image_crawler_utils.utils import custom_tqdm, check_dir, Empty, set_up_nodriver_browser

from .crawler_settings import CrawlerSettings
from .image_info import ImageInfo



class Parser(ABC):

    def __init__(
        self,
        station_url: str,
        crawler_settings: CrawlerSettings=CrawlerSettings(),
        cookies: Optional[Union[Cookies, list, dict, str]]=Cookies(),
    ):
        """
        A Parser include several basic functions.

        Parameters:
            station_url (str): URL of the main station of the Parser.
            crawler_settings (image_crawler_utils.CrawlerSettings): Crawler settings for this parser.
            cookies (Cookies, list, dict, str or None): Cookies used in loading websites.

        Attributes:
            run(): Running the parser. Return total image size and succeeded, failed and skipped ImageInfo list.
            display_all_configs(): Display all configs of parser.
            request_page_content(): Download web page content using configs in Parser.
            threading_request_page_content(): Downloading a list of web page contents.
        """
        super().__init__()
        self.crawler_settings = crawler_settings
        self.station_url = parse.quote(station_url + ('/' if not station_url.endswith('/') else ''), safe='/:?=&')
        if isinstance(cookies, Cookies):
            self.cookies = cookies
        else:
            self.cookies = Cookies.create_by(cookies)


    ##### Funtion requires rewriting


    @abstractmethod
    def run(self) -> list[ImageInfo]:
        """
        MUST BE OVERRIDEN.
        Generate a list of ImageInfo, containing image urls, names and infos.
        """
        raise NotImplemented


    ##### General Function

    
    # Display all config
    def display_all_configs(self):
        """
        Display all config info.
        Dataclasses will be displayed in a neater way.
        """

        print_logging_msg("========== Current Parser Config ==========", "debug")

        # Basic info
        try:
            print('\nBasic Info:')
            print(f"  - Station URL: {self.station_url}")
            if self.cookies.is_none():                
                print(f"  - Cookies: None")
            else:
                print(f"  - Cookies:")
                pprint(self.cookies.cookies_selenium)
        except Exception as e:
            print_logging_msg(f"Basic Info missing because {e}!\n{traceback.format_exc()}", "error")

        # Other info
        if set(self.__init__.__code__.co_varnames) != set(KeywordParser.__init__.__code__.co_varnames):
            print('\nOther Info:')
        for varname in self.__init__.__code__.co_varnames:
            if varname not in KeywordParser.__init__.__code__.co_varnames:
                if getattr(self, varname, None) is not None:
                    print(f"  - {varname}: {getattr(self, varname)}")

        print('')
        print_logging_msg("CrawlerSettings used:", "debug")
        self.crawler_settings.display_all_configs()
            
        print('')
        print_logging_msg("========== Parser Config Ending ==========", "debug")


    def save_to_pkl(
        self, 
        pkl_file: str,
    ) -> Optional[tuple[str, str]]:
        """
        Save the parser in a pkl file. 

        Parameters:
            path (str): Path to save the pkl file. Default is saving to the current path.
            pkl_file (str, optional): Name of the pkl file. (Suffix is optional.)

        Returns:
            (Saved file name, Absolute path of the saved file), or None if failed.
        """

        path, filename = os.path.split(pkl_file)
        check_dir(path, self.crawler_settings.log)
        f_name = os.path.join(path, f"{filename}.pkl")
        f_name = f_name.replace(".pkl.pkl", ".pkl")  # If .pkl is already contained in pkl_file, skip it

        try:
            with open(f_name, "wb") as f:
                dill.dump(self, f)
                self.crawler_settings.log.info(f'{type(self).__name__} has been dumped into "{os.path.abspath(f_name)}"')
                return f_name, os.path.abspath(f_name)
        except Exception as e:
            self.crawler_settings.log.error(f'Failed to dump {type(self).__name__} into "{os.path.abspath(f_name)}" because {e}\n{traceback.format_exc()}')
            return None
        
    
    @classmethod
    def load_from_pkl(
        cls,
        pkl_file: str,
        log: Log=Log(),
    ) -> CrawlerSettings:
        """
        Load parser from .pkl file.

        Parameters:
            pkl_file (str, optional): Name of the pkl file.
            log (crawler_utils.log.Log, optional): Logging config.

        Returns:
            A CrawlerSettings class loaded from pkl file, or None if failed.
        """
        
        try:
            with open(pkl_file, "rb") as f:
                cls = dill.load(f)
                log.info(f'{type(cls).__name__} has been successfully loaded from "{os.path.abspath(pkl_file)}"')
            return cls
        except Exception as e:
            log.error(f'Failed to load {type(cls).__name__} from "{os.path.abspath(pkl_file)}" because {e}\n{traceback.format_exc()}')
            return None


    # Get web page content
    def request_page_content(
        self, 
        url: str, 
        session=requests.Session(),
        headers: Optional[Union[dict, Callable]]=Empty(),
        thread_delay: Union[None, float, Callable]=None,
    ) -> str:
        """
        Download web page content.

        Parameters:
            url (str): The URL of the page to download.
            session (requests from import requests, or requests.Session): Can be requests or requests.Session()
            headers (dict or function, optional): If you need to specify headers for current request, use this argument. Set to None (default) meaning use the headers from self.crawler_settings.download_config.result_headers
            thread_delay: Delay before thread running. Default set to None. Used to deal with websites like Pixiv which has a restriction on requests in a certain period of time.
        
        Returns:
            The HTML content of the web page.
        """

        self.crawler_settings.log.debug(f'Try connecting to \"{url}\"')
        if thread_delay is None:
            real_thread_delay = self.crawler_settings.download_config.result_thread_delay
        else:
            real_thread_delay = thread_delay() if callable(thread_delay) else thread_delay
        time.sleep(real_thread_delay)
        
        for i in range(self.crawler_settings.download_config.retry_times):
            try:
                download_time = self.crawler_settings.download_config.max_download_time

                if isinstance(headers, Empty):
                    request_headers = self.crawler_settings.download_config.result_headers
                else:
                    request_headers = headers() if callable(headers) else headers

                response = session.get(
                    url,
                    headers=request_headers,
                    proxies=self.crawler_settings.download_config.result_proxies,
                    timeout=(self.crawler_settings.download_config.timeout, download_time),
                )

                if response.status_code == requests.status_codes.codes.ok:
                    self.crawler_settings.log.debug(f'Successfully connected to \"{url}\" at attempt {i + 1}.')
                    return response.text
                elif response.status_code == 429:
                    self.crawler_settings.log.warning(f'Connecting to \"{url}\" FAILED at attempt {i + 1} because TOO many requests at the same time (response status code {response.status_code}). Retrying to connect in 1 to 2 minutes, but it is suggested to lower the number of threads and try again.')
                    time.sleep(60 + random.random() * 60)
                elif 400 <= response.status_code < 500:
                    self.crawler_settings.log.error(f'Connecting to \"{url}\" FAILED because response status code is {response.status_code}.')
                    return None
                else:
                    self.crawler_settings.log.warning(f'Failed to connect to \"{url}\" at attempt {i + 1}. Response status code is {response.status_code}.')
                
            except Exception as e:
                self.crawler_settings.log.warning(f"Connecting to \"{url}\" at attempt {i + 1} FAILED because {e} Retry connecting.\n{traceback.format_exc()}",
                                 output_msg=f"Connecting to \"{url}\" at attempt {i + 1} FAILED.")
                time.sleep(self.crawler_settings.download_config.result_fail_delay)

        self.crawler_settings.log.error(f'FAILED to connect to \"{url}\"')
        return None
    

    # Download in threads
    def __request_page_content_thread(
        self, 
        url: str, 
        thread_id: int,
        session=requests.Session(),
        headers: Optional[Union[dict, Callable]]=Empty(),
        thread_delay: Union[None, float, Callable]=None,
    ):
        """
        Works the same as self.request_page_content, except for an thread id appended to its result.
        """

        result = self.request_page_content(
            url=url,
            session=session,
            headers=headers,
            thread_delay=thread_delay,
        )
        return result, thread_id


    def threading_request_page_content(
        self, 
        url_list: Iterable[str], 
        restriction_num: Optional[int]=None, 
        session=requests.Session(),
        headers: Optional[Union[dict, Callable, Iterable]]=Empty(),
        thread_delay: Union[None, float, Callable]=None,
        batch_num: Optional[int]=None,
        batch_delay: Union[float, Callable]=0.0,
    ) -> list[str]:
        """
        Download multiple web page content using threading.

        Parameters:
            url_list (list[str]): The list of URLs of the page to download.
            restriction_num (int, optional): Only download the first restriction_num number of pages. Set to None (default) meaning no restrictions.
            session (requests from import requests, or requests.Session): Can be requests or requests.Session()
            headers (dict, list or function, optional): If you need to specify headers for current threading requests, use this argument. Set to None (default) meaning use the headers from self.crawler_settings.download_config.result_headers
                - If it is a list, it should be of the same length as url_list, and for url_list[i] it will use the headers in headers[i]. The element in this list can be a dict of a function.
            thread_delay (float or function, optional): Delay before thread running. Default set to None. Used to deal with websites like Pixiv which has a restriction on requests in a certain period of time.
            batch_num: Number of pages for each batch; using it with batch_delay to wait a certain period of time after downloading each batch. Used to deal with websites like Pixiv which has a restriction on requests in a certain period of time.
            batch_delay: Delaying time (seconds) after each batch is downloaded. Used to deal with websites like Pixiv which has a restriction on requests in a certain period of time.
        
        Returns:
            A list of the HTML contents of the web pages. Its order is the same as the one of url_list.
        """

        page_num = len(url_list)
        if restriction_num is not None:
            page_num = min(page_num, restriction_num)
        l_url_list = list(url_list)
        if isinstance(headers, Empty):
            headers = self.crawler_settings.download_config.result_headers
        elif isinstance(headers, Iterable) and not isinstance(headers, dict):
            if len(headers) != len(url_list):
                self.crawler_settings.log.critical(f"The number of headers ({len(url_list)}) should be of the same length as the number of URLs ({len(headers)})")
                raise ValueError(f"The number of headers ({len(url_list)}) should be of the same length as the number of URLs ({len(headers)})")
            l_headers = list(headers)

        page_content_dict_with_thread_id = {}
        
        self.crawler_settings.log.info(f"Total web page num: {page_num}")
        if page_num > 0:
            if batch_num is None:
                batch_num = page_num
            batched_url_list = [l_url_list[k * batch_num:min((k + 1) * batch_num, page_num)] 
                                for k in range((page_num - 1) // batch_num + 1)]
            if isinstance(headers, Iterable) and not isinstance(headers, dict):
                batched_headers = [l_headers[k * batch_num:min((k + 1) * batch_num, page_num)] 
                                   for k in range((page_num - 1) // batch_num + 1)]

            with custom_tqdm.trange(
                page_num,
                desc="Downloading web pages",
            ) as pbar:
                for j in range(len(batched_url_list)):
                    with futures.ThreadPoolExecutor(self.crawler_settings.download_config.thread_num) as executor:
                        # Start downloading
                        if isinstance(headers, Iterable) and not isinstance(headers, dict):
                            thread_pool = [executor.submit(
                                self.__request_page_content_thread, 
                                batched_url_list[j][i],
                                j * batch_num + i,
                                session,
                                batched_headers[j][i],
                                thread_delay,
                            ) for i in range(len(batched_url_list[j]))]
                        else:
                            thread_pool = [executor.submit(
                                self.__request_page_content_thread, 
                                batched_url_list[j][i],
                                j * batch_num + i,
                                session,
                                headers,
                                thread_delay,
                            ) for i in range(len(batched_url_list[j]))]

                        for thread in futures.as_completed(thread_pool):
                            if thread.result() is not None:
                                # Successful download
                                page_content_dict_with_thread_id[thread.result()[1]] = thread.result()[0]
                                pbar.update()
                            else:
                                # Failed download
                                pbar.update()
                
                    if (j + 1) * batch_num < page_num:
                        current_batch_delay = batch_delay() if callable(batch_delay) else batch_delay
                        restart_time = datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(seconds=current_batch_delay), '%H:%M:%S')
                        self.crawler_settings.log.info(f"A batch of {len(batched_url_list[j])} {'page' if len(batched_url_list) <= 1 else 'pages'} has been downloaded. Waiting {current_batch_delay} {'second' if current_batch_delay <= 1 else 'seconds'} before resuming at {restart_time}.")
                        time.sleep(current_batch_delay)

        else:
            self.crawler_settings.log.warning(f"No new web pages are to be downloaded.")

        # Return corresponding page result according to their order in URLs
        page_content_list = [page_content_dict_with_thread_id[i]
                             for i in range(len(page_content_dict_with_thread_id))]
        return page_content_list
    

    # Get Cloudflare cf_clearance cookies
    async def __get_cloudflare_cookies(
        self,
        url: Optional[str]=None, 
        headless: bool=False,
        timeout: float=60,
        save_cookies_file: Optional[str]=None,
    ):        
        test_url = url if url is not None else self.station_url
        self.crawler_settings.log.info(f"Loading browser to get Cloudflare cookies from {test_url}.")
        
        # Pass Cloudflare verification
        with custom_tqdm.trange(
            2,
            desc=f'Loading browser components...',
            leave=False,
        ) as pbar:
            try:
                browser = await set_up_nodriver_browser(
                    proxies=self.crawler_settings.download_config.result_proxies,
                    headless=headless,
                    window_width=800,
                    window_height=600,
                )
                
                pbar.update()
                pbar.set_description(f"Loading Cloudflare page and try bypassing it...")

                tab = await browser.get(test_url, new_tab=True)
                start_timestamp = datetime.datetime.now()
                while (datetime.datetime.now() - start_timestamp).seconds < timeout:
                    try:
                        await tab.find('div[class="main-content"]', timeout=3)
                    except:
                        break
                try:
                    await tab.find('div[class="main-content"]', timeout=1)
                    self.crawler_settings.log.error("Failed to pass Cloudflare verification.")
                    return
                except:
                    pass
                
                pbar.update()
            except Exception as e:
                output_msg_base = f"Failed to get Cloudflare cookies"
                self.crawler_settings.log.error(f"{output_msg_base}.\n{traceback.format_exc()}", output_msg=f"{output_msg_base} because {e}")
                return
            
        # Get user agent and cookies
        try:
            user_agent = browser.info.get("User-Agent")
            if self.crawler_settings.download_config.result_headers is None:
                self.crawler_settings.download_config.headers = {'User-Agent': user_agent}
                self.crawler_settings.log.info(f"User agent is replaced by: {user_agent}")
            elif isinstance(self.crawler_settings.download_config.headers, dict):
                self.crawler_settings.download_config.headers['User-Agent'] = user_agent
                self.crawler_settings.log.info(f"User agent is replaced by: {user_agent}")
            else:
                self.crawler_settings.log.warning(f"User agent is unchanged! It might be because download_config.headers is a function. Your cookies may not work.")

            cookies_nodriver = await browser.cookies.get_all()
            self.cookies = Cookies.create_by(cookies_nodriver)
            self.crawler_settings.log.info("Cookies have been replaced. You can use Parser.cookies to extract it. ATTENTION: The cookies only work with certain user agent and IP address in a certain time.")

            if save_cookies_file is not None:
                self.cookies.save_to_json(save_cookies_file)
            
            browser.stop()
        except Exception as e:
            output_msg_base = f"Failed to parse user agent or Cookies"
            self.crawler_settings.log.error(f"{output_msg_base}.\n{traceback.format_exc()}", output_msg=f"{output_msg_base} because {e}")

        
    def get_cloudflare_cookies(
        self, 
        url: Optional[str]=None, 
        headless: bool=False,
        timeout: float=60,
        save_cookies_file: Optional[str]=None,
    ):
        """
        Bypass Cloudflare check and get its cookies.

        Parameters:
            url (str): Get Cloudflare cookies using this URL. Set to None (default) will use the station_url in this class.
            headless (bool): Whether to display a browser window. Recommend setting to True in case you need to manually bypass Cloudflare.
            timeout (float): Try to finish Cloudflare test in timeout seconds.
        """

        nodriver.loop().run_until_complete(
            self.__get_cloudflare_cookies(
                url=url,
                headless=headless,
                timeout=timeout,
                save_cookies_file=save_cookies_file,
            )
        )



class KeywordParser(Parser):

    def __init__(
        self,
        station_url: str,
        crawler_settings: CrawlerSettings=CrawlerSettings(),
        standard_keyword_string: Optional[str]=None,
        keyword_string: Optional[str]=None,
        cookies: Optional[Union[Cookies, list, dict, str]]=Cookies(),
        accept_empty: bool=False,
    ):
        """
        A Parser for keyword conditions.

        Parameters:
            station_url (str): URL of the main station of the Parser.
            crawler_settings (image_crawler_utils.CrawlerSettings): Crawler settings for this parser.
            standard_keyword_string (str): A keyword string using standard syntax.
            keyword_string (str, optional): Specify the keyword string yourself. You can write functions to generate them from the keyword tree afterwards.
            cookies (Cookies, list, dict, str or None): Cookies used in loading websites.
            accept_empty (bool): Accept empty keywords.

        Attributes:
            display_all_configs(): Display all configs of parser.
            generate_standard_keyword_string(): Generate a standard keyword string. Default is using the keyword tree in this class.
        """

        super().__init__(
            station_url=station_url,
            crawler_settings=crawler_settings,
            cookies=cookies,
        )
        self.standard_keyword_string = standard_keyword_string
        if standard_keyword_string is None or len(standard_keyword_string.strip()) == 0:
            if keyword_string is None or len(keyword_string.strip()) == 0:
                if not accept_empty:
                    self.crawler_settings.log.critical("standard_keyword_string and keyword_string cannot be empty / None at the same time!")
                    raise KeyError("standard_keyword_string and keyword_string cannot be empty / None at the same time!")
            else:
                self.crawler_settings.log.debug("standard_keyword_string is empty. Use keyword_string instead.")
                self.keyword_tree = KeywordLogicTree()  # An empty tree. Should not be used.
        else:
            self.keyword_tree = construct_keyword_tree(standard_keyword_string)
        self.keyword_string = keyword_string


    ##### Funtion requires rewriting


    @abstractmethod
    def run(self) -> list[ImageInfo]:
        """
        MUST BE OVERRIDEN.
        Generate a list of ImageInfo, containing image urls, names and infos.
        """
        raise NotImplemented


    ##### General Function

    
    # Display all config
    def display_all_configs(self):
        """
        Display all config info.
        Dataclasses will be displayed in a neater way.
        """
        
        print_logging_msg("========== Current KeywordParser Config ==========", "debug")

        # Basic info
        print('\nBasic Info:')
        try:
            print(f"  - Station URL: {self.station_url}")
            print(f"  - Standard keyword string: {self.standard_keyword_string}")
            print(f"  - Keyword tree: {self.keyword_tree.list_struct()}")
            print(f"  - Keyword string: {self.keyword_string}")
            if self.cookies.is_none():                
                print(f"  - Cookies: None")
            else:
                print(f"  - Cookies:")
                pprint(self.cookies.cookies_selenium)
        except Exception as e:
            print_logging_msg(f"Basic Info missing because {e}!\n{traceback.format_exc()}", "error")

        # Other info
        if set(self.__init__.__code__.co_varnames) != set(KeywordParser.__init__.__code__.co_varnames):
            print('\nOther Info:')
        for varname in self.__init__.__code__.co_varnames:
            if varname not in KeywordParser.__init__.__code__.co_varnames:
                if getattr(self, varname, None) is not None:
                    print(f"  - {varname}: {getattr(self, varname)}")

        print('')
        print_logging_msg("CrawlerSettings used:", "debug")
        self.crawler_settings.display_all_configs()
            
        print('')
        print_logging_msg("========== Keyword Parser Config Ending ==========", "debug")


    # Generate standard keyword string
    def generate_standard_keyword_string(
        self, 
        keyword_tree: Optional[KeywordLogicTree]=None
    ):
        """
        Generate a standard keyword string.
        Generated result may not be the same from the standard_keyword_string input.
        
        Parameters:
            keyword_tree: generate a standard keyword string from this keyword tree, or using the keyword tree already in this class.

        Returns:
            A standard keyword string.
        """
        
        # Standard keyword string            
        kw_tree = self.keyword_tree if keyword_tree is None else keyword_tree
        self.standard_keyword_string = kw_tree.standard_keyword_string()
