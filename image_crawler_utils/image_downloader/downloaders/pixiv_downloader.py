import os, re, json
import time
import random
import ua_generator

import requests
from rich import markup

from typing import Optional
import traceback

from image_crawler_utils.configs import DownloadConfig
from image_crawler_utils.log import Log
from image_crawler_utils.progress_bar import ProgressGroup

from .core_downloader import download_image



def pixiv_download_image_from_url(
    url: str, 
    image_name: str,
    download_config: DownloadConfig=DownloadConfig(),
    log: Log=Log(),
    store_path: str="./",
    session: Optional[requests.Session]=requests.Session(),
    progress_group: Optional[ProgressGroup]=None,
    thread_id: int=0,
) -> tuple[float, int]:
    """
    Download Pixiv image from url. Supports both direct Pixiv picture URL and artwork ID URL.

    Args:
        url (str): The URL of the image to download.
        image_name (str): Name of image to be stored.
        download_config (image_crawler_utils.configs.DownloadConfig): Comprehensive download config.
        log (config.Log): The logger.
        store_path (str): Path of image to be stored.
        session (requests.Session): Session of requests. Can contain cookies.
        progress_group (image_crawler_utils.progress_bar.ProgressGroup): The Group of Progress bars to be displayed in.
        thread_id (int): Nth thread of image downloading.

    Returns:
        (float, int): (the size of the downloaded image in bytes, thread_id)
    """

    # Type I: https://www.pixiv.net/artworks/117469273 type
    if ('artworks' in url and '.' not in url.split('/')[-1]) or 'illust_id=' in url:
        artwork_id = url.split('/')[-1]
        response_text = None
        request_headers = download_config.result_headers
        if request_headers is None:  # Pixiv must have a header
            ua = ua_generator.generate(browser=('chrome', 'edge'))
            ua.headers.accept_ch('Sec-CH-UA-Platform-Version, Sec-CH-UA-Full-Version-List')
            request_headers = ua.headers.get()
        request_headers["Referer"] = f"https://www.pixiv.net/artworks/{artwork_id}"

        try:            
            # Getting URL page
            for i in range(download_config.retry_times):
                try:
                    download_time = download_config.max_download_time

                    response = session.get(
                        f"https://www.pixiv.net/ajax/illust/{artwork_id}/pages",
                        headers=request_headers,
                        proxies=download_config.result_proxies,
                        timeout=(download_config.timeout, download_time),
                    )

                    if response.status_code == requests.status_codes.codes.ok:
                        log.debug(f'Successfully connected to [repr.url]{markup.escape(url)}[reset] at attempt {i + 1}.', extra={"markup": True})
                        response_text = response.text
                        break
                    elif response.status_code == 429:
                        log.warning(f'Connecting to [repr.url]{markup.escape(url)}[reset] FAILED at attempt {i + 1} because TOO many requests at the same time (response status code {response.status_code}). Retrying to connect in 1 to 2 minutes, but it is suggested to lower the number of threads or increase thread delay time and try again.', extra={"markup": True})
                        time.sleep(60 + random.random() * 60)
                    elif 400 <= response.status_code < 500:
                        log.error(f'Connecting to [repr.url]{markup.escape(url)}[reset] FAILED because response status code is {response.status_code}.', extra={"markup": True})
                        break
                    else:
                        log.warning(f'Failed to connect to [repr.url]{markup.escape(url)}[reset] at attempt {i + 1}. Response status code is {response.status_code}.', extra={"markup": True})
                    
                except Exception as e:
                    log.warning(f"Connecting to [repr.url]{markup.escape(url)}[reset] at attempt {i + 1} FAILED because {e} Retry connecting.\n{traceback.format_exc()}",
                                output_msg=f"Downloading [repr.url]{markup.escape(url)}[reset] at attempt {i + 1} FAILED.", extra={"markup": True})
                    time.sleep(download_config.result_fail_delay)

            # Parsing download page text
            try:
                response_dict = json.loads(response_text)
                url_list = [item["urls"]["original"] for item in response_dict["body"]]
                
                image_name_list = [image_name] * len(url_list)
                for i in range(0, len(url_list)):
                    ext = os.path.splitext(url_list[i])[1]
                    if '.' not in image_name_list[i]:
                        # Image has no suffix
                        image_name_list[i] += os.path.splitext(url_list[i])[1]
                    else:
                        # Image has suffix but not right
                        image_name_list[i] = os.path.splitext(image_name_list[i])[0] + ext

                    if os.path.splitext(image_name_list[i])[0] == artwork_id or len(url_list) > 1:
                        # Image name is same as artwork ID, or url_list has multiple images
                        image_name_list[i] = os.path.splitext(image_name_list[i])[0] + f'_p{i}' + os.path.splitext(image_name_list[i])[1]                
            except:
                raise ValueError("No image URLs are detected.")
        except Exception as e:
            log.error(f"Failed to parse Pixiv image URLs from [repr.url]{markup.escape(url)}[reset]. This page might not exist, or not accessible without an account.", extra={"markup": True})
            return 0, thread_id
        
        # Download images
        total_downloaded_size = 0
        for j in range(0, len(url_list)):
            is_success, image_size = download_image(
                url=url_list[j],
                image_name=image_name_list[j],
                download_config=download_config,
                headers=request_headers,
                log=log,
                store_path=store_path,
                session=session,
                progress_group=progress_group,
                thread_id=thread_id,
            )
            total_downloaded_size += image_size            
            if not is_success:
                log.error(f"FAILED to download [repr.filename]{markup.escape(image_name_list[j])}[reset] from [repr.url]{markup.escape(url_list[j])}[reset]", extra={"markup": True})                
        return total_downloaded_size, thread_id

    # Type II: https://foo.bar.net/117469273_p0.jpg type
    else:
        # Edit url
        try:
            try:
                old_names = re.search(r"//.*?pixiv.net", url).group()
                new_url = url.replace(old_names, r'//i.pximg.net').replace("https", "http").replace("http", "https")
            except:
                old_names = re.search(r".*pixiv.net", url).group()
                new_url = url.replace(old_names, r'i.pximg.net').replace("https", "http").replace("http", "https")
        except:
            new_url = url

        if '.' not in image_name and '.' in new_url:
            ext = os.path.splitext(url)[1]
            edited_image_name = image_name + ext
        else:
            edited_image_name = image_name

        request_headers = download_config.result_headers
        if request_headers is None:  # Pixiv must have a header
            ua = ua_generator.generate(browser=('chrome', 'edge'))
            ua.headers.accept_ch('Sec-CH-UA-Platform-Version, Sec-CH-UA-Full-Version-List')
            request_headers = ua.headers.get()
        request_headers["Referer"] = f"https://www.pixiv.net/artworks/{new_url.split('/')[-1].split('_')[0]}"

        is_success, image_size = download_image(
            url=new_url,
            image_name=edited_image_name,
            download_config=download_config,
            headers=request_headers,
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
