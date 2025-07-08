##### Anything in .classes be directly import from image_crawler_utils

from .classes.cookies import (
    Cookies,
    update_nodriver_browser_cookies,
)
from .classes.crawler_settings import (
    CrawlerSettings,
)
from .classes.downloader import (
    Downloader,
)
from .classes.parser import (
    Parser,
    KeywordParser,
)
from .classes.image_info import (
    ImageInfo,
    save_image_infos,
    load_image_infos,
)

__all__ = [
    "Cookies",
    "update_nodriver_browser_cookies",
    "CrawlerSettings",
    "Downloader",
    "Parser",
    "KeywordParser",
    "ImageInfo",
    "save_image_infos",
    "load_image_infos",
]


##### Init functions


import atexit
from nodriver.core.util import deconstruct_browser

from .utils import silent_deconstruct_browser



atexit.unregister(deconstruct_browser)  # NO MORE SPAMMING!
atexit.register(silent_deconstruct_browser)
