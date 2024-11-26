<h1 align="center">
Classes and Functions
</h1>

This document includes information about classes and functions except those in `image_crawler_utils.stations` and `image_crawler_settings.configs`, whose information can be found respectively in [notes for tasks](notes_for_tasks.md) and [tutorials#Configs](tutorials.md#configs). It is suggested to finish [README](../README.md) and [tutorials](tutorials.md) before reading this.

Second-level headings can be imported from first-level headings; for example, `CrawlerSettings` in the `image_crawler_utils` chapter can be imported as `from image_crawler_utils import CrawlerSettings`.

If you want to build a custom you only need to construct a [Parser](#parser) / [KeywordParser](#keywordparser), whose `CustomParser.run()` should return a list of `image_crawler_utils.ImageInfo`. The Downloader class can handle this list for downloading.

+ Detailed information about `image_crawler_utils.ImageInfo` class can be found at [tutorials#The list of ImageInfo()](tutorials.md#the-list-of-imageinfo).

**Table of Contents**

- [image\_crawler\_utils](#image_crawler_utils)
  - [CrawlerSettings](#crawlersettings)
  - [ImageInfo](#imageinfo)
  - [save\_image\_infos()](#save_image_infos)
  - [load\_image\_infos()](#load_image_infos)
  - [Parser](#parser)
  - [KeywordParser](#keywordparser)
  - [Cookies](#cookies)
  - [update\_nodriver\_browser\_cookies()](#update_nodriver_browser_cookies)
- [image\_crawler\_utils.keyword](#image_crawler_utilskeyword)
  - [KeywordLogicTree](#keywordlogictree)
  - [construct\_keyword\_tree()](#construct_keyword_tree)
  - [construct\_keyword\_tree\_from\_list()](#construct_keyword_tree_from_list)
  - [min\_len\_keyword\_group()](#min_len_keyword_group)
- [image\_crawler\_utils.log](#image_crawler_utilslog)
  - [Log](#log)
  - [print\_logging\_msg()](#print_logging_msg)
- [image\_crawler\_utils.user\_agent](#image_crawler_utilsuser_agent)
  - [UserAgent](#useragent)
- [image\_crawler\_utils.utils](#image_crawler_utilsutils)
  - [Empty](#empty)
  - [custom\_tqdm](#custom_tqdm)
  - [check\_dir()](#check_dir)
  - [save\_dataclass()](#save_dataclass)
  - [load\_dataclass()](#load_dataclass)
  - [set\_up\_nodriver\_browser()](#set_up_nodriver_browser)
  - [suppress\_print()](#suppress_print)
---

## image_crawler_utils

### CrawlerSettings

For parameters of CrawlerSettings, please refer to [tutorials#Set up CrawlerSettings()](tutorials.md#set-up-crawlersettings).

Attributes of CrawlerSettings include (asterisk mark \* means its information can be referred from [tutorials#Set up CrawlerSettings()](tutorials.md#set-up-crawlersettings)):

+ `.capacity_count_config`
  + The CapacityCountConfig class in CrawlerSettings. Some parameters in CrawlerSettings are actually stored in `.capacity_count_config`.
  + \* `.capacity_count_config.image_num`
  + \* `.capacity_count_config.capacity`
  + \* `.capacity_count_config.page_num`
+ `.download_config`
  + The Download class in CrawlerSettings. Some parameters in CrawlerSettings are actually stored in `.download_config`.
  + `.download_config.result_headers`: Get headers if `headers` is a `dict`, or `headers()` if `headers` is a callable function.
    + It can be used as normal headers in custom classes and functions.
    + If you set `headers` to a function that generates random headers every run, then every calling of `.download_config.result_headers` will get random headers as a result of `headers()`.
  + `.download_config.result_proxies`: Get proxies if `proxies` is a `dict`, or `proxies()` if `proxies` is a callable function.
    + It can be used as normal proxies in custom classes and functions.
    + If you set `proxies` to a function that generates random proxies every run, then every calling of `.download_config.result_proxies` will get random proxies as a result of `proxies()`.
  + `.download_config.result_thread_delay`: Get `thread_delay` if `randomize_delay` is `False`, or randomized `thread_delay` if `randomize_delay` is `True`.
  + `.download_config.result_fail_delay`: Get `fail_delay` if `randomize_delay` is `False`, or randomized `fail_delay` if `randomize_delay` is `True`.
  + \* `.download_config.randomize_delay`
  + \* `.download_config.thread_num`
  + \* `.download_config.timeout`
  + \* `.download_config.max_download_time`
  + \* `.download_config.retry_time`
  + \* `.download_config.overwrite_images`
+ \* `.extra_configs`
+ `.log`: A `image_crawler_utils.Log` class, controling logging activities.
    + Its parameters and attributes can be referred from the [Log](#log) chapter.
  + The `debug_config` parameter when creating a CrawlerSettings will be directly used to create the `.log` attribute.
    + As a result, it is INVALID to access `.debug_config` in a CrawlerSettings.
  + `.set_logging_file()` will create the file handler of this Log class.
  + If a CrawlerSettings is stored in your class (e.g. as `crawler_settings`), then it is suggested to log messages like `crawler_settings.log.info("some_msg")`.
+ \* `.set_logging_file()`
+ `.dill_base64_sha256_data()`: Return a 3-element tuple which are respectively
    1. The dill-dumped data of the CrawlerSettings.
    2. Base64 encoded string of the former dill-dumped data.
    3. Sha256 encrypted string of the former Base64 string.
+ `.display_all_configs()`: Displays all configs of a CrawlerSettings.
  + Even if the `debug_config` parameter of CrawlerSettings sets `debug` level to `False`, it will still display some `debug`-level messages.
  + This function will not log its messages into a file, no matter whether `.set_logging_file()` is used.
+ \* `.connectivity_test()`
+ \* `.browser_test()`
+ \* `CrawlerSettings.copy()`
+ \* `.save_to_pkl()`
+ \* `CrawlerSettings.load_from_pkl()`

### ImageInfo

Please refer to [tutorials#The list of ImageInfo()](tutorials.md#the-list-of-imageinfo) for detailed information.

### save_image_infos()

Please refer to [tutorials#The list of ImageInfo()](tutorials.md#the-list-of-imageinfo) for detailed information.

### load_image_infos()

Please refer to [tutorials#The list of ImageInfo()](tutorials.md#the-list-of-imageinfo) for detailed information.

### Parser

Parser is the base class to get information of images.

It **CANNOT** be directly used. You have to inherit it and override its `.run()` function to create a custom Parser for yourself.

Its parameters include:

+ `station_url`: The URL of the main page of a website.
  + This parameter SHOULD be used when several websites use the same structure. For its specific usages in different conditions, refer to the [tutorials.md#Configuring DanbooruKeywordParser()](tutorials.md#configuring-danboorukeywordparser) chapter for more information.
+ `crawler_settings`: The CrawlerSettings used in current Parser.
+ `cookies`: Cookies used to access information from a website by this Parser.
  + Can be one of `image_crawler_utils.Cookies`, `list`, `dict`, `str` or `None`.
    + For the usage of each class, see [tutorials.md#Cookies class](tutorials.md#cookies-class) chapter for detailed information.
    + `None` means no cookies and works the same as `Cookies()`.
    + Leave this parameter blank works the same as `None` / `Cookies()`.

Its attributes include:

+ `.station_url`
  + It will be processed to a valid URL format that ends with '/', like `https://foo.bar.url/`.
+ `.crawler_settings`
  + The meanings of the above 2 attributes are the same as their corresponding parameters.
+ `.cookies`: A `image_crawler_utils.Cookies` class that generated from the cookies provided in `cookies` parameter.
  + Even if `cookies` parameter is set to `None`, `.cookies` will still be a Cookies class only with its `.is_none()` result being `True`.
+ `.run()`: The main function of a Parser.
  + It **MUST BE OVERRIDEN** when you inherit a Parser class, and the result SHOULD be **a list of `image_crawler_utils.ImageInfo` class**.
+ `.display_all_configs()`: Displays all configs of a CrawlerSettings.
  + Even if the `debug_config` parameter in the `crawler_settings` parameter sets `debug` level to `False`, it will still display some debug-level messages.
  + This function will not log its messages into a file.
+ `.save_to_pkl()`
+ `Parser.load_from_pkl()`
  + Please refer to [tutorials.md#Configuring Parsers](tutorials.md#configuring-parsers) for their detailed information.
  + If `.save_to_pkl()` saved a class inherited from a Parser class (e.g. `DanbooruKeywordParser`), then you should use the `load_from_pkl()` of the corresponding inheriting class, like `DanbooruKeywordParser.load_from_pkl()`.
+ `.request_page_content()`: Send a request with certain URL and get the content (source code) of the webpage. The parameters are like:
  
  ```Python
  import requests

  Parser().request_page_content(
      url: str, 
      session=requests.Session(),
      headers: Optional[Union[dict, Callable]]=Empty(),
      thread_delay: Union[None, float, Callable]=None,
  ) -> str
  ```

  + `url`: The URL of the request.
  + `session`: A `requests.Session` class (or the class that inherits `requests.Session()`). 
    + If you want to set cookies or other configurations when requesting, you should store them in the session.
    + Leave it blank will create a separate empty session for each run.
  + `headers`: Headers of this request.
    + Headers should be `None`, a `dict` or a callable function that returns a `dict`.
      + If set `headers` to a function, it will be called for every run of `.request_page_content()`.
    + Leave it blank will use the headers in `.crawler_settings.crawler_settings.download_config.result_headers`.
  + `thread_delay`: Delaying time (seconds) before sending this request.
    + Should be a positive float or a callable function that returns a positive float.
      + If set `thread_delay` to a function, it will be called for every run of `.request_page_content()`.
    + Leave it blank will use the thread delaying time in `.crawler_settings.download_config.result_thread_delay`.
+ `.threading_request_page_content()`: Using threading method to send requests with URLs from a list. Every thread will call the `.request_page_content()` for once. The parameters are like:
  
  ```Python
  import requests

  Parser().threading_request_page_content(
      url_list: Iterable[str], 
      restriction_num: Optional[int]=None, 
      session=requests.Session(),
      headers: Optional[Union[dict, Callable, Iterable]]=Empty(),
      thread_delay: Union[None, float, Callable]=None,
      batch_num: Optional[int]=None,
      batch_delay: Union[float, Callable]=0.0,
  ) -> list[str]
  ```
  
  + `url_list`: The list of URLs of the requests.
  + `restriction_num`: Only request the first `restriction_num` URLs. Set to `None` (default) will request all URLs in the `url_list`.
  + `session`: A `requests.Session` class (or the class that inherits `requests.Session()`). 
    + If you want to set cookies or other configurations when requesting, you should store them in the session.
    + Leave it blank will create a separate empty session for each thread.
  + `headers`: Headers of the requests.
    + Headers should be `None`, a `dict`, a callable function that returns a `dict`, or a iterable list of the former 3 types of headers.
      + If set `headers` to a function, it will be called for every thread.
      + If set `headers` to a iterable list, it should be of the same length as `url_list`. For the request with `url_list[n]`, the nth headers in `headers` will be used.
    + Leave it blank will use the headers in `.crawler_settings.crawler_settings.download_config.result_headers` for every thread.
  + `thread_delay`: Delaying time (seconds) before sending this request.
    + Should be a positive float or a callable function that returns a positive float.
      + If set `thread_delay` to a function, it will be called for every thread.
    + Leave it blank will use the thread delaying time in `.crawler_settings.download_config.result_thread_delay` for every thread.
  + `batch_num`: Divide the `url_list` into batches, and wait `batch_delay` seconds after downloading each batch.
    + Set to `None` (default) will not divide `url_list` into batches.
    + Mostly used when a website has strict restrictions on the number of pages accessible in a certain period (like [Pixiv](https://www.pixiv.net/)).
  + `batch_delay`: Delaying time (seconds) after each batch of URLs are requested.
    + Should be a positive float or a callable function that returns a positive float.
      + If set `batch_delay` to a function, it will be called after each batch that finished downloading.
    + Only works when `batch_num` is not `None`.
  + **ATTENTION:** The order of the result list of page contents is the same as the order of the URLs in `url_list`.
+ `.get_cloudflare_cookies()`: For websites that have a Cloudflare protection, calling this function will pop up a window for manually passing the verification. The parameters are like:
  
  ```Python
  Parser().get_cloudflare_cookies(
      url: Optional[str]=None, 
      headless: bool=False,
      timeout: float=60,
      save_cookies_file: Optional[str]=None,
  )
  ```

  + `url`: The URL of the webpage that is protected by Cloudflare.
  + `headless`: Do not display browsers window when a browser is started. Set to `False` will pop up browser windows.
  + `timeout`: If the Cloudflare page do not disappear in `timeout` seconds, the function will exit and an error will be displayed.
  + `save_cookies_file`: Save all of the cookies after Cloudflare verification is successfully passed to `save_cookies_file` JSON file.
  + **ATTENTION:** Mostly, Cloudflare will detect both the cookies and user-agent in the headers. If you want to use the cookies in `save_cookies_file`, you should set the `'User-Agent'` in headers to the one that displayed on the console when this function is running.

### KeywordParser

KeywordParser is the base class that inherits the `image_crawler_utils.Parser` class. It is particularly for searching images with keywords.

Similar to the Parser class, it **CANNOT** be directly used. You have to inherit it and override its `.run()` function to create a custom Parser for yourself.

Its parameters include:

+ `station_url`
+ `crawler_settings`
+ `cookies`
  + Please refer to the [Parser](#parser) chapter for their meanings.
+ `standard_keyword_string`: Query keyword string using standard syntax. See [tutorials.md#Standard Syntax for Keywords](tutorials.md#standard-syntax-for-keywords) chapter for detailed instructions.
+ `keyword_string`: If you want to directly specify the keywords used in searching, set `keyword_string` to a custom non-empty string. It will OVERWRITE `standard_keyword_string`.
  + For example, set `keyword_string` to `"kuon_(utawarerumono) rating:safe"` in DanbooruKeywordParser means searching directly with this string in Danbooru, and its standard keyword string equivalent is `"kuon_(utawarerumono) AND rating:safe"`.
+ `accept_empty`: If set to `False` (default), when both `standard_keyword_string` and `keyword_string` is an empty string (like `''` or `'  '`), a critical error will be thrown. If set to `True`, no error will be thrown and the parameters are accepted.

As it inherits the Parser class, it contains all attributes of Parser. Refer to the [Parser](#parser) chapter for their detailed information. Other attributes include:

+ `.generate_standard_keyword_string()`: Generate a standard keyword string (a string that follows the [Standard Syntax for Keywords](tutorials.md#standard-syntax-for-keywords)) from a KeywordLogicTree. Its parameters are like:

  ```Python
  KeywordParser().generate_standard_keyword_string(
      keyword_tree: Optional[KeywordLogicTree]=None
  )
  ```

  + `keyword_tree`: The KeywordLogicTree that a standard keyword string will be built from. Set to `None` (default) will use the KeywordLogicTree generated from the `standard_keyword_string` parameter.
    + **ATTENTION:** When set to `None`, the standard keyword string may not be the same as `standard_keyword_string`.

### Cookies

Please refer to [tutorials#Cookies() class](tutorials.md#cookies-class) for detailed information.

### update_nodriver_browser_cookies()

Please refer to [tutorials#Cookies() class](tutorials.md#cookies-class) for detailed information.

## image_crawler_utils.keyword

### KeywordLogicTree

The binary tree class generated after parsing a standard keyword string (keyword string that follows the [standard keyword syntax of Image Crawler Utils](tutorials.md#standard-syntax-for-keywords)). It is not suggested to directly create a KeywordLogicTree; instead, using the functions listed below to create a KeywordLogicTree with simple syntax check can be safer.

Its attributes include:
+ `.lchild`: Left child.
+ `.rchild`: Right child.
+ `.logic_operator`: Logic operator. Can be one of `"AND"`, `"OR"`, `"NOT"` and `"SINGLE"`.
  + `"SINGLE"` means current tree has only one node.
  + For `"NOT"` and `"SINGLE"`, only `.rchild` will be used, and `.lchild` will be set to an empty string.
+ `.is_empty()`: Returns `True` if the current tree is empty, or `False` if not.
+ `.is_leaf()`: Returns `True` if the current tree (node) is a leaf node, or `False` if not.
+ `.simplify_tree()`: Simplify the tree structure, including: `NOT NOT key -> key` and `SINGLE key -> key`.
  + If you create a KeywordLogicTree through the functions provided, `.simplify_tree()` will be automatically executed.
+ `.list_struct()`: Returns the structure of current tree as a recursive `list`.
  + For example, standard keyword string `"A AND B OR C"` will be returned as `[['A', 'AND', 'B'], 'OR', 'C']`.
+ `.standard_keyword_string()`: Returns the reconstructed standard keyword string.
  + The result may not be the same as the string that is used to construct the KeywordLogicTree.
  + For example, standard keyword string `"A AND B OR C"` will be returned as `[[A AND B] OR C]`.
+ `.all_keywords()`: Returns all keywords in the current tree in a `list`.
+ `.keyword_list_check()`: Check whether the keyword list matches this tree. Its parameters are like:
  
  ```Python
  KeywordLogicTree().keyword_list_check(
      keyword_list: Iterable[str],
  )
  ```

  + For example, keyword list `['A', 'B']`, `['C', 'D']` and `['A', 'B', 'C']` match `"A AND B OR C"`, while keyword list `['B', 'D']` cannot match `"A AND B OR C"`.
+ `.keyword_include_group_list()`: Returns a list of keyword groups (list of keywords) which are minimal supersets of current tree.
  + For example:
    + For `"A AND B OR C"`, its minimal supersets are `['A', 'C']` and `['B', 'C']`.
      + That is, if you search `"A OR C"` or `"B OR C"`, you can get all results that match `"A AND B OR C"`. 
    + For `"A AND [B OR C]"`, its minimal supersets are `['A']` and `['B', 'C']`.
  + Useful for websites that have a restriction on the number of keywords when seaching.

### construct_keyword_tree()

Returns a KeywordLogicTree that is constructed from a standard keyword string.

The parameters are like:

```Python
construct_keyword_tree(
    keyword_str: str,
    log: Log=Log(),
) -> KeywordLogicTree
```

+ `keyword_str`: The standard keyword string used to construct KeywordLogicTree.
+ `log`: The `image_crawler_utils.log.Log` class that controls logging.

### construct_keyword_tree_from_list()

Returns a KeywordLogicTree that is constructed from a list of keywords.

The parameters are like:

```Python
construct_keyword_tree_from_list(
    keyword_list: Iterable[str],
    connect_symbol: str='OR',
    log: Log=Log(),
) -> KeywordLogicTree
```

+ `keyword_list`: The list of keywords.
+ `connect_symbol`: Choose the connection logic symbol. Must be one of `AND` / `&` and `OR` / `|`.
  + Default is `|` (`OR`).
  + For example, set `connect_symbol` to `AND` for keyword list `['A', 'B', 'C']` will generate standard keyword string `"A AND B ANC C"` for constructing KeywordLogicTree.
+ `log`: The `image_crawler_utils.log.Log` class that controls logging.

### min_len_keyword_group()

Returns a list of keyword groups (list of keywords) whose number of keywords are the smallest from a list of keyword groups, or lower than the `below` parameter.

The parameters are like:

```Python
min_len_keyword_group(
    keyword_group_list: Iterable[Iterable],
    below: Optional[int]=None,
) -> list[list]
```

+ `keyword_group_list`: List of keyword groups (list of keywords).
+ `below`: Select all keyword groups whose number of keywords are no larger than this parameter. Set to `None` (default) will only select those with smallest number of keywords.
  + If no keyword groups whose number of keywords are no larger than `below`, then the ones with smallest number of keywords will be selected (same as `below=None`).

An example is like:

```Python
>>> from image_crawler_utils.keyword import min_len_keyword_group
>>> kw_group = [['A', 'B', 'C'], ['D', 'E'], ['F', 'G'], ['H', 'I', 'J', 'K']]
>>> min_len_keyword_group(kw_group)
[['D', 'E'], ['F', 'G']]
>>> min_len_keyword_group(kw_group, below=3)
[['A', 'B', 'C'], ['D', 'E'], ['F', 'G']]
>>> min_len_keyword_group(kw_group, below=1)
[['D', 'E'], ['F', 'G']]
```

## image_crawler_utils.log

### Log

A class that controls all logging activities, including logging onto the console and into files. `logging` module is used when logging into files. In Image Crawler Utils, all functions with `log` parameter will be initialized with `Log()` and only accepts `image_crawler_utils.log.Log` class.

Its parameters include:

+ `log_file`: File name of logging.
  + Default is `None`, which means do not logging into any files. The file handler of Log will be empty.
  + If `log_file` do not ends with `.log`, it will be automatically appended with a `.log`.
  + The logging file is encoded with `UTF-8` format.
+ `debug_config`: A `image_crawler_utils.configs.DebugConfig` class, controls which level of messages will be displayed ON CONSOLE.
  + It does not affect logging into file.
+ `logging_level`: Controls the level of logging INTO FILES. Default is `logging.DEBUG`.
  + It can be any of the levels from the `logging` module, like `logging.DEBUG`, `logging.INFO`, etc. For detailed information, please refer to the documentation of the `logging` module.
  + It does not affect logging onto console.

Its attributes include:

+ `.logging_file_handler()`: Returns the file handler if exists (i.e. if logging into file), or `None` if not.
+ `.logging_file_path()`: Returns the absolute path of the logging file if exists (i.e. if logging into file), or `None` if not.
+ `.debug()`
+ `.info()`
+ `.warning()`
+ `.error()`
+ `.critical()`
  + Five levels of logging messages, which share a common parameters like:
  
    ```Python
    Log().info(
        msg: str,
        output_msg: Optional[str]=None,
    )
    ```
  
    + `msg`: The message that will be logged into the `.log` file and (if `output_msg` is `None`) print to console.
    + `output_msg`: The message that will be print to console if set to a string.
      + Set `output_msg` to `None` (default) will output `msg` onto the console instead.
      + Can be used to simplify messages displayed on console, while `msg` can contain full information.
    + **ATTENTION:** Whether the messages will be logged into files / logged onto console is respectively controlled by the `logging_level` and `debug_config` when you create the current Log class.
  
### print_logging_msg()

To be compatible with `tqdm` bars, `print_logging_msg()` will use `tqdm.write()` method to print messages onto the console. Set logging level in `print_logging_msg()` will also output time and logging level as the prefix before the message, like:

```Python
>>> from image_crawler_utils.log import print_logging_msg
>>> print_logging_msg("message")
message
>>> print_logging_msg("message", "info")
[08:18:31] [INFO]: message
```

It is STRONGLY SUGGESTED to use `print_logging_msg()` instead of `print()` to print messages onto console. You can combine it with [suppress_print()](#suppress_print) from `image_crawler_utils.utils` to prevent messages messing up console output when `tqdm` bars are being displayed.

The parameters are like:

```Python
print_logging_msg(
    msg: str,
    level: str='',
    debug_config: DebugConfig=DebugConfig.level("debug"),
)
```

+ `msg`: The message string to be output.
+ `level`: Level of output.
  + Set it to one of `debug`, `info`, `warning` / `warn`, `error` and `critical` will output time & level as the prefix before the message string in `msg`, if DebugConfig in the `debug_config` allows this level of messages to be output.
  + Set it to other string (default) will only and always output the `msg` no matter how `debug_config` is set.
+ `debug_config`: A `image_crawler_utils.configs.DebugConfig` class, controls whether the message will be output.
  + For example, if `level` is set to `info` and `debug_config` is set to `DebugConfig.level('warning')`, then the `msg` will not be output.
  + If `level` is set to a string other than `debug`, `info`, `warning` / `warn`, `error` and `critical`, then this parameter will be omitted and the `msg` will always be output.

## image_crawler_utils.user_agent

### UserAgent

A class that provides several basic user agents to build a header.

+ **WARNING:** Some user agents may be outdated, or not acceptable for certain websites!

Its attributes include:

+ `UserAgent.pc_user_agents`: A `dict` that includes all user agents that simulates a PC browser.
+ `UserAgent.mobile_user_agents`: A `dict` that includes all user agents that simulates a PC browser.
+ `UserAgent.user_agents`: A `dict` that includes all user agents, including all the user agents in the former attributes.
+ `UserAgent.random_agent_with_name()`: Returns a random agent with a certain name in its name string.
  + For example: `UserAgent.random_agent_with_name("Chrome")` will select a random user agent with `"Chrome"` in its name, like `{"Chrome - Windows": "A Chrome UA"}` might be selected while `{"Safari 5.1 - MAC": "A Safari UA"}` will not be selected.
  + Both input string and the name will be in lowercase when compared. That is, `UserAgent.random_agent_with_name("Chrome")` works the same as `UserAgent.random_agent_with_name("chrome")`, while `{"Chrome UA": "UA"}` and `{"chrome ua": "UA"}` are the same as the name of user agents.
+ `UserAgent.random_pc_agent()`: Returns a random PC user agent.
+ `UserAgent.random_mobile_agent()`: Returns a random mobile user agent.
+ `UserAgent.random_agent()`: Returns a random user agent.
  + The format of the user agent that returned from all of the random_agent functions above will be in the `{'User-Agent': "Returned UA"}` format.

## image_crawler_utils.utils

### Empty

A placeholder class, meaning the parameter is blank. If `None` is not a meaningless value of a parameter, you can set its default value to `Empty()`, which means no values are designated for this parameter.

### custom_tqdm

`custom_tqdm` will use different `tqdm` bars according to whether current environment is IPython kernel.

Its usage is the same as `tqdm` from `import tqdm`, like:

```Python
from image_crawler_utils.utils import custom_tqdm

with custom_tqdm.tqdm() as pbar:
    # Do something
with custom_tqdm.trange(10) as pbar:
    # Do something
```

### check_dir()

This function will check whether a directory exists, and try to create it when not existing. A logging message will be print to console when succeeded, and a critical error will be thrown when failed.

The parameters are like:

```Python
check_dir(
    dir_path: str, 
    log: Log=Log()
)
```

+ `dir_path`: The directory that will be checked.
+ `log`: The `image_crawler_utils.log.Log` class that controls logging.

### save_dataclass()

Please refer to [tutorials#Save and Load Configs](tutorials.md#save-and-load-configs) for detailed information.

### load_dataclass()

Please refer to [tutorials#Save and Load Configs](tutorials.md#save-and-load-configs) for detailed information.

### set_up_nodriver_browser()

**Async function:** This funciton provides a fast setup of a nodriver browser. The result is a `nodriver.Browser` class, which is the same as the one generated by `nodriver.start()`. The parameters are like:

```Python
set_up_nodriver_browser(
    proxies: Optional[Union[dict, Callable]]=None, 
    headless: bool=True,
    window_width: Optional[int]=None,
    window_height: Optional[int]=None,
    no_image_stylesheet: bool=False,
) -> nodriver.Browser
```

+ `proxies`: The proxies used in nodriver browser.
  + The pattern should be in a `requests`-acceptable form like:
    + HTTP type: `{'http': '127.0.0.1:7890'}`
    + HTTPS type: `{'https': '127.0.0.1:7890'}`, or `{'https': '127.0.0.1:7890', 'http': '127.0.0.1:7890'}`
    + SOCKS type: `{'https': 'socks5://127.0.0.1:7890'}`
+ `headless`: Do not display browsers window when a browser is started. Set to `False` will pop up browser windows.
+ `window_width`: Width of browser window.
  + Set `headless` to `True` will omit this parameter.
+ `window_height`: Height of browser window.
  + Set `headless` to `True` will omit this parameter.
+ `no_image_stylesheet`: Do not load any images or stylesheet when loading webpages in this browser.
  + Set this parameter to `True` can reduce the traffic when loading pages and accelerate loading speed.

### suppress_print()

As `tqdm` bars are widely used in Image Crawler Utils, in order to prevent `print()` from messing up the console output, it is suggested to use `suppress_print()` to stop any messages from being output to console by `print()`.
+ Messages output from `image_crawler_utils.log.print_logging_msg()` or the attribute functions of `image_crawler_utils.log.Log` will not be suppressed.

```Python
from image_crawler_utils.log import print_logging_msg

def custom_print(string):
    print(string)

with suppress_print():
    print("Suppressed output")  # Will NOT be print to console
    custom_print("Suppressed output")  # Will NOT be print to console
    print_logging_msg("Normal output")  # Will be print to console
print("Normal output")  # Will be print to console
```
