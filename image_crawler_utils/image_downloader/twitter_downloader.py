import os
import time
import re

import requests

import nodriver

from typing import Optional
import traceback

from image_crawler_utils import Cookies, update_nodriver_browser_cookies
from image_crawler_utils.configs import DownloadConfig
from image_crawler_utils.log import Log
from image_crawler_utils.utils import custom_tqdm, check_dir, set_up_nodriver_browser

from .core_downloader import download_image



# Parsing images
async def __get_image_from_status(
    url: str, 
    download_config: DownloadConfig=DownloadConfig(),
    log: Log=Log(),
    session: Optional[requests.Session]=requests.Session(),
):
    with custom_tqdm.trange(
        3,
        desc=f'Loading browser components...',
        leave=False,
    ) as pbar:
        # Connect once to get cookies
        try:
            log.debug(f"Parsing Twitter / X status page: \"{url}\"")
            browser = await set_up_nodriver_browser(
                proxies=download_config.result_proxies,
            )

            pbar.update()
            pbar.set_description(f"Requesting Twitter / X status once...")

            tab = await browser.get(url, new_tab=True)
            await tab.find('div[id="react-root"]')
        except Exception as e:
            browser.stop()
            raise ConnectionError(f"{e}")
        
        # Replace cookies
        cookies = Cookies.create_by(session.cookies.get_dict())
        await update_nodriver_browser_cookies(browser, cookies)

        # Connect twice to get images
        try:
            pbar.update()
            pbar.set_description(f"Requesting Twitter / X status again with cookies...")

            await tab.get(url)
            await tab.scroll_up(1000)  # Sometimes it does not load from the first tweet. Scroll to top in case of this!
            await tab.sleep()  # Wait until the whole page is fully loaded!
            # Get main structure
        except Exception as e:
            browser.stop()
            raise ConnectionError(f"{e}")
        
        # Check if it is empty
        try:
            await tab.find('article[data-testid="tweet"]', timeout=30)  # Try to get a tweet first
        except:
            main_structure = await tab.find('div[data-testid="primaryColumn"]')
            empty_element = None  # Twitter / X page not exist
            try:
                empty_element = await main_structure.query_selector('div[data-testid="error-detail"]')
            finally:
                if empty_element is not None:
                    raise FileExistsError("This Twitter / X page does not exist, or not accessible without an account.")

        # Check if the tweet itself is banned (comment tweets may exist)
        main_structure = await tab.find('div[data-testid="primaryColumn"]')
        banned_element = None  # Twitter / X page banned
        try:
            banned_element = await main_structure.query_selector('a[href="https:\\/\\/help.twitter.com\\/rules-and-policies\\/notices-on-twitter"]')
        finally:
            if banned_element is not None:
                raise FileExistsError("This Twitter / X page does not exist because the status or user violated Twitter / X rules and policies.")
        
        # Try parsing image elements
        try:
            tweet_element = await main_structure.query_selector('article[data-testid="tweet"]')
            img_elements = await tweet_element.query_selector_all('img')
            available_src = [element.attrs['src'] for element in img_elements
                             if ('src' in element.attrs.keys()
                                 and "pbs.twimg.com/media" in element.attrs['src'])]
            if len(available_src) == 0:
                raise FileNotFoundError("Images not found on Twitter / X status.")

            pbar.update()
            browser.stop()
        except Exception as e:
            browser.stop()
            raise FileNotFoundError(f"{e}")
        
    return available_src


# Downloading images
async def __twitter_download_image_from_status(
    url: str, 
    image_name: str,
    download_config: DownloadConfig=DownloadConfig(),
    log: Log=Log(),
    store_path: str="./",
    session: Optional[requests.Session]=requests.Session(),
    thread_id: int=0,
) -> tuple[float, int]:
    
    # Get image from status webpage
    available_src = None
    for i in range(download_config.retry_times):
        try:
            available_src = await __get_image_from_status(
                url=url,
                download_config=download_config,
                log=log,
                session=session,
            )
            break
        except FileExistsError as e:  # Status itself has error (not found, banned, etc.)
            error_msg = e
            break
        except Exception as e:
            log.warning(f"Parsing Twitter / X status page failed at attempt {i + 1} because {e}")
            error_msg = e
    if available_src is None:
        output_msg_base = f"Parsing Twitter / X status page \"{url}\" failed"
        log.error(f"{output_msg_base}.\n{traceback.format_exc()}", output_msg=f"{output_msg_base} because {error_msg}")
        return (0, thread_id)
    
    # Edit URLs and names
    url_list = [(re.search(r".*&", src).group()[:-1] + '&name=orig') for src in available_src]

    image_name_list = [image_name] * len(url_list)
    for i in range(0, len(url_list)):
        try:
            ext = re.search(r"format=.*?&", url_list[i]).group()[len('format='):-1]
        except:
            ext = re.search(r"format=.*?", url_list[i]).group()[len('format='):]
        if '.' not in image_name_list[i]:
        # Image has no suffix
            image_name_list[i] += f'.{ext}'
        else:
        # Image has suffix but not right
            image_name_list[i] = os.path.splitext(image_name_list[i])[0] + f'.{ext}'
        if len(url_list) > 1:
            # More than 1 image in the status page
            image_name_list[i] = os.path.splitext(image_name_list[i])[0] + f'_{i + 1}' + os.path.splitext(image_name_list[i])[1]

    # Start downloading
    check_dir(store_path, log)
    total_downloaded_size = 0
    for j in range(0, len(url_list)):
        is_success, image_size = download_image(
            url=url_list[j],
            image_name=image_name_list[j],
            download_config=download_config,
            log=log,
            store_path=store_path,
            session=session,
            thread_id=thread_id,
        )
        total_downloaded_size += image_size
        
        if not is_success:
            log.error(f"FAILED to download {image_name_list[j]} from {url_list[j]}")

    return total_downloaded_size, thread_id


# Actually used
def twitter_download_image_from_status(
    url: str, 
    image_name: str,
    download_config: DownloadConfig=DownloadConfig(),
    log: Log=Log(),
    store_path: str="./",
    session: Optional[requests.Session]=requests.Session(),
    thread_id: int=0,
) -> tuple[float, int]:
    """
    Download image from url

    Parameters:
        url (str): The URL of the image to download.
        image_name (str): Name of image to be stored.
        download_config (image_crawler_utils.config.DownloadConfig): Comprehensive download config.
        log (config.Log): The logger.
        store_path (str): Path of image to be stored.
        session (requests.Session): Session of requests. Can contain cookies.
        thread_id (int): Nth thread of image downloading.

    Returns:
        (float, int): (the size of the downloaded image in Bytes, thread_id)
    """

    return nodriver.loop().run_until_complete(
        __twitter_download_image_from_status(
            url=url,
            image_name=image_name,
            download_config=download_config,
            log=log,
            store_path=store_path,
            session=session,
            thread_id=thread_id,
        )
    )
