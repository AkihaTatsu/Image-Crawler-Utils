import dataclasses
import pathvalidate
import json, os, traceback
from typing import Iterable, Optional
from rich import markup

from image_crawler_utils.log import Log
from image_crawler_utils.progress_bar import CustomProgress
from image_crawler_utils.utils import check_dir



##### Classes


@dataclasses.dataclass
class ImageInfo:
    """
    A class consisting of image URL, name, info and back up URLs.
    
    Can be used to download images and write result to files.
    """

    url: str
    """The URL used AT FIRST in downloading the image."""
    name: str
    """Name of the image when saved."""
    info: dict = dataclasses.field(default_factory=lambda: {})  # Info should be a dict
    """
    A :py:class:`dict`, containing information of the image.

        + ``info`` will not affect Downloader directly. It only works if you set the ``image_info_filter`` parameter in the Downloader class.
        + Different sites may have different ``info`` structures which are defined respectively by their Parsers.
        + **ATTENTION:** If you define you own ``info`` structure, please ENSURE it can be JSON-serialized (e.g. The values of the :py:class:`dict` should be ``int``, ``float``, :py:class:`str`, :py:class:`list`, :py:class:`dict`, etc.) in order to make it compatible with ``save_image_infos()`` and ``load_image_infos()``.
    """
    backup_urls: Iterable[str] = dataclasses.field(default_factory=lambda: [])
    """When downloading from ``.url`` failed, try downloading from URLs in the list of ``.backup_urls``."""

    
    # Remove invalid char
    def __post_init__(self):
        self.name = pathvalidate.sanitize_filename(self.name, replacement_text="_")


##### Functions


def save_image_infos(
    image_info_list: Iterable[ImageInfo], 
    json_file: str,
    encoding: str='UTF-8',
    display_progress: bool=True,
    log: Log=Log(),
) -> Optional[tuple[str, str]]:
    """
    Save the ImageInfo list into a JSON file.

    ONLY WORKS IF the info can be JSON serialized.

    Args:
        image_info_list (Iterable[image_crawler_utils.ImageInfo]): An iterable list (e.g. :py:class:`list` or :py:class:`tuple`) of :class:`image_crawler_utils.ImageInfo`.
        json_file (str): Name / Path of the JSON file. Suffix (.json) is optional.
        encoding (str): Encoding of the JSON file.
        display_progress (bool): Display a ``rich`` progress bar when running. Progress bar will be hidden after finishing.
        log (image_crawler_utils.log.Log, None): Logging config.
        
    Returns:
        (Saved file name, Absolute path of the saved file), or :py:data:`None` if failed.
    """
    
    try:
        if display_progress:
            with CustomProgress(has_spinner=True, transient=True) as progress:
                task = progress.add_task(description="Converting ImageInfo to dict:", total=3)
                dict_list = [
                    dataclasses.asdict(image_info) 
                    for image_info in progress.track(image_info_list, description="Converting ImageInfo...")
                ]

                progress.update(task, description="Dumping dict list into JSON:", advance=1)
                dict_list_data = json.dumps(dict_list, indent=4, ensure_ascii=False).encode(encoding)

                progress.update(task, description="Saving into a JSON file:", advance=1)
                path, filename = os.path.split(json_file)
                check_dir(path, log)
                f_name = os.path.join(path, f"{filename}.json")
                f_name = f_name.replace(".json.json", ".json")  # If .JSON is already contained in json_file, skip it
                with open(f_name, mode="wb") as f:
                    f.write(dict_list_data)
                log.info(f'The list of ImageInfo has been saved at [repr.filename]{markup.escape(os.path.abspath(f_name))}[reset]', extra={"markup": True})
                progress.update(task, description="[green]ImageInfo successfully saved!", advance=1)
        else:
            dict_list = [
                dataclasses.asdict(image_info) 
                for image_info in image_info_list
            ]

            dict_list_data = json.dumps(dict_list, indent=4, ensure_ascii=False).encode(encoding)

            path, filename = os.path.split(json_file)
            check_dir(path, log)
            f_name = os.path.join(path, f"{filename}.json")
            f_name = f_name.replace(".json.json", ".json")  # If .JSON is already contained in json_file, skip it
            with open(f_name, mode="wb") as f:
                f.write(dict_list_data)
            log.info(f'The list of ImageInfo has been saved at [repr.filename]{markup.escape(os.path.abspath(f_name))}[reset]', extra={"markup": True})

        return f_name, os.path.abspath(f_name)
    except Exception as e:
        log.error(f'Failed to save the list of ImageInfo at [repr.filename]{markup.escape(os.path.abspath(f_name))}[reset] because {e}\n{traceback.format_exc()}', extra={"markup": True})
        return None


def load_image_infos(
    json_file: str,
    encoding: str='UTF-8',
    display_progress: bool=True,
    log: Log=Log(),
) -> Optional[list[ImageInfo]]:
    """
    Load the ImageInfo list from a JSON file.
    
    ONLY WORKS IF the info can be JSON serialized.

    Args:
        json_file (str): Name / Path of the JSON file.
        encoding (str): Encoding of the JSON file.
        display_progress (bool): Display a ``rich`` progress bar when running. Progress bar will be hidden after finishing.
        log (image_crawler_utils.log.Log, None): Logging config.

    Returns:
        List of ImageInfo, or None if failed.
    """
    
    try:
        if display_progress:
            with CustomProgress(has_spinner=True, transient=True) as progress:
                task = progress.add_task(description="Loading JSON file:", total=3)
                with open(json_file, mode="rb") as f:
                    file_data = f.read()

                progress.update(task, description="Parsing JSON from loaded data:", advance=1)            
                dict_list = json.loads(file_data.decode(encoding))
                
                progress.update(task, description="Parsing ImageInfo from JSON data:", advance=1)
                image_info_list = [ImageInfo(
                    url=item["url"],
                    backup_urls=item["backup_urls"],
                    name=item["name"],
                    info=item["info"],
                ) for item in progress.track(dict_list, description="Parsing ImageInfo...")]
                progress.update(task, description="[green]ImageInfo successfully loaded!", advance=1)
        else:
            with open(json_file, mode="rb") as f:
                file_data = f.read()

            dict_list = json.loads(file_data.decode(encoding))
            
            image_info_list = [ImageInfo(
                url=item["url"],
                backup_urls=item["backup_urls"],
                name=item["name"],
                info=item["info"],
            ) for item in dict_list]

        log.info(f'The list of ImageInfo has been loaded from [repr.filename]{markup.escape(os.path.abspath(json_file))}[reset]', extra={"markup": True})
        return image_info_list

    except Exception as e:
        log.error(f'Failed to load the list of ImageInfo from [repr.filename]{markup.escape(os.path.abspath(json_file))}[reset] because {e}\n{traceback.format_exc()}', extra={"markup": True})
        return None
