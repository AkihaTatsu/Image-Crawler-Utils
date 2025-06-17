import dataclasses
from typing import Optional
import time

from image_crawler_utils.log import print_logging_msg



# No, I don't have a premium account so I won't add features that can only be accessed by premium account.
@dataclasses.dataclass
class PixivSearchSettings:
    """
    Search settings for Pixiv.
    """

    age_rating: str = "all"
    """Age rating. MUST be selected from "all", "safe" and "r18"."""
    order: str = "newest"
    """Order of images. MUST be selected from "newest" and "oldest"."""
    target_illust: bool = True
    """Whether to include illustrations in results."""
    target_manga: bool = True
    """Whether to include mangas in results."""
    target_ugoira: bool = True
    """
    Whether to include ugoiras (animations) in results.
    
        + Cannot set ``target_illust``, ``target_manga`` and ``target_ugoira`` to :py:data:`False` at the same time.
        + Cannot set only one of ``target_illust`` and ``target_ugoira`` to :py:data:``False`` with the rest set to ``True`` at the same time.  
    """
    tags_match_type: str = "partial"
    """
    Matching type of tags. MUST be selected from "partial", "perfect", "title_caption".

        + "partial": Partially matched tags are accepted.
        + "perfect": Tags must be perfectly matched.
        + "title_caption": Searched keywords will be matched with titles and captions.
    """
    display_ai: bool = True
    """Whether to display AI-generated images."""
    width_lowest: Optional[int] = None
    """Lowest width (in pixels) of images. Default is None (no restrictions)."""
    width_highest: Optional[int] = None
    """Highest width (in pixels) of images. Default is None (no restrictions)."""
    height_lowest: Optional[int] = None
    """Lowest height (in pixels) of images. Default is None (no restrictions)."""
    height_highest: Optional[int] = None
    """Highest height (in pixels) of images. Default is None (no restrictions)."""
    ratio: Optional[float] = None
    """
    Ratio of images. Default is None (no restrictions).

        + Set to 0 means select only square images.
        + Set to positive means select horizontal images. For example, ratio=0.5 means selecting images with width / height >= 1 + 0.5 = 1.5
        + Set to negative means select vertical images. For example, ratio=-0.5 means selecting images with height / width >= 1 + 0.5 = 1.5
    """
    creation_tool: str = "all"
    """
    Creation tool of images. Default is "all".
    
    Can be one of these strings: 

    .. collapse:: CLICK HERE TO DISPLAY

        .. code-block::

            'all'
            'sai'
            'photoshop'
            'clip studio paint'
            'illuststudio'
            'comicstudio'
            'pixia'
            'azpainter2'
            'painter'
            'illustrator'
            'gimp'
            'firealpaca'
            'oekaki bbs'
            'azpainter'
            'cgillust'
            'oekaki chat'
            'tegaki blog'
            'ms_paint'
            'pictbear'
            'opencanvas'
            'paintshoppro'
            'edge'
            'drawr'
            'comicworks'
            'azdrawing'
            'sketchbookpro'
            'photostudio'
            'paintgraphic'
            'medibang paint'
            'nekopaint'
            'inkscape'
            'artrage'
            'azdrawing2'
            'fireworks'
            'ibispaint'
            'aftereffects'
            'mdiapp'
            'graphicsgale'
            'krita'
            'kokuban.in'
            'retas studio'
            'e-mote'
            '4thpaint'
            'comilabo'
            'pixiv sketch'
            'pixelmator'
            'procreate'
            'expression'
            'picturepublisher'
            'processing'
            'live2d'
            'dotpict'
            'aseprite'
            'pastela'
            'poser'
            'metasequoia'
            'blender'
            'shade'
            '3dsmax'
            'daz studio'
            'zbrush'
            'comi po!'
            'maya'
            'lightwave3d'
            'hexagon king'
            'vue'
            'sketchup'
            'cinema4d'
            'xsi'
            'carrara'
            'bryce'
            'strata'
            'sculptris'
            'modo'
            'animationmaster'
            'vistapro'
            'sunny3d'
            '3d-coat'
            'paint 3d'
            'vroid studio'
            'mechanical pencil'
            'pencil'
            'ballpoint pen'
            'thin marker'
            'colored pencil'
            'copic marker'
            'dip pen'
            'watercolors'
            'brush'
            'calligraphy pen'
            'felt-tip pen'
            'magic marker'
            'watercolor brush'
            'paint'
            'acrylic paint'
            'fountain pen'
            'pastels'
            'airbrush'
            'color ink'
            'crayon'
            'oil paint'
            'coupy pencil'
            'gansai'
            'pastel crayons'
    """
    starting_date: str = ''
    """Search images uploaded after this date. MUST be "YYYY-MM-DD", "YYYY.MM.DD" or "YYYY/MM/DD" format."""
    ending_date: str = ''
    """Search images uploaded before this date. MUST be "YYYY-MM-DD", "YYYY.MM.DD" or "YYYY/MM/DD" format."""


    def __post_init__(self):
        self.age_rating = self.age_rating.lower()
        self.tags_match_type = self.tags_match_type.lower()
        self.creation_tool = self.creation_tool.lower()
        self.starting_date = self.starting_date.lower()
        self.ending_date = self.ending_date.lower()

        if not self.target_illust and not self.target_manga and not self.target_ugoira:
            print_logging_msg(f'There must be at least one target of searching. Set to the default of searching all.', 'warning')
            self.target_illust = True
            self.target_manga = True
            self.target_ugoira = True
        elif (self.target_manga and self.target_illust and not self.target_ugoira) or (self.target_manga and self.target_ugoira and not self.target_illust):
            print_logging_msg(f'You cannot search only one of illustrations and ugoira (animations) with manga at the same time. Set to the default of searching all.', 'warning')
            self.target_illust = True
            self.target_manga = True
            self.target_ugoira = True

        if self.age_rating not in ["all", "safe", "r18"]:
            print_logging_msg(f'{self.order} is not one of {str(["all", "safe", "r18"])}! It will be set to default ("all").', 'warning')
            self.tags_match_type = "all"

        if self.order not in ["newest", "oldest"]:
            print_logging_msg(f'{self.order} is not one of {str(["newest", "oldest"])}! It will be set to default ("newest").', 'warning')
            self.tags_match_type = "newest"

        if self.tags_match_type not in ["partial", "perfect", "title_caption"]:
            print_logging_msg(f'{self.order} is not one of {str(["partial", "perfect", "title_caption"])}! It will be set to default ("partial").', 'warning')
            self.tags_match_type = "partial"

        if self.creation_tool not in [
            'all', 'sai', 'photoshop', 'clip studio paint', 'illuststudio', 'comicstudio', 'pixia', 'azpainter2', 'painter', 'illustrator', 'gimp', 'firealpaca', 'oekaki bbs', 'azpainter', 'cgillust', 'oekaki chat', 'tegaki blog', 'ms_paint', 'pictbear', 'opencanvas', 'paintshoppro', 'edge', 'drawr', 'comicworks', 'azdrawing', 'sketchbookpro', 'photostudio', 'paintgraphic', 'medibang paint', 'nekopaint', 'inkscape', 'artrage', 'azdrawing2', 'fireworks', 'ibispaint', 'aftereffects', 'mdiapp', 'graphicsgale', 'krita', 'kokuban.in', 'retas studio', 'e-mote', '4thpaint', 'comilabo', 'pixiv sketch', 'pixelmator', 'procreate', 'expression', 'picturepublisher', 'processing', 'live2d', 'dotpict', 'aseprite', 'pastela', 'poser', 'metasequoia', 'blender', 'shade', '3dsmax', 'daz studio', 'zbrush', 'comi po!', 'maya', 'lightwave3d', 'hexagon king', 'vue', 'sketchup', 'cinema4d', 'xsi', 'carrara', 'bryce', 'strata', 'sculptris', 'modo', 'animationmaster', 'vistapro', 'sunny3d', '3d-coat', 'paint 3d', 'vroid studio', 'mechanical pencil', 'pencil', 'ballpoint pen', 'thin marker', 'colored pencil', 'copic marker', 'dip pen', 'watercolors', 'brush', 'calligraphy pen', 'felt-tip pen', 'magic marker', 'watercolor brush', 'paint', 'acrylic paint', 'fountain pen', 'pastels', 'airbrush', 'color ink', 'crayon', 'oil paint', 'coupy pencil', 'gansai', 'pastel crayons',
        ]:
            print_logging_msg(f'{self.order} is not one of available creation tools! It will be set to default ("all").', 'warning')
            self.creation_tool = "all"

        def time_format(s):
            if len(s) == 0:  # No restrictions
                return s
            # Try parsing time
            new_s = s.replace('/', '-').replace('.', '-')
            try:
                time.strptime(new_s, "%Y-%m-%d")
                return new_s
            except:
                print_logging_msg(f'{s} is not a valid "year-month-date" format! It will be ignored.', 'warning')
                return ''
        self.starting_date = time_format(self.starting_date)
        self.ending_date = time_format(self.ending_date)


    def build_search_appending_str_website(self, keyword_string: str):
        """
        Building a searching appending suffix for website.

        Args:
            keyword_string (str): the constructed keyword string for Pixiv.
        """

        append_str = f"tags/{keyword_string}/"

        if self.target_illust and self.target_ugoira and self.target_manga:
            append_str += "artworks?"
        elif self.target_manga:
            append_str += "manga?"
        elif self.target_illust and self.target_ugoira:
            append_str += "illustrations?"
        elif self.target_illust:
            append_str += "illustrations?type=illust&"
        elif self.target_ugoira:
            append_str += "illustrations?type=ugoira&"

        order_dict = {"newest": "date_d", "oldest": "date"}
        append_str += f"order={order_dict[self.order]}&"
        
        tags_matching_type_dict = {"partial": "s_tag", "perfect": "s_tag_full", "title_caption": "s_tc"}
        append_str += f"s_mode={tags_matching_type_dict[self.tags_match_type]}&"

        append_str += f"mode={self.age_rating}&" if self.age_rating != "all" else '&'
        append_str += "ai_type=1&" if not self.display_ai else '&'
        append_str += f"wlt={self.width_lowest}&" if self.width_lowest is not None else '&'
        append_str += f"hlt={self.height_lowest}&" if self.height_lowest is not None else '&'
        append_str += f"wgt={self.width_highest}&" if self.width_highest is not None else '&'
        append_str += f"hgt={self.height_highest}&" if self.height_highest is not None else '&'
        append_str += f"ratio={self.ratio}&" if self.ratio is not None else '&'
        append_str += f"tool={self.creation_tool}&" if self.creation_tool != "all" else '&'
        append_str += f"scd={self.starting_date}&" if len(self.starting_date) > 0 else '&'
        append_str += f"ecd={self.ending_date}&" if len(self.ending_date) > 0 else '&'

        while '&&' in append_str:
            append_str = append_str.replace('&&', '&')

        append_str = append_str.strip('&').replace('  ', ' ').strip()

        return append_str


    def build_search_appending_str_json(self, keyword_string: str):
        """
        Building a searching appending suffix for ajax api.
        
        Args:
            keyword_string (str): the constructed keyword string for Pixiv.
        """

        append_str = "ajax/search/"

        if self.target_illust and self.target_ugoira and self.target_manga:
            append_str += f"artworks/{keyword_string}?"
        elif self.target_manga:
            append_str += f"manga/{keyword_string}?"
        elif self.target_illust and self.target_ugoira:
            append_str += f"illustrations/{keyword_string}?"
        elif self.target_illust:
            append_str += f"illustrations/{keyword_string}?type=illust&"
        elif self.target_ugoira:
            append_str += f"illustrations/{keyword_string}?type=ugoira&"

        order_dict = {"newest": "date_d", "oldest": "date"}
        append_str += f"order={order_dict[self.order]}&"
        
        tags_matching_type_dict = {"partial": "s_tag", "perfect": "s_tag_full", "title_caption": "s_tc"}
        append_str += f"s_mode={tags_matching_type_dict[self.tags_match_type]}&"
        
        append_str += f"mode={self.age_rating}&" if self.age_rating != "all" else '&'
        append_str += "ai_type=1&" if not self.display_ai else '&'
        append_str += f"wlt={self.width_lowest}&" if self.width_lowest is not None else '&'
        append_str += f"hlt={self.height_lowest}&" if self.height_lowest is not None else '&'
        append_str += f"wgt={self.width_highest}&" if self.width_highest is not None else '&'
        append_str += f"hgt={self.height_highest}&" if self.height_highest is not None else '&'
        append_str += f"ratio={self.ratio}&" if self.ratio is not None else '&'
        append_str += f"tool={self.creation_tool}&" if self.creation_tool != "all" else '&'
        append_str += f"scd={self.starting_date}&" if len(self.starting_date) > 0 else '&'
        append_str += f"ecd={self.ending_date}&" if len(self.ending_date) > 0 else '&'

        while '&&' in append_str:
            append_str = append_str.replace('&&', '&')

        append_str = append_str.strip('&').replace('  ', ' ').strip()

        return append_str
