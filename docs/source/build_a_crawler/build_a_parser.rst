Construct a Custom Parser
=========================

Basicallly, constructing a custom Parser should follow 3 rules:

1. Inherit the :class:`Parser <image_crawler_utils.Parser>` or :class:`KeywordParser <image_crawler_utils.Parser>` class, according to your task requirements.
#. Use the parameters provided in the base class with additional parameters for your task to finish the custom Parser class.
#. Override the ``.run()`` attribute with its returning value following the form of a list of :class:`ImageInfo <image_crawler_utils.ImageInfo>`. An error will be raised if you do not override it!

Inherit a Parser Class
~~~~~~~~~~~~~~~~~~~~~~

Parser Class
------------

For most tasks, you can just inherit the Parser class.

You can utilize the attribute functions provided to simplify your programs, especially these functions for fetching websites:

+ :func:`image_crawler_utils.Parser.request_page_content` for fetching content for one single page.
+ :func:`image_crawler_utils.Parser.threading_request_page_content` for fetching contents for multiple pages.
+ Their nodriver counterpart, :func:`image_crawler_utils.Parser.nodriver_request_page_content` and :func:`image_crawler_utils.Parser.nodriver_threading_request_page_content`, for websites having rather stronger anti-crawling measures.
    + Google Chrome is required for running these 2 functions.

All parameters and attribute functions are listed here:

.. autoclass:: image_crawler_utils.Parser
    :no-index:
    :members:
    :show-inheritance:
    :undoc-members:

KeywordParser class
-------------------

If your task is to download from the result of searching with a query string, it is recommended to inherit :class:`KeywordParser <image_crawler_utils.Parser>`, which inherits the base :class:`Parser <image_crawler_utils.Parser>` class with several parameters and attribute functions defined specifically for this purpose.

+ For parameters and attribute functions in the original :class:`Parser <image_crawler_utils.Parser>` class, please read the documentation above.

.. autoclass:: image_crawler_utils.KeywordParser
    :no-index:
    :members:
    :show-inheritance:
    :undoc-members:

Completing the Parser Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

About the Usage of CrawlerSettings Class
----------------------------------------

The parameters passed into CrawlerSettings class is arranged as such:

+ ``image_num``, ``capacity`` and ``page_num`` will be stored in ``CrawlerSettings().capacity_count_config``, which is a :class:`CapacityCountConfig <image_crawler_utils.configs.CapacityCountConfig>` class.
    + To use the parameter in the Parser with the ``crawler_settings`` parameter passed in, you need to write the code like

    .. code-block:: python
        
        self.crawler_settings.capacity_count_config.image_num

+ ``headers``, ``proxies``, ``thread_delay``, ``fail_delay``, ``randomize_delay``, ``thread_num``, ``timeout``, ``max_download_time``, ``retry_time`` and ``overwrite_images`` will be stored in ``CrawlerSettings().download_config``, which is a :class:`DownloadConfig <image_crawler_utils.configs.DownloadConfig>` class.
    + To use the parameter in the Parser with the ``crawler_settings`` parameter passed in, you need to write the code like

    .. code-block:: python
        
        self.crawler_settings.download_config.headers

+ ``debug_config`` and ``detailed_console_log`` will be used to set up ``CrawlerSettings().log``, which is a :class:`Log <image_crawler_utils.log.Log>` class that controls logging information.
    + If you use ``.set_logging_file()`` to set the logging file, the ``CrawlerSettings().log`` will be accordingly changed.
    + To log information in your custom Parser, you need to write the code like

    .. code-block:: python
        
        self.crawler_settings.log.info("LOGGING INFO")

    + For detailed information, check out the documentation of :class:`Log <image_crawler_utils.log.Log>` class.
+ ``extra_configs`` will be stored in ``CrawlerSettings().extra_configs``.

KeywordParser Tips
------------------

If you inherit the KeywordParser, the first thing suggested to do is to write a function (like ``.generate_keyword_string()``) which converts the :ref:`Standard Keyword String` (stored in ``.standard_keyword_string``) to the query string for your task and store it in ``.keyword_string``.

1. Run the ``super().__init__()`` in the ``__init__()`` function of the inherited class to generate the ``self.keyword_tree`` attribute, which is a :class:`image_crawler_utils.keyword.KeywordLogicTree`.
    + It is suggested to read the documentation of :class:`image_crawler_utils.keyword.KeywordLogicTree` first.
#. Write the function that construct the function that generates the ``.keyword_string`` attribute from ``self.keyword_tree``.

Also, to be consistent with preset KeywordParsers, it is suggested to use ``.keyword_string`` before converted ``.standard_keyword_string`` if ``.keyword_string`` is not empty, and an error shall be raised only if both parameters are empty.

An example (from :class:`DanbooruKeywordParser <image_crawler_utils.stations.booru.DanbooruKeywordParser>`) is like:

.. code-block:: python

    def __init__(
        self, 
        station_url: str="https://danbooru.donmai.us/",
        crawler_settings: CrawlerSettings=CrawlerSettings(),
        standard_keyword_string: Optional[str]=None, 
        keyword_string: Optional[str]=None,
        cookies: Optional[Union[Cookies, list, dict, str]]=Cookies(),
        replace_url_with_source_level: str="None",
        use_keyword_include: bool=False,
    ):

        super().__init__(
            station_url=station_url,
            crawler_settings=crawler_settings,  
            standard_keyword_string=standard_keyword_string, 
            keyword_string=keyword_string,
            cookies=cookies,
        )
        self.replace_url_with_source_level = replace_url_with_source_level.lower()
        self.use_keyword_include = use_keyword_include


    # Generate keyword string from keyword tree
    def __build_keyword_str(self, tree: KeywordLogicTree) -> str:
        # Generate standard keyword string
        if isinstance(tree.lchild, str):
            res1 = tree.lchild
        else:
            res1 = self.__build_keyword_str(tree.lchild)
        if isinstance(tree.rchild, str):
            res2 = tree.rchild
        else:
            res2 = self.__build_keyword_str(tree.rchild)

        if tree.logic_operator == "AND":
            return f'({res1} {res2})'
        elif tree.logic_operator == "OR":
            return f'({res1} or {res2})'
        elif tree.logic_operator == "NOT":
            return f'(-{res2})'
        elif tree.logic_operator == "SINGLE":
            return f'{res2}'


    # Basic keyword string
    def generate_keyword_string(self) -> str:            
        self.keyword_string = self.__build_keyword_str(self.keyword_tree)
        return self.keyword_string
