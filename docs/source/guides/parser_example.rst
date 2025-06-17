Guide: Parser Class (DanbooruKeywordParser)
===========================================

Basic Usage
~~~~~~~~~~~

A Parser will parse image information from websites.

Parsers for a certain website are provided in ``image_crawler_utils.stations.certain_website``; for example, to import the keyword Parser for Danbooru, use ``from image_crawler_utils.stations.booru import DanbooruKeywordParser``.

Parsers should be configured when created, and once you set up a Parser, use ``image_info_list = Parser.run()`` to get a list of image information, which can be passed on to Downloader.

DanbooruKeywordParser Class
~~~~~~~~~~~~~~~~~~~~~~~~~~~

DanbooruKeywordParser can be a typical example of showing how a Parser works.

The most used attributes of :class:`DanbooruKeywordParser <image_crawler_utils.stations.booru.DanbooruKeywordParser>` are like:

.. autoclass:: image_crawler_utils.stations.booru.DanbooruKeywordParser
    :no-index:
    :show-inheritance:
    :members: run, save_to_pkl, load_from_pkl, display_all_configs

Examples of DanbooruKeywordParser
---------------------------------

An example of parsing information of images with keyword ``kuon_(utawarerumono)`` and ``rating:safe`` from Danbooru is like:

.. code-block:: python

    from image_crawler_utils.stations.booru import DanbooruKeywordParser

    parser = DanbooruKeywordParser(
        crawler_settings=crawler_settings,  # Need to be defined in advance
        standard_keyword_string="kuon_(utawarerumono) AND rating:safe",
    )
    image_info_list = parser.run()


A Parser class can be saved by ``.save_to_pkl()``, or loaded with ``.load_from_pkl()`` from its corresponding class (e.g. ``DanbooruKeywordParser.load_from_pkl()``), like:

.. code-block:: python

    from image_crawler_utils.stations.booru import DanbooruKeywordParser

    parser = DanbooruKeywordParser(
        crawler_settings=crawler_settings,  # Must be defined in advance
        standard_keyword_string="kuon_(utawarerumono) AND rating:safe",
    )
    # Save a DanbooruKeywordParser
    parser.save_to_pkl('parser.pkl')

    # Load a DanbooruKeywordParser
    new_parser = DanbooruKeywordParser.load_from_pkl('parser.pkl')

Use ``.display_all_configs()`` to check all parameters of current Parser.

Standard Keyword String
~~~~~~~~~~~~~~~~~~~~~~~

As different stations may have different syntaxes for keyword searching, Image Crawler Utils uses a standard syntax to parse the keyword string. It is can be used in most preset Parsers for the ``standard_keyword_string`` parameter.

The grammar is like:

+ Logic symbols:

    + ``AND`` / ``&`` means searching images with both keywords / tags.
    + ``OR`` / ``|`` means searching images with either of the keywords / tags.
    + ``NOT`` / ``!`` means searching images without this keyword / tag.
    + ``[`` and ``]`` works like brackets in normal expressions, increasing the priority of the keyword / tag string included.

        + It is STRONGLY recommended to use ``[`` and ``]`` in order to avoid ambiguity.

    + Priority of logic symbols is the same as C language, which is: **OR < AND < NOT < [ = ]**

.. important::

    ``(`` and ``)`` are considered part of the keywords / tags instead of a logic symbol.
            
+ Escape characters: Add ``\`` before any of the characters above except ``(`` and ``)`` to represent itself (like ``\&``), while ``\\`` represents ``\``.

.. tip::
    
    ``\[`` and ``\]`` are not escape characters in Python.

+ If two keywords / tags have no logic symbols in between, they will be considered one keyword / tag connected by ``_``. For example, ``kuon (utawarerumono)`` works the same as ``kuon_(utawarerumono)``.
+ Keyword wildcards: ``*`` can be replaced with any string (include empty string).

    + ``*key`` means all keywords / tags that end with ``key``. For example, ``*dress`` can match ``dress`` and ``chinadress``.
    + ``key*`` means all keywords / tags that start with ``key``. For example, ``dress*`` can match ``dress`` and ``dress_shirt``.
    + ``*key*`` means all keywords / tags that contain ``key``. For example, ``*dress*`` can match ``dress``, ``chinadress`` and ``dress_shirt``.
    + ``ke*y`` means all keywords / tags that start with ``ke`` and end with ``y``. For example, ``satono*(umamusume)`` can match ``satono_diamond_(umamusume)`` and ``satono_crown_(umamusume)``.
    + These wildcards can be combined, like ``*ke*y``.

Example: ``*dress AND NOT [kuon (utawarerumono) OR chinadress]`` means search for images with keywords including ones ending with ``dress`` while excluding those having keywords ``kuon_(utawarerumono)`` and ``chinadress``.

.. important::
    
    Some sites may not support all of the syntaxes above, or have restrictions on keyword searching. Refer to the corresponding Parser class documentation for more details.

Cookies Class
~~~~~~~~~~~~~

Cookies are frequently used in Parsers and (sometimes) Downloader class to obtain some information and images. Image Crawler Utils provides :class:`Cookies <image_crawler_utils.Cookies>` to provide a unified class for loading and utilizing cookies.

Cookies class can be directly used as parameters in Parsers and Downloader classes, saved (:func:`image_crawler_utils.Cookies.save_to_json`) and loaded (:func:`image_crawler_utils.Cookies.load_from_json`) for later use, and use its different forms (attributes, like ``.cookies_string``) for other uses.

.. important::
    
    Once a Cookies class is created, its attributes cannot be changed.

Some functions are provided to fetch cookies from certain websites (usually requires manual operations due to protections like Cloudflare), like :func:`get_pixiv_cookies <image_crawler_utils.stations.pixiv.get_pixiv_cookies>` and :func:`get_twitter_cookies <image_crawler_utils.stations.twitter.get_twitter_cookies>`. Their return value is a Cookies class. Please check out their documentation and :doc:`../task_notes/index_tasks` for more details.

.. autoclass:: image_crawler_utils.Cookies
    :no-index:
    :members:
    :show-inheritance:
    :undoc-members:
    :inherited-members:

ImageInfo class
~~~~~~~~~~~~~~~

The result of Parsers is (and must be) a list of :class:`ImageInfo <image_crawler_utils.ImageInfo>`. The structure of ImageInfo class is like:

.. autoclass:: image_crawler_utils.ImageInfo
    :no-index:
    :members:
    :show-inheritance:
    :undoc-members:
    :inherited-members:

Save and Load the List of ImageInfo Class
-----------------------------------------

The list of ImageInfo class can be saved with :func:`image_crawler_utils.save_image_infos` and loaded with :func:`image_crawler_utils.load_image_infos`:

.. autofunction:: image_crawler_utils.save_image_infos
    :no-index:

.. autofunction:: image_crawler_utils.load_image_infos
    :no-index:

Examples of ImageInfo
-----------------------------------------------------------------------

A JSON-converted example of ImageInfo generated by DanbooruKeywordParser from `image ID 4994142 <https://danbooru.donmai.us/posts/4994142>`_ is like:

.. collapse:: CLICK HERE TO DISPLAY

    .. literalinclude:: ../JSONs/Danbooru 4994142.json

---------

If you want to get the tags of this image (assume its ``image_info`` is an ImageInfo class), you should use ``image_info.info["tags"]`` instead of ``image_info["info"]["tags"]`` or ``image_info.info.tags``.
