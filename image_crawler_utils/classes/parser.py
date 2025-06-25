from abc import ABC, abstractmethod

import requests
import traceback
import random
import time, datetime
from typing import Optional, Union
from collections.abc import Iterable, Callable
import os, dill
from rich import print, markup

import json
from bs4 import BeautifulSoup
from urllib import parse
from concurrent import futures

import nodriver, asyncio

from image_crawler_utils import Cookies, update_nodriver_browser_cookies
from image_crawler_utils.keyword import KeywordLogicTree, construct_keyword_tree
from image_crawler_utils.log import Log
from image_crawler_utils.progress_bar import CustomProgress, ProgressGroup
from image_crawler_utils.utils import check_dir, Empty, set_up_nodriver_browser

from .crawler_settings import CrawlerSettings
from .image_info import ImageInfo



class Parser(ABC):
    """
    A Parser include several basic functions.

    Args:
        station_url (str): The URL of the main page of a website.

            + This parameter works when several websites use the same structure. For example, https://yande.re/ and https://konachan.com/ both use Moebooru to build their websites, and this parameter must be filled to deal with these sites respectively.
            + For websites like https://www.pixiv.net/, as no other website uses its structure, this parameter has already been initialized and do not need to be filled.

        crawler_settings (image_crawler_utils.CrawlerSettings): The CrawlerSettings used in this Parser.
        cookies (image_crawler_utils.Cookies, list, dict, str, None): Cookies used in loading websites.

            + Can be one of :class:`image_crawler_utils.Cookies`, :py:class:`list`, :py:class:`dict`, :py:class:`str` or :py:data:`None`.
                + :py:data:`None` means no cookies and works the same as ``Cookies()``.
                + Leave this parameter blank works the same as :py:data:`None` / ``Cookies()``.

    """

    def __init__(
        self,
        station_url: str,
        crawler_settings: CrawlerSettings=CrawlerSettings(),
        cookies: Optional[Union[Cookies, list, dict, str]]=Cookies(),
    ):
        super().__init__()
        self.crawler_settings = crawler_settings
        self.station_url = parse.quote(station_url + ('/' if not station_url.endswith('/') else ''), safe='/:?=&')
        if isinstance(cookies, Cookies):
            self.cookies = cookies
        else:
            self.cookies = Cookies(cookies)


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

        print("========== Current Parser Config ==========")

        # Basic info
        try:
            print('\nBasic Info:')
            print(f"  + Station URL: [repr.url]{markup.escape(self.station_url)}[reset]")
            if self.cookies.is_none():                
                print(f"  + Cookies: None")
            else:
                print(f"  + Cookies:")
                print(self.cookies.cookies_selenium)
        except Exception as e:
            print(f"Basic Info missing because {e}!\n{traceback.format_exc()}", "error")

        # Other info
        if set(self.__init__.__code__.co_varnames) != set(KeywordParser.__init__.__code__.co_varnames):
            print('\nOther Info:')
        for varname in self.__init__.__code__.co_varnames:
            if varname not in KeywordParser.__init__.__code__.co_varnames:
                if getattr(self, varname, None) is not None:
                    print(f"  + {varname}: {getattr(self, varname)}")

        print('')
        print("CrawlerSettings used:")
        self.crawler_settings.display_all_configs()
            
        print('')
        print("========== Parser Config Ending ==========")


    def save_to_pkl(
        self, 
        pkl_file: str,
    ) -> Optional[tuple[str, str]]:
        """
        Save the parser in a .pkl file. 

        Args:
            path (str): Path to save the pkl file. Default is saving to the current path.
            pkl_file (str, None): Name of the pkl file. (Suffix is optional.)

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
                self.crawler_settings.log.info(f'{type(self).__name__} has been dumped into [repr.filename]{markup.escape(os.path.abspath(f_name))}[reset]', extra={"markup": True})
                return f_name, os.path.abspath(f_name)
        except Exception as e:
            self.crawler_settings.log.error(f'Failed to dump {type(self).__name__} into [repr.filename]{markup.escape(os.path.abspath(f_name))}[reset] because {e}\n{traceback.format_exc()}', extra={"markup": True})
            return None
        
    
    @classmethod
    def load_from_pkl(
        cls,
        pkl_file: str,
        log: Log=Log(),
    ) -> CrawlerSettings:
        """
        Load the parser from .pkl file.

        ATTENTION: You should use the correspondent Parser class when loading. For example, loading DanbooruKeywordParser should use ``DanbooruKeywordParser.load_from_pkl()``.

        Args:
            pkl_file (str, None): Name of the pkl file.
            log (image_crawler_utils.log.Log, None): Logging config.

        Returns:
            A CrawlerSettings class loaded from pkl file, or None if failed.
        """
        
        try:
            with open(pkl_file, "rb") as f:
                cls = dill.load(f)
                log.info(f'{type(cls).__name__} has been successfully loaded from [repr.filename]{markup.escape(os.path.abspath(pkl_file))}[reset]', extra={"markup": True})
            return cls
        except Exception as e:
            log.error(f'Failed to load {type(cls).__name__} from [repr.filename]{markup.escape(os.path.abspath(pkl_file))}[reset] because {e}\n{traceback.format_exc()}', extra={"markup": True})
            return None


    # --------------------------------------------------------- #
    # BASIC REQUEST METHOD: Using requests to get contents      #
    # --------------------------------------------------------- #


    # Get webpage content
    def request_page_content(
        self, 
        url: str, 
        session=requests.Session(),
        headers: Optional[Union[dict, Callable]]=Empty(),
        thread_delay: Union[None, float, Callable]=None,
    ) -> str:
        """
        Download webpage content.

        Args:
            url (str): The URL of the page to download.
            session (requests from import requests, or requests.Session): Can be requests or requests.Session()
            headers (dict, Callable, None): If you need to specify headers for current request, use this argument. Set to None (default) meaning use the headers from self.crawler_settings.download_config.result_headers
            thread_delay: Delay before thread running. Default set to None. Used to deal with websites like Pixiv which has a restriction on requests in a certain period of time.
        
        Returns:
            The HTML content of the webpage.
        """

        self.crawler_settings.log.debug(f'Try connecting to [repr.url]{markup.escape(url)}[reset]', extra={"markup": True})
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
                    self.crawler_settings.log.debug(f'Successfully connected to [repr.url]{markup.escape(url)}[reset] at attempt {i + 1}.', extra={"markup": True})
                    return response.text
                elif response.status_code == 429:
                    self.crawler_settings.log.warning(f'Connecting to [repr.url]{markup.escape(url)}[reset] FAILED at attempt {i + 1} because TOO many requests at the same time (response status code {response.status_code}). Retrying to connect in 1 to 2 minutes, but it is suggested to lower the number of threads or increase thread delay time and try again.', extra={"markup": True})
                    time.sleep(60 + random.random() * 60)
                elif 400 <= response.status_code < 500:
                    self.crawler_settings.log.error(f'Connecting to [repr.url]{markup.escape(url)}[reset] FAILED because response status code is {response.status_code}.', extra={"markup": True})
                    return None
                else:
                    self.crawler_settings.log.warning(f'Failed to connect to [repr.url]{markup.escape(url)}[reset] at attempt {i + 1}. Response status code is {response.status_code}.', extra={"markup": True})
                
            except Exception as e:
                self.crawler_settings.log.warning(f"Connecting to [repr.url]{markup.escape(url)}[reset] at attempt {i + 1} FAILED because {e} Retry connecting.\n{traceback.format_exc()}",
                                                  output_msg=f"Connecting to [repr.url]{markup.escape(url)}[reset] at attempt {i + 1} FAILED.", extra={"markup": True})
                time.sleep(self.crawler_settings.download_config.result_fail_delay)

        self.crawler_settings.log.error(f'FAILED to connect to [repr.url]{markup.escape(url)}[reset]', extra={"markup": True})
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
        Download multiple webpage content using threading.

        Args:
            url_list (list[str]): The list of URLs of the page to download.
            restriction_num (int, None): Only download the first restriction_num number of pages. Set to None (default) meaning no restrictions.
            session (requests from import requests, or requests.Session): Can be requests or requests.Session()
            headers (dict, list, Callable, None): If you need to specify headers for current threading requests, use this argument. Set to None (default) meaning use the headers from self.crawler_settings.download_config.result_headers
                + If it is a list, it should be of the same length as url_list, and for url_list[i] it will use the headers in headers[i]. The element in this list can be a dict of a function.
            thread_delay (float, Callable, None): Delay before thread running. Default set to None. Used to deal with websites like Pixiv which has a restriction on requests in a certain period of time.
            batch_num: Number of pages for each batch; using it with batch_delay to wait a certain period of time after downloading each batch. Used to deal with websites like Pixiv which has a restriction on requests in a certain period of time.
            batch_delay: Delaying time (seconds) after each batch is downloaded. Used to deal with websites like Pixiv which has a restriction on requests in a certain period of time.
        
        Returns:
            A list of the HTML contents of the webpages. Its order is the same as the one of url_list.
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
                raise ValueError(f"The number of headers ({len(headers)}) should be of the same length as the number of URLs ({len(url_list)})")
            l_headers = list(headers)

        page_content_dict_with_thread_id = {}
        
        self.crawler_settings.log.info(f"Total webpage num: {page_num}")
        if page_num > 0:
            if batch_num is None:
                batch_num = page_num
            batched_url_list = [l_url_list[k * batch_num:min((k + 1) * batch_num, page_num)] 
                                for k in range((page_num - 1) // batch_num + 1)]
            if isinstance(headers, Iterable) and not isinstance(headers, dict):
                batched_headers = [l_headers[k * batch_num:min((k + 1) * batch_num, page_num)] 
                                   for k in range((page_num - 1) // batch_num + 1)]

            with ProgressGroup(panel_title="Downloading [yellow]Webpages[reset]") as progress_group:
                task = progress_group.main_count_bar.add_task("Downloading webpages:", total=page_num)
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
                            page_content_dict_with_thread_id[thread.result()[1]] = thread.result()[0]  # Successful -> content, Failed -> None
                            progress_group.main_count_bar.update(task, advance=1)
                
                    if (j + 1) * batch_num < page_num:
                        current_batch_delay = batch_delay() if callable(batch_delay) else batch_delay
                        restart_time = datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(seconds=current_batch_delay), '%H:%M:%S')
                        self.crawler_settings.log.info(f"A batch of {len(batched_url_list[j])} {'page' if len(batched_url_list) <= 1 else 'pages'} has been downloaded. Waiting {current_batch_delay} {'second' if current_batch_delay <= 1 else 'seconds'} before resuming at {restart_time}.")

                        # Update progress bar to pausing
                        progress_group.main_count_bar.update(task, description=f"[yellow bold](Pausing)[reset] Downloading webpages:")
                        time.sleep(current_batch_delay)
                        # Reset progress bar from pausing
                        progress_group.main_count_bar.update(task, description=f"Downloading webpages:")

                # Finished normally, set progress bar to finished state
                progress_group.main_count_bar.update(task, description=f"[green]Downloading webpages finished!")
        else:
            self.crawler_settings.log.warning(f"No webpages are to be downloaded.")

        # Return corresponding page result according to their order in URLs
        page_content_list = [page_content_dict_with_thread_id[i]
                             for i in range(len(page_content_dict_with_thread_id))]
        return page_content_list
    

    # --------------------------------------------------------- #
    # ADVANCED REQUEST METHOD: Using nodriver to get contents   #
    # --------------------------------------------------------- #


    # Get webpage content
    async def __nodriver_request_page_content(
        self, 
        url: str, 
        browser: Optional[nodriver.Browser]=None,
        is_json: bool=False,
        thread_delay: Union[None, float, Callable]=None,
    ) -> str:
        
        if thread_delay is None:
            real_thread_delay = self.crawler_settings.download_config.result_thread_delay
        else:
            real_thread_delay = thread_delay() if callable(thread_delay) else thread_delay
        await asyncio.sleep(real_thread_delay)
        
        # If no browser exists, set up the browser                    
        if browser is None:
            # Display a progress bar if and only if browser is None
            progress = CustomProgress(has_spinner=True, transient=True)
            progress.start()
            task = progress.add_task(description=f'Loading browser components...', total=2)

            use_browser = await set_up_nodriver_browser(
                proxies=self.crawler_settings.download_config.result_proxies,
                window_width=800,
                window_height=600,
            )
        
            # Replace cookies
            await update_nodriver_browser_cookies(use_browser, self.cookies)
        else:
            use_browser = browser
        if browser is None:  # Display a progress bar if and only if browser is None
            progress.update(task, advance=1, description=f"Loading page...")

        for i in range(self.crawler_settings.download_config.retry_times):
            try:
                status_code = []

                # Timeout func
                async def tab_get_await():
                    if browser is None:  # Use the main tab
                        tab = use_browser.main_tab
                    else:  # Open a new tab
                        tab = await use_browser.get(new_tab=True)
                    def get_response_status(event):  # Get response status code
                        if event.response.url == url:
                            status_code.append(event.response.status)
                    tab.add_handler(nodriver.cdp.network.ResponseReceived, get_response_status)  # Add a handler to control this

                    await tab.get(url)
                    await tab
                    return tab
                
                # Check timeout
                if self.crawler_settings.download_config.timeout is None:
                    tab = await tab_get_await()
                else:
                    timeout_sec = self.crawler_settings.download_config.timeout
                    try:
                        tab = await asyncio.wait_for(tab_get_await(), timeout=timeout_sec)
                    except:
                        raise TimeoutError(f"Cannot connect to {url} in {timeout_sec} {'second' if timeout_sec <= 1 else 'seconds'} with nodriver.")
                
                status_code = status_code[0]

                if status_code == requests.status_codes.codes.ok:
                    self.crawler_settings.log.debug(f'Successfully connected to [repr.url]{markup.escape(url)}[reset] at attempt {i + 1}.', extra={"markup": True})
                    if is_json:
                        result = await tab.get_content()  # tab.select cannot deal with TOO long text!
                        soup = BeautifulSoup(result, 'lxml')
                        text = soup.find('pre').text
                        content = json.dumps(json.loads(text), ensure_ascii=False)
                    else:
                        content = await tab.get_content()
                    
                    if browser is None:  # Display a progress bar if and only if browser is None
                        progress.update(task, advance=1)
                        progress.finish_task(task)
                        use_browser.stop()
                    else:
                        await tab.close()
                    return content
                elif status_code == 429:
                    self.crawler_settings.log.warning(f'Connecting to [repr.url]{markup.escape(url)}[reset] FAILED at attempt {i + 1} because TOO many requests at the same time (response status code {status_code}). Retrying to connect in 1 to 2 minutes, but it is suggested to lower the number of threads or increase thread delay time and try again.', extra={"markup": True})
                    await asyncio.sleep(60 + random.random() * 60)
                elif 400 <= status_code < 500:
                    self.crawler_settings.log.error(f'Connecting to [repr.url]{markup.escape(url)}[reset] FAILED because response status code is {status_code}.', extra={"markup": True})
                    return None
                else:
                    self.crawler_settings.log.warning(f'Failed to connect to [repr.url]{markup.escape(url)}[reset] at attempt {i + 1}. Response status code is {status_code}.', extra={"markup": True})
                
            except Exception as e:
                self.crawler_settings.log.warning(f"Connecting to [repr.url]{markup.escape(url)}[reset] at attempt {i + 1} FAILED because {e} Retry connecting.\n{traceback.format_exc()}",
                                                output_msg=f"Connecting to [repr.url]{markup.escape(url)}[reset] at attempt {i + 1} FAILED.", extra={"markup": True})
                await asyncio.sleep(self.crawler_settings.download_config.result_fail_delay)

        if browser is None:  # Only stop the browser when it is independently set up
            use_browser.stop()

        self.crawler_settings.log.error(f'FAILED to connect to [repr.url]{markup.escape(url)}[reset]', extra={"markup": True})
        return None


    def nodriver_request_page_content(
        self, 
        url: str, 
        browser: Optional[nodriver.Browser]=None,
        is_json: bool=False,
        thread_delay: Union[None, float, Callable]=None,
    ):
        """
        Download webpage content with nodriver.

        For those sites having strong anti-crawling measures, try using this function to bypass them.

        Args:
            url (str): The URL of the page to download.
            browser (nodriver.Browser, None): Whether to use an existing browser instance.
            is_json (bool): Whether the result is a JSON text. Default set to False.
            thread_delay (float, Callable, None): Delay before thread running. Default set to None. Used to deal with websites like Pixiv which has a restriction on requests in a certain period of time.
        
        Returns:
            The HTML content of the webpage.
        """

        return nodriver.loop().run_until_complete(
            self.__nodriver_request_page_content(
                url=url,
                browser=browser,
                is_json=is_json,
                thread_delay=thread_delay,
            )
        )


    async def __nodriver_threading_request_page_content(
        self, 
        url_list: Iterable[str], 
        restriction_num: Optional[int]=None, 
        is_json: Union[bool, Iterable[bool]]=False,
        thread_delay: Union[None, float, Callable]=None,
        batch_num: Optional[int]=None,
        batch_delay: Union[float, Callable]=0.0,
    ) -> list[str]:

        page_num = len(url_list)
        if restriction_num is not None:
            page_num = min(page_num, restriction_num)
        l_url_list = list(url_list)
        if isinstance(is_json, Iterable):
            if len(is_json) != len(url_list):
                self.crawler_settings.log.critical(f"The number of is_json ({len(is_json)}) should be of the same length as the number of URLs ({len(url_list)})")
                raise ValueError(f"The number of is_json ({len(is_json)}) should be of the same length as the number of URLs ({len(url_list)})")
            l_is_json = list(l_is_json)

        self.crawler_settings.log.info(f"Total webpage num: {page_num}")
        page_content_list = []

        if page_num > 0:
            if batch_num is None:
                batch_num = min(page_num, 500)
                batch_delay = 0.0
                silent_batch = True  # Only reload browsers, no delaying.
            else:
                silent_batch = False
            batched_url_list = [l_url_list[k * batch_num:min((k + 1) * batch_num, page_num)] 
                                for k in range((page_num - 1) // batch_num + 1)]
            if isinstance(is_json, Iterable):
                batched_is_json = [l_is_json[k * batch_num:min((k + 1) * batch_num, page_num)] 
                                   for k in range((page_num - 1) // batch_num + 1)]

            with ProgressGroup(panel_title="Downloading [yellow]Webpages[reset]") as progress_group:
                task = progress_group.main_count_bar.add_task("Downloading webpages:", total=page_num)
                
                # Define an async task function
                async def page_task(
                    bar: CustomProgress,
                    task,
                    url: str,
                    browser: nodriver.Browser,
                    is_json: bool,
                    thread_delay: Union[float, Callable],
                    sem: asyncio.Semaphore,  # Control max corountine number
                ):
                    async with sem:
                        result = await self.__nodriver_request_page_content(
                            url=url,
                            browser=browser,
                            is_json=is_json,
                            thread_delay=thread_delay,
                        )
                        bar.update(task, advance=1)
                        return result
                    
                sem = asyncio.Semaphore(self.crawler_settings.download_config.thread_num)  # Max coroutine number

                for j in range(len(batched_url_list)):
                    
                    # Set up browser instance for every batch
                    browser = await set_up_nodriver_browser(
                        proxies=self.crawler_settings.download_config.result_proxies,
                        window_width=800,
                        window_height=600,
                    )

                    await update_nodriver_browser_cookies(browser=browser, cookies=self.cookies)
            
                    self.crawler_settings.log.debug("Browser components loaded.")

                    results = await asyncio.gather(*[
                        asyncio.create_task(
                            page_task(
                                bar=progress_group.main_count_bar,
                                task=task,
                                url=batched_url_list[j][i],
                                browser=browser,
                                is_json=is_json if not isinstance(is_json, Iterable) else batched_is_json[j][i],
                                thread_delay=thread_delay,
                                sem=sem,
                            )
                        )
                    for i in range(len(batched_url_list[j]))])

                    for result in results:
                        page_content_list.append(result)
                
                    if (j + 1) * batch_num < page_num:
                        current_batch_delay = batch_delay() if callable(batch_delay) else batch_delay
                        restart_time = datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(seconds=current_batch_delay), '%H:%M:%S')

                        if not silent_batch:
                            self.crawler_settings.log.info(f"A batch of {len(batched_url_list[j])} {'page' if len(batched_url_list) <= 1 else 'pages'} has been downloaded. Waiting {current_batch_delay} {'second' if current_batch_delay <= 1 else 'seconds'} before resuming at {restart_time}.")

                            # Update progress bar to pausing
                            progress_group.main_count_bar.update(task, description=f"[yellow bold](Pausing)[reset] Downloading webpages:")
                            await asyncio.sleep(current_batch_delay)
                            # Reset progress bar from pausing
                            progress_group.main_count_bar.update(task, description=f"Downloading webpages:")
                        
                    # Stop the browser
                    browser.stop()

                    self.crawler_settings.log.debug("Browser components stopped.")

                # Finished normally, set progress bar to finished state
                progress_group.main_count_bar.update(task, description=f"[green]Downloading webpages finished!")

        else:
            self.crawler_settings.log.warning(f"No webpages are to be downloaded.")

        return page_content_list


    def nodriver_threading_request_page_content(
        self, 
        url_list: Iterable[str], 
        restriction_num: Optional[int]=None, 
        is_json: Union[bool, Iterable[bool]]=False,
        thread_delay: Union[None, float, Callable]=None,
        batch_num: Optional[int]=None,
        batch_delay: Union[float, Callable]=0.0,
    ) -> list[str]:
        """
        Download multiple webpage content using asynchronous coroutines (similar to threads) with nodriver.

        For those sites having strong anti-crawling measures, try using this function to bypass them.

        Args:
            url_list (list[str]): The list of URLs of the page to download.
            restriction_num (int, None): Only download the first restriction_num number of pages. Set to None (default) meaning no restrictions.
            is_json (bool or Iterable instance): Whether the result is a JSON text. Can be a bool or a iterable object with the same length as url_list. Default set to False.
            thread_delay (float, Callable, None): Delay before thread running. Default set to None. Used to deal with websites like Pixiv which has a restriction on requests in a certain period of time.
            batch_num: Number of pages for each batch; using it with batch_delay to wait a certain period of time after downloading each batch. Used to deal with websites like Pixiv which has a restriction on requests in a certain period of time.
            batch_delay: Delaying time (seconds) after each batch is downloaded. Used to deal with websites like Pixiv which has a restriction on requests in a certain period of time.
        
        Returns:
            A list of the HTML contents of the webpages. Its order is the same as the one of url_list.
        """

        return nodriver.loop().run_until_complete(
            self.__nodriver_threading_request_page_content(
                url_list=url_list,
                restriction_num=restriction_num,
                is_json=is_json,
                thread_delay=thread_delay,
                batch_num=batch_num,
                batch_delay=batch_delay,
            )
        )


    # --------------------------------------------------------- #
    # Cloudflare related functions                              #
    # --------------------------------------------------------- #


    # Get Cloudflare cf_clearance cookies
    async def __get_cloudflare_cookies(
        self,
        url: Optional[str]=None, 
        headless: bool=False,
        timeout: float=60,
        save_cookies_file: Optional[str]=None,
        try_clicking: bool=False,
    ):        
        test_url = url if url is not None else self.station_url
        self.crawler_settings.log.info(f"Loading browser to get Cloudflare cookies from [repr.url]{markup.escape(test_url)}[reset].", extra={"markup": True})
        
        # Pass Cloudflare verification
        with CustomProgress(has_spinner=True, transient=True) as progress:
            task = progress.add_task(description='Loading browser components...', total=2)
            try:
                browser = await set_up_nodriver_browser(
                    proxies=self.crawler_settings.download_config.result_proxies,
                    headless=headless,
                    window_width=800,
                    window_height=600,
                )
                
                progress.update(task, advance=1, description="Loading Cloudflare page and try passing it...")

                tab = await browser.get(test_url)
                await tab
                start_timestamp = datetime.datetime.now()
                while (datetime.datetime.now() - start_timestamp).seconds < timeout:
                    try:
                        result = await tab.select('input[name="cf-turnstile-response"]', timeout=3)
                        if result is None:
                            break
                        if try_clicking:
                            await tab.verify_cf(flash=True)
                    except:
                        break
                try:
                    result = await tab.select('input[name="cf-turnstile-response"]', timeout=1)
                    if result is not None:
                        self.crawler_settings.log.error("Failed to pass the Cloudflare verification.")
                        return
                except:
                    pass
                
                progress.update(task, advance=1, description="[green]Cloudflare page successfully passed!")
                progress.finish_task(task)
            except Exception as e:
                output_msg_base = f"Failed to get the Cloudflare cookies"
                self.crawler_settings.log.error(f"{output_msg_base}.\n{traceback.format_exc()}", output_msg=f"{output_msg_base} because {e}")
                progress.finish_task(task)
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
            self.cookies = Cookies(cookies_nodriver)
            self.crawler_settings.log.info("Cookies have been replaced. You can use Parser.cookies to extract it. ATTENTION: The cookies only work with certain user agent and IP address in a certain time.")

            if save_cookies_file is not None:
                self.cookies.save_to_json(save_cookies_file)
            
            browser.stop()
        except Exception as e:
            output_msg_base = f"Failed to parse user agent or Cookies"
            self.crawler_settings.log.error(f"{output_msg_base}.\n{traceback.format_exc()}", output_msg=f"{output_msg_base} because {e}")
            browser.stop()

        
    def get_cloudflare_cookies(
        self, 
        url: Optional[str]=None, 
        headless: bool=False,
        timeout: float=60,
        save_cookies_file: Optional[str]=None,
        try_clicking: bool=False,
    ):
        """
        Bypass Cloudflare check and get its cookies.

        Args:
            url (str): Get Cloudflare cookies using this URL. Set to None (default) will use the station_url in this class.
            headless (bool): Whether to display a browser window. Recommend setting to True in case you need to manually bypass Cloudflare.
            save_cookies_file (str, None): Path to save the new cookies. Default set to :py:data:`None`, meaning not saving cookies.
            timeout (float): Try to finish Cloudflare test in timeout seconds.
            try_clicking (bool): Try to repeatedly click the verification box. MAY CAUSE THE WEBSITE TO GET STUCK IN THE VERIFICATION PAGE.
        """

        nodriver.loop().run_until_complete(
            self.__get_cloudflare_cookies(
                url=url,
                headless=headless,
                timeout=timeout,
                save_cookies_file=save_cookies_file,
                try_clicking=try_clicking,
            )
        )



class KeywordParser(Parser):
    """
    A Parser for fetching result from keyword searching.

    Args:
        station_url (str): The URL of the main page of a website.

            + This parameter works when several websites use the same structure. For example, https://yande.re/ and https://konachan.com/ both use Moebooru to build their websites, and this parameter must be filled to deal with these sites respectively.
            + For websites like https://www.pixiv.net/, as no other website uses its structure, this parameter has already been initialized and do not need to be filled.

        crawler_settings (image_crawler_utils.CrawlerSettings): The CrawlerSettings used in this Parser.
        standard_keyword_string (str): Query keyword string using standard syntax. Refer to the documentation for detailed instructions.
        keyword_string (str, None): If you want to directly specify the keywords used in searching, set ``keyword_string`` to a custom non-empty string. It will OVERWRITE ``standard_keyword_string``.

            + For example, set ``keyword_string`` to ``"kuon_(utawarerumono) rating:safe"`` in DanbooruKeywordParser means searching directly with this string in Danbooru, and its standard keyword string equivalent is ``"kuon_(utawarerumono) AND rating:safe"``.

        cookies (image_crawler_utils.Cookies, list, dict, str, None): Cookies used in loading websites.

            + Can be one of :class:`image_crawler_utils.Cookies`, :py:class:`list`, :py:class:`dict`, :py:class:`str` or :py:data:`None`.
                + :py:data:`None` means no cookies and works the same as ``Cookies()``.
                + Leave this parameter blank works the same as :py:data:`None` / ``Cookies()``.

        accept_empty (bool): If set to :py:data:`False` (default), when both ``standard_keyword_string`` and ``keyword_string`` is an empty string (like '' or '  '), a critical error will be thrown. If set to :py:data:`True`, no error will be thrown and the parameters are accepted.
    """

    def __init__(
        self,
        station_url: str,
        crawler_settings: CrawlerSettings=CrawlerSettings(),
        standard_keyword_string: Optional[str]=None,
        keyword_string: Optional[str]=None,
        cookies: Optional[Union[Cookies, list, dict, str]]=Cookies(),
        accept_empty: bool=False,
    ):

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
        Generate a list of ImageInfo, containing image urls, names and infos by crawling the website.

        MUST BE OVERRIDDEN if inherited from Parser or KeywordParser class.
        """
        raise NotImplemented


    ##### General Function

    
    # Display all config
    def display_all_configs(self):
        """
        Display all config info.
        Dataclasses will be displayed in a neater way.
        """
        
        print("========== Current KeywordParser Config ==========")

        # Basic info
        print('\nBasic Info:')
        try:
            print(f"  + Station URL: [repr.url]{markup.escape(self.station_url)}[reset]")
            print(f"  + Standard keyword string: {self.standard_keyword_string}")
            print(f"  + Keyword tree: {self.keyword_tree.list_struct()}")
            print(f"  + Keyword string: {self.keyword_string}")
            if self.cookies.is_none():                
                print(f"  + Cookies: None")
            else:
                print(f"  + Cookies:")
                print(self.cookies.cookies_selenium)
        except Exception as e:
            print(f"Basic Info missing because {e}!\n{traceback.format_exc()}", "error")

        # Other info
        if set(self.__init__.__code__.co_varnames) != set(KeywordParser.__init__.__code__.co_varnames):
            print('\nOther Info:')
        for varname in self.__init__.__code__.co_varnames:
            if varname not in KeywordParser.__init__.__code__.co_varnames:
                if getattr(self, varname, None) is not None:
                    print(f"  + {varname}: {getattr(self, varname)}")

        print('')
        print("CrawlerSettings used:")
        self.crawler_settings.display_all_configs()
            
        print('')
        print("========== Keyword Parser Config Ending ==========")


    # Generate standard keyword string
    def generate_standard_keyword_string(
        self, 
        keyword_tree: Optional[KeywordLogicTree]=None
    ):
        """
        Generate a standard keyword string.

        Generated result may not be the same from the standard_keyword_string input.
        
        Args:
            keyword_tree: The KeywordLogicTree that a standard keyword string will be built from. Set to :py:data:`None` (default) will use the KeywordLogicTree generated from the ``standard_keyword_string`` parameter.

                + **ATTENTION:** When set to :py:data:`None`, the standard keyword string may not be absolutely same as ``standard_keyword_string``.

        Returns:
            A standard keyword string.
        """
        
        # Standard keyword string            
        kw_tree = self.keyword_tree if keyword_tree is None else keyword_tree
        self.standard_keyword_string = kw_tree.standard_keyword_string()
