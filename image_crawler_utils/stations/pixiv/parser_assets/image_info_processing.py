from image_crawler_utils import ImageInfo
from image_crawler_utils.keyword import construct_keyword_tree



# Keyword Filter for pixiv
def filter_keyword_pixiv(image_info: ImageInfo, standard_keyword_string: str):
    """
    A keyword filter for xxxbooru-style image info.

    The "tags" should be accessed by info["tags"].

    Args:
        image_info (image_crawler_utils.ImageInfo): list of ImageInfo
        standard_keyword_string (str): A standard-syntax keyword string.
    """

    keyword_tree = construct_keyword_tree(standard_keyword_string)
    return keyword_tree.keyword_list_check(image_info.info['tags'])
