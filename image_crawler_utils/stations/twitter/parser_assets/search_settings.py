import dataclasses
from typing import Optional, Union
import time

from image_crawler_utils.log import print_logging_msg



@dataclasses.dataclass
class TwitterSearchSettings:
    """
    TwitterSearchSettings controls advanced searching settings. It will append an string to the keyword string according to the settings in this class.
    """

    from_users: Optional[Union[list[str], str]] = None
    """Select tweets sent by a certain user / a certain list of users."""
    to_users: Optional[Union[list[str], str]] = None
    """Select tweets replying to a certain user / a certain list of users."""
    mentioned_users: Optional[Union[list[str], str]] = None
    """Select tweets that mention a certain user / a certain list of users."""
    including_replies: bool = True
    """Including reply tweets."""
    only_replies: bool = False
    """Only including reply tweets. Works only if ``including_replies`` is set to :py:data:`True` (default)."""
    including_links: bool = True
    """Including tweets that contain at least one link."""
    only_links: bool = False
    """Only including tweets that contain at least one link. Works only if ``including_replies`` is set to :py:data:`True` (default)."""
    including_media: bool = True
    """Including tweets that contain at least one media."""
    only_media: bool = False
    """Only including tweets that contain at least one media. Works only if ``including_replies`` is set to :py:data:`True` (default)."""
    min_reply_num: Optional[int] = None
    """Including tweets with more than ``min_reply_num`` replies."""
    min_favorite_num: Optional[int] = None
    """Including tweets with more than ``min_favorite_num`` favorites."""
    min_retweet_num: Optional[int] = None
    """Including tweets with more than ``min_retweet_num`` retweets."""
    starting_date: str = ''
    """Tweets after this date. Must be \"YYYY-MM-DD\", \"YYYY.MM.DD\" or \"YYYY/MM/DD\" format."""
    ending_date: str = ''
    """Tweets before this date. Must be \"YYYY-MM-DD\", \"YYYY.MM.DD\" or \"YYYY/MM/DD\" format."""


    def __post_init__(self):
        if isinstance(self.from_users, str):
            self.from_users = [self.from_users]
        if isinstance(self.to_users, str):
            self.to_users = [self.to_users]
        if isinstance(self.mentioned_users, str):
            self.mentioned_users = [self.mentioned_users]

        def time_format(s):
            if len(s) == 0:  # No restrictions
                return s
            # Try parsing time
            new_s = s.replace('/', '-').replace('.', '-')
            try:
                time.strptime(new_s, "%Y-%m-%d")
                return new_s
            except:
                print_logging_msg(f'{s} is not a valid "year-month-date" format! It will be ignored.', "warning")
                return ''
        self.starting_date = time_format(self.starting_date)
        self.ending_date = time_format(self.ending_date)


    def build_search_appending_str(self, keyword_string: str):
        """
        Building a searching appending suffix.

        Args:
            keyword_string (str): the constructed keyword string for Twitter.
        """

        append_str = keyword_string + ' '

        append_str += f" ({' OR '.join(['from:' + user for user in self.from_users])})" if self.from_users is not None else ''
        append_str += f" ({' OR '.join(['to:' + user for user in self.to_users])})" if self.to_users is not None else ''
        append_str += f" ({' OR '.join(['@' + user for user in self.mentioned_users])})" if self.mentioned_users is not None else ''
        if not self.including_replies:
            append_str += " -filter:replies"
        elif self.only_replies:
            append_str += " filter:replies"
        if not self.including_links:
            append_str += " -filter:links"
        elif self.only_links:
            append_str += " filter:links"
        if not self.including_media:
            append_str += " -filter:media"
        elif self.only_media:
            append_str += " filter:media"
        append_str += f" min_replies:{self.min_reply_num}" if self.min_reply_num is not None else ''
        append_str += f" min_faves:{self.min_favorite_num}" if self.min_favorite_num is not None else ''
        append_str += f" min_retweets:{self.min_retweet_num}" if self.min_retweet_num is not None else ''
        append_str += f" since:{self.starting_date}" if len(self.starting_date) > 0 else ''
        append_str += f" until:{self.ending_date}" if len(self.ending_date) > 0 else ''

        append_str = append_str.strip().replace('  ', ' ').strip()

        return append_str
