<h1 align="center">
Notes for Tasks
</h1>

This document includes detailed information about every supported features and tasks. It is suggested to finish [README](../README.md) and [tutorials](tutorials.md) before reading this.

**Table of Contents**

- [Booru](#booru)
  - [Keyword Filter for Downloader](#keyword-filter-for-downloader)
  - [Danbooru](#danbooru)
    - [CrawlerSettings](#crawlersettings)
    - [DanbooruKeywordParser](#danboorukeywordparser)
    - [ImageInfo Structure](#imageinfo-structure)
    - [Example Program](#example-program)
  - [Moebooru (yande.re, konachan.com, konachan.net)](#moebooru-yandere-konachancom-konachannet)
    - [MoebooruKeywordParser](#moeboorukeywordparser)
    - [ImageInfo Structure](#imageinfo-structure-1)
    - [Example Program](#example-program-1)
  - [Gelbooru](#gelbooru)
    - [GelbooruKeywordParser](#gelboorukeywordparser)
    - [ImageInfo Structure](#imageinfo-structure-2)
    - [Example Program](#example-program-2)
  - [Safebooru](#safebooru)
    - [SafebooruKeywordParser](#safeboorukeywordparser)
    - [ImageInfo Structure](#imageinfo-structure-3)
    - [Example Program](#example-program-3)
- [Pixiv](#pixiv)
  - [Get Pixiv Cookies](#get-pixiv-cookies)
  - [Parsers](#parsers)
    - [PixivKeywordParser](#pixivkeywordparser)
      - [PixivSearchSettings](#pixivsearchsettings)
    - [PixivUserParser](#pixivuserparser)
  - [Keyword Filter for Downloader](#keyword-filter-for-downloader-1)
  - [ImageInfo Structure](#imageinfo-structure-4)
  - [Example Program](#example-program-4)
- [Twitter / X](#twitter--x)
  - [Get Twitter Cookies](#get-twitter-cookies)
  - [Parsers](#parsers-1)
    - [TwitterKeywordMediaParser](#twitterkeywordmediaparser)
      - [TwitterSearchSettings](#twittersearchsettings)
    - [TwitterUserMediaParser](#twitterusermediaparser)
  - [ImageInfo Structure](#imageinfo-structure-5)
  - [Example Program](#example-program-5)
---

## Booru

Booru-related Parsers can be imported from `image_crawler_utils.stations.booru`.

### Keyword Filter for Downloader

Booru-structured sites share a keyword filter `filter_keyword_booru()` from `image_crawler_utils.stations.booru`. It will check whether a standard syntax keyword string matches the tags of an image.

+ For example, `"kuon_(utawarerumono) OR chinadress"` matches tags `"kuon_(utawarerumono)", "hair_ornament"`, while `"kuon_(utawarerumono) AND chinadress"` does not match.

To use it in Downloader is like:

```Python
from image_crawler_utils.stations.booru import filter_keyword_booru

downloader = Downloader(
    image_info_filter=lambda info: filter_keyword_booru(info, "kuon_(utawarerumono) OR chinadress")
)
```

### Danbooru

The main station URL of Danbooru is: https://danbooru.donmai.us/

+ For advanced keyword searching methods, check out [its cheatsheet](https://danbooru.donmai.us/wiki_pages/help:cheatsheet).

#### CrawlerSettings

**ATTENTION:** Danbooru does not accept user agents provided in `image_crawler_utils.user_agent.UserAgent`. Leave the `headers` blank (or set to `None`) in `DownloadConfig` when setting up CrawlerSettings is acceptable.

#### DanbooruKeywordParser

**WARNING:** For free users, Danbooru only supports searching at most 2 keywords / tags at the same time (can be connected by logic symbols).

Refer to [tutorials#Configuring DanbooruKeywordParser()](tutorials.md#configuring-danboorukeywordparser) for more detailed description.

The parameters are like:

```Python
from image_crawler_utils.stations.booru import DanbooruKeywordParser

DanbooruKeywordParser(
    station_url: str="https://danbooru.donmai.us/",
    crawler_settings: CrawlerSettings=CrawlerSettings(),
    standard_keyword_string: str | None=None,
    keyword_string: str | None=None,
    cookies: Cookies | list | dict | str | None=Cookies(),
    replace_url_with_source_level: str="None",
    use_keyword_include: bool=False,
)
```

+ `station_url`: The URL of the main page of a website.
  + If several websites share the same structure (like yande.re and konachan.com both use Moebooru structure), this parameter should be manually set.
+ `crawler_settings`: The CrawlerSettings used in this parser.
+ `standard_keyword_string`: Query keyword string using standard syntax.
+ `keyword_string`: If you want to directly specify the keywords used in searching, set `keyword_string` to a custom non-empty string. It will OVERWRITE `standard_keyword_string`.
+ `cookies`: Cookies used to access information from a website.
  + Can be one of `image_crawler_utils.Cookies`, `list`, `dict`, `str` or `None`.
    + Leave this parameter blank works the same as `None` / `Cookies()`.
+ `replace_url_with_source_level`: A level controlling whether the Parser will try to download from the source URL of images instead of from Danbooru.
  + It has 3 available levels, and default is `"None"`:
    + `"All"` or `"all"`: As long as the image has a source URL, try to download from this URL first.
    + `"File"` or `"file"`: If the source URL looks like a file (e.g. `https://foo.bar/image.png`) or it is one of several special websites (e.g. Pixiv or Twitter / X status), try to download from this URL first.
    + `"None"` or `"none"`: Do not try to download from any source URL first.
+ `use_keyword_include`: If this parameter is set to `True`, DanbooruKeywordParser will try to find keyword / tag subgroups with less than 2 keywords / tags (Danbooru restrictions for those without an account) that contain all searching results with the least page number.
  + Only works when `standard_keyword_string` is used. When `keyword_string` is specified, this parameter is omitted.
  + If no subgroup with less than 2 keywords / tags exists (e.g. `"kuon_(utawarerumono) OR rating:safe OR utawarerumono"`), the Parser will try to find keyword / tag subgroups with the least keyword / tag number.

#### ImageInfo Structure

The example image (Danbooru ID 4994142) is from [this Danbooru page](https://danbooru.donmai.us/posts/4994142).

<details>
<summary><b>ImageInfo Structure in JSON</b></summary>

```json
{
    "url": "https://cdn.donmai.us/original/cd/91/cd91f0000b9574bf142d125a1e886e5c.png",
    "name": "Danbooru 4994142 cd91f0000b9574bf142d125a1e886e5c.png",
    "info": {
        "info": {
            "id": 4994142,
            "created_at": "2021-12-21T08:02:13.706-05:00",
            "uploader_id": 772564,
            "score": 10,
            "source": "https://i.pximg.net/img-original/img/2020/08/11/12/41/43/83599609_p0.png",
            "md5": "cd91f0000b9574bf142d125a1e886e5c",
            "last_comment_bumped_at": null,
            "rating": "s",
            "image_width": 2000,
            "image_height": 2828,
            "tag_string": "1girl absurdres animal_ears black_eyes black_hair coat grabbing_own_breast hair_ornament hairband highres holding holding_mask japanese_clothes kuon_(utawarerumono) long_hair looking_at_viewer mask ponytail shirokuro_neko_(ouma_haruka) smile solo utawarerumono utawarerumono:_itsuwari_no_kamen",
            "fav_count": 10,
            "file_ext": "png",
            "last_noted_at": null,
            "parent_id": null,
            "has_children": false,
            "approver_id": null,
            "tag_count_general": 17,
            "tag_count_artist": 1,
            "tag_count_character": 1,
            "tag_count_copyright": 2,
            "file_size": 4527472,
            "up_score": 10,
            "down_score": 0,
            "is_pending": false,
            "is_flagged": false,
            "is_deleted": false,
            "tag_count": 23,
            "updated_at": "2024-07-10T12:21:31.782-04:00",
            "is_banned": false,
            "pixiv_id": 83599609,
            "last_commented_at": null,
            "has_active_children": false,
            "bit_flags": 0,
            "tag_count_meta": 2,
            "has_large": true,
            "has_visible_children": false,
            "media_asset": {
                "id": 5056745,
                "created_at": "2021-12-21T08:02:04.132-05:00",
                "updated_at": "2023-03-02T04:43:15.608-05:00",
                "md5": "cd91f0000b9574bf142d125a1e886e5c",
                "file_ext": "png",
                "file_size": 4527472,
                "image_width": 2000,
                "image_height": 2828,
                "duration": null,
                "status": "active",
                "file_key": "nxj2jBet8",
                "is_public": true,
                "pixel_hash": "5d34bcf53ddde76fd723f29aae5ebc53",
                "variants": [
                    {
                        "type": "180x180",
                        "url": "https://cdn.donmai.us/180x180/cd/91/cd91f0000b9574bf142d125a1e886e5c.jpg",
                        "width": 127,
                        "height": 180,
                        "file_ext": "jpg"
                    },
                    {
                        "type": "360x360",
                        "url": "https://cdn.donmai.us/360x360/cd/91/cd91f0000b9574bf142d125a1e886e5c.jpg",
                        "width": 255,
                        "height": 360,
                        "file_ext": "jpg"
                    },
                    {
                        "type": "720x720",
                        "url": "https://cdn.donmai.us/720x720/cd/91/cd91f0000b9574bf142d125a1e886e5c.webp",
                        "width": 509,
                        "height": 720,
                        "file_ext": "webp"
                    },
                    {
                        "type": "sample",
                        "url": "https://cdn.donmai.us/sample/cd/91/sample-cd91f0000b9574bf142d125a1e886e5c.jpg",
                        "width": 850,
                        "height": 1202,
                        "file_ext": "jpg"
                    },
                    {
                        "type": "original",
                        "url": "https://cdn.donmai.us/original/cd/91/cd91f0000b9574bf142d125a1e886e5c.png",
                        "width": 2000,
                        "height": 2828,
                        "file_ext": "png"
                    }
                ]
            },
            "tag_string_general": "1girl animal_ears black_eyes black_hair coat grabbing_own_breast hair_ornament hairband holding holding_mask japanese_clothes long_hair looking_at_viewer mask ponytail smile solo",
            "tag_string_character": "kuon_(utawarerumono)",
            "tag_string_copyright": "utawarerumono utawarerumono:_itsuwari_no_kamen",
            "tag_string_artist": "shirokuro_neko_(ouma_haruka)",
            "tag_string_meta": "absurdres highres",
            "file_url": "https://cdn.donmai.us/original/cd/91/cd91f0000b9574bf142d125a1e886e5c.png",
            "large_file_url": "https://cdn.donmai.us/sample/cd/91/sample-cd91f0000b9574bf142d125a1e886e5c.jpg",
            "preview_file_url": "https://cdn.donmai.us/180x180/cd/91/cd91f0000b9574bf142d125a1e886e5c.jpg"
        },
        "family_group": null,
        "tags": [
            "1girl",
            "absurdres",
            "animal_ears",
            "black_eyes",
            "black_hair",
            "coat",
            "grabbing_own_breast",
            "hair_ornament",
            "hairband",
            "highres",
            "holding",
            "holding_mask",
            "japanese_clothes",
            "kuon_(utawarerumono)",
            "long_hair",
            "looking_at_viewer",
            "mask",
            "ponytail",
            "shirokuro_neko_(ouma_haruka)",
            "smile",
            "solo",
            "utawarerumono",
            "utawarerumono:_itsuwari_no_kamen"
        ],
        "tags_class": {
            "1girl": "general",
            "animal_ears": "general",
            "black_eyes": "general",
            "black_hair": "general",
            "coat": "general",
            "grabbing_own_breast": "general",
            "hair_ornament": "general",
            "hairband": "general",
            "holding": "general",
            "holding_mask": "general",
            "japanese_clothes": "general",
            "long_hair": "general",
            "looking_at_viewer": "general",
            "mask": "general",
            "ponytail": "general",
            "smile": "general",
            "solo": "general",
            "kuon_(utawarerumono)": "character",
            "utawarerumono": "copyright",
            "utawarerumono:_itsuwari_no_kamen": "copyright",
            "shirokuro_neko_(ouma_haruka)": "artist",
            "absurdres": "meta",
            "highres": "meta"
        }
    },
    "backup_urls": [
        "https://i.pximg.net/img-original/img/2020/08/11/12/41/43/83599609_p0.png"
    ]
}
```

</details>

#### Example Program

Check out [this example](../examples/example.py), which downloads the first 20 images from [Danbooru](https://danbooru.donmai.us/) with keyword / tag `kuon_(utawarerumono)` and `rating:general` into the "Danbooru" folder. Information of images will be stored in `image_info_list.json` at same the path of your program.

### Moebooru (yande.re, konachan.com, konachan.net)

The main station URL of yande.re is: https://yande.re/

+ For advanced keyword searching methods, check out [its cheatsheet](https://yande.re/help/cheatsheet).

The main station URL of konachan.com is: https://konachan.com/

+ For advanced keyword searching methods, check out [its cheatsheet](https://konachan.com/help/cheatsheet).
+ konachan.com has a Cloudflare protection. Set `has_cloudflare` to `True` in MoebooruKeywordParser and do a manual clicking when Cloudflare page is displayed.
  + If you got stuck in the Cloudflare checking page, try changing an IP address (use a proxy) to access.

The main station URL of konachan.net is: https://konachan.net/

+ konachan.net is the non-explicit version of konachan.com. Both share the same rules when searching.
+ konachan.net does not require a cookie when accessing.

#### MoebooruKeywordParser

**WARNING:** Current Moebooru-structured sites only support using only `AND` or only `OR` in standard keyword string.

The parameters are like:

```Python
from image_crawler_utils.stations.booru import MoebooruKeywordParser

MoebooruKeywordParser(
    station_url: str,
    crawler_settings: CrawlerSettings=CrawlerSettings(),
    standard_keyword_string: str | None=None, 
    keyword_string: str | None=None,
    cookies: Cookies | list | dict | str | None=Cookies(),
    use_api=True,
    image_num_per_gallery_page: int=1,
    image_num_per_json: int=10, 
    replace_url_with_source_level: str="None",
    use_keyword_include: bool=False,
    has_cloudflare: bool=False,
)
```

+ `station_url`
+ `crawler_settings`
+ `standard_keyword_string`
+ `keyword_string`
+ `cookies`
+ `replace_url_with_source_level`
+ `use_keyword_include`
  + Refer to the [DanbooruKeywordParser](#danboorukeywordparser) chapter for the meaning of these parameters.
+ `use_api`: Whether to use the JSON-API page of Moebooru.
  + set to `True` will use the JSON-API page, like [this page](https://yande.re/post.json?api_version=2). It will usually be faster.
  + set to `False` will parse the image information from gallery page HTMLs, like [this page](https://yande.re/). It will be slower but contains more information (e.g. classification of tags).
+ `image_num_per_gallery_page`: Denotes how many images are displayed on a gallery page.
  + When `use_api` is set to `True`, this parameter will be used to estimate the total JSON page number (as we can only acquire total gallery page num from a gallery page). Otherwise it is not used.
  + Several predefined constants are provided for this. You can import them from `image_crawler_utils.stations.booru`, like:
    ```Python
    from image_crawler_utils.stations.booru import (
        YANDERE_IMAGE_NUM_PER_GALLERY_PAGE,  # yande.re
        KONACHAN_COM_IMAGE_NUM_PER_GALLERY_PAGE,  # konachan.com
        KONACHAN_NET_IMAGE_NUM_PER_GALLERY_PAGE,  # konachan.net
    )
    ```
+ `image_num_per_gallery_page`: When `use_api` is set to `True`, this parameter will control how many images are displayed on a JSON-API page.
  + Several predefined constants are provided for this. You can import them from `image_crawler_utils.stations.booru`, like:
    ```Python
    from image_crawler_utils.stations.booru import (
        YANDERE_IMAGE_NUM_PER_JSON,  # yande.re
        KONACHAN_NET_IMAGE_NUM_PER_JSON,  # konachan.com
        KONACHAN_COM_IMAGE_NUM_PER_JSON,  # konachan.net
    )
    ```
+ `has_cloudflare`: Set to `True` meaning current site is protected by Cloudflare (e.g. konachan.com). A browser window will be popped (and often MANUAL operations will be needed) to get cookies in order to bypass it.

#### ImageInfo Structure

The example image (Yandere ID 444116) is from [this yande.re page](https://yande.re/post/show/444116).

If `use_api` is set to `True`, the result is like:

<details>
<summary><b>ImageInfo Structure in JSON</b></summary>

```JSON
{
    "url": "https://files.yande.re/image/17c3abed8cd494314be5fe786d43ec13/yande.re%20444116%20amaduyu_tatsuki%20animal_ears%20kuon_%28utawarerumono%29%20nekone_%28utawarerumono%29%20seifuku%20tail%20utawarerumono%20utawarerumono_itsuwari_no_kamen.jpg",
    "name": "yande.re 444116 amaduyu_tatsuki animal_ears kuon_(utawarerumono) nekone_(utawarerumono) seifuku tail utawarerumono utawarerumono_itsuwari_no_kamen.jpg",
    "info": {
        "info": {
            "id": 444116,
            "tags": "amaduyu_tatsuki animal_ears kuon_(utawarerumono) nekone_(utawarerumono) seifuku tail utawarerumono utawarerumono_futari_no_hakuoro utawarerumono_itsuwari_no_kamen",
            "created_at": 1522675895,
            "updated_at": 1708546561,
            "creator_id": 1305,
            "approver_id": null,
            "author": "Radioactive",
            "change": 5864926,
            "source": "",
            "score": 47,
            "md5": "17c3abed8cd494314be5fe786d43ec13",
            "file_size": 3189824,
            "file_ext": "jpg",
            "file_url": "https://files.yande.re/image/17c3abed8cd494314be5fe786d43ec13/yande.re%20444116%20amaduyu_tatsuki%20animal_ears%20kuon_%28utawarerumono%29%20nekone_%28utawarerumono%29%20seifuku%20tail%20utawarerumono%20utawarerumono_itsuwari_no_kamen.jpg",
            "is_shown_in_index": true,
            "preview_url": "https://assets.yande.re/data/preview/17/c3/17c3abed8cd494314be5fe786d43ec13.jpg",
            "preview_width": 105,
            "preview_height": 150,
            "actual_preview_width": 211,
            "actual_preview_height": 300,
            "sample_url": "https://files.yande.re/sample/17c3abed8cd494314be5fe786d43ec13/yande.re%20444116%20sample%20amaduyu_tatsuki%20animal_ears%20kuon_%28utawarerumono%29%20nekone_%28utawarerumono%29%20seifuku%20tail%20utawarerumono%20utawarerumono_itsuwari_no_kamen.jpg",
            "sample_width": 1053,
            "sample_height": 1500,
            "sample_file_size": 363658,
            "jpeg_url": "https://files.yande.re/image/17c3abed8cd494314be5fe786d43ec13/yande.re%20444116%20amaduyu_tatsuki%20animal_ears%20kuon_%28utawarerumono%29%20nekone_%28utawarerumono%29%20seifuku%20tail%20utawarerumono%20utawarerumono_itsuwari_no_kamen.jpg",
            "jpeg_width": 4877,
            "jpeg_height": 6950,
            "jpeg_file_size": 0,
            "rating": "s",
            "is_rating_locked": false,
            "has_children": true,
            "parent_id": null,
            "status": "active",
            "is_pending": false,
            "width": 4877,
            "height": 6950,
            "is_held": false,
            "frames_pending_string": "",
            "frames_pending": [],
            "frames_string": "",
            "frames": [],
            "is_note_locked": false,
            "last_noted_at": 0,
            "last_commented_at": 0
        },
        "family_group": null,
        "tags": [
            "amaduyu_tatsuki",
            "animal_ears",
            "kuon_(utawarerumono)",
            "nekone_(utawarerumono)",
            "seifuku",
            "tail",
            "utawarerumono",
            "utawarerumono_futari_no_hakuoro",
            "utawarerumono_itsuwari_no_kamen"
        ]
    },
    "backup_urls": []
}
```

</details>

If `use_api` is set to `False`, the result is like:

<details>
<summary><b>ImageInfo Structure in JSON</b></summary>

```JSON
{
    "url": "https://files.yande.re/image/17c3abed8cd494314be5fe786d43ec13/yande.re%20444116%20amaduyu_tatsuki%20animal_ears%20kuon_%28utawarerumono%29%20nekone_%28utawarerumono%29%20seifuku%20tail%20utawarerumono%20utawarerumono_itsuwari_no_kamen.jpg",
    "name": "yande.re 444116 amaduyu_tatsuki animal_ears kuon_(utawarerumono) nekone_(utawarerumono) seifuku tail utawarerumono utawarerumono_itsuwari_no_kamen.jpg",
    "info": {
        "info": {
            "id": 444116,
            "tags": "amaduyu_tatsuki animal_ears kuon_(utawarerumono) nekone_(utawarerumono) seifuku tail utawarerumono utawarerumono_futari_no_hakuoro utawarerumono_itsuwari_no_kamen",
            "created_at": 1522675895,
            "updated_at": 1708546561,
            "creator_id": 1305,
            "approver_id": null,
            "author": "Radioactive",
            "change": 5864926,
            "source": "",
            "score": 47,
            "md5": "17c3abed8cd494314be5fe786d43ec13",
            "file_size": 3189824,
            "file_ext": "jpg",
            "file_url": "https://files.yande.re/image/17c3abed8cd494314be5fe786d43ec13/yande.re%20444116%20amaduyu_tatsuki%20animal_ears%20kuon_%28utawarerumono%29%20nekone_%28utawarerumono%29%20seifuku%20tail%20utawarerumono%20utawarerumono_itsuwari_no_kamen.jpg",
            "is_shown_in_index": true,
            "preview_url": "https://assets.yande.re/data/preview/17/c3/17c3abed8cd494314be5fe786d43ec13.jpg",
            "preview_width": 105,
            "preview_height": 150,
            "actual_preview_width": 211,
            "actual_preview_height": 300,
            "sample_url": "https://files.yande.re/sample/17c3abed8cd494314be5fe786d43ec13/yande.re%20444116%20sample%20amaduyu_tatsuki%20animal_ears%20kuon_%28utawarerumono%29%20nekone_%28utawarerumono%29%20seifuku%20tail%20utawarerumono%20utawarerumono_itsuwari_no_kamen.jpg",
            "sample_width": 1053,
            "sample_height": 1500,
            "sample_file_size": 363658,
            "jpeg_url": "https://files.yande.re/image/17c3abed8cd494314be5fe786d43ec13/yande.re%20444116%20amaduyu_tatsuki%20animal_ears%20kuon_%28utawarerumono%29%20nekone_%28utawarerumono%29%20seifuku%20tail%20utawarerumono%20utawarerumono_itsuwari_no_kamen.jpg",
            "jpeg_width": 4877,
            "jpeg_height": 6950,
            "jpeg_file_size": 0,
            "rating": "s",
            "is_rating_locked": false,
            "has_children": true,
            "parent_id": null,
            "status": "active",
            "is_pending": false,
            "width": 4877,
            "height": 6950,
            "is_held": false,
            "frames_pending_string": "",
            "frames_pending": [],
            "frames_string": "",
            "frames": [],
            "is_note_locked": false,
            "last_noted_at": 0,
            "last_commented_at": 0
        },
        "family_group": null,
        "tags": [
            "amaduyu_tatsuki",
            "animal_ears",
            "kuon_(utawarerumono)",
            "nekone_(utawarerumono)",
            "seifuku",
            "tail",
            "utawarerumono",
            "utawarerumono_futari_no_hakuoro",
            "utawarerumono_itsuwari_no_kamen"
        ],
        "tags_class": {
            "amaduyu_tatsuki": "artist",
            "animal_ears": "general",
            "kuon_(utawarerumono)": "character",
            "nekone_(utawarerumono)": "character",
            "seifuku": "general",
            "tail": "general",
            "utawarerumono": "copyright",
            "utawarerumono_futari_no_hakuoro": "copyright",
            "utawarerumono_itsuwari_no_kamen": "copyright"
        }
    },
    "backup_urls": []
}
```

</details>

For konachan.com / konachan.net, an example image (Konachan ID 249445) is from [this konachan.net page](https://konachan.net/post/show/249445/autumn-bow-goumudan-kuon_-utawarerumono-leaves-lon) (`use_api` is set to `False`).

<details>
<summary><b>ImageInfo Structure in JSON</b></summary>

```JSON
{
    "url": "https://konachan.com/image/5e19a855a70f2ebc986ee4aa745995dc/Konachan.com%20-%20249445%20autumn%20bow%20goumudan%20kuon_%28utawarerumono%29%20leaves%20long_hair%20utawarerumono%20utawarerumono_itsuwari_no_kamen%20yellow_eyes.jpg",
    "name": "Konachan.com - 249445 autumn bow goumudan kuon_(utawarerumono) leaves long_hair utawarerumono utawarerumono_itsuwari_no_kamen yellow_eyes.jpg",
    "info": {
        "info": {
            "id": 249445,
            "tags": "autumn bow goumudan kuon_(utawarerumono) leaves long_hair utawarerumono utawarerumono_itsuwari_no_kamen yellow_eyes",
            "created_at": 1504211939,
            "creator_id": 156425,
            "author": "RyuZU",
            "change": 2181553,
            "source": "https://www.pixiv.net/member_illust.php?mode=medium&illust_id=56743404",
            "score": 61,
            "md5": "5e19a855a70f2ebc986ee4aa745995dc",
            "file_size": 1076152,
            "file_url": "https://konachan.com/image/5e19a855a70f2ebc986ee4aa745995dc/Konachan.com%20-%20249445%20autumn%20bow%20goumudan%20kuon_%28utawarerumono%29%20leaves%20long_hair%20utawarerumono%20utawarerumono_itsuwari_no_kamen%20yellow_eyes.jpg",
            "is_shown_in_index": true,
            "preview_url": "https://konachan.com/data/preview/5e/19/5e19a855a70f2ebc986ee4aa745995dc.jpg",
            "preview_width": 150,
            "preview_height": 106,
            "actual_preview_width": 300,
            "actual_preview_height": 211,
            "sample_url": "https://konachan.com/sample/5e19a855a70f2ebc986ee4aa745995dc/Konachan.com%20-%20249445%20sample.jpg",
            "sample_width": 1500,
            "sample_height": 1056,
            "sample_file_size": 834664,
            "jpeg_url": "https://konachan.com/image/5e19a855a70f2ebc986ee4aa745995dc/Konachan.com%20-%20249445%20autumn%20bow%20goumudan%20kuon_%28utawarerumono%29%20leaves%20long_hair%20utawarerumono%20utawarerumono_itsuwari_no_kamen%20yellow_eyes.jpg",
            "jpeg_width": 1800,
            "jpeg_height": 1267,
            "jpeg_file_size": 0,
            "rating": "s",
            "has_children": false,
            "parent_id": null,
            "status": "active",
            "width": 1800,
            "height": 1267,
            "is_held": false,
            "frames_pending_string": "",
            "frames_pending": [],
            "frames_string": "",
            "frames": []
        },
        "family_group": null,
        "tags": [
            "autumn",
            "bow",
            "goumudan",
            "kuon_(utawarerumono)",
            "leaves",
            "long_hair",
            "utawarerumono",
            "utawarerumono_itsuwari_no_kamen",
            "yellow_eyes"
        ],
        "tags_class": {
            "autumn": "general",
            "bow": "general",
            "goumudan": "artist",
            "kuon_(utawarerumono)": "character",
            "leaves": "general",
            "long_hair": "general",
            "utawarerumono": "copyright",
            "utawarerumono_itsuwari_no_kamen": "copyright",
            "yellow_eyes": "general"
        }
    },
    "backup_urls": [
        "https://www.pixiv.net/member_illust.php?mode=medium&illust_id=56743404"
    ]
}
```

</details>

#### Example Program

For yande.re, [this example](../examples/yandere_example.py) will download images with keyword / tag `kuon_(utawarerumono)` and `rating:safe` into the "Yandere" folder using JSON-API.

For konachan.com, [this example](../examples/konachan_example.py) will download images with keyword / tag `kuon_(utawarerumono)` and `rating:safe` into the "Konachan_com" folder without using JSON-API.

### Gelbooru

The main station URL of Gelbooru is: https://gelbooru.com/

+ For advanced keyword searching methods, check out [its cheatsheet](https://gelbooru.com/index.php?page=help&topic=cheatsheet).

#### GelbooruKeywordParser

**WARNING:** `OR` is currently not supported in Gelbooru.

The parameters are like:

```Python
from image_crawler_utils.stations.booru import GelbooruKeywordParser

GelbooruKeywordParser(
    station_url: str="https://gelbooru.com/",
    crawler_settings: CrawlerSettings=CrawlerSettings(),
    standard_keyword_string: str | None=None,
    keyword_string: str | None=None,
    cookies: Cookies | list | dict | str | None=Cookies(),
    replace_url_with_source_level: str="None",
    use_keyword_include: bool=False,
)
```

+ `station_url`
+ `crawler_settings`
+ `standard_keyword_string`
+ `keyword_string`
+ `cookies`
+ `replace_url_with_source_level`
+ `use_keyword_include`
  + Refer to the [DanbooruKeywordParser](#danboorukeywordparser) chapter for the meaning of these parameters.

#### ImageInfo Structure

The example image (Gelbooru ID 7963712) is from [this Gelbooru page](https://gelbooru.com/index.php?page=post&s=view&id=7963712).

<details>
<summary><b>ImageInfo Structure in JSON</b></summary>

```JSON
{
    "url": "https://img3.gelbooru.com/images/b6/48/b648128800c3206cd322de500058c558.jpeg",
    "name": "Gelbooru 7963712 b648128800c3206cd322de500058c558.jpeg",
    "info": {
        "info": {
            "id": 7963712,
            "created_at": "Sat Nov 26 11:08:44 -0600 2022",
            "score": 4,
            "width": 1790,
            "height": 2048,
            "md5": "b648128800c3206cd322de500058c558",
            "directory": "b6/48",
            "image": "b648128800c3206cd322de500058c558.jpeg",
            "rating": "general",
            "source": "https://twitter.com/nike_abc/status/819734442604273664/photo/1",
            "change": 1678866174,
            "owner": "angel...",
            "creator_id": 725689,
            "parent_id": 0,
            "sample": 1,
            "preview_height": 250,
            "preview_width": 218,
            "tags": "1girl animal_ears aquaplus blush bowl chewing eating festival flower flower_on_head food from_behind gradient_eyes hair_between_eyes hair_bun hair_up highres holding holding_bowl japanese_clothes kimono kuon_(utawarerumono) lily_(flower) long_hair long_sleeves looking_at_viewer multicolored_eyes nike_abc noodles raised_eyebrows sidelocks sitting solo swept_bangs udon utawarerumono utawarerumono:_itsuwari_no_kamen wide_sleeves yellow_eyes yukata",
            "title": "",
            "has_notes": "false",
            "has_comments": "false",
            "file_url": "https://img3.gelbooru.com/images/b6/48/b648128800c3206cd322de500058c558.jpeg",
            "preview_url": "https://img3.gelbooru.com/thumbnails/b6/48/thumbnail_b648128800c3206cd322de500058c558.jpg",
            "sample_url": "https://img3.gelbooru.com/samples/b6/48/sample_b648128800c3206cd322de500058c558.jpg",
            "sample_height": 973,
            "sample_width": 850,
            "status": "active",
            "post_locked": 0,
            "has_children": "false"
        },
        "family_group": null,
        "tags": [
            "1girl",
            "animal_ears",
            "aquaplus",
            "blush",
            "bowl",
            "chewing",
            "eating",
            "festival",
            "flower",
            "flower_on_head",
            "food",
            "from_behind",
            "gradient_eyes",
            "hair_between_eyes",
            "hair_bun",
            "hair_up",
            "highres",
            "holding",
            "holding_bowl",
            "japanese_clothes",
            "kimono",
            "kuon_(utawarerumono)",
            "lily_(flower)",
            "long_hair",
            "long_sleeves",
            "looking_at_viewer",
            "multicolored_eyes",
            "nike_abc",
            "noodles",
            "raised_eyebrows",
            "sidelocks",
            "sitting",
            "solo",
            "swept_bangs",
            "udon",
            "utawarerumono",
            "utawarerumono:_itsuwari_no_kamen",
            "wide_sleeves",
            "yellow_eyes",
            "yukata"
        ]
    },
    "backup_urls": [
        "https://twitter.com/nike_abc/status/819734442604273664/photo/1"
    ]
}
```

</details>

#### Example Program

[This example](../examples/gelbooru_example.py) will download images with keyword / tag `kuon_(utawarerumono)` and `rating:general` into the "Gelbooru" folder.

### Safebooru

The main station URL of Safebooru is: https://safebooru.org/

+ For advanced keyword searching methods, check out [its cheatsheet](https://safebooru.org/index.php?page=help&topic=cheatsheet).

#### SafebooruKeywordParser

The parameters are like:

```Python
from image_crawler_utils.stations.booru import SafebooruKeywordParser

SafebooruKeywordParser(
    station_url: str="https://safebooru.org/",
    crawler_settings: CrawlerSettings=CrawlerSettings(),
    standard_keyword_string: str | None=None,
    keyword_string: str | None=None,
    cookies: Cookies | list | dict | str | None=Cookies(),
    replace_url_with_source_level: str="None",
    use_keyword_include: bool=False,
)
```

+ `station_url`
+ `crawler_settings`
+ `standard_keyword_string`
+ `keyword_string`
+ `cookies`
+ `replace_url_with_source_level`
+ `use_keyword_include`
  + Refer to the [DanbooruKeywordParser](#danboorukeywordparser) chapter for the meaning of these parameters.

#### ImageInfo Structure

The example image (Safebooru ID 2193950) is from [this Safebooru page](https://safebooru.org/index.php?page=post&s=view&id=2193950).

<details>
<summary><b>ImageInfo Structure in JSON</b></summary>

```JSON
{
    "url": "https://safebooru.org/images/2104/de86b60fda7c55aaa6b4bc919334e83cc230a828.jpg",
    "name": "Safebooru 2193950 de86b60fda7c55aaa6b4bc919334e83cc230a828.jpg",
    "info": {
        "info": {
            "preview_url": "https://safebooru.org/thumbnails/2104/thumbnail_de86b60fda7c55aaa6b4bc919334e83cc230a828.jpg",
            "sample_url": "https://safebooru.org/samples/2104/sample_de86b60fda7c55aaa6b4bc919334e83cc230a828.jpg",
            "file_url": "https://safebooru.org/images/2104/de86b60fda7c55aaa6b4bc919334e83cc230a828.jpg",
            "directory": 2104,
            "hash": "060dc85cf55e4bc3038a778235e93601",
            "width": 1124,
            "height": 1754,
            "id": 2193950,
            "image": "de86b60fda7c55aaa6b4bc919334e83cc230a828.jpg",
            "change": 1491160788,
            "owner": "gelbooru",
            "parent_id": 0,
            "rating": "safe",
            "sample": true,
            "sample_height": 1326,
            "sample_width": 850,
            "score": 1,
            "tags": "1girl amazuyu_tatsuki animal_ears arm_up arms_up blue_hair boots breasts brown_eyes cat_ears cat_tail cherry_blossoms dagger eyebrows_visible_through_hair hair_ornament highres japanese_clothes kuon_(utawareru_mono) looking_at_viewer medium_breasts obi open_mouth outdoors petals sash scarf side_slit solo sunlight tail utawareru_mono utawareru_mono:_itsuwari_no_kamen weapon wide_sleeves",
            "source": "うたわれるもの　偽りの仮面／二人の白皇　公式ビジュアルコレクション",
            "status": "active",
            "has_notes": false,
            "comment_count": 0
        },
        "family_group": null,
        "tags": [
            "1girl",
            "amazuyu_tatsuki",
            "animal_ears",
            "arm_up",
            "arms_up",
            "blue_hair",
            "boots",
            "breasts",
            "brown_eyes",
            "cat_ears",
            "cat_tail",
            "cherry_blossoms",
            "dagger",
            "eyebrows_visible_through_hair",
            "hair_ornament",
            "highres",
            "japanese_clothes",
            "kuon_(utawareru_mono)",
            "looking_at_viewer",
            "medium_breasts",
            "obi",
            "open_mouth",
            "outdoors",
            "petals",
            "sash",
            "scarf",
            "side_slit",
            "solo",
            "sunlight",
            "tail",
            "utawareru_mono",
            "utawareru_mono:_itsuwari_no_kamen",
            "weapon",
            "wide_sleeves"
        ]
    },
    "backup_urls": []
}
```

</details>

#### Example Program

[This example](../examples/safebooru_example.py) will download images with keyword / tag `kuon_(utawareru_mono)` into the "Safebooru" folder.

## Pixiv

The main station URL of Pixiv is: https://www.pixiv.net/

+ You must have an account to use Pixiv-related Parsers. It is compulsory to use cookies that contains your account information (manually get or using `get_pixiv_cookies()`) in Parsers.
+ For advanced keyword searching methods, check out [this article](https://www.pixiv.help/hc/en-us/articles/235646387-I-would-like-to-know-how-to-search-for-content-on-pixiv).
  + It is recommended to use keywords in Japanese. Translations of tags to other languages are currently not supported.
+ Pixiv has a VERY STRICT restriction on crawling! If too many **429 error warning** appears, you should **STOP THE CRAWLER** at once in case your account become suspended!

### Get Pixiv Cookies

Please refer to the [tutorials#Acquiring Cookies](tutorials.md#acquiring-cookies) chapter for detailed information.

You can save Pixiv cookies for later use instead of calling `get_pixiv_cookies()` every run.

### Parsers

Parsers of Pixiv will use the `image_num` parameter to restrict the number of artworks fetched from Pixiv.

+ For PixivKeywordParser, setting this parameter will get artworks according to the order in PixivSearchSettings. For other Parsers, setting this parameter will get the newest artworks.
+ **ATTENTION:** `image_num` only restricts the number of Pixiv artworks, and an artwork may contain multiple images!

#### PixivKeywordParser

The parameters are like:

```Python
from image_crawler_utils.stations.pixiv import PixivKeywordParser

PixivKeywordParser(
    station_url: str="https://www.pixiv.net/",
    crawler_settings: CrawlerSettings=CrawlerSettings(),
    standard_keyword_string: str | None=None, 
    keyword_string: str | None=None,
    cookies: Cookies | list | dict | str | None=Cookies(),
    pixiv_search_settings: PixivSearchSettings=PixivSearchSettings(),
    use_keyword_include: bool=False,
    quick_mode: bool=False,
    info_page_batch_num: int | None=100,
    info_page_batch_delay: float | Callable | None=300,
    headless: bool=True,
)
```

+ `station_url`: Main URL of Pixiv station. Default set to `"https://www.pixiv.net/"`.
+ `crawler_settings`: The CrawlerSettings used in this parser.
+ `standard_keyword_string`: Query keyword string using standard syntax.
+ `keyword_string`: If you want to directly specify the keywords used in searching, set `keyword_string` to a custom non-empty string. It will OVERWRITE `standard_keyword_string`.
+ `cookies`: Cookies used to access information from a website.
  + Can be one of `image_crawler_utils.Cookies`, `list`, `dict`, `str` or `None`.
    + Leave this parameter blank works the same as `None` / `Cookies()`.
+ `pixiv_search_settings`: A PixivSearchSettings class that contains extra options when searching. Refer to the [PixivSearchSettings](#pixivsearchsettings) for more details.
+ `use_keyword_include`: If this parameter is set to `True`, the Parser will try to find keyword / tag subgroups that contain all searching results with the least page number.
+ `quick_mode`: Only collect the basic information.
  + Pixiv has a strict anti-crawling restriction on acquiring the pages containing information of images. Set this parameter to `True` will not request these pages and collect only the basic information of images for downloading.
  + Different Parsers may have different structures of image information. Refer to the [ImageInfo Structure](#imageinfo-structure-4) chapter for the difference between results.
    + If set to `False` (get full information), then the `DownloadConfig.thread_delay` when downloading information pages will be forced to set to `DownloadConfig.thread_num * 1.0` (not randomized). Other pages are not affected.
+ `info_page_batch_num`: After downloading `info_page_batch_num` number of image information pages, the crawler will wait for `info_page_batch_delay` seconds before continue.
+ `info_page_batch_delay`: After downloading `info_page_batch_num` number of image information pages, the crawler will wait for `info_page_batch_delay` seconds before continue.
  + If `quick_mode` is set to `True`, both `info_page_batch_num` and `info_page_batch_delay` will be ignored.
  + If you are not sure, leaving both `info_page_batch_num` and `info_page_batch_delay` blank (use their default values) is likely enough for preventing your account to be suspended.
  + `info_page_batch_delay` can be a function that will be called for every usage.
+ `headless`: Do not display browsers window when a browser is started. Set to `False` will pop up browser windows.

##### PixivSearchSettings

PixivSearchSettings controls advanced searching settings. It will append an string to the keyword string according to the settings in this class.

The parameters are like:

```Python
from image_crawler_utils.stations.pixiv import PixivSearchSettings

PixivSearchSettings(
    age_rating: str="all"
    order: str="newest"
    target_illust: bool=True
    target_manga: bool=True
    target_ugoira: bool=True
    tags_match_type: str="partial"
    display_ai: bool=True
    width_lowest: int | None=None
    width_highest: int | None=None
    height_lowest: int | None=None
    height_highest: int | None=None
    ratio: float | None=None
    creation_tool: str="all"
    starting_date: str=''
    ending_date: str=''
)
```

+ `age_rating`: Age rating of images. Must be one of `"all"`, `"safe"` and `"r18"`.
+ `order`: Order of images. Must be one of `"newest"` and `"oldest"`.
+ `target_illust`: Whether to display illustrations.
+ `target_manga`: Whether to display mangas.
+ `target_ugoira`: Whether to display ugoiras (animated illustrations).
  + Cannot set `target_illust`, `target_manga` and `target_ugoira` to `False` at the same time.
  + Cannot set only one of `target_illust` and `target_ugoira` to `False` with the rest set to `True` at the same time.
+ `tags_match_type`: Type of matching tags. Must be one of these types:
  + `"partial"`: Partially matched tags are accepted.
  + `"perfect"`: Tags must be perfectly matched.
  + `"title_caption"`: Searched keywords will be matched with titles and captions.
+ `display_ai`: Whether to display AI-generated images.
+ `width_lowest`: Lowest width (in pixels) of images.
+ `width_highest`: Highest width (in pixels) of images.
+ `height_lowest`: Lowest height (in pixels) of images.
+ `height_highest`: Highest height (in pixels) of images.
+ `ratio`: Ratio of images.
  + Set to 0 means select only square images.
  + Set to positive means select horizontal images. For example, `ratio=0.5` means selecting images with: width / height >= 1 + 0.5 = 1.5
  + Set to negative means select vertical images. For example, `ratio=-0.5` means selecting images with: height / width >= 1 + 0.5 = 1.5
+ `creation_tool`: Creation tool of images. Must be a string from this list:

<details>
<summary>List of acceptable creation_tool values</summary>

```Python
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
```

</details>

+ `starting_date`: Images after this date. Must be "YYYY-MM-DD", "YYYY.MM.DD" or "YYYY/MM/DD" format.
+ `ending_date`: Images before this date. Must be "YYYY-MM-DD", "YYYY.MM.DD" or "YYYY/MM/DD" format.

#### PixivUserParser

This Parser will collect information of images uploaded by a user.

The parameters are like:

```Python
from image_crawler_utils.stations.pixiv import PixivUserParser

PixivUserParser(
    crawler_settings: CrawlerSettings=CrawlerSettings(),
    member_id: str,
    station_url: str="https://www.pixiv.net/",
    cookies: Cookies | list | dict | str | None=Cookies(),
    thread_delay: float | Callable | None=0,
    quick_mode: bool=False,
    info_page_batch_num: int | None=100,
    info_page_batch_delay: float | Callable | None=300,
)
```

+ `station_url`
+ `crawler_settings`
+ `cookies`
+ `quick_mode`
+ `info_page_batch_num`
+ `info_page_batch_delay`
  + Refer to the [PixivKeywordParser](#pixivkeywordparser) chapter for the meaning of these parameters.
+ `member_id`: The member id of a Pixiv user. Can be acquired by their user pages. For example, user page https://www.pixiv.net/users/2175653 contains their member id 2175653.

### Keyword Filter for Downloader

`filter_keyword_pixiv()` from `image_crawler_utils.stations.pixiv` is provided for Pixiv. It will check whether a standard syntax keyword string matches the tags of an image.

Its parameters and usage can be referred from the [Keyword Filter for Downloader](#keyword-filter-for-downloader) chapter of booru.

### ImageInfo Structure

The example image (Pixiv ID 60066082) is from [this Pixiv page](https://www.pixiv.net/artworks/60066082).

<details>
<summary><b>ImageInfo Structure in JSON</b></summary>

```JSON
{
    "url": "https://i.pximg.net/img-original/img/2016/11/23/00/10/12/60066082_p0.jpg",
    "name": "60066082_p0.jpg",
    "info": {
        "id": "60066082",
        "width": 2067,
        "height": 1124,
        "tags": [
            "うたわれるもの",
            "クオン",
            "クオン(うたわれるもの)",
            "偽りの仮面",
            "うたわれるもの1000users入り",
            "はいてない"
        ],
        "info": {
            "illustId": "60066082",
            "illustTitle": "クオン",
            "illustComment": "LEAF！(￣︶￣)↗",
            "id": "60066082",
            "title": "クオン",
            "description": "LEAF！(￣︶￣)↗",
            "illustType": 0,
            "createDate": "2016-11-22T15:10:00+00:00",
            "uploadDate": "2016-11-22T15:10:00+00:00",
            "restrict": 0,
            "xRestrict": 0,
            "sl": 4,
            "urls": {
                "mini": "https://i.pximg.net/c/48x48/img-master/img/2016/11/23/00/10/12/60066082_p0_square1200.jpg",
                "thumb": "https://i.pximg.net/c/250x250_80_a2/img-master/img/2016/11/23/00/10/12/60066082_p0_square1200.jpg",
                "small": "https://i.pximg.net/c/540x540_70/img-master/img/2016/11/23/00/10/12/60066082_p0_master1200.jpg",
                "regular": "https://i.pximg.net/img-master/img/2016/11/23/00/10/12/60066082_p0_master1200.jpg",
                "original": "https://i.pximg.net/img-original/img/2016/11/23/00/10/12/60066082_p0.jpg"
            },
            "tags": {
                "authorId": "2175653",
                "isLocked": false,
                "tags": [
                    {
                        "tag": "うたわれるもの",
                        "locked": true,
                        "deletable": false,
                        "userId": "2175653",
                        "translation": {
                            "en": "传颂之物"
                        },
                        "userName": "白糸"
                    },
                    {
                        "tag": "クオン",
                        "locked": true,
                        "deletable": false,
                        "userId": "2175653",
                        "translation": {
                            "en": "久远"
                        },
                        "userName": "白糸"
                    },
                    {
                        "tag": "クオン(うたわれるもの)",
                        "locked": true,
                        "deletable": false,
                        "userId": "2175653",
                        "translation": {
                            "en": "Kuon (Utawarerumono)"
                        },
                        "userName": "白糸"
                    },
                    {
                        "tag": "偽りの仮面",
                        "locked": false,
                        "deletable": true,
                        "translation": {
                            "en": "Mask of Deception"
                        }
                    },
                    {
                        "tag": "うたわれるもの1000users入り",
                        "locked": false,
                        "deletable": true,
                        "translation": {
                            "en": "传颂之物1000收藏"
                        }
                    },
                    {
                        "tag": "はいてない",
                        "locked": false,
                        "deletable": true,
                        "translation": {
                            "en": "真空"
                        }
                    }
                ],
                "writable": true
            },
            "alt": "#うたわれるもの クオン - 白糸的插画",
            "userId": "2175653",
            "userName": "白糸",
            "userAccount": "m2022620",
            "userIllusts": {
                "123027089": null,
                "122247290": null,
                "122247263": null,
                "117772585": null,
                "112585667": null,
                "112166673": null,
                "111638409": null,
                "111232057": null,
                "109798403": null,
                "109500879": null,
                "109476315": null,
                "109476262": null,
                "109476189": null,
                "107761368": null,
                "106932565": null,
                "106098160": null,
                "105043397": null,
                "104793992": null,
                "104793969": null,
                "103571043": null,
                "102008444": null,
                "101581727": null,
                "101013381": null,
                "100747070": null,
                "100153054": null,
                "99809302": null,
                "98882547": null,
                "98509823": null,
                "97787325": null,
                "97161880": null,
                "96784531": null,
                "96507049": null,
                "94925150": null,
                "93336909": null,
                "92511349": null,
                "91982111": null,
                "89382371": null,
                "88618174": null,
                "87133557": null,
                "86826633": null,
                "86287114": null,
                "86207483": null,
                "85553379": null,
                "85228711": null,
                "84941093": null,
                "84180102": null,
                "83745547": null,
                "83252665": null,
                "81470594": null,
                "81164191": null,
                "80510626": null,
                "79363479": null,
                "78408878": null,
                "78016842": null,
                "78016832": null,
                "78016814": null,
                "77299454": null,
                "76451370": null,
                "75492207": null,
                "74144536": null,
                "73619028": null,
                "72148007": null,
                "71167936": null,
                "70667068": null,
                "69972920": null,
                "68845484": null,
                "67467570": null,
                "66697470": null,
                "66439020": null,
                "64794423": null,
                "63792807": null,
                "63342815": null,
                "63119451": null,
                "63075327": null,
                "62341856": null,
                "62303518": null,
                "62259051": null,
                "62001710": null,
                "61403897": null,
                "60993258": null,
                "60909436": null,
                "60752393": null,
                "60581381": null,
                "60181296": {
                    "id": "60181296",
                    "title": "Ciel",
                    "illustType": 0,
                    "xRestrict": 0,
                    "restrict": 0,
                    "sl": 4,
                    "url": "https://i.pximg.net/c/250x250_80_a2/img-master/img/2016/12/01/00/07/20/60181296_p0_square1200.jpg",
                    "description": "",
                    "tags": [
                        "GE2",
                        "ゴッドイーター",
                        "シエル・アランソン",
                        "GODEATER",
                        "GE1000users入り"
                    ],
                    "userId": "2175653",
                    "userName": "白糸",
                    "width": 859,
                    "height": 1100,
                    "pageCount": 1,
                    "isBookmarkable": true,
                    "bookmarkData": null,
                    "alt": "#GE2 Ciel - 白糸的插画",
                    "titleCaptionTranslation": {
                        "workTitle": null,
                        "workCaption": null
                    },
                    "createDate": "2016-12-01T00:07:20+09:00",
                    "updateDate": "2016-12-01T00:07:20+09:00",
                    "isUnlisted": false,
                    "isMasked": false,
                    "aiType": 0,
                    "profileImageUrl": "https://i.pximg.net/user-profile/img/2015/03/30/16/31/47/9164255_825d9067d54dfc635e4477c38508b6f5_50.jpg"
                },
                "60066082": {
                    "id": "60066082",
                    "title": "クオン",
                    "illustType": 0,
                    "xRestrict": 0,
                    "restrict": 0,
                    "sl": 4,
                    "url": "https://i.pximg.net/c/250x250_80_a2/img-master/img/2016/11/23/00/10/12/60066082_p0_square1200.jpg",
                    "description": "LEAF！(￣︶￣)↗",
                    "tags": [
                        "うたわれるもの",
                        "クオン",
                        "クオン(うたわれるもの)",
                        "偽りの仮面",
                        "うたわれるもの1000users入り",
                        "はいてない"
                    ],
                    "userId": "2175653",
                    "userName": "白糸",
                    "width": 2067,
                    "height": 1124,
                    "pageCount": 1,
                    "isBookmarkable": true,
                    "bookmarkData": null,
                    "alt": "#うたわれるもの クオン - 白糸的插画",
                    "titleCaptionTranslation": {
                        "workTitle": null,
                        "workCaption": null
                    },
                    "createDate": "2016-11-23T00:10:12+09:00",
                    "updateDate": "2016-11-23T00:10:12+09:00",
                    "isUnlisted": false,
                    "isMasked": false,
                    "aiType": 0
                },
                "59876296": {
                    "id": "59876296",
                    "title": "火防女",
                    "illustType": 0,
                    "xRestrict": 0,
                    "restrict": 0,
                    "sl": 2,
                    "url": "https://i.pximg.net/c/250x250_80_a2/img-master/img/2016/11/10/00/06/36/59876296_p0_square1200.jpg",
                    "description": "",
                    "tags": [
                        "ダークソウル",
                        "火防女",
                        "落書き",
                        "ダークソウル1000users入り"
                    ],
                    "userId": "2175653",
                    "userName": "白糸",
                    "width": 826,
                    "height": 1500,
                    "pageCount": 1,
                    "isBookmarkable": true,
                    "bookmarkData": null,
                    "alt": "#ダークソウル 火防女 - 白糸的插画",
                    "titleCaptionTranslation": {
                        "workTitle": null,
                        "workCaption": null
                    },
                    "createDate": "2016-11-10T00:06:36+09:00",
                    "updateDate": "2016-11-10T00:06:36+09:00",
                    "isUnlisted": false,
                    "isMasked": false,
                    "aiType": 0,
                    "profileImageUrl": "https://i.pximg.net/user-profile/img/2015/03/30/16/31/47/9164255_825d9067d54dfc635e4477c38508b6f5_50.jpg"
                },
                "59756349": null,
                "59534422": null,
                "59378859": null,
                "59296786": null,
                "59248875": null,
                "59199786": null,
                "59171589": null,
                "59088907": null,
                "58599621": null,
                "58228283": null,
                "58089967": null,
                "57645161": null,
                "57296786": null,
                "56852068": null,
                "56655498": null,
                "56469404": null,
                "56347460": null,
                "55980759": null,
                "55708506": null,
                "55624849": null,
                "55501670": null,
                "55426555": null,
                "55262397": null,
                "55093517": null,
                "54975682": null,
                "54895318": null,
                "54752415": null,
                "54539709": null,
                "54171672": null,
                "54120897": null,
                "54061660": null,
                "53996923": null,
                "53825081": null,
                "53727984": null,
                "53659284": null,
                "53643441": null,
                "53457352": null,
                "52770404": null,
                "52584732": null,
                "52283585": null,
                "51999695": null,
                "51629731": null,
                "51305367": null,
                "51193355": null,
                "51061575": null,
                "50731006": null,
                "50621938": null,
                "50260419": null,
                "50143466": null,
                "50063513": null,
                "49983419": null,
                "49939686": null,
                "49760760": null,
                "49630952": null,
                "49572025": null,
                "49496407": null,
                "49280105": null,
                "49170386": null,
                "48870060": null,
                "48094048": null,
                "47230834": null,
                "47165729": null,
                "47074939": null,
                "47005699": null,
                "46841504": null,
                "46783222": null,
                "46658411": null,
                "46542888": null,
                "46424195": null,
                "46335960": null,
                "46280543": null,
                "46193586": null,
                "45068381": null,
                "44770301": null,
                "44292299": null,
                "43898752": null,
                "43511315": null,
                "43265473": null,
                "42611051": null,
                "42445631": null,
                "42144929": null,
                "41989305": null,
                "41587004": null,
                "41522901": null,
                "41214443": null,
                "41044638": null,
                "40699965": null,
                "40559876": null,
                "40294494": null,
                "40236070": null,
                "40165191": null,
                "40087464": null,
                "40001513": null,
                "39968493": null,
                "39915208": null,
                "39631667": null,
                "39517132": null,
                "39050362": null,
                "38890387": null,
                "38863003": null,
                "38431160": null,
                "38253261": null,
                "38006246": null,
                "37914737": null,
                "36785381": null,
                "36554640": null,
                "36073611": null,
                "35950851": null,
                "35792776": null,
                "35399258": null,
                "34769177": null,
                "34286400": null,
                "33990421": null,
                "33646497": null,
                "33392274": null,
                "33136097": null,
                "32859651": null,
                "32186891": null,
                "31986000": null,
                "31910538": null,
                "31555320": null,
                "31301931": null,
                "31229996": null,
                "30960075": null,
                "30801430": null,
                "30566306": null,
                "29905757": null,
                "29521466": null,
                "29341925": null,
                "29172246": null,
                "29110416": null,
                "28869010": null,
                "28689114": null,
                "28331120": null,
                "28230846": null,
                "28016341": null,
                "27749866": null,
                "27607489": null,
                "27328462": null,
                "27177288": null,
                "27050781": null,
                "27045019": null,
                "27034666": null,
                "26906518": null,
                "26451821": null,
                "26376801": null,
                "26040386": null,
                "25891324": null,
                "25286806": null,
                "24870618": null,
                "24667534": null,
                "24551721": null,
                "24125148": null,
                "23873927": null,
                "23730017": null,
                "23729222": null,
                "23602294": null,
                "23520648": null,
                "23458965": null,
                "23427957": null,
                "23344517": null,
                "23197968": null,
                "23096530": null,
                "22873991": null,
                "22794952": null,
                "22692551": null,
                "22632053": null,
                "22521777": null,
                "22393681": null,
                "22274230": null,
                "22269891": null,
                "22190895": null,
                "22135747": null,
                "22101448": null,
                "22081271": null,
                "22011641": null,
                "21710605": null,
                "21700472": null,
                "21659141": null,
                "21658981": null,
                "21658823": null,
                "21658615": null,
                "21658485": null,
                "21348243": null,
                "21208006": null,
                "21119442": null,
                "21040567": null,
                "20878155": null,
                "20839327": null,
                "20820653": null,
                "20791620": null,
                "20765548": null,
                "20740870": null,
                "20721231": null,
                "20720968": null,
                "20688163": null,
                "20671712": null,
                "20346718": null,
                "20331678": null,
                "20307157": null,
                "20143420": null,
                "20072110": null,
                "20001948": null,
                "19926408": null,
                "19831180": null,
                "19810519": null,
                "19387360": null,
                "19294929": null,
                "19166205": null,
                "19139336": null,
                "19139246": null,
                "18661450": null,
                "18628933": null,
                "18610147": null,
                "18468542": null,
                "18468233": null,
                "18446956": null,
                "18426305": null,
                "18406690": null,
                "18391161": null,
                "18351865": null,
                "18253079": null,
                "18187055": null,
                "18171018": null,
                "17849916": null,
                "17723722": null,
                "17714279": null,
                "17240446": null,
                "16649385": null,
                "16649069": null,
                "16648415": null,
                "16647934": null,
                "16646788": null,
                "16523207": null,
                "16522974": null,
                "16522794": null,
                "13505702": null,
                "13472832": null,
                "11909886": null
            },
            "likeData": false,
            "width": 2067,
            "height": 1124,
            "pageCount": 1,
            "bookmarkCount": 4312,
            "likeCount": 3668,
            "commentCount": 39,
            "responseCount": 0,
            "viewCount": 52433,
            "bookStyle": 0,
            "isHowto": false,
            "isOriginal": false,
            "imageResponseOutData": [],
            "imageResponseData": [],
            "imageResponseCount": 0,
            "pollData": null,
            "seriesNavData": null,
            "descriptionBoothId": null,
            "descriptionYoutubeId": null,
            "comicPromotion": null,
            "fanboxPromotion": null,
            "contestBanners": [],
            "isBookmarkable": true,
            "bookmarkData": null,
            "contestData": null,
            "zoneConfig": {
                "responsive": {
                    "url": "https://pixon.ads-pixiv.net/show?zone_id=illust_responsive_side&format=js&s=0&up=0&a=27&ng=g&l=zh&uri=%2Fajax%2Fillust%2F_PARAM_&ref=www.pixiv.netwww.pixiv.net%2Fartworks%2F60066082&illust_id=60066082&K=ef5b3468b7e72&D=6b2199d8c9c19f0&ab_test_digits_first=15&yuid=EZY5FJU&num=6725a989629"
                },
                "rectangle": {
                    "url": "https://pixon.ads-pixiv.net/show?zone_id=illust_rectangle&format=js&s=0&up=0&a=27&ng=g&l=zh&uri=%2Fajax%2Fillust%2F_PARAM_&ref=www.pixiv.netwww.pixiv.net%2Fartworks%2F60066082&illust_id=60066082&K=ef5b3468b7e72&D=6b2199d8c9c19f0&ab_test_digits_first=15&yuid=EZY5FJU&num=6725a9892"
                },
                "500x500": {
                    "url": "https://pixon.ads-pixiv.net/show?zone_id=bigbanner&format=js&s=0&up=0&a=27&ng=g&l=zh&uri=%2Fajax%2Fillust%2F_PARAM_&ref=www.pixiv.netwww.pixiv.net%2Fartworks%2F60066082&illust_id=60066082&K=ef5b3468b7e72&D=6b2199d8c9c19f0&ab_test_digits_first=15&yuid=EZY5FJU&num=6725a989995"
                },
                "header": {
                    "url": "https://pixon.ads-pixiv.net/show?zone_id=header&format=js&s=0&up=0&a=27&ng=g&l=zh&uri=%2Fajax%2Fillust%2F_PARAM_&ref=www.pixiv.netwww.pixiv.net%2Fartworks%2F60066082&illust_id=60066082&K=ef5b3468b7e72&D=6b2199d8c9c19f0&ab_test_digits_first=15&yuid=EZY5FJU&num=6725a989140"
                },
                "footer": {
                    "url": "https://pixon.ads-pixiv.net/show?zone_id=footer&format=js&s=0&up=0&a=27&ng=g&l=zh&uri=%2Fajax%2Fillust%2F_PARAM_&ref=www.pixiv.netwww.pixiv.net%2Fartworks%2F60066082&illust_id=60066082&K=ef5b3468b7e72&D=6b2199d8c9c19f0&ab_test_digits_first=15&yuid=EZY5FJU&num=6725a989164"
                },
                "expandedFooter": {
                    "url": "https://pixon.ads-pixiv.net/show?zone_id=multiple_illust_viewer&format=js&s=0&up=0&a=27&ng=g&l=zh&uri=%2Fajax%2Fillust%2F_PARAM_&ref=www.pixiv.netwww.pixiv.net%2Fartworks%2F60066082&illust_id=60066082&K=ef5b3468b7e72&D=6b2199d8c9c19f0&ab_test_digits_first=15&yuid=EZY5FJU&num=6725a989813"
                },
                "logo": {
                    "url": "https://pixon.ads-pixiv.net/show?zone_id=logo_side&format=js&s=0&up=0&a=27&ng=g&l=zh&uri=%2Fajax%2Fillust%2F_PARAM_&ref=www.pixiv.netwww.pixiv.net%2Fartworks%2F60066082&illust_id=60066082&K=ef5b3468b7e72&D=6b2199d8c9c19f0&ab_test_digits_first=15&yuid=EZY5FJU&num=6725a98910"
                },
                "ad_logo": {
                    "url": "https://pixon.ads-pixiv.net/show?zone_id=t_logo_side&format=js&s=0&up=0&a=27&ng=g&l=zh&os=and&uri=%2Fajax%2Fillust%2F_PARAM_&ref=www.pixiv.netwww.pixiv.net%2Fartworks%2F60066082&illust_id=60066082&K=ef5b3468b7e72&D=6b2199d8c9c19f0&ab_test_digits_first=15&yuid=EZY5FJU&num=6725a989382"
                },
                "relatedworks": {
                    "url": "https://pixon.ads-pixiv.net/show?zone_id=relatedworks&format=js&s=0&up=0&a=27&ng=g&l=zh&uri=%2Fajax%2Fillust%2F_PARAM_&ref=www.pixiv.netwww.pixiv.net%2Fartworks%2F60066082&illust_id=60066082&K=ef5b3468b7e72&D=6b2199d8c9c19f0&ab_test_digits_first=15&yuid=EZY5FJU&num=6725a989737"
                }
            },
            "extraData": {
                "meta": {
                    "title": "#うたわれるもの クオン - 白糸的插画 - pixiv",
                    "description": "この作品 「クオン」 は 「うたわれるもの」「クオン」 等のタグがつけられた「白糸」さんのイラストです。 「LEAF！(￣︶￣)↗」",
                    "canonical": "https://www.pixiv.net/artworks/60066082",
                    "alternateLanguages": {
                        "ja": "https://www.pixiv.net/artworks/60066082",
                        "en": "https://www.pixiv.net/en/artworks/60066082"
                    },
                    "descriptionHeader": "本作「クオン」为附有「うたわれるもの」「クオン」等标签的插画。",
                    "ogp": {
                        "description": "LEAF！(￣︶￣)↗",
                        "image": "https://embed.pixiv.net/decorate.php?illust_id=60066082&mdate=1479827412",
                        "title": "#うたわれるもの クオン - 白糸的插画 - pixiv",
                        "type": "article"
                    },
                    "twitter": {
                        "description": "LEAF！(￣︶￣)↗",
                        "image": "https://embed.pixiv.net/decorate.php?illust_id=60066082&mdate=1479827412",
                        "title": "クオン",
                        "card": "summary_large_image"
                    }
                }
            },
            "titleCaptionTranslation": {
                "workTitle": null,
                "workCaption": null
            },
            "isUnlisted": false,
            "request": null,
            "commentOff": 0,
            "aiType": 0,
            "reuploadDate": null,
            "locationMask": false,
            "commissionLinkHidden": false
        }
    },
    "backup_urls": []
}
```

</details>

If you set `quick_mode` to `True` in PixivKeywordParser, then the result is like:

<details>
<summary><b>ImageInfo Structure in JSON</b></summary>

```JSON
{
    "url": "https://i.pximg.net/img-original/img/2016/11/23/00/10/12/60066082_p0.jpg",
    "name": "60066082_p0.jpg",
    "info": {
        "id": "60066082",
        "width": 2067,
        "height": 1124,
        "tags": [
            "うたわれるもの",
            "クオン",
            "クオン(うたわれるもの)",
            "偽りの仮面",
            "うたわれるもの1000users入り",
            "はいてない"
        ],
        "info": {
            "id": "60066082",
            "title": "クオン",
            "illustType": 0,
            "xRestrict": 0,
            "restrict": 0,
            "sl": 4,
            "url": "https://i.pximg.net/c/250x250_80_a2/img-master/img/2016/11/23/00/10/12/60066082_p0_square1200.jpg",
            "description": "",
            "tags": [
                "うたわれるもの",
                "クオン",
                "クオン(うたわれるもの)",
                "偽りの仮面",
                "うたわれるもの1000users入り",
                "はいてない"
            ],
            "userId": "2175653",
            "userName": "白糸",
            "width": 2067,
            "height": 1124,
            "pageCount": 1,
            "isBookmarkable": true,
            "bookmarkData": null,
            "alt": "#うたわれるもの クオン - 白糸的插画",
            "titleCaptionTranslation": {
                "workTitle": null,
                "workCaption": null
            },
            "createDate": "2016-11-23T00:10:12+09:00",
            "updateDate": "2016-11-23T00:10:12+09:00",
            "isUnlisted": false,
            "isMasked": false,
            "aiType": 0,
            "profileImageUrl": "https://i.pximg.net/user-profile/img/2015/03/30/16/31/47/9164255_825d9067d54dfc635e4477c38508b6f5_50.jpg"
        }
    },
    "backup_urls": []
}
```

</details>

If you set `quick_mode` to `True` in PixivUserParser, then the result is like:

<details>
<summary><b>ImageInfo Structure in JSON</b></summary>

```JSON
{
    "url": "https://i.pximg.net/img-original/img/2016/11/23/00/10/12/60066082_p0.jpg",
    "name": "60066082_p0.jpg",
    "info": {
        "id": "60066082",
        "width": 2067,
        "height": 1124
    },
    "backup_urls": []
}
```

</details>

### Example Program

For PixivKeywordParser, [This example](../examples/pixiv_keyword_example.py) will download images with keyword / tag `クオン` and `うたわれるもの1000users入り` which are neither manga nor generated by AI into the "Pixiv" folder. After you logging in to Pixiv, the cookies will be saved at `Pixiv_cookies.json` for later use. `quick_mode` is set to `True` in this example.

For PixivUserParser, [This example](../examples/pixiv_user_example.py) will download the newest 30 images from [Pixiv member ID 2175653](https://www.pixiv.net/users/2175653) into the "Pixiv_user_2175653" folder. After you logging in to Pixiv, the cookies will be saved at `Pixiv_cookies.json` for later use. `quick_mode` is set to `False` (default) in this example.

## Twitter / X

The main station URL of Twitter / X is: https://x.com/

If you want to download restricted contents, please configure your account settings before using Parsers.

### Get Twitter Cookies

```Python
from image_crawler_utils.stations.twitter import get_twitter_cookies

cookies = get_twitter_cookies(
    twitter_account='phone_number or user_id or mail@address',
    user_id='user_id',
    password='password',
    proxies={"proxy_type": "proxy_address"},
)
```

+ `twitter_account`: Your phone number / user ID / mail address
+ `user_id`: Your user ID, in case there are verifications.
  + User ID is the string behind @ in your account, like `@Account -> Account`
+ `password`: Password of your account.
+ `proxies`: Proxies to use when opening the logging-in webpage. It uses the same form as the one in [tutorials.md#DownloadConfig](tutorials.md#downloadconfig).

The result is a `image_crawler_utils.Cookies` class.

### Parsers

Parsers of Twitter / X will not use the `page_num` parameter, as no gallery pages exist in Twitter / X.

`image_num` will be used by Parsers of Twitter / X, but actual image number may exceed this parameter.
+ Twitter / X Parsers will only determine whether the number of images has exceeded `image_num` after a Twitter / X searching result page is fully scanned, or a batch of Twitter / X searching result pages are fully scanned.

#### TwitterKeywordMediaParser

The parameters are like:

```Python
from image_crawler_utils.stations.twitter import TwitterKeywordMediaParser

TwitterKeywordMediaParser(
    station_url: str="https://x.com/",
    crawler_settings: CrawlerSettings=CrawlerSettings(),
    standard_keyword_string: str | None=None, 
    keyword_string: str | None=None,
    cookies: Cookies | list | dict | str | None=Cookies(),
    twitter_search_settings: TwitterSearchSettings=TwitterSearchSettings(),
    reload_times: int=1,
    error_retry_delay: float=200,
    headless: bool=True,
)
```

+ `station_url`: Main URL of Pixiv station. Default set to `"https://x.com/"`.
+ `crawler_settings`: The CrawlerSettings used in this parser.
+ `standard_keyword_string`: Query keyword string using standard syntax.
+ `keyword_string`: If you want to directly specify the keywords used in searching, set `keyword_string` to a custom non-empty string. It will OVERWRITE `standard_keyword_string`.
+ `cookies`: Cookies used to access information from a website.
  + Can be one of `image_crawler_utils.Cookies`, `list`, `dict`, `str` or `None`.
    + Leave this parameter blank works the same as `None` / `Cookies()`.
+ `twitter_search_settings`: A TwitterSearchSettings class that contains extra options when searching. Refer to the [TwitterSearchSettings](#twittersearchsettings) chapter for more details.
+ `reload_times`: Reload the page for `reload_times` times. May be useful when there are status (tweets) not detected.
+ `error_retry_delay`: When Twitter / X returns an error, the Parser will retry after `error_retry_delay` seconds.
+ `headless`: Do not display browsers window when a browser is started. Set to `False` will pop up browser windows.

##### TwitterSearchSettings

TwitterSearchSettings controls advanced searching settings. It will append an string to the keyword string according to the settings in this class.

The parameters are like:

```Python
from image_crawler_utils.stations.twitter import TwitterSearchSettings

TwitterSearchSettings(
    from_users: list[str] | str | None = None
    to_users: list[str] | str | None = None
    mentioned_users: list[str] | str | None = None
    including_replies: bool = True
    only_replies: bool = False
    including_links: bool = True
    only_links: bool = False
    including_media: bool = True
    only_media: bool = False
    min_reply_num: int | None = None
    min_favorite_num: int | None = None
    min_retweet_num: int | None = None
    starting_date: str = ''
    ending_date: str = ''
)
```

+ `from_users`: Select tweets sent by a certain user / a certain list of users.
+ `to_users`: Select tweets replying to a certain user / a certain list of users.
+ `mentioned_users`: Select tweets that mention a certain user / a certain list of users.
+ `including_replies`: Including reply tweets.
+ `only_replies`: Only including reply tweets. Works only if `including_replies` is set to `True` (default).
+ `including_links`: Including tweets that contain at least one link.
+ `only_links`: Only including tweets that contain at least one link. Works only if `including_links` is set to `True` (default).
+ `including_media`: Including tweets that contain at least one media.
+ `only_links`: Only including tweets that contain at least one media. Works only if `including_media` is set to `True` (default).
+ `min_reply_num`: Including tweets with more than `min_reply_num` replies.
+ `min_favorite_num`: Including tweets with more than `min_reply_num` favorites.
+ `min_retweet_num`: Including tweets with more than `min_reply_num` retweets.
+ `starting_date`: Tweets after this date. Must be "YYYY-MM-DD", "YYYY.MM.DD" or "YYYY/MM/DD" format.
+ `ending_date`: Tweets before this date. Must be "YYYY-MM-DD", "YYYY.MM.DD" or "YYYY/MM/DD" format.

#### TwitterUserMediaParser

TwitterUserMediaParser uses searching status (tweets) with media sent by a certain users to get their media images.

The parameters are like:

```Python
from image_crawler_utils.stations.twitter import TwitterUserMediaParser

TwitterUserMediaParser(
    user_id: str,
    station_url: str="https://x.com/",
    crawler_settings: CrawlerSettings=CrawlerSettings(),
    cookies: Cookies | list | dict | str | None=Cookies(),
    reload_times: int=1,
    error_retry_delay: float=200,
    interval_days: int=180,
    starting_date: str | None=None,
    ending_date: str | None=None,
    exit_when_empty: bool=False,
    headless: bool=True,
)
```

+ `station_url`
+ `crawler_settings`
+ `cookies`
+ `reload_times`
+ `error_retry_delay`
+ `headless`
  + Refer to the [TwitterKeywordMediaParser](#TwitterKeywordMediaParser) chapter for the meaning of these parameters.
+ `user_id`: The user id of a Twitter / X user. Can be acquired by their user pages, or the string behind @ in their tweets. For example, user page https://x.com/ywwuyi contains their user id ywwuyi.
+ `interval_days`: Interval day length of one searching result page.
+ `starting_date`: Retrieving media images after this date. Must be "YYYY-MM-DD", "YYYY.MM.DD" or "YYYY/MM/DD" format.
+ `ending_date`: Retrieving media images before this date. Must be "YYYY-MM-DD", "YYYY.MM.DD" or "YYYY/MM/DD" format.
  + `interval_days`, `starting_date` and `ending_date` will decide how many searching result pages will be loaded. For example, setting `starting_date="2023-01-01", ending_date="2024-01-01", interval_days=180` will let the Parser searches three pages which are respectively from 2023-01-01 to 2023-01-06, from 2023-01-06 to 2023-07-05, and from 2023-07-05 to 2024-01-01.
  + It is suggested to set `interval_days` to a smaller value if a user sent many status (tweets) in a short period, and vice versa.
+ `exit_when_empty`: If a page without any status (tweets) is detected in a batch of pages, then after this batch finished, stop loading new pages.
  + Should only set to `True` if the user send tweets frequently (at least 1 status (tweet) in every `interval_days`) till now (or `ending_date` if it is not `None`).
  + If the conditions above are met, set this parameter to `True` will reduce the time of parsing images and the probability of Twitter / X error happening.

### ImageInfo Structure

The example image is from [this Twitter / X status (tweet)](https://x.com/InarikoNkoNa/status/1622634960543973376).

<details>
<summary><b>ImageInfo Structure in JSON</b></summary>

```JSON
{
    "url": "https://pbs.twimg.com/media/FoTAPazaUAIXFk4?format=jpg&name=orig",
    "name": "1622634960543973376.jpg",
    "info": {
        "status_url": "https://x.com/InarikoNkoNa/status/1622634960543973376",
        "status_id": "1622634960543973376",
        "user_id": "InarikoNkoNa",
        "user_name": "こんこんいなり",
        "time": "2023-02-06T16:34:56.000Z",
        "reply_num": 0,
        "retweet_num": 45,
        "like_num": 135,
        "view_num": 3430,
        "text": "#うたわれるもの \n\nたくさん食べるクオンがかわいい\nhttps://pixiv.net/artworks/105154125…",
        "hashtags": [
            "#うたわれるもの"
        ],
        "links": [
            "https://t.co/cqC48ELZxW"
        ],
        "media_list": [
            {
                "link": "https://x.com/InarikoNkoNa/status/1622634960543973376/photo/1",
                "image_source": "https://pbs.twimg.com/media/FoTAPazaUAIXFk4?format=jpg&name=orig",
                "image_id": "FoTAPazaUAIXFk4",
                "image_name": "1622634960543973376.jpg"
            }
        ]
    },
    "backup_urls": []
}
```

</details>

### Example Program

For TwitterKeywordMediaParser, [This example](../examples/twitter_keyword_example.py) will download images with keyword (hashtags) `#クオン`, `#イラスト` and `#うたわれるもの` which are sent before 2024/01/01 and only includes tweets with media into the "Twitter" folder. After you logging in to Twitter / X, the cookies will be saved at `Twitter_cookies.json` for later use.

For TwitterUserMediaParser, [This example](../examples/twitter_user_example.py) will download media images of user `idonum` from 2023/1/1 to 2024/1/1 into the "Twitter_user_idonum" folder. After you logging in to Twitter / X, the cookies will be saved at `Twitter_cookies.json` for later use.
