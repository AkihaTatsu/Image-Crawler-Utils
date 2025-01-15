from __future__ import annotations
import dataclasses
from typing import Optional, Callable, Union

import random



@dataclasses.dataclass
class DebugConfig:
    """
    Contains config for whether displaying a certain level of debugging messages in console.
    Default set to "info" level.

    Parameters:
        show_debug (bool): Print debug-level information.
        show_info (bool): Print info-level information.
        show_warning (bool): Print warning-level information.
        show_error (bool): Print error-level information.
        show_critical (bool): Print critical-level information.

    Attributes:
        set_level(): Set to display messages over the level. For example, set to "warning" will display warning, error and critical messages. Parameters can be (from lower to higher) "debug", "info", "warning", "error" or "critical".
    """

    show_debug: bool = False
    show_info: bool = True
    show_warning: bool = True
    show_error: bool = True
    show_critical: bool = True

    
    def set_level(self, level_str: str):
        """
        Set to display messages over the level. For example, set to "warning" will display warning, error and critical messages.

        Parameters:
            A string. Must be one of (from lower to higher) "debug", "info", "warning", "error", "critical" or "silenced".

        Returns:
            The altered DebugConfig itself. PAY ATTENTION that the class itself is also altered.
        """

        level_class = ("debug", "info", ("warn", "warning"), "error", "critical", "silenced")
        attr_list = ("show_debug", "show_info", "show_warning", "show_error", "show_critical")
        level_int = -1
        for i in range(len(level_class)):
            if isinstance(level_class[i], str):
                if level_str.lower() == level_class[i]:
                    level_int = i
            else:
                if level_str.lower() in level_class[i]:  # A tuple
                    level_int = i

        if level_int >= 0:  # Valid level_str
            flag = False
            for i in range(len(attr_list)):
                if i == level_int:
                    flag = True
                setattr(self, attr_list[i], flag)
    

    @classmethod
    def level(cls, level_str: str) -> DebugConfig:
        """
        Create a DebugConfig that is set to display messages over the level. For example, set to "warning" will display warning, error and critical messages.

        Parameters:
            A string. Must be one of (from lower to higher) "debug", "info", "warning", "error", "critical" or "silenced".

        Returns:
            Created DebugConfig.
        """
        config = cls()
        config.set_level(level_str)
        return config



@dataclasses.dataclass
class CapacityCountConfig:
    """
    Contains config for restrictions of images number, total size or webpage number.

    Parameters:
        image_num (int, optional): Number of images to be parsed / downloaded in total; None means no restriction.
        capacity (float, optional): Total size of images (MB); None means no restriction.
        page_num (int, optional): Number of gallery pages to detect images in total; None means no restriction.
    """

    image_num: Optional[int] = None
    capacity: Optional[float] = None
    page_num: Optional[int] = None



@dataclasses.dataclass
class DownloadConfig:
    """
    Contains config for downloading.

    Parameters:
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
    """

    headers: Optional[Union[dict, Callable]] = None
    proxies: Optional[Union[dict, Callable]] = None
    thread_delay: float = 5
    fail_delay: float = 3
    randomize_delay: bool = True
    thread_num: int = 5
    timeout: Optional[float] = 10
    max_download_time: Optional[float] = None
    retry_times: int = 5
    overwrite_images: bool = True

    
    def __post_init__(self):
        # Process HTTPS proxies
        if isinstance(self.proxies, dict):
            if "https" in self.proxies.keys() and "http" not in self.proxies.keys():
                self.proxies["http"] = self.proxies["https"]
        elif not (isinstance(self.proxies, dict) or callable(self.proxies) or (self.proxies is None)):
            raise TypeError("Proxies should be a dict, a callable function or None.")
        
    
    @property
    def result_headers(self) -> dict:
        if callable(self.headers):
            return self.headers()
        else:
            return self.headers
        
    
    @property
    def result_proxies(self) -> dict:
        if callable(self.proxies):
            return self.proxies()
        else:
            return self.proxies


    @property
    def result_thread_delay(self) -> float:
        if self.randomize_delay:
            return random.random() * self.thread_delay
        else:
            return self.thread_delay

    
    @property
    def result_fail_delay(self) -> float:
        if self.randomize_delay:
            return random.random() * self.fail_delay
        else:
            return self.fail_delay
