import dataclasses
from typing import Optional, Union
import time

from image_crawler_utils.log import print_logging_msg



@dataclasses.dataclass
class TwitterSearchSettings:
    """
    Twitter / X search settings.

    Parameters:
        from_users (str or list, optional): A user / A list of users that sent these tweets.
        to_users (str or list, optional): A user / A list of users that these tweets replied to.
        mentionedd_users (str or list, optional): A user / A list of users mentioned in these tweets.
        including_replies (bool): Including replies. Default set to True.
        only_replies (bool): Showing only replies. Default set to False. "including_replies" must be True.
        including_links (bool): Including links. Default set to True.
        only_links (bool): Showing only links. Default set to False. "including_links" must be True.
        including_media (bool): Including media. Default set to True.
        only_media (bool): Showing only media. Default set to False. "including_media" must be True.
        min_reply_num (int): Minimum reply number.
        min_favorite_num (int): Minimum favorite number.
        min_retweet_num (int): Minimum retweet number.
        starting_date (str): Date which image was uploaded after. MUST be "YYYY-MM-DD", "YYYY.MM.DD" or "YYYY/MM/DD" format.
        ending_date (str): Date which image was uploaded before. MUST be "YYYY-MM-DD", "YYYY.MM.DD" or "YYYY/MM/DD" format.
    """

    from_users: Optional[Union[list[str], str]] = None
    to_users: Optional[Union[list[str], str]] = None
    mentioned_users: Optional[Union[list[str], str]] = None
    including_replies: bool = True
    only_replies: bool = False
    including_links: bool = True
    only_links: bool = False
    including_media: bool = True
    only_media: bool = False
    min_reply_num: Optional[int] = None
    min_favorite_num: Optional[int] = None
    min_retweet_num: Optional[int] = None
    starting_date: str = ''
    ending_date: str = ''


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
                print_logging_msg("warning", f'{s} is not a valid "year-month-date" format! It will be ignored.')
                return ''
        self.starting_date = time_format(self.starting_date)
        self.ending_date = time_format(self.ending_date)


    def build_search_appending_str(self, keyword_string: str):
        """
        Building a searching appending suffix.

        Parameters:
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
