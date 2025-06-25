Booru Tasks
===========

Booru-related Parsers can be imported from :mod:`image_crawler_utils.stations.booru`. Check out its documentation for more details.

Keyword Filter for Booru
~~~~~~~~~~~~~~~~~~~~~~~~

Booru-structured sites share a keyword filter :func:`image_crawler_utils.stations.booru.filter_keyword_booru`. It will check whether a standard syntax keyword string matches the tags of an image.

+ For example, "kuon\_(utawarerumono) OR chinadress" matches tags "kuon\_(utawarerumono)", "hair_ornament", while "kuon\_(utawarerumono) AND chinadress" does not match.

To use it in Downloader is like:

.. code-block:: python

    from image_crawler_utils.stations.booru import filter_keyword_booru

    downloader = Downloader(
        image_info_filter=lambda info: filter_keyword_booru(info, "kuon_(utawarerumono) OR chinadress")
    )

Danbooru Tips
~~~~~~~~~~~~~

+ The main station URL of Danbooru is: https://danbooru.donmai.us/

.. seealso::

    `Danbooru's cheatsheet <https://danbooru.donmai.us/wiki_pages/help:cheatsheet>`_
        Read this page before searching in Danbooru.

About DanbooruKeywordParser
---------------------------

For the meaning of parameters and attributes, check out the documentation of :class:`DanbooruKeywordParser <image_crawler_utils.stations.booru.DanbooruKeywordParser>`.

.. important::
    
    Danbooru sometimes does not accept user agents. Leave the parameter ``headers`` blank (or set to :py:data:`None`) in :class:`CrawlerSettings <image_crawler_utils.CrawlerSettings>` is acceptable.

.. note::
    
    For free users, Danbooru only supports searching at most 2 keywords / tags at the same time (can be connected by logic symbols). Refer to the :class:`DanbooruKeywordParser <image_crawler_utils.stations.booru.DanbooruKeywordParser>` documentation for more details.

Example Program of DanbooruKeywordParser
----------------------------------------

This example program downloads the first 20 images from Danbooru with keyword / tag "kuon\_(utawarerumono)" and "rating:general" into the ``Danbooru`` folder. Information of images will be stored in ``image_info_list.json`` at same the path of your program.

.. literalinclude:: ../../../examples/danbooru_example.py

Example ImageInfo of DanbooruKeywordParser
------------------------------------------

This example image information (Danbooru ID 4994142) is from `this Danbooru page <https://danbooru.donmai.us/posts/4994142>`_. Its :class:`ImageInfo <image_crawler_utils.ImageInfo>` structure in JSON is like:

.. collapse:: CLICK HERE TO DISPLAY

    .. literalinclude:: ../JSONs/Danbooru 4994142.json

---------

Moebooru Tips
~~~~~~~~~~~~~

Currently supported Moebooru websites are listed below.

+ The main station URL of yande.re is: https://yande.re/
+ The main station URL of konachan.com is: https://konachan.com/
+ The main station URL of konachan.net is: https://konachan.net/

    + konachan.net is the non-explicit version of konachan.com. Both share the same rules when searching.

.. important::

    konachan.com sometimes has a Cloudflare protection. Set ``has_cloudflare`` to :py:data:`True` in MoebooruKeywordParser and do a manual clicking when Cloudflare page is displayed.

    If you got stuck in the Cloudflare checking page, try changing an IP address (with a proxy) or switch to another environment to access.

.. seealso::

    `yande.re's cheatsheet <https://yande.re/help/cheatsheet>`_
        Read this pages before searching in yande.re.

    `Konachan's cheatsheet <https://konachan.net/help/cheatsheet>`_
        Read this pages before searching in Konachan.

About MoebooruKeywordParser
---------------------------

For the meaning of parameters and attributes, check out the documentation of :class:`MoebooruKeywordParser <image_crawler_utils.stations.booru.MoebooruKeywordParser>`.

.. important::

    Currently, Moebooru-supported websites allow keywords connected by only one type of logic symbol (``AND`` or ``OR`` in ``standard_keyword_string``).

Example Program of MoebooruKeywordParser
----------------------------------------

For yande.re, this example will download images with keyword / tag "kuon\_(utawarerumono)" and "rating:safe" into the "Yandere" folder using JSON-API.

.. literalinclude:: ../../../examples/yandere_example.py

For konachan.com, this example will download images with keyword / tag "kuon\_(utawarerumono)" and "rating:safe" into the "Konachan_com" folder without using JSON-API.

.. literalinclude:: ../../../examples/konachan_example.py

Example ImageInfo of MoebooruKeywordParser
------------------------------------------

This example image information (yande.re ID 444116) is from `this yande.re page <https://yande.re/post/show/444116>`_.

With ``use_api`` set to :py:data:`True`, its :class:`ImageInfo <image_crawler_utils.ImageInfo>` structure in JSON is like:

.. collapse:: CLICK HERE TO DISPLAY

    .. literalinclude:: ../JSONs/yande.re 444116 use_api.json

---------

With ``use_api`` set to :py:data:`False`, its :class:`ImageInfo <image_crawler_utils.ImageInfo>` structure in JSON is like:

.. collapse:: CLICK HERE TO DISPLAY

    .. literalinclude:: ../JSONs/yande.re 444116 gallery.json

---------

This example image information (Konachan ID 249445) is from `this konachan.net page <https://konachan.net/post/show/249445/autumn-bow-goumudan-kuon_-utawarerumono-leaves-lon>`_.

.. collapse:: CLICK HERE TO DISPLAY

    .. literalinclude:: ../JSONs/konachan.net 249445.json

---------

Gelbooru Tips
~~~~~~~~~~~~~

+ The main station URL of Gelbooru is: https://gelbooru.com/

.. seealso::

    `Gelbooru's cheatsheet <https://gelbooru.com/index.php?page=wiki&s=view&id=26263>`_
        Read this page before searching in Gelbooru.

About GelbooruKeywordParser
---------------------------

For the meaning of parameters and attributes, check out the documentation of :class:`GelbooruKeywordParser <image_crawler_utils.stations.booru.GelbooruKeywordParser>`.

.. important::

    Currently, logic symbol ``OR`` (in ``standard_keyword_string``) is not supported in Gelbooru.

.. important::

    Some keywords / tags are protected by Cloudflare and thus not directly accessible by GelbooruKeywordParser. Please check out in your browser first before crawling!.

.. warning::

    If ``use_api`` is set to :py:data:`True`, it is required to have ``api_key`` and ``user_id`` in order to access JSON-API pages. The values can be found at the **API Access Credentials** column of https://gelbooru.com/index.php?page=account&s=options after logging in.

Example Program of GelbooruKeywordParser
----------------------------------------

For Gelbooru, this example will download images with keyword / tag "kuon\_(utawarerumono)" and "rating:general" into the "Gelbooru" folder.

.. literalinclude:: ../../../examples/gelbooru_example.py

Example ImageInfo of GelbooruKeywordParser
------------------------------------------

This example image information (Gelbooru ID 7963712) is from `this Gelbooru page <https://gelbooru.com/index.php?page=post&s=view&id=7963712>`_.

With ``use_api`` set to :py:data:`True`, its :class:`ImageInfo <image_crawler_utils.ImageInfo>` structure in JSON is like:

.. collapse:: CLICK HERE TO DISPLAY

    .. literalinclude:: ../JSONs/Gelbooru 7963712 use_api.json

---------

With ``use_api`` set to :py:data:`False`, its :class:`ImageInfo <image_crawler_utils.ImageInfo>` structure in JSON is like:

.. collapse:: CLICK HERE TO DISPLAY

    .. literalinclude:: ../JSONs/Gelbooru 7963712 gallery.json

---------

Safebooru Tips
~~~~~~~~~~~~~~

+ The main station URL of Safebooru is: https://safebooru.org/

.. seealso::

    `Safebooru's cheatsheet <https://safebooru.org/index.php?page=help&topic=cheatsheet>`_
        Read this page before searching in Gelbooru.

About SafebooruKeywordParser
----------------------------

For the meaning of parameters and attributes, check out the documentation of :class:`SafebooruKeywordParser <image_crawler_utils.stations.booru.SafebooruKeywordParser>`.

Example Program of SafebooruKeywordParser
-----------------------------------------

For Safebooru, this example will download images with keyword / tag "kuon\_(utawarerumono)" into the "Safebooru" folder.

.. literalinclude:: ../../../examples/safebooru_example.py

Example ImageInfo of SafebooruKeywordParser
-------------------------------------------

This example image information (Safebooru ID 2193950) is from `this Safebooru page <https://safebooru.org/index.php?page=post&s=view&id=2193950>`_. Its :class:`ImageInfo <image_crawler_utils.ImageInfo>` structure in JSON is like:

.. collapse:: CLICK HERE TO DISPLAY

    .. literalinclude:: ../JSONs/Safebooru 2193950.json

---------
