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
    info: dict = dataclasses.field(default_factory=lambda: {})  # Info should be a dict
    backup_urls: Iterable[str] = dataclasses.field(default_factory=lambda: [])

    
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
    Save the ImageInfo list into a json file.
    ONLY WORKS IF the info can be JSON serialized.

    Parameters:
        image_info_list (list of image_crawler_utils.ImageInfo): A list of ImageInfo.
        json_file (str): Name / path of json file. Suffix (.json) is optional.
        encoding (str): Encoding of JSON file.
        display_progress (bool): Display a progress bar when running. Progress bar will be hidden after finishing.
        log (crawler_utils.log.Log, optional): Logging config.
        
    Returns:
        (Saved file name, Absolute path of the saved file), or None if failed.
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
                f_name = f_name.replace(".json.json", ".json")  # If .json is already contained in json_file, skip it
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
            f_name = f_name.replace(".json.json", ".json")  # If .json is already contained in json_file, skip it
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
    Load the ImageInfo list from a json file.
    ONLY WORKS IF the info can be JSON serialized.

    Parameters:
        json_file (str): Name / path of json file.
        encoding (str): Encoding of JSON file.
        display_progress (bool): Display a progress bar when running. Progress bar will be hidden after finishing.
        log (crawler_utils.log.Log, optional): Logging config.

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
