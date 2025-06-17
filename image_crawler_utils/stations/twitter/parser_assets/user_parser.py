import dataclasses
import datetime

from typing import Optional, Union

from urllib import parse
import nodriver
from concurrent import futures

from image_crawler_utils import Cookies, Parser, ImageInfo, CrawlerSettings, update_nodriver_browser_cookies
from image_crawler_utils.progress_bar import ProgressGroup
from image_crawler_utils.utils import set_up_nodriver_browser

from .search_settings import TwitterSearchSettings
from .search_status_analyzer import scrolling_to_find_status
from .status_classes import TwitterStatus



##### Twitter Media Parser


class TwitterUserMediaParser(Parser):

    def __init__(
        self, 
        user_id: str,
        station_url: str="https://x.com/",
        crawler_settings: CrawlerSettings=CrawlerSettings(),
        cookies: Optional[Union[Cookies, list, dict, str]]=Cookies(),
        reload_times: int=1,
        error_retry_delay: float=200,
        interval_days: int=180,
        starting_date: Optional[str]=None,
        ending_date: Optional[str]=None,
        exit_when_empty: bool=False,
        headless: bool=True,
    ):
        """
        Args:
            crawler_settings (image_crawler_utils.CrawlerSettings): The CrawlerSettings used in this Parser.
            user_id: Twitter / X ID of a user.
            station_url (str): The URL of the main page of a website.

            + This parameter works when several websites use the same structure. For example, https://yande.re/ and https://konachan.com/ both use Moebooru to build their websites, and this parameter must be filled to deal with these sites respectively.
            + For websites like https://www.pixiv.net/, as no other website uses its structure, this parameter has already been initialized and do not need to be filled.

            cookies (image_crawler_utils.Cookies, str, dict, list, None): Cookies containing logging information.
            reload_times (int): Time of reloading page in case some status are omitted.
            error_retry_delay (float): Pause error_retry_delay seconds if an error happened.
            interval_days (int): Interval of days for each searching result page.
            starting_date ("YYYY-MM-DD" format str): Get images posted only after this date.
            ending_date ("YYYY-MM-DD" format str): Get images posted only before this date.
            exit_when_empty (bool): Stop loading new batches when no result are found in one of the pages. Used only when you set a large interval_days and user always tweets at a high frequency.
            headless (bool): Hide browser window when browser is loaded.
        """

        super().__init__(
            station_url=station_url,
            crawler_settings=crawler_settings, 
            cookies=cookies,
        )
        self.user_id = user_id
        self.reload_times = reload_times
        self.error_retry_delay = error_retry_delay
        self.interval_days = interval_days
        self.starting_date = starting_date
        self.ending_date = ending_date
        self.exit_when_empty = exit_when_empty
        self.headless = headless

   
    def run(self) -> list[ImageInfo]:
        """
        The main function that runs the Parser and returns a list of :class:`image_crawler_utils.ImageInfo`.
        """
        if self.cookies.is_none():
            raise ValueError('Cookies cannot be empty!')
        self.generate_search_settings()
        self.get_status_from_urls()
        return self.parse_images_from_status()


    ##### Custom funcs
    

    # Generate search settings
    def generate_search_settings(self) -> list[TwitterSearchSettings]:
        if self.ending_date is None:
            self.ending_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if self.starting_date is None:
            self.starting_date = "2006-01-01"

        starting_datetime = datetime.datetime.strptime(self.starting_date, "%Y-%m-%d")
        ending_datetime = datetime.datetime.strptime(self.ending_date, "%Y-%m-%d")

        # Generate search time intervals
        interval_list = []
        interval_end = ending_datetime
        while True:
            interval_begin = interval_end - datetime.timedelta(days=self.interval_days)
            if interval_begin < starting_datetime:
                if self.starting_date == "2006-01-01":  # Beginning of Twitter / X date
                    interval_begin = None
                else:
                    interval_begin = starting_datetime

            interval_list.append([interval_begin, interval_end])
            interval_end = interval_end - datetime.timedelta(days=self.interval_days)
            if interval_end < starting_datetime:
                break

        # Generate TwitterSearchSettings list
        search_settings_list: list[TwitterSearchSettings] = []
        for interval in interval_list:
            search_settings = TwitterSearchSettings(
                from_users=self.user_id,
                only_media=True,
                starting_date=interval[0].strftime("%Y-%m-%d") if interval[0] is not None else '',
                ending_date=interval[1].strftime("%Y-%m-%d") if interval[1] is not None else '',
            )
            search_settings_list.append(search_settings)

        self.crawler_settings.log.info(f"{len(search_settings_list)} {'pages' if len(search_settings_list) > 1 else 'page'} will be loaded to detect status.")
        self.search_settings_list = search_settings_list
        return self.search_settings_list
    

    # Get all status from urls
    async def __get_status_from_urls_thread(
        self, 
        search_setting: TwitterSearchSettings,
        progress_group: ProgressGroup,
        thread_id: int,
    ) -> list[TwitterStatus]:
        browser = await set_up_nodriver_browser(
            proxies=self.crawler_settings.download_config.result_proxies,
            headless=self.headless,
            no_image_stylesheet=True,
        )
        await update_nodriver_browser_cookies(browser, self.cookies)
        search_str = search_setting.build_search_appending_str('')
        url = parse.quote(f'{self.station_url}search?q={search_str}&src=typed_query&f=live', safe='/:?=&')
        tab = await browser.get(url)
        self.crawler_settings.log.debug(f'Starting thread {thread_id + 1}/{len(self.search_settings_list)} to detect Twitter / X status from [repr.url]{url}[reset].', extra={"markup": True})
        result_status_list, media_count = await scrolling_to_find_status(
            tab=tab, 
            tab_url=url,
            crawler_settings=self.crawler_settings,
            reload_times=self.reload_times,
            error_retry_delay=self.error_retry_delay,
            progress_group=progress_group,
            transient=True,
        )
        browser.stop()
        self.crawler_settings.log.info(f'Finished thread {thread_id + 1}/{len(self.search_settings_list)} that detected from {search_setting.starting_date} to {search_setting.ending_date}. {len(result_status_list)} status & {media_count} {"images" if media_count > 1 else "image"} are detected.')
        return result_status_list
    

    def get_status_from_urls(self) -> list[TwitterStatus]:
        total_status_list: list[TwitterStatus] = []
        total_media_num = 0
        finished_num = 0
        self.crawler_settings.log.info("Loading searching pages to get media from status...")

        # Segment search_settings_list to prepare it for threading
        thread_num = self.crawler_settings.download_config.thread_num
        batched_search_settings_list = [self.search_settings_list[k * thread_num:min((k + 1) * thread_num, len(self.search_settings_list))] 
                                        for k in range((len(self.search_settings_list) - 1) // thread_num + 1)]
        
        exit_flag = False 
        with ProgressGroup(panel_title="Scrolling to Find [yellow]Status[reset]") as progress_group:
            task = progress_group.main_no_total_count_bar.add_task("Media image number:")

            for j in range(len(batched_search_settings_list)):
                # Get status using threading method
                thread_num = self.crawler_settings.download_config.thread_num
                with futures.ThreadPoolExecutor(thread_num) as executor:
                    thread_pool = [executor.submit(
                        nodriver.loop().run_until_complete, 
                        self.__get_status_from_urls_thread(
                            batched_search_settings_list[j][i],
                            progress_group,
                            j * thread_num + i,
                        ),
                    ) for i in range(len(batched_search_settings_list[j]))]
                    # Get result
                    for thread in futures.as_completed(thread_pool):
                        finished_num += 1
                        total_status_url_list = [status.status_url for status in total_status_list]

                        for status in thread.result():
                            if status.status_url not in total_status_url_list:
                                total_status_list.append(status)
                                total_media_num += len(status.media_list)

                                progress_group.main_no_total_count_bar.update(task, advance=len(status.media_list))

                        # Update search result
                        progress_group.main_no_total_count_bar.update(task, description=f'Got [repr.number]{finished_num}[reset] {"pages" if finished_num > 1 else "page"} & [repr.number]{len(total_status_list)}[reset] status with media image number:')
                        
                        # Exit when empty
                        if len(thread.result()) == 0 and self.exit_when_empty:
                            self.crawler_settings.log.debug("An empty page is detected. No new batches of page threads will be loaded.")
                            exit_flag = True

                # Check if media image num has exceeded capacity_count_config.image_num
                image_num = self.crawler_settings.capacity_count_config.image_num
                if (image_num is not None and total_media_num >= image_num):
                    self.crawler_settings.log.info(f"Collected {total_media_num} media {'images have' if total_media_num > 1 else 'image has'} exceeded the restrictions on image num ({image_num} {'images' if image_num > 1 else 'image'}).")
                    break

                if exit_flag:
                    self.crawler_settings.log.info(f"As empty pages are detected, no new pages will be loaded to detect status.")
                    break
            
        
            progress_group.main_no_total_count_bar.update(task, description=f'[green]Finished finding status![reset] Got [repr.number]{finished_num}[reset] {"pages" if finished_num > 1 else "page"} & [repr.number]{len(total_status_list)}[reset] status with media image number:')

        self.crawler_settings.log.info(f"Finished getting status. {len(total_status_list)} status {'are' if len(total_status_list) > 1 else 'is'} fetched.")

        total_status_list.sort(reverse=True)  # Sort by status_id from large to small
        self.status_list = total_status_list
        return self.status_list
    

    # Parse images from status
    def parse_images_from_status(self) -> list[ImageInfo]:
        self.crawler_settings.log.info("Parsing image info from collected status...")

        image_info_list = []
        for status in self.status_list:
            for image in status.media_list:
                image_info_list.append(ImageInfo(
                    url=image.image_source,
                    name=image.image_name,
                    info=dataclasses.asdict(status),
                ))

        if self.crawler_settings.capacity_count_config.image_num is not None:  # Get only image_num images
            image_info_list = image_info_list[:self.crawler_settings.capacity_count_config.image_num]
        self.crawler_settings.log.info(f"Image info parsed. {len(image_info_list)} {'images' if len(image_info_list) > 1 else 'image'} collected.")
        self.image_info_list = image_info_list
        return self.image_info_list
