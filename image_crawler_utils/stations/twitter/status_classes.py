import dataclasses
from functools import total_ordering
from collections.abc import Iterable
from typing import Optional



@dataclasses.dataclass
class TwitterStatusMedia:
    link: Optional[str] = None
    image_source: Optional[str] = None
    image_id: Optional[str] = None
    image_name: Optional[str] = None



@total_ordering
@dataclasses.dataclass
class TwitterStatus:
    """
    Contains config of a tweet (Twitter / X status).
    """

    status_url: Optional[str] = None
    status_id: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    time: Optional[str] = None
    reply_num: int = 0
    retweet_num: int = 0
    like_num: int = 0
    view_num: Optional[int] = None
    text: Optional[str] = None
    hashtags: Iterable[str] = dataclasses.field(default_factory=lambda: [])
    links: Iterable[str] = dataclasses.field(default_factory=lambda: [])
    media_list: Iterable[TwitterStatusMedia] = dataclasses.field(default_factory=lambda: [])


    def __lt__(self, other):  # Sort by status_id (convert to int)
        return int(self.status_id) < int(other.status_id)
