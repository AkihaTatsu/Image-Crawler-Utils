import os
from typing import Optional, Union, Callable
from collections.abc import Iterable

import dill
import traceback
from concurrent import futures
import requests
from rich import print, markup
from rich.progress import SpinnerColumn

from image_crawler_utils import Cookies, CrawlerSettings
from image_crawler_utils.image_downloader import download_image_from_url
from image_crawler_utils.progress_bar import ProgressGroup
from image_crawler_utils.utils import check_dir
from image_crawler_utils.log import Log

from .image_info import ImageInfo



class Downloader:
    """
    Downloading images using threading method.

    Args:
        crawler_settings (image_crawler_utils.CrawlerSettings): The CrawlerSettings used in this Downloader.
        image_info_list (image_crawler_utils.ImageInfo): A list of ImageInfo.
        store_path (str): Path to store images, or a list of storage paths respectively for every image.

            + Default is the current working directory.
            + If it set to an iterable list, then its length should be the same as ``image_info_list``.

        image_info_filter (callable, bool): A callable function used to filter the images in the list of ImageInfo.

            + The function of ``image_info_filter`` should only accept 1 argument of ImageInfo type and returns `True` (download this image) or `False` (do not download this image), like:
            
                .. code-block:: python

                    def filter_func(image_info: ImageInfo) -> bool:
                        # Meet the conditions
                        return True
                        # Do not meet the conditions
                        return False
            
            + If the function have other parameters, use ``lambda`` to exclude other parameters:
            
                .. code-block:: python

                    image_info_filter=lambda info: filter_func(info, param1, param2, ...)
            
            + If you want to download all images in the ImageInfo list, set ``image_info_filter`` to :py:data:`True`.
            + **TIPS**: If you want to search images with complex restrictions that the image station sites may not support (e.g. Images with many keywords and restrictions on the ratio between width and height), you can simplify the query with some keywords to get all images with Parsers, and filter them with your custom ``image_info_filter`` function.

        cookies (image_crawler_utils.Cookies, str, dict, list, None): Cookies used to access images from a website.

            + :py:data:`None` means no cookies and works the same as ``Cookies()``.
            + Leave this parameter blank works the same as :py:data:`None` / ``Cookies()``.
            + **TIPS**: You can add corresponding cookies to Downloader if there are URLs of images only accessible with an account. For example, if you have saved Pixiv and Twitter / X cookies respectively in ``Pixiv_cookies.json`` and ``Twitter_cookies.json``, then you can use ``cookies=Cookies.load_from_json("Pixiv_cookies.json") + Cookies.load_from_json("Twitter_cookies.json")`` to add both cookies to the Downloader.
    """

    def __init__(
        self,
        image_info_list: Iterable[ImageInfo],
        crawler_settings: CrawlerSettings=CrawlerSettings(),
        store_path: Union[str, Iterable[str]]='./',
        image_info_filter: Union[Callable, bool]=True,
        cookies: Optional[Union[Cookies, list, dict, str]]=Cookies(),
    ):
        
        self.crawler_settings = crawler_settings
        self.image_info_list = image_info_list
        if isinstance(store_path, str):
            self.store_path = store_path + ('/' if not store_path.endswith('/') else '')
        else:
            if len(store_path) != len(image_info_list):
                raise ValueError(f'The length of store_path ({len(store_path)}) should be the same as the length of image_info_list ({len(image_info_list)}).')
            self.store_path = [path + ('/' if not path.endswith('/') else '') for path in store_path]
        self.image_info_filter = image_info_filter
        if isinstance(cookies, Cookies):
            self.cookies = cookies
        else:
            self.cookies = Cookies(cookies)


    def run(self) -> tuple[int, list[ImageInfo], list[ImageInfo], list[ImageInfo]]:
        """
        Run the Threading Downloader Object.
        
        Returns:
            (Total size of image downloaded, Succeeded ImageInfo list, Failed ImageInfo list, Skipped ImageInfo list)

                + **Total size of image downloaded**: An int denoting the total size (in bytes) of images downloaded.
                + **Succeeded ImageInfo list**: A list of ImageInfo containing successfully downloaded images.
                + **Failed ImageInfo list**: A list of ImageInfo containing images failed to be downloaded.

                    + Images not downloaded due to reaching ``capacity`` defined in :class:`image_crawler_utils.CrawlerSettings` will be classified to this list.

                + **Skipped ImageInfo list**: A list of ImageInfo containing images skipped.
                
                    + Images filtered out by ``image_info_filter``, not downloaded due to the restriction of ``image_num`` in :class:`image_crawler_utils.CrawlerSettings`, and skipped due to such images already exist when ``overwrite_images`` in DownloadConfig is set to :py:data:`False` will be classified to this list.
        """

        # Filter image info list
        download_num, filtered_ordinals_list, skipped_ordinals_list = self.__filter_ordinals_list()
        
        # Download images
        download_traffic, succeeded_ordinals_list, failed_ordinals_list = self.__download_images(download_num, filtered_ordinals_list)

        # Conclude
        self.crawler_settings.log.info(f"{len(succeeded_ordinals_list)} succeeded ({download_traffic / 2**20:.2f} MB in total), {len(failed_ordinals_list)} failed, {len(skipped_ordinals_list)} skipped.")

        # Convert ordinal list into ImageInfo list
        succeeded_image_info_list = [self.image_info_list[i] for i in succeeded_ordinals_list]
        failed_image_info_list = [self.image_info_list[i] for i in failed_ordinals_list]
        skipped_image_info_list = [self.image_info_list[i] for i in skipped_ordinals_list]
        return download_traffic, succeeded_image_info_list, failed_image_info_list, skipped_image_info_list
    

    def save_to_pkl(
        self, 
        pkl_file: str,
    ) -> Optional[tuple[str, str]]:
        """
        Save the Downloader with settings in a pkl file. 

        Args:
            path (str): Path to save the pkl file. Default is saving to the current path.
            pkl_file (str, None): Name of the pkl file. (Suffix is optional.)

        Returns:
            (Saved file name, Absolute path of the saved file), or None if failed.
        """

        path, filename = os.path.split(pkl_file)
        check_dir(path, self.crawler_settings.log)
        f_name = os.path.join(path, f"{filename}.pkl")
        f_name = f_name.replace(".pkl.pkl", ".pkl")  # If .pkl is already contained in pkl_file, skip it

        try:
            with open(f_name, "wb") as f:
                dill.dump(self, f)
                self.crawler_settings.log.info(f'{type(self).__name__} has been dumped into [repr.filename]{markup.escape(os.path.abspath(f_name))}[reset]', extra={"markup": True})
                return f_name, os.path.abspath(f_name)
        except Exception as e:
            self.crawler_settings.log.error(f'Failed to dump {type(self).__name__} into [repr.filename]{markup.escape(os.path.abspath(f_name))}[reset] because {e}\n{traceback.format_exc()}', extra={"markup": True})
            return None
        
    
    @classmethod
    def load_from_pkl(
        cls,
        pkl_file: str,
        log: Log=Log(),
    ) -> CrawlerSettings:
        """
        Load parser from .pkl file.

        Args:
            pkl_file (str, None): Name of the pkl file.
            log (image_crawler_utils.log.Log, None): Logging config.

        Returns:
            A CrawlerSettings class loaded from pkl file, or None if failed.
        """
        
        try:
            with open(pkl_file, "rb") as f:
                cls = dill.load(f)
                log.info(f'{type(cls).__name__} has been successfully loaded from [repr.filename]{markup.escape(os.path.abspath(pkl_file))}[reset]', extra={"markup": True})
            return cls
        except Exception as e:
            log.error(f'Failed to load {type(cls).__name__} from [repr.filename]{markup.escape(os.path.abspath(pkl_file))}[reset] because {e}\n{traceback.format_exc()}', extra={"markup": True})
            return None
    

    # Filter image info list
    def __filter_ordinals_list(self) -> tuple[int, list[ImageInfo], list[ImageInfo]]:
        # Filter iamges
        filtered_ordinals_list: list[int] = []
        skipped_ordinals_list: list[int] = []
        for i in range(len(self.image_info_list)):
            item = self.image_info_list[i]
            if type(self.image_info_filter) is bool and self.image_info_filter:
                filtered_ordinals_list.append(i)
            elif callable(self.image_info_filter) and self.image_info_filter(item):
                filtered_ordinals_list.append(i)
            else:
                skipped_ordinals_list.append(i)
        if len(skipped_ordinals_list) > 0:
            self.crawler_settings.log.info(f"{len(skipped_ordinals_list)} {'images' if len(skipped_ordinals_list) > 1 else 'image'} will be skipped because {'these images are' if len(skipped_ordinals_list) > 1 else 'this image is'} filtered out by image_info_filter.")

        # Skip downloaded images if set in download_config
        existed_ordinals_list = []
        if self.crawler_settings.download_config.overwrite_images is False:
            for ord in filtered_ordinals_list:
                if isinstance(self.store_path, str):  # Single store path
                    image_path = os.path.join(self.store_path, self.image_info_list[ord].name)
                else:  # List of store paths
                    image_path = os.path.join(self.store_path[ord], self.image_info_list[ord].name)
                if os.path.exists(image_path):
                    existed_ordinals_list.append(ord)
                    self.crawler_settings.log.debug(f"{image_path} exists and will be skipped.")
        for ord in existed_ordinals_list:
            filtered_ordinals_list.remove(ord)
            skipped_ordinals_list.append(ord)
        filtered_ordinals_list.sort()  # Sort ordinals from small to large
        skipped_ordinals_list.sort()  # Sort ordinals from small to large
        if len(existed_ordinals_list) > 0:
            self.crawler_settings.log.info(f"{len(existed_ordinals_list)} {'images' if len(existed_ordinals_list) > 1 else 'image'} will be skipped because {'these images have' if len(existed_ordinals_list) > 1 else 'this image has'} existed.")
        
        # Calc download image num
        total_num = len(filtered_ordinals_list)
        download_num = total_num if self.crawler_settings.capacity_count_config.image_num is None else min(total_num, self.crawler_settings.capacity_count_config.image_num)
        # Move image num over download_num into skipped_ordinals_list
        skipped_ordinals_list.extend(filtered_ordinals_list[download_num:])
        skipped_ordinals_list.sort()  # Sort ordinals from small to large
        filtered_ordinals_list = filtered_ordinals_list[:download_num]
        return download_num, filtered_ordinals_list, skipped_ordinals_list
    

    # Download images
    def __download_images(self, download_num: int, filtered_ordinals_list: list[ImageInfo]) -> tuple[float, list[ImageInfo], list[ImageInfo]]:
        if download_num <= 0:
            self.crawler_settings.log.warning(f"No images are to be downloaded.")
            return 0, [], []

        if isinstance(self.store_path, str):  # Single store path
            check_dir(self.store_path, self.crawler_settings.log)
            self.crawler_settings.log.info(f'Images will be saved at [repr.filename]{markup.escape(os.path.abspath(self.store_path))}[reset]', extra={"markup": True})
        else:  # List of store paths
            for ord in filtered_ordinals_list:
                check_dir(self.store_path[ord], self.crawler_settings.log)
            self.crawler_settings.log.info(f'Images will be saved at paths specified in the iterable store_path.')

        self.crawler_settings.log.info("Starting image downloading.", output_msg="========== Start Image Downloading ==========")
        self.crawler_settings.log.info(f"Total downloading num: {download_num}")
        download_traffic = 0
        succeeded_id = []

        # Start downloading
        with ProgressGroup(panel_title="Downloading [cyan]Images[reset]") as progress_group:
            progress_group.sub_count_bar.columns = (SpinnerColumn(), *progress_group.sub_count_bar.columns)  # Add a spinner to its left
            task = progress_group.main_count_bar.add_task("Downloading:", total=download_num)

            undone_ids = list(range(download_num))
            failed_ids = []
            fail_count = [0] * download_num
            shutdown_flag = False
                    
            with requests.Session() as session:
                if not self.cookies.is_none():
                    session.cookies.update(self.cookies.cookies_dict)
                while len(undone_ids) > 0:
                    # Threading current undone ids
                    with futures.ThreadPoolExecutor(self.crawler_settings.download_config.thread_num) as executor:
                        
                        if isinstance(self.store_path, str):  # Single store path
                            download_thread_pool = [executor.submit(
                                download_image_from_url, 
                                self.image_info_list[filtered_ordinals_list[i]].url if fail_count[i] == 0 else self.image_info_list[filtered_ordinals_list[i]].backup_urls[fail_count[i] - 1],
                                self.image_info_list[filtered_ordinals_list[i]].name,
                                self.crawler_settings.download_config,
                                self.crawler_settings.log,
                                self.store_path,
                                session,
                                progress_group,
                                i,
                                None,
                            ) for i in undone_ids]
                        else:  # List of store paths
                            download_thread_pool = [executor.submit(
                                download_image_from_url, 
                                self.image_info_list[filtered_ordinals_list[i]].url if fail_count[i] == 0 else self.image_info_list[filtered_ordinals_list[i]].backup_urls[fail_count[i] - 1],
                                self.image_info_list[filtered_ordinals_list[i]].name,
                                self.crawler_settings.download_config,
                                self.crawler_settings.log,
                                self.store_path[filtered_ordinals_list[i]],
                                session,
                                progress_group,
                                i,
                                None,
                            ) for i in undone_ids]

                        for thread in futures.as_completed(download_thread_pool):
                            if thread.result()[0] > 0:
                                # Successful download
                                succeeded_n = thread.result()[1]
                                download_traffic += thread.result()[0]
                                succeeded_id.append(succeeded_n)
                                undone_ids.remove(succeeded_n)
                                progress_group.main_count_bar.update(task, advance=1, description=f"Downloading [repr.number]{download_traffic / 2**20:.2f}[reset] MB:")
                            else:
                                # Failed download
                                download_traffic += thread.result()[0]
                                failed_n = thread.result()[1]
                                fail_count[failed_n] += 1

                                # If there are backup URLs, record it
                                if len(self.image_info_list[filtered_ordinals_list[failed_n]].backup_urls) >= fail_count[failed_n]:
                                    self.crawler_settings.log.info(f"Found other URLs, putting [repr.filename]{markup.escape(self.image_info_list[filtered_ordinals_list[failed_n]].name)}[reset] into downloading queue again.", extra={"markup": True})
                                    if failed_n not in failed_ids:
                                        failed_ids.append(failed_n)
                                else:
                                    progress_group.main_count_bar.update(task, advance=1, description=f"Downloading [repr.number]{download_traffic / 2**20:.2f}[reset] MB:")
                                    # Remove from failed_ids recording
                                    if failed_n in failed_ids:
                                        failed_ids.remove(failed_n)
                                    undone_ids.remove(failed_n)

                            if self.crawler_settings.capacity_count_config.capacity is not None and download_traffic > self.crawler_settings.capacity_count_config.capacity:
                                self.crawler_settings.log.warning("Downloading capacity reached!")
                                executor.shutdown(wait=False, cancel_futures=True)
                                undone_ids = []
                                failed_ids = []
                                shutdown_flag = True
                                break
            
            if shutdown_flag:  # Interrupted!
                progress_group.main_count_bar.update(task, description=f"[red]Downloading interrupted! [repr.number]{download_traffic / 2**20:.2f}[reset] MB:")
            else:  # Finished normally, set progress bar to finished state
                progress_group.main_count_bar.update(task, description=f"[green]Downloading finished! [repr.number]{download_traffic / 2**20:.2f}[reset] MB:")

        succeeded_ordinals_list = [filtered_ordinals_list[i] 
                                   for i in succeeded_id]
        failed_ordinals_list = [filtered_ordinals_list[i] 
                                for i in range(len(filtered_ordinals_list)) if i not in succeeded_id]
        
        # Remove .tmp files
        if isinstance(self.store_path, str):
            for root, dirs, files in os.walk(self.store_path):
                for name in files:
                    if os.path.splitext(name)[1] == '.tmp':
                        os.remove(os.path.join(self.store_path, name))
        else:
            for path in self.store_path:
                for root, dirs, files in os.walk(path):
                    for name in files:
                        if os.path.splitext(name)[1] == '.tmp':
                            os.remove(os.path.join(self.store_path, name))

        self.crawler_settings.log.info("Image downloading completed.", output_msg="========== Image Downloading Complete ==========")

        return download_traffic, succeeded_ordinals_list, failed_ordinals_list
    

    ##### Not directly related to downloading


    # Display all config
    def display_all_configs(self):
        """
        Display all config info.
        Dataclasses will be displayed in a neater way.
        """
        
        print("========== Current Downloader Config ==========")

        print('\nBasic Info:')
        try:
            print(f"  + Image info filter: {self.image_info_filter}")
            print(f"  + Store path: [repr.filename]{markup.escape(self.store_path)}[reset]")
            print(f"  + Absolute store path: [repr.filename]{markup.escape(os.path.abspath(self.store_path))}[reset]")
        except Exception as e:
            print(f"Basic Info missing because {e}!\n{traceback.format_exc()}", "error")

        print('\nImage downloading info:')
        try:
            download_num, filtered_ordinals_list, skipped_ordinals_list = self.__filter_ordinals_list()
            print(f"  + Number of images to be downloaded: {len(filtered_ordinals_list)}")
        except Exception as e:
            print(f"Image downloading info has an error because {e}!\n{traceback.format_exc()}", "error")

        print('')
        print("CrawlerSettings used:")
        self.crawler_settings.display_all_configs()
            
        print('')
        print("========== Config Display Ending ==========")
