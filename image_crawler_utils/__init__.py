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


import shutil
import time
import atexit

from rich import markup
from nodriver.core.util import deconstruct_browser, __registered__instances__

from .log import Log


# Some atexit-related function
def silent_deconstruct_browser(log: Log=Log()):
    """
    I have had enough with nodriver's annoying removing temp file messages.
    This function will do the same thing without those spamming messages.

    Args:
        log (image_crawler_utils.log.Log): Displaying those spamming messages.
    """

    for _ in __registered__instances__:
        if not _.stopped:
            _.stop()
        for attempt in range(5):
            try:
                if _.config and not _.config.uses_custom_data_dir:
                    shutil.rmtree(_.config.user_data_dir, ignore_errors=False)
            except FileNotFoundError as e:
                break
            except (PermissionError, OSError) as e:
                if attempt == 4:
                    log.error(f'Has problem when removing temp data directory [repr.filename]{markup.escape(_.config.user_data_dir)}[reset]; consider checking whether it\'s there and removing it manually. Error: {e}', extra={"markup": True})
                    break
                time.sleep(0.15)
                continue
        log.debug(f"Successfully removed temp profile [repr.filename]{markup.escape(_.config.user_data_dir)}[reset]", extra={"markup": True})


atexit.unregister(deconstruct_browser)  # NO MORE SPAMMING!
atexit.register(silent_deconstruct_browser)
