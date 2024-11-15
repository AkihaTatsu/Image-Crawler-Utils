import dataclasses
import pathvalidate
import json, os, traceback
from typing import Iterable, Optional

from image_crawler_utils.log import Log
from image_crawler_utils.utils import check_dir



##### Classes


@dataclasses.dataclass
class ImageInfo:
    """
    A pack of image url, name, info and filter.
    Can be used to download images and write result to files.

    Parameters:
        url (str): URL of the image.
        name (str): Name of the image to be stored.
        info (dict): The info of the image.
        backup_urls (Iterable(str)): If the original url fails, use these urls instead.
    """

    url: str
    name: str
    info: dict  # Info should be a dict
    backup_urls: Iterable[str] = dataclasses.field(default_factory=lambda: [])

    
    # Remove invalid char
    def __post_init__(self):
        self.name = pathvalidate.sanitize_filename(self.name, replacement_text="_")


##### Functions


def save_image_infos(
    image_info_list: Iterable[ImageInfo], 
    json_file: str,
    log: Log=Log(),
) -> Optional[tuple[str, str]]:
    """
    Save the ImageInfo list into a json file.
    ONLY WORKS IF the info can be JSON serialized.

    Parameters:
        image_info_list (list of image_crawler_utils.ImageInfo): A list of ImageInfo.
        json_file (str): Name / path of json file. Suffix (.json) is optional.
        log (crawler_utils.log.Log, optional): Logging config.
        
    Returns:
        (Saved file name, Absolute path of the saved file), or None if failed.
    """
    
    dict_list = [dataclasses.asdict(image_info) for image_info in image_info_list]
    path, filename = os.path.split(json_file)
    check_dir(path, log)
    f_name = os.path.join(path, f"{filename}.json")
    f_name = f_name.replace(".json.json", ".json")  # If .json is already contained in json_file, skip it
    try:
        with open(f_name, "w", encoding='UTF-8') as f:
            json.dump(dict_list, f, indent=4, ensure_ascii=False)
            log.info(f'The list of ImageInfo has been saved at "{os.path.abspath(f_name)}"')
            return f_name, os.path.abspath(f_name)
    except Exception as e:
        log.error(f'Failed to save the list of ImageInfo at "{os.path.abspath(f_name)}" because {e}\n{traceback.format_exc()}')
        return None


def load_image_infos(
    json_file: str,
    log: Log=Log(),
) -> Optional[list[ImageInfo]]:
    """
    Load the ImageInfo list from a json file.
    ONLY WORKS IF the info can be JSON serialized.

    Parameters:
        json_file (str): Name / path of json file.
        log (crawler_utils.log.Log, optional): Logging config.

    Returns:
        List of ImageInfo, or None if failed.
    """
    
    try:
        with open(json_file, "r", encoding='UTF-8') as f:
            dict_list = json.load(f)

        image_info_list = [ImageInfo(
            url=item["url"],
            backup_urls=item["backup_urls"],
            name=item["name"],
            info=item["info"],
        ) for item in dict_list]

        log.info(f'The list of ImageInfo has been loaded from "{os.path.abspath(json_file)}"')
        return image_info_list
        
    except Exception as e:
        log.error(f'Failed to load the list of ImageInfo from "{os.path.abspath(json_file)}" because {e}\n{traceback.format_exc()}')
        return None
