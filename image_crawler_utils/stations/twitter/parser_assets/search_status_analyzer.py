from typing import Optional
import re
import datetime
import os

import traceback

from bs4 import BeautifulSoup

import nodriver
import asyncio

from image_crawler_utils import CrawlerSettings
from image_crawler_utils.log import Log
from image_crawler_utils.progress_bar import CustomProgress, ProgressGroup

from .constants import SCROLL_DELAY, SCROLL_NUM, DOWN_SCROLL_LENGTH, LOAD_SCROLL_LENGTH
from .status_classes import TwitterStatus, TwitterStatusMedia
from .utils import twitter_progress_bar_loading, twitter_empty_check, twitter_error_check



def parse_twitter_status_element(
    status_html: str, 
    log: Log=Log()
) -> Optional[TwitterStatus]:
    """
    Parse Twitter / X status element from search result page: "<article ...></article>".

    Args:
        status_html (str): HTML string of status element "<article ...></article>".
        log (image_crawler_utils.log.Log, None): Logging config.

    Returns:
        A image_crawler_utils.stations.twitter.TwitterStatus class.
    """

    soup = BeautifulSoup(status_html, "lxml")
    result = TwitterStatus()

    # Basic elements
    try:
        result.status_url = f'https://x.com{soup.find("a", class_="css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41 r-xoduu5 r-1q142lx r-1w6e6rj r-9aw3ui r-3s2u2q r-1loqt21").get("href")}'
        result.status_id = result.status_url.split('/')[-1]
        result.user_id = result.status_url.split('/')[3]
    except Exception as e:
        return None  # If a status does not contain these elements, then it is likely an advertisement!

    # User name
    try:
        result.user_name = soup.find('span', class_='css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3').text
    except Exception as e:
        log.warning(f"Cannot get user name from [repr.url]{result.status_url}[reset] because {e}", extra={"markup": True})

    # Posting time
    try:
        result.time = soup.find('time').get("datetime")
    except Exception as e:
        log.warning(f"Cannot get time from [repr.url]{result.status_url}[reset] because {e}", extra={"markup": True})

    # Replies, retweets, and likes; string found is like '123 replies'
    try:
        stats_box = soup.find('div', attrs={'role': "group"})
        buttons = stats_box.find_all('button')
        try:
            reply_num_str = buttons[0].get('aria-label')
            result.reply_num = int(reply_num_str.split(' ')[0])
        except Exception as e:
            log.warning(f"Cannot get reply num from [repr.url]{result.status_url}[reset] because {e}", extra={"markup": True})
        try:
            retweet_num_str = buttons[1].get('aria-label')
            result.retweet_num = int(retweet_num_str.split(' ')[0])
        except Exception as e:
            log.warning(f"Cannot get retweet num from [repr.url]{result.status_url}[reset] because {e}", extra={"markup": True})
        try:
            like_num_str = buttons[2].get('aria-label')
            result.like_num = int(like_num_str.split(' ')[0])
        except Exception as e:
            log.warning(f"Cannot get like num from [repr.url]{result.status_url}[reset] because {e}", extra={"markup": True})
    except Exception as e:
        log.warning(f"Cannot get replies / retweets / likes information from [repr.url]{result.status_url}[reset] because {e}", extra={"markup": True})

    # Optional elements: view num (Some old tweets do not have this)
    try:
        view_num_str = soup.find('a', class_="css-175oi2r r-1777fci r-bt1l66 r-bztko3 r-lrvibr r-1ny4l3l r-1loqt21").get('aria-label')
        result.view_num = int(view_num_str.split(' ')[0])
    except:
        result.view_num = None

    # Optional elements: Text
    text_box = soup.find('div', attrs={'data-testid': "tweetText"})
    if text_box is not None:
        try:
            result.text = ''.join([(content.get("alt") if "alt" in content.attrs else content.text) for content in text_box.contents])
            result.hashtags = [content.text for content in text_box.find_all('a') if content.get("href").startswith('/hashtag')]
            result.links = [content.get("href") for content in text_box.find_all('a') if not content.get("href").startswith('/hashtag')]
        except:
            pass

    # Optional elements: Media
    media_box = [div for div in soup.find_all('div') if "aria-labelledby" in div.attrs]
    if len(media_box) > 0:
        media_box = media_box[0]
        
        try:
            for link in media_box.find_all('a'):
                if link.find('img') is not None:
                    media_info = TwitterStatusMedia()
                    media_info.link = f'https://x.com{link.get("href")}' if 'https' not in link.get("href") else link.get("href")
                    image_source = link.find("img").get("src")
                    if 'abs-0.twimg.com/emoji' in image_source:  # .svg is emoji images
                        continue
                    media_info.image_source = re.search(r".*&", image_source).group()[:-1] + '&name=orig'
                    media_info.image_id = image_source.split('/')[-1].split('?')[0]
                    try:
                        ext = re.search(r"format=.*?&", image_source).group()[len('format='):-1]
                    except:
                        ext = re.search(r"format=.*?", image_source).group()[len('format='):]
                    media_info.image_name = result.status_id + f'.{ext}'
                    result.media_list.append(media_info)
            if len(result.media_list) > 1:
                # Multiple media in a status
                for i in range(len(result.media_list)):
                    name, ext = os.path.splitext(result.media_list[i].image_name)
                    result.media_list[i].image_name = name + f'_{i + 1}' + ext
        except Exception as e:
            output_msg_base = f"There should be at least 1 media in [repr.url]{result.status_url}[reset], but none is detected"
            log.warning(f"{output_msg_base}.\n{traceback.format_exc()}", output_msg=f"{output_msg_base} because {e}")

    return result


async def find_twitter_status(
    tab: nodriver.Tab, 
    log: Log=Log(),
) -> list[TwitterStatus]:
    """
    Finding all Twitter / X status on current searching result page.

    Args:
        tab (unodriver.Tab): Nodriver tab with loaded searching result page.
        log (image_crawler_utils.log.Log, None): Logging config.

    Returns:
        A list of image_crawler_utils.stations.twitter.TwitterStatus class.
    """

    status_list: list[TwitterStatus] = []

    # Find status
    await tab  # Let the page be loaded
    main_structure = await tab.select('div[data-testid="primaryColumn"]')
    status_elements = await main_structure.query_selector_all('article[data-testid="tweet"]')
    for element in status_elements:
        element_html = await element.get_html()
        parsed_twitter_status = parse_twitter_status_element(element_html, log=log)
        if parsed_twitter_status is not None:
            status_list.append(parsed_twitter_status)
    
    return status_list


async def scrolling_to_find_status(
    tab: nodriver.Tab,
    tab_url: str,
    crawler_settings: CrawlerSettings=CrawlerSettings(),
    reload_times: int=1,
    error_retry_delay: float=200,
    image_num_restriction: Optional[int]=None,
    progress_group: Optional[ProgressGroup]=None,
    transient: bool=False,
) -> list[TwitterStatus]:
    """
    Scrolling to finding all Twitter / X status on current searching result page.

    Args:
        crawler_settings (image_crawler_utils.CrawlerSettings): The CrawlerSettings used in this Parser.
        tab (nodriver.Tab): nodriver.Tab with loaded searching result page.
        reload_times (int): To deal with (possible) missing status, reload pages for reload_times to get status results.
        error_retry_delay (float): When an error happens (especially Twitter / X returns an error), sleep error_retry_delay before reloading again.
        progress_group (image_crawler_utils.progress_bar.ProgressGroup): The Group of Progress bars to be displayed in.
        transient (bool): Hide Progress bars after finishing.

    Returns:
        A list of image_crawler_utils.stations.twitter.TwitterStatus class, sort by status from large to small.
    """
    
    # Fetching status with retrying; every attempt may lead to different results
    final_status_list: list[TwitterStatus] = []  # All status

    # Load the page for reload_count times
    for reload_count in range(reload_times):
        not_from_retry_button = True

        if progress_group is None:  # No father tasks are provided, create an separate progress
            progress = CustomProgress(has_total=False, transient=transient)
            progress.start()
        else:
            if transient:
                progress = progress_group.sub_no_total_count_bar
            else:
                progress = progress_group.main_no_total_count_bar

        task = progress.add_task(description=f'Loading [repr.number]{reload_count + 1}[reset]/[repr.number]{reload_times}[reset], scrolling times:')

        # Different from reload_count, retry_count only works when an error happens
        retry_count = 0
        while retry_count < crawler_settings.download_config.retry_times:
            try:
                # Loading until progress bar (rotating circle) disappears
                crawler_settings.log.debug(f'Awaiting loading icons to disappear in [repr.url]{tab_url}[reset] ...', extra={"markup": True})
                await twitter_progress_bar_loading(tab)
                crawler_settings.log.debug(f'Loading icons disappeared in [repr.url]{tab_url}[reset].', extra={"markup": True})

                if not_from_retry_button:  # If the page is new, do some initialization
                    retry_count += 1
                    attempt_status_list: list[TwitterStatus] = []  # Status retrieved in every retry
                    len_attempt_status = -1
                    scroll_count = 0
                    media_count = 0
                    await tab.scroll_up(1000)  # Sometimes it does not load from the first tweet. Scroll to top in case of this!
                
                # Check if it is empty
                crawler_settings.log.debug(f'Checking "empty" elements in [repr.url]{tab_url}[reset].', extra={"markup": True})
                check = await twitter_empty_check(tab)
                if check:
                    crawler_settings.log.warning(f'Page [repr.url]{tab_url}[reset] contains no result.', extra={"markup": True})
                    return [], 0  # Exit directly
                
                # Check if there is an error
                crawler_settings.log.debug(f'Checking error elements in [repr.url]{tab_url}[reset].', extra={"markup": True})
                check = await twitter_error_check(tab)
                if check:
                    raise ConnectionRefusedError
                
                # Start scrolling down batch
                while len(attempt_status_list) != len_attempt_status or not not_from_retry_button:  # When it is loaded from retry button, force the loop to run once
                    len_attempt_status = len(attempt_status_list)

                    if not_from_retry_button:  # When retry button is detected, the page had already scrolled down
                        # Scroll down LOAD_SCROLL_LENGTH
                        progress.update(task, advance=1)
                        await tab.scroll_down(LOAD_SCROLL_LENGTH)
                        crawler_settings.log.debug(f'Scrolled down {LOAD_SCROLL_LENGTH} at [repr.url]{tab_url}[reset]', extra={"markup": True})

                    # Loading until progress bar (rotating circle) disappears
                    crawler_settings.log.debug(f'Awaiting loading icons to disappear in [repr.url]{tab_url}[reset] ...', extra={"markup": True})
                    await twitter_progress_bar_loading(tab)
                    crawler_settings.log.debug(f'Loading icons disappeared in [repr.url]{tab_url}[reset].', extra={"markup": True})
                    
                    # Check if there is an error
                    crawler_settings.log.debug(f'Checking error elements in [repr.url]{tab_url}[reset].', extra={"markup": True})
                    check = await twitter_error_check(tab)
                    if check:
                        raise ConnectionRefusedError

                    # Scroll up LOAD_SCROLL_LENGTH
                    progress.update(task, advance=1)
                    await tab.scroll_up(LOAD_SCROLL_LENGTH)
                    crawler_settings.log.debug(f'Scrolled up {LOAD_SCROLL_LENGTH} at [repr.url]{tab_url}[reset]', extra={"markup": True})

                    # Only compare the results after SCROLL_NUM scrollings
                    for i in range(SCROLL_NUM):
                        await asyncio.sleep(SCROLL_DELAY)
                        progress.update(task, advance=1)
                        await tab.scroll_down(DOWN_SCROLL_LENGTH)
                        crawler_settings.log.debug(f'Scrolled down {DOWN_SCROLL_LENGTH} at [repr.url]{tab_url}[reset]', extra={"markup": True})
                        scroll_count += 1
                        
                        # Twitter has f**king StaleElementReferenceException, which means you may retry several times to retrieve the element
                        for j in range(crawler_settings.download_config.retry_times):
                            try:
                                current_status_list = await find_twitter_status(
                                    tab=tab, 
                                    log=crawler_settings.log,
                                )
                                
                                break  # Successful, stop retrying
                            except ConnectionRefusedError as e:  # An Twitter / X error happens!
                                raise ConnectionRefusedError(e)
                            except Exception as e:
                                current_status_list = None
                                error_msg = e

                        if current_status_list is None:  # An error happened
                            raise ConnectionError(error_msg)
                        else:  # No error, status successfully got
                            attempt_status_url_list = [status.status_url for status in attempt_status_list]
                            for status in current_status_list:
                                if status.status_url not in attempt_status_url_list:
                                    attempt_status_list.append(status)
                                    media_count += len(status.media_list)

                        progress.update(task, description=f'Loading [repr.number]{reload_count + 1}[reset]/[repr.number]{reload_times}[reset], [repr.number]{len(attempt_status_list)}[reset] status & [repr.number]{media_count}[reset] {"images" if media_count > 1 else "image"} detected after scrolling times:')

                        # Reached restrictions on media num
                        if image_num_restriction is not None and media_count >= image_num_restriction:
                            crawler_settings.log.info(f'Collected {media_count} media {"images have" if media_count > 1 else "image has"} exceeded the restrictions on image num ({image_num_restriction} {"images" if image_num_restriction > 1 else "image"}).')
                            len_attempt_status = len(attempt_status_list)  # Set this to break the outer loop
                            break
                    not_from_retry_button = True  # Current scrolling down finished
                        
                break  # Succeeded, no retrying
            
            except ConnectionRefusedError:
                restart_time = datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(seconds=error_retry_delay), '%H:%M:%S')
                crawler_settings.log.warning(f'Twitter / X returns an error when loading [repr.url]{tab_url}[reset], next reloading will start {error_retry_delay} {"seconds" if error_retry_delay > 1 else "second"} later at {restart_time}.', extra={"markup": True})

                # Update progress bar to pausing
                progress.update(task, description=f'[yellow bold](Pausing)[reset] Loading [repr.number]{reload_count + 1}[reset]/[repr.number]{reload_times}[reset], [repr.number]{len(attempt_status_list)}[reset] status & [repr.number]{media_count}[reset] {"images" if media_count > 1 else "image"} detected after scrolling times:')
                await asyncio.sleep(error_retry_delay)
                # Reset progress bar from pausing
                progress.update(task, description=f'Loading [repr.number]{reload_count + 1}[reset]/[repr.number]{reload_times}[reset], [repr.number]{len(attempt_status_list)}[reset] status & [repr.number]{media_count}[reset] {"images" if media_count > 1 else "image"} detected after scrolling times:')
                
                try:  # Try clicking the retry button
                    main_structure = await tab.select('div[data-testid="primaryColumn"]')
                    error_element = await main_structure.query_selector('button[class="css-175oi2r r-sdzlij r-1phboty r-rs99b7 r-lrvibr r-2yi16 r-1qi8awa r-3pj75a r-1loqt21 r-o7ynqc r-6416eg r-1ny4l3l"]')
                    await error_element.click()
                    await tab
                    not_from_retry_button = False  # Keep collected status and do not scroll up & update retry count
                except:  # Failed to find the button, then reload the page
                    crawler_settings.log.warning(f'Retry button is missing in [repr.url]{tab_url}[reset]! Refreshing this page.', extra={"markup": True})
                    await tab.get(tab_url)  # Refresh
                    retry_count -= 1  # Do not update retry count
                    not_from_retry_button = True
            except Exception as e:
                output_msg_base = f'Failed to load page [repr.url]{tab_url}[reset] at attempt {retry_count}'
                crawler_settings.log.warning(f"{output_msg_base}.\n{traceback.format_exc()}", output_msg=f"{output_msg_base} because {e}", extra={"markup": True})
                if retry_count < crawler_settings.download_config.retry_times - 1:  # Not the last reloading
                    await asyncio.sleep(crawler_settings.download_config.result_thread_delay)
                    await tab.get(tab_url)  # Refresh
                    not_from_retry_button = True

        progress.finish_task(task, hide=transient)  # No matter success of failure, finish the task in this reload_count

        # Add status in this loading to the final_status_list
        final_status_url_list = [status.status_url for status in final_status_list]
        for status in attempt_status_list:
            if status.status_url not in final_status_url_list:
                final_status_list.append(status)
        
        # Reload page again
        if reload_count < reload_times - 1:
            await tab.get(tab_url)  # Refresh
            await tab
            await tab.scroll_up(1000)

    final_status_list.sort(reverse=True)  # Sort by status_id from large to small
    return final_status_list, media_count
