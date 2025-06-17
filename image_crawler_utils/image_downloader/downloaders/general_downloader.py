import os
import time

import requests
from typing import Optional, Union
from rich import markup

from image_crawler_utils import Cookies
from image_crawler_utils.configs import DownloadConfig
from image_crawler_utils.log import Log
from image_crawler_utils.progress_bar import ProgressGroup

from .core_downloader import download_image
from .pixiv_downloader import pixiv_download_image_from_url
from .twitter_downloader import twitter_download_image_from_status


def download_image_from_url(
    url: str, 
    image_name: str,
    download_config: DownloadConfig=DownloadConfig(),
    log: Log=Log(),
    store_path: str="./",
    session: Optional[requests.Session]=None,
    progress_group: Optional[ProgressGroup]=None,
    thread_id: int=0,
    cookies: Optional[Union[Cookies, list, dict, str]]=Cookies(),
) -> tuple[int, int]:
    """
    Download image from url. Automatically separate Pixiv, Twitter, etc. image URLs from normal URLs.

    Args:
        url (str): The URL of the image to download.
        image_name (str): Name of image to be stored.
        download_config (image_crawler_utils.configs.DownloadConfig): Comprehensive download config.
        log (config.Log): The logger.
        store_path (str): Path of image to be stored.
        session (requests.Session): A session that may contain cookies.
        progress_group (image_crawler_utils.progress_bar.ProgressGroup): The Group of Progress bars to be displayed in.
        thread_id (int): Nth thread of image downloading.
        cookies (image_crawler_utils.Cookies, str, dict, list, None): If session parameter is empty, use cookies to create a session with cookies.

    Returns:
        (float, int): (the size of the downloaded image in bytes, thread_id)
    """

    if session is None:
        if not isinstance(cookies, Cookies):
            cookies = Cookies(cookies)
        session = requests.Session()
        session.cookies.update(cookies.cookies_dict)

    # Check whether it is special websites

    if "pximg.net" in url or "pixiv.net" in url:
        return pixiv_download_image_from_url(
            url=url,
            image_name=image_name,
            download_config=download_config,
            log=log,
            store_path=store_path,
            session=session,
            progress_group=progress_group,
            thread_id=thread_id,
        )
    elif ("x.com" in url or "twitter.com" in url) and "/status/" in url:
        return twitter_download_image_from_status(
            url=url,
            image_name=image_name,
            download_config=download_config,
            log=log,
            store_path=store_path,
            session=session,
            progress_group=progress_group,
            thread_id=thread_id,
        )

    if '.' not in image_name and '.' in url:
        ext = os.path.splitext(url)[1]
        edited_image_name = image_name + ext
    else:
        edited_image_name = image_name

    time.sleep(download_config.result_thread_delay)

    # Start downloading
    
    is_success, image_size = download_image(
        url=url,
        image_name=edited_image_name,
        download_config=download_config,
        log=log,
        store_path=store_path,
        session=session,
        progress_group=progress_group,
        thread_id=thread_id,
    )
    if is_success:
        return image_size, thread_id
    else:
        log.error(f'FAILED to download [repr.filename]{markup.escape(image_name)}[reset] from [repr.url]{markup.escape(url)}[reset]', extra={"markup": True})
        return 0, thread_id
