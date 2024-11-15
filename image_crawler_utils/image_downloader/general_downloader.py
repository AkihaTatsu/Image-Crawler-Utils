import os
import time

import requests
from typing import Optional, Union

from image_crawler_utils import Cookies
from image_crawler_utils.configs import DownloadConfig
from image_crawler_utils.log import Log

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
    thread_id: int=0,
    cookies: Optional[Union[Cookies, list, dict, str]]=Cookies(),
) -> tuple[int, int]:
    """
    Download image from url

    Parameters:
        url (str): The URL of the image to download.
        image_name (str): Name of image to be stored.
        download_config (image_crawler_utils.config.DownloadConfig): Comprehensive download config.
        log (config.Log): The logger.
        store_path (str): Path of image to be stored.
        session (requests.Session): A session that may contain cookies.
        thread_id (int): Nth thread of image downloading.
        cookies (crawler_utils.cookies.Cookies, str, dict or list, optional): If session parameter is empty, use cookies to create a session with cookies.

    Returns:
        (float, int): (the size of the downloaded image in Bytes, thread_id)
    """

    if session is None:
        if not isinstance(cookies, Cookies):
            cookies = Cookies.create_by(cookies)
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
            thread_id=thread_id,
        )

    if '.' not in image_name and '.' in url:
        ext = os.path.splitext(url)[1]
        edited_image_name = image_name + ext
    else:
        edited_image_name = image_name

    time.sleep(download_config.randomized_thread_delay)
    # Start downloading
    is_success, image_size = download_image(
        url=url,
        image_name=edited_image_name,
        download_config=download_config,
        log=log,
        store_path=store_path,
        session=session,
        thread_id=thread_id,
    )
    if is_success:
        return image_size, thread_id
    else:
        log.error(f'FAILED to download "{image_name}" from \"{url}\"')
        return 0, thread_id
