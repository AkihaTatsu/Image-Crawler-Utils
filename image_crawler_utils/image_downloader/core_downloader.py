import os
import time
import random

import requests

from typing import Optional, Union
from collections.abc import Callable
import traceback

from image_crawler_utils.configs import DownloadConfig
from image_crawler_utils.log import Log
from image_crawler_utils.progress_bar import CustomProgress, ProgressGroup
from image_crawler_utils.utils import check_dir, shorten_file_name



def download_image(
    url: str, 
    image_name: str,
    download_config: DownloadConfig=DownloadConfig(),
    headers: Optional[Union[dict, Callable]]=None,
    proxies: Optional[Union[dict, Callable]]=None,
    log: Log=Log(),
    store_path: str='./',
    session: Optional[requests.Session]=requests.Session(),
    progress_group: Optional[ProgressGroup]=None,
    thread_id: int=0,
) -> tuple[bool, int]:
    """
    Download image from url.

    Parameters:
        url (str): The URL of the image to download.
        image_name (str): Name of image to be stored.
        download_config (image_crawler_utils.configs.DownloadConfig): Comprehensive download config.
        headers (dict, function or None): Custom headers that will overwrite the ones in download_config.
        proxies (dict, function or None): Custom proxies that will overwrite the ones in download_config.
        log (config.Log): The logger.
        store_path (str): Path of image to be stored.
        session (requests.Session): A session that may contain cookies.
        progress_group (image_crawler_utils.progress_bar.ProgressGroup): The Group of Progress bars to be displayed in.
        thread_id (int): Nth thread of image downloading.

    Returns:
        (bool, int): (bool denoting whether succeeded, the size of the downloaded image in Bytes)
    """

    # Start downloading
    log.debug(f"Start downloading {image_name} from \"{url}\"")
    
    # Set image path
    check_dir(store_path, log)
    original_image_path = os.path.join(store_path, image_name)
    temp_image_name = image_name + '.tmp'
    image_path = os.path.join(store_path, temp_image_name)

    # Try several times
    for i in range(download_config.retry_times):

        try:                    
            # Set configs
            download_time = download_config.max_download_time
            if headers is None:
                request_headers = download_config.result_headers
            else:
                request_headers = headers() if callable(headers) else headers
            if proxies is None:
                use_proxies = download_config.result_proxies
            else:
                use_proxies = proxies() if callable(proxies) else proxies

            # Send a request
            response = session.get(
                url,
                headers=request_headers,
                proxies=use_proxies,
                timeout=(download_config.timeout, download_time),
                stream=True,
            )

            # Check result
            if response.status_code == requests.status_codes.codes.ok:  # Success
                if "content-length" in response.headers.keys() and response.headers["content-length"].isdigit():  # Has content-length
                    # Set up progress bar
                    if progress_group is None:  # No father tasks are provided, create an separate progress
                        progress = CustomProgress(is_file=True, transient=True)
                        progress.start()
                    else:
                        progress = progress_group.sub_file_bar

                    image_size = int(response.headers["content-length"])
                    downloaded_size = 0
                    
                    display_image_name = shorten_file_name(image_name)

                    # Loading progress bar
                    task = progress.add_task(f'- Thread [repr.number]{thread_id}[reset], [white bold]{display_image_name}[reset]:', total=image_size)
                    with open(image_path, "wb") as f:
                        for data in response.iter_content(chunk_size=32768):
                            size = f.write(data)
                            downloaded_size += size
                            progress.update(task, advance=size)

                        # Detect incomplete image
                        if downloaded_size != image_size:
                            time.sleep(download_config.result_fail_delay)
                            log.warning(f'"{image_name}" downloaded at attempt {i + 1} is incomplete. Retry downloading.')
                            continue

                    progress.finish_task(task)  # Hide progress bar

                else:  # Failed to get content-length
                    log.debug(f'"content-length" not found in response.headers.keys() for {image_name} from \"{url}\"')
                    downloaded_size = 0

                    # Set up progress bar
                    if progress_group is None:  # No father tasks are provided, create an separate progress
                        progress = CustomProgress(has_total=False, is_file=True, transient=True)
                        progress.start()
                    else:
                        progress = progress_group.sub_no_total_file_bar
                        
                    display_image_name = shorten_file_name(image_name)

                    # Loading progress bar
                    task = progress.add_task(f'- Thread [repr.number]{thread_id}[reset], [white bold]{display_image_name}[reset]:')
                    with open(image_path, "wb") as f:       
                        for data in response.iter_content(chunk_size=1024):
                            size = f.write(data)
                            downloaded_size += size
                            progress.update(task, advance=size)

                    image_size = downloaded_size  # Size of images is the size of downloaded contents
                    progress.finish_task(task)  # Hide progress bar

                # Overwrite images
                if os.path.exists(original_image_path):
                    log.debug(f"{os.path.abspath(original_image_path)} will be overwritten.")
                    os.remove(original_image_path)
                
                # Rename images and finish
                os.rename(image_path, original_image_path)
                log.debug(f"Finished downloading {image_name} from \"{url}\"")
                return True, image_size

            else:
                if response.status_code == 429:
                    log.warning(f'Connecting to \"{url}\" FAILED at attempt {i + 1} because TOO many requests at the same time (response status code {response.status_code}). Retrying to connect in 1 to 2 minutes, but it is suggested to lower the number of threads or increase the delay time and try again.')
                    time.sleep(60 + random.random() * 60)
                    continue
                elif 400 <= response.status_code < 500:
                    log.error(f'Downloading "{image_name}" FAILED because response status code is {response.status_code} from \"{url}\"')
                    break
                else:
                    log.warning(f'Downloading "{image_name}" at attempt {i + 1} from \"{url}\" FAILED because response code is {response.status_code}. Retry downloading.')
                    time.sleep(download_config.result_fail_delay)
                    continue
            
        except Exception as e:
            log.warning(f'Downloading "{image_name}" at attempt {i + 1} FAILED because {e} Retry downloading.\n{traceback.format_exc()}',
                        output_msg=f'Downloading "{image_name}" at attempt {i + 1} FAILED. Retry downloading.')
            if os.path.exists(image_path):  # Remove tmp file
                os.remove(image_path)
            time.sleep(download_config.result_fail_delay)
        
    return False, 0
