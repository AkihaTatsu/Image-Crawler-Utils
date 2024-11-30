from __future__ import annotations
import dataclasses

import requests
import os
import logging, traceback
import dill, base64, hashlib
from typing import Optional, Union
from collections.abc import Callable
from rich import print

import nodriver
import asyncio

from image_crawler_utils.configs import DebugConfig, CapacityCountConfig, DownloadConfig
from image_crawler_utils.log import Log
from image_crawler_utils.progress_bar import CustomProgress
from image_crawler_utils.utils import check_dir, Empty, set_up_nodriver_browser



class CrawlerSettings:

    def __init__(
        self,
        # Original config input
        capacity_count_config: CapacityCountConfig=Empty(),
        download_config: DownloadConfig=Empty(),
        debug_config: DebugConfig=DebugConfig(),
        # CapacityCountConfig
        image_num: Optional[int]=None,
        capacity: Optional[float]=None,
        page_num: Optional[int]=None,
        # DownloadConfig
        headers: Optional[Union[dict, Callable]]=None,
        proxies: Optional[Union[dict, Callable]]=None,
        thread_delay: float=5,
        fail_delay: float=3,
        randomize_delay: bool=True,
        thread_num: int=5,
        timeout: Optional[float]=10,
        max_download_time: Optional[float]=None,
        retry_times: int=5,
        overwrite_images: bool=True,
        # Logging settings
        detailed_console_log: bool=False,
        # ExtraConfig
        extra_configs: Optional[dict]=None,
    ):
        """
        A general framework to design a custom crawler.

        Parameters:
            capacity_count_config (image_crawler_utils.configs.CapacityCountConfig, optional): Contains configs that restricts downloading numbers and capacity.
            download_config (image_crawler_utils.configs.DownloadConfig, optional): Contains configs about parameters in downloading.
            debug_config (image_crawler_utils.configs.DebugConfig, optional): Contains configs that define which types of messages are shown on the console.

            image_num (int, optional): Number of images to be parsed / downloaded in total; None means no restriction.
            capacity (float, optional): Total size of images (MB); None means no restriction.
            page_num (int, optional): Number of gallery pages to detect images in total; None means no restriction.

            headers (dict or function, optional): Headers settings. Can be a function (should return a dict), a dict or nothing. If it is a function, it will be called at every usage.
            proxies (dict or function, optional): Proxy settings. Can be a function (should return a dict), a dict or nothing. If it is a function, it will be called at every usage.
            thread_delay (float): Waiting time (s) after thread start.
            fail_delay (float): Waiting time (s) after failing.
            randomize_delay (bool): Randomize delay time between 0 and delay_time.
            thread_num (int): Downloading thread num.
            timeout (float, optional): Timeout for requests. Set to None means no timeout.
            max_download_time (float, optional): Maximum download time for a image. Set to None means no timeout.
            retry_times (int): Times of retrying to download.
            overwrite_images (bool): Overwrite existing images.

            detailed_console_log (bool): When logging info to the console, always log `msg` (the messages logged into files) even if `output_msg` exists.

            extra_configs (dict, optional): A dict of custom configs.

        Attributes:
            set_logging_file(): Adding logging to file with logging level (default logging.DEBUG).
            dill_base64_sha256_data(): Generate dill-pickled byte data of current crawler settings, its base_64 string, and the sha245 processed base_64 string.
            display_all_configs(): Display all configs of crawler settings.
            connectivity_test(): Test the connectivity of a URL.
            browser_test(): Test whether untected_chromeriver works.
        """

        self.capacity_count_config = capacity_count_config if not isinstance(capacity_count_config, Empty) else CapacityCountConfig(
            image_num=image_num,
            capacity=capacity,
            page_num=page_num,
        )
        self.download_config = download_config if not isinstance(download_config, Empty) else DownloadConfig(
            headers=headers,
            proxies=proxies,
            thread_delay=thread_delay,
            fail_delay=fail_delay,
            randomize_delay=randomize_delay,
            thread_num=thread_num,
            timeout=timeout,
            max_download_time=max_download_time,
            retry_times=retry_times,
            overwrite_images=overwrite_images,
        )
        self.__debug_config = debug_config
        self.extra_configs = extra_configs
        
        # Default no logging to file
        self.log = Log(
            log_file=None,
            debug_config=self.__debug_config, 
            logging_level=logging.DEBUG,
            detailed_console_log=detailed_console_log,
        )


    ##### General Function


    def set_logging_file(
        self,
        log_file: str,
        logging_level: Union[str, int]=logging.DEBUG,
    ):
        """
        Set logging to file.
        PAY ATTENTION: You cannot add logging to file info when creatiing a class. Logging to file info is only available using this function.

        Parameters:
            log_file (str): Output name for the logging file. Suffix (.json) is optional. Set to None (Default) is not to output any file.
            logging_level (int): Set the logging level of the LOGGING FILE. Select from: logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR and logging.CRITICAL .

        Returns:
            The changed crawler settings itself.
        """

        self.log = Log(
            log_file=log_file,
            debug_config=self.__debug_config,
            logging_level=logging_level,
        )

        return self


    def dill_base64_sha256_data(self) -> dict:
        """
        Return the serialized bytes of current CrawlerSettings, base64 encoded str of the bytes, and sha256 str of the bytes.

        Returns:
            A dict like {"bytes": dill.dumps() bytes, 
                         "base64": base64 encoding of the dill.dumps() bytes, 
                         "sha256": sha256 encoding of the base64 code}
        """

        dumped_bytes = dill.dumps(self)
        base_64_str = base64.b64encode(dumped_bytes)
        sha256_str = hashlib.sha256(base_64_str).hexdigest()
        return {"bytes": dumped_bytes, 
                "base64": base_64_str, 
                "sha256": sha256_str}
        

    def display_all_configs(self):
        """
        Display all config info.
        Dataclasses will be displayed in a neater way.
        """
        
        print("========== Current CrawlerSettings ==========")

        for config in [
            self.capacity_count_config,
            self.download_config,
        ]:
            print('\n' + type(config).__name__ + ':')
            config_dict = dataclasses.asdict(config)
            for key, value in config_dict.items():
                print('  - ' + str(key) + ': ' + str(value))
                
        if self.extra_configs is not None:
            for var_name, config in self.extra_configs.items():
                print('\nExtra configs - ' + var_name + ':')

                if dataclasses.is_dataclass(config):
                    # Dataclasses use neater print
                    config_dict = dataclasses.asdict(config)
                    for key, value in config_dict.keys():
                        print('  - ' + str(key) + ': ' + str(value))
                else:
                    # Traditional print
                    try:
                        print(end='  ')
                        print(config)
                    except Exception as e:
                        self.log.error(f"Failed to print extra configs - {var_name} because {e}")
        
        ##### Logging info
        print('\nLogging Info:')
        print('  - ' + type(self.log.debug_config).__name__ + ' (Logging to console):')
        config_dict = dataclasses.asdict(self.log.debug_config)
        for key, value in config_dict.items():
            print('    - ' + str(key) + ': ' + str(value))
        # Have logging file info
        if self.log.logging_file_handler():
            print(f'  - Logging file: \"{self.log.logging_file_path()}\"')
            
        print('')
        print("========== Crawler Settings Ending ==========")
    

    # Connectivity test
    def connectivity_test(
        self, 
        url: str
    ):
        """
        Test connectivity of internet.
        Using config in download_config.

        Parameters:
            url (str): Test connectivity using this URL.

        Returns:
            A bool. Successful connection returns True, in other cases returns False.
        """

        self.log.info(f"Testing connectivity using url \"{url}\" ...")
        
        try:
            response = requests.get(
                url,
                headers=self.download_config.result_headers,
                proxies=self.download_config.result_proxies,
                timeout=(self.download_config.timeout, self.download_config.max_download_time),
            )
            
            if response.status_code == requests.status_codes.codes.ok:
                self.log.info('Successfully connected.')
                return True
            else:
                self.log.error(f'Failed to connect to \"{url}\" because response code is {response.status_code}.')
                return False
        except Exception as e:
            self.log.error(f"Failed to connect to \"{url}\".\n{traceback.format_exc()}")
            return False
        

    # Browser test
    async def __browser_test(
        self, 
        url: str, 
        headless: bool=True,
        stay_time: float=30,
    ):
        self.log.info(f"Testing browser using url \"{url}\" ...")
        
        with CustomProgress(has_spinner=True, transient=True) as progress:
            task = progress.add_task(description='Loading browser components...', total=2)
            try:
                browser = await set_up_nodriver_browser(
                    proxies=self.download_config.result_proxies,
                    headless=headless,
                    window_width=800,
                    window_height=600,
                )

                progress.update(task, advance=1, description="Requesting webpage...")
            except Exception as e:
                self.log.error(f"FAILED to set up browser components.\n{traceback.format_exc()}")
                return False
            
            try:
                tab = await browser.get(url, new_tab=True)
                await tab.sleep()
                self.log.info(f'Webpage is successfully loaded.')
                if not headless:
                    await asyncio.sleep(stay_time)
                browser.stop()
                self.log.info(f'Browser successfully closed.')
                progress.update(task, advance=1, description="Process finished.")
                return True
            except Exception as e:
                browser.stop()
                self.log.error(f"FAILED to load the browser.\n{traceback.format_exc()}")
                progress.update(task, advance=1, description="Process finished.")
                return False


    def browser_test(
        self, 
        url: str, 
        headless: bool=True,
        stay_time: float=30,
    ):
        """
        Test whether browser works normally.
        ATTENTION: This function DO NOT check the connectivity of the URL. Use connectivity_test() instead.

        Parameters:
            url (str): Test connectivity using this URL.
            headless (bool): Whether to display a window when testing chromdriver. You can have a quick glimpse of whether the page is correctly loaded.
            stay_time (float): If set to not headless, the window will stay for stay_time seconds.

        Returns:
            A bool. Successful connection returns True, in other cases returns False.
        """
        nodriver.loop().run_until_complete(
            self.__browser_test(
                url=url,
                headless=headless,
                stay_time=stay_time,
            )
        )
    

    def copy(
        self,
        # Original config input
        capacity_count_config: CapacityCountConfig=Empty(),
        download_config: DownloadConfig=Empty(),
        debug_config: DebugConfig=Empty(),
        # CapacityCountConfig
        image_num: Optional[int]=Empty(),
        capacity: Optional[float]=Empty(),
        page_num: Optional[int]=Empty(),
        # DownloadConfig
        headers: Optional[Union[dict, Callable]]=Empty(),
        proxies: Optional[Union[dict, Callable]]=Empty(),
        thread_delay: float=Empty(),
        fail_delay: float=Empty(),
        randomize_delay: bool=Empty(),
        thread_num: int=5,
        timeout: Optional[float]=Empty(),
        max_download_time: Optional[float]=Empty(),
        retry_times: int=Empty(),
        overwrite_images: bool=Empty(),
        # ExtraConfig
        extra_configs: Optional[dict]=Empty(),
    ):
        """
        Generate a copy of a CrawlerSettings, with (optional) parameters changed.

        Parameters:
            capacity_count_config (image_crawler_utils.configs.CapacityCountConfig, optional): Contains configs that restricts downloading numbers and capacity.
            download_config (image_crawler_utils.configs.DownloadConfig, optional): Contains configs about parameters in downloading.
            debug_config (image_crawler_utils.configs.DebugConfig, optional): Contains configs that define which types of messages are shown on the console.

            image_num (int, optional): Number of images to be parsed / downloaded in total; None means no restriction.
            capacity (float, optional): Total size of images (MB); None means no restriction.
            page_num (int, optional): Number of gallery pages to detect images in total; None means no restriction.

            headers (dict or function, optional): Headers settings. Can be a function (should return a dict), a dict or nothing. If it is a function, it will be called at every usage.
            proxies (dict or function, optional): Proxy settings. Can be a function (should return a dict), a dict or nothing. If it is a function, it will be called at every usage.
            thread_delay (float): Waiting time (s) after thread start.
            fail_delay (float): Waiting time (s) after failing.
            randomize_delay (bool): Randomize delay time between 0 and delay_time.
            thread_num (int): Downloading thread num.
            timeout (float, optional): Timeout for requests. Set to None means no timeout.
            max_download_time (float, optional): Maximum download time for a image. Set to None means no timeout.
            retry_times (int): Times of retrying to download.
            overwrite_images (bool): Overwrite existing images.

            extra_configs (dict, optional): A list of custom configs.
        """

        if isinstance(capacity_count_config, Empty):
            new_capacity_count_config = CapacityCountConfig(
                image_num=self.capacity_count_config.image_num if isinstance(image_num, Empty) else image_num,
                capacity=self.capacity_count_config.capacity if isinstance(capacity, Empty) else capacity,
                page_num=self.capacity_count_config.page_num if isinstance(page_num, Empty) else page_num,
            )
        else:
            new_capacity_count_config = capacity_count_config

        if isinstance(download_config, Empty):
            new_download_config = DownloadConfig(
                headers=self.download_config.headers if isinstance(headers, Empty) else headers,
                proxies=self.download_config.proxies if isinstance(proxies, Empty) else proxies,
                thread_delay=self.download_config.thread_delay if isinstance(thread_delay, Empty) else thread_delay,
                fail_delay=self.download_config.fail_delay if isinstance(fail_delay, Empty) else fail_delay,
                randomize_delay=self.download_config.randomize_delay if isinstance(randomize_delay, Empty) else randomize_delay,
                thread_num=self.download_config.thread_num if isinstance(thread_num, Empty) else thread_num,
                timeout=self.download_config.timeout if isinstance(timeout, Empty) else timeout,
                max_download_time=self.download_config.max_download_time if isinstance(max_download_time, Empty) else max_download_time,
                retry_times=self.download_config.retry_times if isinstance(retry_times, Empty) else retry_times,
                overwrite_images=self.download_config.overwrite_images if isinstance(overwrite_images, Empty) else overwrite_images,
            )
        else:
            new_download_config = download_config

        debug_config=self.log.debug_config if isinstance(debug_config, Empty) else debug_config
        extra_configs=self.extra_configs if isinstance(extra_configs, Empty) else extra_configs
        
        new_crawler_settings = CrawlerSettings(
            capacity_count_config=new_capacity_count_config,
            download_config=new_download_config,
            debug_config=debug_config,
            extra_configs=extra_configs,
        )
        return new_crawler_settings
    

    def save_to_pkl(
        self, 
        pkl_file: Optional[str]=None,
    ) -> Optional[tuple[str, str]]:
        """
        Save the crawler settings in a pkl file. 
        It is recommended to use the default file name, which uses the sha256 encoded string generated by dill_base64_sha256_data().

        Parameters:
            path (str): Path to save the pkl file. Default is saving to the current path.
            pkl_file (str, optional): Name of the pkl file. (Suffix is optional.) Default is using the sha256 encoded string generated by dill_base64_sha256_data().

        Returns:
            (Saved file name, Absolute path of the saved file), or None if failed.
        """

        if pkl_file is None:
            filename = self.dill_base64_sha256_data()['sha256']
            f_name = f"{filename}.pkl"
        else:
            path, filename = os.path.split(pkl_file)
            check_dir(path, self.log)
            f_name = os.path.join(path, f"{filename}.pkl")
        f_name = f_name.replace(".pkl.pkl", ".pkl")  # If .pkl is already contained in pkl_file, skip it

        try:
            with open(f_name, "wb") as f:
                dill.dump(self, f)
                self.log.info(f'{type(self).__name__} has been dumped into "{os.path.abspath(f_name)}"')
                return f_name, os.path.abspath(f_name)
        except Exception as e:
            self.log.error(f'Failed to dump {type(self).__name__} into "{os.path.abspath(f_name)}" because {e}\n{traceback.format_exc()}')
            return None
        
    
    @classmethod
    def load_from_pkl(
        cls,
        pkl_file: str,
        log: Log=Log(),
    ) -> CrawlerSettings:
        """
        Load crawler settings from .pkl file.

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
        