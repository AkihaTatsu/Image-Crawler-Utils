<h1 align="center">
Tutorials
</h1>
<p align="center">
English | <a href="tutorials_zh.md">简体中文</a>
</p>

This tutorial will help you going through the construction of a crawler, and downloading images from Danbooru with certain keywords. It is suggested to finish [README](../README.md) before reading this.

**WARNING: Do not load any `.pkl` file from unknown sources!** 

**Table of Contents**

- [Set up CrawlerSettings()](#set-up-crawlersettings)
  - [Configs](#configs)
    - [CapacityCountConfig()](#capacitycountconfig)
    - [DebugConfig()](#debugconfig)
    - [DownloadConfig()](#downloadconfig)
    - [Save and Load Configs](#save-and-load-configs)
- [Configuring Parsers](#configuring-parsers)
  - [Acquiring Cookies](#acquiring-cookies)
    - [Cookies() class](#cookies-class)
  - [Configuring DanbooruKeywordParser()](#configuring-danboorukeywordparser)
    - [Standard Syntax for Keywords](#standard-syntax-for-keywords)
  - [The list of ImageInfo()](#the-list-of-imageinfo)
- [Running Downloader()](#running-downloader)
---

## Set up CrawlerSettings()

A CrawlerSettings class contains basic information and configurations for Parsers and Downloaders. It can be imported from `image_crawler_utils`.

The default value of CrawlerSettings is like:

```Python
from image_crawler_utils import CrawlerSettings
from image_crawler_utils.configs import DebugConfig

crawler_settings = CrawlerSettings(
    # Configs restrict downloading numbers and capacity
    image_num: int | None=None,
    capacity: float | None=None,
    page_num: int | None=None,
    # Configs about parameters in downloading
    headers: dict | Callable | None=None,
    proxies: dict | Callable | None=None,
    thread_delay: float=5,
    fail_delay: float=3,
    randomize_delay: bool=True,
    thread_num: int=5,
    timeout: float | None=10,
    max_download_time: float | None=None,
    retry_times: int=5,
    overwrite_images: bool=True,
    # Configs define which types of messages are shown on the console.
    debug_config=DebugConfig.level("info"),
    # Logging settings
    detailed_console_log: bool=False,
    # Extra configs for custom use
    extra_configs={
        "arg_name": config, 
        "arg_name2": config2, 
        ...
    },
)
```

+ Details about most of these parameters parameters are provided in [Configs](#configs) chapter:
  + `image_num`
  + `capacity`
  + `page_num`
    + Please refer to the [CapacityCountConfig()](#capacitycountconfig) chapter for their meaning. These parameters control the number of images, pages and total size of images when crawling.
    + Leave any of them blank will use the default value of the corresponding parameter in CapacityCountConfig.
    + It is also acceptable to pass a CapacityCountConfig class into the `capacity_count_config` parameter of a CrawlerSettings class. It will overwrite the parameters above, like:
      
      ```Python
      from image_crawler_utils import CrawlerSettings
      from image_crawler_utils.configs import CapacityCountConfig

      crawler_settings = CrawlerSettings(
          capacity_count_config=CapacityCountConfig(
              image_num=200,
          )
          # As CapacityCountConfig is set, these parameters will not be used
          image_num=100,
          page_num=3,
      )
      ```

  + `headers`
  + `proxies`
  + `thread_delay`
  + `fail_delay`
  + `randomize_delay`
  + `thread_num`
  + `timeout`
  + `max_download_time`
  + `retry_time`
  + `overwrite_images`
    + Please refer to the [DownloadConfig()](#downloadconfig) chapter for their meaning. These parameters control settings relating to downloading pages and images.
    + Leave any of them blank will use the default value of the corresponding parameter in DownloadConfig.
    + It is also acceptable to pass a DownloadConfig class into the `download_config` parameter of a CrawlerSettings class. It will overwrite the parameters above.
  + `debug_config`: A `image_crawler_utils.configs.DebugConfig` class, which controls the displaying level of messages on the console. Please refer to the [DebugConfig()](#debugconfig) chapter. 
+ `detailed_console_log`: Logging detailed information to the console.
  + When logging info to the console, always log `msg` (the messages logged into files) even if `output_msg` exists (Please refer to the [Classes and Functions#Log](classes_and_functions.md#log) chapter).
+ `extra_configs`: This optional `dict` is not used in any of the supported sites and crawling tasks, as it is reserved for developing your custom image crawler.

It is recommended to add a logging file when running the crawler, as the message displayed on the console is simplified and usually not complete. After you set up a CrawlerSettings, use `.set_logging_file()` to set a logging file handler to current settings:

```Python
import logging

# crawler_settings = CrawlerSettings()

crawler_settings.set_logging_file(
    log_file: str,
    logging_level: int=logging.DEBUG,
)

# Example
crawler_settings.set_logging_file("test.log")
```

+ `log_file`: File name of the logging file, e.g. `test.log`
+ `logging_level`: Level of logging into the FILE.
  + The level of logging can be set by `import logging`, which includes `logging.DEBUG`, `logging.INFO`, `logging.WARNING`, `logging.ERROR`, `logging.CRITICAL` five levels. Each level will tell the logging file to record messages with itself or higher levels. Default is `logging.DEBUG` level.
  + **ATTENTION:** it is indepedent from the level of logging onto the console!
    + The latter is controlled by the `debug_config` parameter, and this parameter in turn does not affect logging into file.

You can use `.display_all_configs()` to display and check all configs in current CrawlerSettings.

These attribute functions are provided:

+ `.connectivity_test(url: str)` can check whether the url is accessible with current settings. Logging messages will be recorded on the console or in the file according to your settings.
  + Returns `True` when successful, and `False` when failed. 
+ `.browser_test(url: str, headless: bool=True)` can check whether the browser works normally with current settings. Logging messages will be recorded on the console or in the file according to your settings.
  + Returns `True` when successful, and `False` when failed. 
  + Set `headless` to `False` will pop up the browser window to display the whole process of loading the webpage.
+ `.save_to_pkl(pkl_file: str | None=None)` can save the whole class into a `.pkl` file.
  + Leaving the `pkl_file` parameter blank will set its file name to the result of the sha256 encryption on the string of the original class being serialized in base64. This can normally ensure every different CrawlerSettings class has a different file name.
  + Returns a tuple of `(saved .pkl file name, absolute path of saved .pkl file name)` when succeeded, or `None` when failed.

New CrawlerSettings classes can be generated with these functions：

+ `CrawlerSettings.copy()` can copy an existing CrawlerSettings with parameters changed.
  + **ATTENTION:** It is not suggested to directly change the attributes of CrawlerSettings in order to update it.
  + The parameters can be set to change their values in the copied CrawlerSettings, like:
    
    ```Python
    new_settings = CrawlerSettings.copy_from(
        old_crawler_settings, 
        image_num=30,
    )
    ```

+ `CrawlerSettings.load_from_pkl()` can load a CrawlerSettings class from a `.pkl` file.
  + The first parameter of this function is a `.pkl` file name (suffix must be included)
  + The second parameter `log` controls the level of logging onto the console.

An example of saving and loading CrawlerSettings is like:

```Python
from image_crawler_utils import CrawlerSettings
from image_crawler_utils.configs import DownloadConfig

crawler_settings = CrawlerSettings(download_config=DownloadConfig(image_num=20))

# Save a CrawlerSettings
crawler_settings.save_to_pkl("crawler_settings.pkl")

# Load a CrawlerSettings from a file
new_crawler_settings = CrawlerSettings.load_from_pkl("crawler_settings.pkl")

# Copy a CrawlerSettings, and change its download_config
copied_crawler_settings = crawler_settings.copy(
    image_num=30,
)
```

### Configs

#### CapacityCountConfig()

A CapacityCountConfig is like:

```Python
from image_crawler_utils.configs import CapacityCountConfig

CapacityCountConfig(
    image_num: int | None=None,
    capacity: float | None=None,
    page_num: int | None=None,
)

# Example
capacity_count_config = CapacityCountConfig(
    image_num=60,
    capacity=1024,
    page_num=2,
)
```

+ `image_num`: The number of images to be parsed from websites or downloaded.
  + Default is set to `None`, meaning no restrictions.
  + Mostly only used in the Downloader to control the number of images to be downloaded, but some Parsers may also use this parameter. Please refer to [notes for tasks](notes_for_tasks.md) for detailed information.
+ `capacity`: The total size of images to be downloaded.
  + Default is set to `None`, meaning no restrictions.
  + When capacity is reached, no new downloading threads will be added. However, downloading threads that already started will not be affected, which means actual image size will be larger than the capacity.
+ `page_num`: The number of pages to be downloaded. Mostly used in Parsers for websites with gallery pages.
  + Default is set to `None`, meaning no restrictions.
  + Some websites, like [Twitter / X](https://x.com/), do not use gallery pages or JSON-API pages (Image Crawler Utils uses the method of scrolling the webpage to get Twitter / X images), and this parameter is not used. Please refer to [notes for tasks](notes_for_tasks.md) for detailed information.

#### DebugConfig()

DebugConfig only controls what kind of messages will be displayed on console. For logging into a `.log` file, use `image_crawler_utils.CrawlerSettings.set_logging_file()`.

A DebugConfig is like:

```Python
from image_crawler_utils.configs import DebugConfig

DebugConfig(
    show_debug: bool = False,
    show_info: bool = True,
    show_warning: bool = True,
    show_error: bool = True,
    show_critical: bool = True,
)
```

+ `show_debug`: Display debug-level messages.
  + Default set to `False`.
  + Include messages of many detailed information about running the crawler, especially connections with websites.
  + Set `show_debug` to `False` will not stop displaying debug messages from any `.display_all_configs()`.
+ `show_info`: Display info-level messages.
  + Default set to `True`.
  + Include messages of basic information indicating the progress of the crawler.
+ `show_warning`: Display warning-level messages.
  + Default set to `True`.
  + Include messages of errors that basically do not affect the final results, mostly connection failures with the websites.
+ `show_error`: Display error-level messages.
  + Default set to `True`.
  + Include messages of errors that may affect the final results but do not interrupt the crawler.
+ `show_critical`: Display critical-level messages.
  + Default set to `True`.
  + Include messages of errors that interrupt the crawler. Usually a Python error will be raised when critical errors happen.

If you want to display messages above certain levels, use `.set_level()`.

+ The parameter can be `"debug"`, `"info"`, `"warning"`, `"error"`, `"critical"`, or `"silenced"`.
+ Set a logging level will display messages including and above this level. For example, `.set_level("warning")` will only display messages with `"warning"`, `"error"` and `"critical"` levels.
+ Set to `silenced` level will not display any messages except those generated by the progress bars.

You can use `DebugConfig.level("some_level")` to directly generate a DebugConfig with a certain logging level (can be used in parameters, like `CrawlerSettings(debug_config=DebugConfig.level("debug"))`).

Also, if you already have a `debug_config = DebugConfig()`, you can use `debug_config.set_level("some_level")` to change its logging level.

#### DownloadConfig()

A DownloadConfig is like:

```Python
from image_crawler_utils.configs import DownloadConfig

DownloadConfig(
    headers: dict | Callable | None=None,
    proxies: dict | Callable | None=None,
    thread_delay: float=5,
    fail_delay: float=3,
    randomize_delay: bool=True,
    thread_num: int=5,
    timeout: float | None=10,
    max_download_time: float | None=None,
    retry_times: int=5,
    overwrite_images: bool=True,
)

# Example
download_config = DownloadConfig(
    headers={'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36"},
    proxies={'https': 'socks5://127.0.0.1:7890'}
    thread_delay=4.0,
    fail_delay=4.0,
    randomize_delay=False,
    thread_num=5,
    timeout=30.0,
    max_download_time=60.0,
    retry_times=3,
    overwrite_images=False,
)
```

+ `headers`：Headers of the requests.
  + Both fetching webpages and downloading images will use this parameter.
  + Headers should be `None`, a `dict` or a callable function that returns a `dict`.
    + If you want to have a random header with every request, you can set `headers` to a callable function. This function should not accept any parameters (which can be implemented by `lambda`) and returns a `dict`.
  + This only works when the requests is sent by `requests` (like `requests.get()`). For webpages loaded by browsers, this parameter is omitted.
  + Basically, this contains the user agent of the requests. `UserAgent` from `image_crawler_utils.user_agent` provides some predefined user agents to select from.
    + **ATTENTION:** Not all user agents are supported by the websites you are accessing! Please refer to [notes for tasks](notes_for_tasks.md) for detailed information.

      ```Python
      from image_crawler_utils.user_agent import UserAgent
      
      download_config = DownloadConfig(
          # Use a random Chrome headers
          headers=lambda: UserAgent.random_agent_with_name("chrome")
      )
      ```

+ `proxies`: Proxies used by the crawler.
  + Both fetching webpages and downloading images will use this parameter.
  + Proxies should be `None`, a `dict` or a callable function that returns a `dict`.
    + Set to `None` (Default) will let the crawler use system proxies.
    + If you want to have a random proxy with every request, you can set `proxies` to a callable function. This function should not accept any parameters (which can be implemented by `lambda`) and returns a `dict`.
  + Both `requests` and browsers use these proxies, but the structure should be in a `requests`-acceptable form like:
    + HTTP type: `{'http': '127.0.0.1:7890'}`
    + HTTPS type: `{'https': '127.0.0.1:7890'}`
    + SOCKS type: `{'https': 'socks5://127.0.0.1:7890'}`
    + If you input `'https'` proxies, `'http'` proxies will be automatically generated.
    + **ATTENTION:** Using usernames and passwords is currently not supported.
+ `thread_delay`: Delaying time (seconds) before every thread starts.
  + Both fetching webpages and downloading images will use this parameter.
  + Some Parsers may use different parameters to control their delaying time. Please refer to [notes for tasks](notes_for_tasks.md) for detailed information.
+ `fail_delay`: Delaying time (seconds) after every failure.
  + Both fetching webpages and downloading images will use this parameter.
  + Some Parsers may use different parameters to control their delaying time when a failure happens. Please refer to [notes for tasks](notes_for_tasks.md) for detailed information.
+ `randomize_delay`: Randomize `thread_delay` and `fail_delay` between 0 and their values.
  + For example, `thread_delay=5.0` and `randomize_delay=False` will cause the `thread_delay` to choose a random value between 0 and 5.0 every time.
+ `thread_num`: Total number of threads.
  + Both fetching webpages and downloading images will use this parameter.
  + Some Parsers do not use threading to fetching pages, and this parameter is not used. Please refer to [notes for tasks](notes_for_tasks.md) for detailed information.
+ `timeout`: Timeout for connection. When no response is returned in `timeout` seconds, a failure will happen.
  + Both fetching webpages and downloading images will use this parameter.
  + Setting to `None` means no restrictions.
+ `max_download_time`: When no new data is fetched when downloading images in `max_download_time` seconds, a failure will happen.
  + Only downloading images will use this parameter.
  + Default is set to `None`, meaning no restrictions.
+ `retry_times`: Total times of retrying to fetch a webpage / download an image.
  + Both fetching webpages and downloading images will use this parameter.
+ `overwrite_images`: Overwrite existing images when downloading.
  + Only downloading images will use this parameter.

#### Save and Load Configs

Most of the configs can be saved or loaded using `save_dataclass()` and `load_dataclass()`. Both functions support 2 types of file: `.json` and `.pkl`.

```Python
from image_crawler_utils.utils import save_dataclass, load_dataclass

save_dataclass(
    dataclass,
    file_name: str,
    file_type: Optional[str]=None,
    encoding: str='UTF-8',
    log: Log=Log(),
)
load_dataclass(
    dataclass_to_load,
    file_name: str,
    file_type: Optional[str]=None,
    encoding: str='UTF-8',
    log: Log=Log(),
)

# Example
from image_crawler_utils.configs import CapacityCountConfig, DownloadConfig
from image_crawler_utils.user_agent import UserAgent

capacity_count_config = CapacityCountConfig(image_num=30)
save_dataclass(capacity_count_config, "capacity_count_config.json")
new_config = CapacityCountConfig()
load_dataclass(new_config, "capacity_count_config.json")

download_donfig = DownloadConfig(headers=lambda: UserAgent.random_agent_with_name("chrome"))
save_dataclass(download_donfig, "download_config.pkl")
new_config = DownloadConfig()
load_dataclass(new_config, "download_config.pkl")
```

+ `save_dataclass()` will save the dataclass (config) into a file.
  + Set `file_type` parameter to `json` or `pkl` will force the function to save the dataclass (config) into this type, or leaving this parameter blank will cause the funtion to determine the file type according to `file_name`.
    + That is, `save_dataclass(dataclass, 'foo.json')` works the same as `save_dataclass(dataclass, 'foo', 'json')`.
    + `.json` is suggested when your dataclasses (configs) do not include objects that cannot be JSON-serialized (e.g. a function), while serialized data file `.pkl` can support most data types but the saved file is not readable.
    + `encoding` will only work when saving to a `.json` files.
  + The function will return a tuple of `(saved file name, absolute path of saved file name)` when succeeded, or `None` when failed.
+ `load_dataclass()` will load the dataclass (config) from the designated file into the provided `dataclass_to_load` parameter.
  + Set `file_type` parameter to `json` or `pkl` will force the function to consider the file as this type, or leaving this parameter blank will cause the funtion to determine file type according to `file_name`.
    + That is, `load_dataclass(dataclass, 'foo.json')` works the same as `load_dataclass(dataclass, 'foo.json', 'json')`.
    + `encoding` will only work when loading from a `.json` files.
  + The `dataclass_to_load` should be the same class as the dataclass (config) you saved in the file.
  + The function will return `dataclass_to_load` itself when succeeded, or `None` when failed.
+ The `log` parameter controls the levels of logging onto the console and into the file. You can use `log=crawler_settings.log` to make it the same as the CrawlerSettings you set up.

## Configuring Parsers

A Parser will parse image information from websites.

Parsers for a certain website are provided in `image_crawler_utils.stations.certain_website`; for example, to import the keyword Parser for Danbooru, use `from image_crawler_utils.stations.booru import DanbooruKeywordParser`.

Parsers should be configured when created, and once you set up a Parser, use `image_info_list = Parser.run()` to get a list of image information, which can be passed on to Downloader.

An example of parsing information of images with keyword `kuon_(utawarerumono)` and `rating:safe` from Danbooru is like:

```Python
from image_crawler_utils.stations.booru import DanbooruKeywordParser

parser = DanbooruKeywordParser(
    crawler_settings=crawler_settings,  # Need to be defined
    standard_keyword_string="kuon_(utawarerumono) AND rating:safe",
)
image_info_list = parser.run()
```

A Parser class can be saved by `.save_to_pkl()`, or loaded with `.load_from_pkl()` from its corresponding class (e.g. `DanbooruKeywordParser.load_from_pkl()`), like:

```Python
from image_crawler_utils.stations.booru import DanbooruKeywordParser

parser = DanbooruKeywordParser(
    crawler_settings=crawler_settings,  # Must be defined in advance
    standard_keyword_string="kuon_(utawarerumono) AND rating:safe",
)
# Save a DanbooruKeywordParser
parser.save_to_pkl('parser.pkl')

# Load a DanbooruKeywordParser
new_parser = DanbooruKeywordParser.load_from_pkl('parser.pkl')
```

Use `.display_all_configs()` to check all parameters of current Parser.

### Acquiring Cookies

Some websites requires cookies to get result. Several functions are provided to get cookies of logging in.

For example, to get Pixiv cookies, use `get_pixiv_cookies` from `image_crawler_utils.stations.pixiv`: 

```Python
from image_crawler_utils.stations.pixiv import get_pixiv_cookies

cookies = get_pixiv_cookies(
    pixiv_id="mail@address",
    password="password",
    proxies={"proxy_type": "proxy_address"},
    headless=False, 
)
```

+ `pixiv_id`: Your Pixiv ID or mail address. Leave it blank to input manually.
+ `password`: Your password for Pixiv account. Leave it blank to input manually.
+ `proxies`: Proxies to use when opening the logging-in webpage. It uses the same form as the one in [DownloadConfig](#downloadconfig).
+ `headless`: A `bool` parameter controlling whether to use the headless mode (not displaying the browser window). Default is `False`. **It is strongly recommended to not set it to `True`**, as it may cause failure in passing protections like CAPTCHA and e-mail verification.

`get_pixiv_cookies()` uses a browser to generate a browser window to log in. If some confirmation process (e.g. reCAPTCHA check, mail confirmation, etc.) is required, you need to finish it manually.

#### Cookies() class

The result of `get_pixiv_cookies()` is a `image_crawler_utils.Cookies` class, which can be used in Parsers and Downloaders.

Cookies can be imported from `image_crawler_utils`. A Cookies can be created using `Cookies.create_by()` with 4 types:

+ `str`: This form of cookies can be acquired by using Developer Mode (F12) in some browsers, etc.

  ```Python
  from image_crawler_utils import Cookies
  
  cookies = Cookies.create_by("your_cookies_string")
  ```

+ `dict`: This form of cookies can be generated by `requests`-related functions and classes, or other cookie functions like `get_dict()`, etc.

  ```Python
  import requests
  from image_crawler_utils import Cookies
  
  session = requests.Session()
  # Some process that adds cookies to session
  requests_cookies = session.cookies.get_dict()  # A list
  cookies = Cookies.create_by(requests_cookies)
  ```

+ `list[dict]`: This form of cookies can be generated by selenium-related functions and classes, etc.

  ```Python
  from selenium.webdriver import Chrome
  from image_crawler_utils import Cookies
  
  chrome_driver_path = '/path/to/chromedriver'
  chrome_browser = webdriver.Chrome(executable_path=chrome_driver_path)
  chrome_browser.get('https://foo.bar.com')
  # Some other process
  selenium_cookies = chrome_browser.get_cookies()  # A dict
  cookies = Cookies.create_by(selenium_cookies)
  ```

+ `list[nodriver.cdp.network.Cookie]`: This form of cookies can be generated by nodriver-related functions and classes, etc.

  ```Python
  import nodriver
  from image_crawler_utils.utils import set_up_nodriver_browser
  from image_crawler_utils import Cookies
  
  async def nodriver_func():      
      browser = await set_up_nodriver_browser()
      tab = await browser.get('https://foo.bar.com')
      # Some other process
      nodriver_cookies = await browser.cookies.get_all()
      return nodriver_cookies

  nodriver_cookies = nodriver.loop().run_until_complete(nodriver_func())
  cookies = Cookies.create_by(nodriver_cookies)
  ```

Several attributes are provided for different uses:

+ `.cookies_string`: Cookies in `str` form.
+ `.cookies_dict`: Cookies in `dict` form, can be used in `requests`-related occasions like:

  ```Python
  import requests
  
  session = requests.Session()
  session.cookies.update(cookies.cookies_dict)
  ```

+ `.cookies_selenium`: Cookies in `list[dict]` form, can be used in selenium-related occasions.
  + **ATTENTION:** If you create a Cookies class through `str` or `dict`, then `.cookies_selenium` CANNOT be directly used in selenium webdrivers (some information is missing). `.update_selenium_cookies()` is provided in such occasions.
+ `.cookies_nodriver`: Cookies in `list[nodriver.cdp.network.Cookie]` form, can be used in nodriver-related occasions.
+ `.update_selenium_cookies()`: Update cookies in selenium webdrivers. Input should be a selenium-type cookies (a `list[dict]`), and the function will return a new selenium-type cookies with information stored in Cookies class added. If you create a Cookies class through `str` or `dict`, this function can be used to add such Cookies to selenium webdrivers.
  + The cookies generated without a domain will be given the domain appeared the most in the input cookies.

    ```Python
    from selenium.webdriver import Chrome
    from image_crawler_utils import Cookies
    
    chrome_driver_path = '/path/to/chromedriver'
    chrome_browser = webdriver.Chrome(executable_path=chrome_driver_path)
    chrome_browser.get('https://foo.bar.com')
    
    # Update selenium cookies
    new_cookies = cookies.update_selenium_cookies(driver.get_cookies())
    for new_cookie in new_cookies:
        driver.add_cookie(new_cookie)
    chrome_browser.get('https://foo.bar.com')
    ```

+ `.update_nodriver_cookies()`: Update cookies in nodriver instances. Input should be a nodriver-type cookies (a `list[nodriver.cdp.network.Cookie]`), and the function will return a new nodriver-type cookies with information stored in Cookies class added.
  + Cookies from nodriver can be generated by `browser.cookies.get_all()`, where `browser` is a `nodriver.Browser` instance.
  + If you create a Cookies class through `str` or `dict`, **DO NOT** directly use this function to set cookies for nodriver instances. Use `update_nodriver_browser_cookies()` mentioned below instead.
  + The cookies generated without a domain will be given the domain appeared the most in the input cookies.
+ `.is_none()`: Returns a bool telling whether current Cookies is empty.
  + If Cookies is created directly (like `cookies = Cookies()`), then `.is_none()` will return `True`. Otherwise it will return `False`.

`update_nodriver_browser_cookies()` from `image_crawler_utils` is particularly provided for adding Cookies created through `str` or `dict` to a nodriver instance.

```Python
import nodriver
from image_crawler_utils.utils import set_up_nodriver_browser
from image_crawler_utils import Cookies, update_nodriver_browser_cookies

async def nodriver_func(cookies: Cookies):
    browser = await set_up_nodriver_browser()
    tab = await browser.get('https://foo.bar.com')

    # Update nodriver cookies
    await update_nodriver_browser_cookies(browser, cookies)  # This is an async function
    browser.get('https://foo.bar.com')

foo_cookies: Cookies = # Your cookies created from other sources
nodriver.loop().run_until_complete(nodriver_func(cookies=foo_cookies))
```

A Cookies class can be saved by `.save_to_json()`, or loaded with `Cookies.load_from_json()`, like:

```Python
from image_crawler_utils import Cookies
cookies = Cookies.create_by(foo_cookies)

# Save a Cookies
cookies.save_to_json('cookies.json', encoding='UTF-8')

# Load a Cookies
new_cookies = Cookies.load_from_json('cookies.json', encoding='UTF-8')
```

+ Two Cookies can be added. If both Cookies have cookies with same `name` value, then the latter will be omitted.

### Configuring DanbooruKeywordParser()

Danbooru shares many features with other booru-structured websites, which means their Parsers have several common parameters. Please read [Danbooru's cheatsheet](https://danbooru.donmai.us/wiki_pages/help:cheatsheet) before starting.

A detailed list of DanbooruKeywordParser parameters is like:

```Python
from image_crawler_utils.stations.booru import DanbooruKeywordParser

parser = DanbooruKeywordParser(
    crawler_settings: CrawlerSettings=CrawlerSettings(),
    station_url: str="https://danbooru.donmai.us/",
    standard_keyword_string: str | None=None, 
    keyword_string: str | None=None,
    cookies: Cookies | list | dict | str | None=Cookies(),
    replace_url_with_source_level: str="None",
    use_keyword_include: bool=False,
)

# Example
parser = DanbooruKeywordParser(
    crawler_settings=crawler_settings,
    station_url="https://danbooru.donmai.us/",
    standard_keyword_string="kuon_(utawarerumono) AND rating:safe", 
    keyword_string="kuon_(utawarerumono) rating:safe",
    cookies='some_danbooru_cookies_string',
    replace_url_with_source_level="File",
    use_keyword_include=True,
)
```

+ `crawler_settings`: The CrawlerSettings used in this parser.
+ `station_url`: The URL of the main page of a website.
  + This parameter works when several websites use the same structure. For example, [yande.re](https://yande.re/) and [konachan.com](https://konachan.com/) both use Moebooru to build their websites, and this parameter must be filled to deal with these sites respectively.
  + For websites like [Pixiv](https://www.pixiv.net/), as no other website uses its structure, this parameter has already been initialized and do not need to be filled.
+ `standard_keyword_string`: Query keyword string using standard syntax. See [Standard Syntax for Keywords](#standard-syntax-for-keywords) chapter for detailed instructions.
+ `keyword_string`: If you want to directly specify the keywords used in searching, set `keyword_string` to a custom non-empty string. It will OVERWRITE `standard_keyword_string`.
  + For example, set `keyword_string` to `"kuon_(utawarerumono) rating:safe"` in DanbooruKeywordParser means searching directly with this string in Danbooru, and its standard keyword string equivalent is `"kuon_(utawarerumono) AND rating:safe"`.
  + `standard_keyword_string` and `keyword_string` CANNOT be `None` or empty (contains only spaces) at the same time. Otherwise, a critical error will happen!
+ `cookies`: Cookies used to access information from a website.
  + Can be one of `image_crawler_utils.Cookies`, `list`, `dict`, `str` or `None`.
    + For the usage of each class, see [Cookies class](#cookies-class) chapter for detailed information.
    + `None` means no cookies and works the same as `Cookies()`.
    + Leave this parameter blank works the same as `None` / `Cookies()`.
+ `replace_url_with_source_level`: A level controlling whether the Parser will try to download from the source URL of images instead of from Danbooru.
  + It has 3 available levels, and default is `"None"`:
    + `"All"` or `"all"` (NOT SUGGESTED): As long as the image has a source URL, try to download from this URL first.
    + `"File"` or `"file"`: If the source URL looks like a file (e.g. `https://foo.bar/image.png`) or it is one of several special websites (e.g. Pixiv or Twitter / X status), try to download from this URL first.
    + `"None"` or `"none"`: Do not try to download from any source URL first.
  + Both source URLs and Danbooru URLs are stored in ImageInfo class and will be used when downloading. This parameters only controls the priority of URLs.
  + Set to a level other than `"None"` / `"none"` will reduce the pressure on Danbooru server but cost longer time (as source URLs may not be directly accessible, or they are absolutely unavailable).
+ `use_keyword_include`: If this parameter is set to `True`, DanbooruKeywordParser will try to find keyword / tag subgroups with less than 2 keywords / tags (Danbooru restrictions for those without an account) that contain all searching results with the least page number.
  + Only works when `standard_keyword_string` is used. When `keyword_string` is specified, this parameter is omitted.
  + For example, if the `standard_keyword_string` is set to `"kuon_(utawarerumono) AND rating:safe OR utawarerumono"`, then the Parser will check `"kuon_(utawarerumono) OR utawarerumono"` and `"rating:safe OR utawarerumono"` and select the group with the least page number of results as the keyword string in later queries.
  + If no subgroup with less than 2 keywords / tags exists (e.g. `"kuon_(utawarerumono) OR rating:safe OR utawarerumono"`), the Parser will try to find keyword / tag subgroups with the least keyword / tag number. This may often CAUSE ERRORS, so make a quick check of your keywords before setting this parameter to `True`.

#### Standard Syntax for Keywords

As different stations may have different syntaxes for keyword searching, Image Crawler Utils uses a standard syntax to parse the keyword string.

+ Logic symbols:
  + `AND` / `&` means searching images with both keywords / tags.
  + `OR` / `|` means searching images with either of the keywords / tags.
  + `NOT` / `!` means searching images without this keyword / tag.
  + `[` and `]` works like brackets in normal expressions, increasing the priority of the keyword / tag string included.
    + It is STRONGLY recommended to use `[` and `]` in order to avoid ambiguity.
    + **ATTENTION:** `(` and `)` are considered part of the keywords / tags instead of a logic symbol.
  + Priority of logic symbols is the same as C language, which is: **OR < AND < NOT < [ = ]**
+ Escape characters: Add `\` before any of the characters above except `(` and `)`to represent itself (like `\&`), while `\\` represents `\`.
  + **ATTENTION:** Python may not regard combinations like `\[` and `\]` as valid escape characters, and you should consider altering the string in this case.
+ If two keywords / tags have no logic symbols in between, they will be considered one keyword / tag connected by `_`. For example, `kuon (utawarerumono)` works the same as `kuon_(utawarerumono)`.
+ Keyword wildcards: `*` can be replaced with any string (include empty string).
  + `*key` means all keywords / tags that end with `key`. For example, `*dress` can match `dress` and `chinadress`.
  + `key*` means all keywords / tags that start with `key`. For example, `dress*` can match `dress` and `dress_shirt`.
  + `*key*` means all keywords / tags that contain `key`. For example, `*dress*` can match `dress`, `chinadress` and `dress_shirt`.
  + `ke*y` means all keywords / tags that start with `ke` and end with `y`. For example, `satono*(umamusume)` can match `satono_diamond_(umamusume)` and `satono_crown_(umamusume)`.
  + These wildcards can be combined, like `*ke*y`.

Example: `*dress AND NOT [kuon (utawarerumono) OR chinadress]` means search for images with keywords including ones ending with `dress` while excluding those having keywords `kuon_(utawarerumono)` and `chinadress`.

**ATTENTION:** Some sites may not support all of the syntaxes above, or have restrictions on keyword searching. Please refer to [notes for tasks](notes_for_tasks.md) for advanced usage.

### The list of ImageInfo()

`Parser.run()` returns a list of ImageInfo, which is defined in `image_crawler_utils`. ImageInfo is the basic unit for downloading with four attributes:

+ `url`: The URL used AT FIRST in downloading the image.
+ `name`: Name of the image when saved.
+ `info`: A `dict`, containing information of the image.
  + `info` will not affect Downloader directly. It only works if you set the `image_info_filter` parameter in the Downloader class.
  + Different sites may have different `info` structures which are defined respectively by their Parsers. Please refer to [notes for tasks](notes_for_tasks.md) for detailed information.
  + **ATTENTION:** If you define you own `info` structure, please ENSURE it can be JSON-serialized (e.g. The values of the `dict` should be `int`, `float`, `str`, `list`, `dict`, etc.) so that it is compatible with `save_image_infos()` and `load_image_infos()`.
+ `backup_urls`: When downloading from `url` failed, try downloading from URLs in the list of `backup_urls`.

The list of ImageInfo can be saved to a JSON file and loaded using `save_image_infos()` and `load_image_infos()` from `image_crawler_utils`.

```Python
from image_crawler_utils import save_image_infos, load_image_infos

save_image_infos(
    image_info_list: Iterable[ImageInfo], 
    json_file: str,
    encoding: str='UTF-8',
    display_progress: bool=True,
    log: Log=Log(),
)
image_info_list = load_image_infos(
    json_file: str,
    encoding: str='UTF-8',
    display_progress: bool=True,
    log: Log=Log(),
)

# Example
save_image_infos(image_info_list, "image_info_list.json")
new_image_info_list = load_image_infos("image_info_list.json")
```

+ `save_image_infos()` will return a tuple of `(saved .json file name, absolute path of saved .json file name)` when succeeded, or `None` when failed.
  + `image_info_list`: An iterable list (e.g. `list` or `set`) of `image_crawler_utils.ImageInfo`.
  + `json_file`: Name of the JSON file.
  + `encoding`: Encoding of the file. Default is `UTF-8`.
  + `display_progress`: Display an `rich` progress bar. Default is `True`.
  + `log`: An `image_crawler_utils.log.Log` class that controls logging.
+ `load_image_infos()` will return a list of ImageInfo when succeeded, or `None` when failed.
  + `json_file`: Name of the JSON file.
  + `encoding`: Encoding of the file. Default is `UTF-8`.
  + `display_progress`: Display an `rich` progress bar. Default is `True`.
  + `log`: An `image_crawler_utils.log.Log` class that controls logging.
+ The `log` parameter controls the levels of logging onto the console and into the file. You can use `log=crawler_settings.log` to make it the same as the CrawlerSettings you set up.

A JSON example of ImageInfo generated by DanbooruKeywordParser from [image ID 4994142](https://danbooru.donmai.us/posts/4994142) is like:

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

If you want to get the tags of this image (assume its `image_info` is an ImageInfo class), you should use `image_info.info["tags"]` instead of `image_info["info"]["tags"]` or `image_info.info.tags`.

## Running Downloader()

A Downloader will download images with information from the list of ImageInfo.

You can import Downloader from `image_crawler_utils`. A list of parameters in a Downloader is like:

```Python
from image_crawler_utils import Downloader

Downloader(
    crawler_settings: CrawlerSettings=CrawlerSettings(),
    image_info_list: Iterable[ImageInfo],
    store_path: str | Iterable[str]='./',
    image_info_filter: Callable | bool=True,
    cookies: Cookies | list | dict | str | None=Cookies(),
)

# Example
from image_crawler_utils.stations.booru import filter_keyword_booru

downloader = Downloader(
    crawler_settings=crawler_settings,
    image_info_list=image_info_list,
    store_path='path/folder/',
    image_info_filter=lambda info: filter_keyword_booru(info, "kuon_(utawarerumono)"),
    cookies='some_cookies_string',
)
```

+ `crawler_settings`: The CrawlerSettings used in this downloader.
+ `image_info_list`: A list of ImageInfo.
+ `store_path`: Path to store images, or a list of storage paths respectively for every image.
  + Default is the current working directory.
  + If it set to an iterable list, then its length should be the same as `image_info_list`.
+ `image_info_filter`: A callable function used to filter the images in the list of ImageInfo.
  + The function of `image_info_filter` should only accept 1 argument of ImageInfo type and returns `True` (download this image) or `False` (do not download this image), like:
  
    ```Python
    def filter_func(image_info: ImageInfo) -> bool:
        # Meet the conditions
        return True
        # Do not meet the conditions
        return False
    ```
  
  + If the function have other parameters, use `lambda` to exclude other parameters:
  
    ```Python
    image_info_filter=lambda info: filter_func(info, param1, param2, ...)
    ```
  
  + If you want to download all images in the ImageInfo list, set `image_info_filter` to `True`.
  + **TIPS:** If you want to search images with complex restrictions that the image station sites may not support (e.g. Images with many keywords and restrictions on the ratio between width and height), you can simplify the query with some keywords to get all images with Parsers, and filter them with your custom `image_info_filter` function.
+ `cookies`: Cookies used to access images from a website.
  + Can be one of `image_crawler_utils.Cookies`, `list`, `dict`, `str` or `None`.
    + For `image_crawler_utils.Cookies`, `list`, `dict` and `str` classes, see [Cookies class](#cookies-class) chapter for detailed information.
    + `None` means no cookies and works the same as `Cookies()`.
    + Leave this parameter blank works the same as `None` / `Cookies()`.
  + **TIPS:** You can add corresponding cookies to Downloader if there are URLs of images only accessible with an account. For example, if you have saved Pixiv and Twitter / X cookies respectively in `Pixiv_cookies.json` and `Twitter_cookies.json`, then you can use `cookies=Cookies.load_from_json("Pixiv_cookies.json") + Cookies.load_from_json("Twitter_cookies.json")` to add both cookies to the Downloader.

Use `.display_all_configs()` to display all parameters and configurations after a Downloader class is set up.

A Downloader class can be saved by `.save_to_pkl()`, or loaded with `Downloader.load_from_pkl()`, like:

```Python
from image_crawler_utils import Downloader
downloader = # Created in advance

# Save a Cookies
downloader.save_to_pkl('downloader.pkl')

# Load a Cookies
new_downloader = Downloader.load_from_pkl('downloader.pkl')
```

`downloader.run()` will download all images to `store_path`. The elements in tuple `(float, list[ImageInfo], list[ImageInfo], list[ImageInfo])` returned by `downloader.run()` are like:

```Python
download_traffic, succeeded_list, failed_list, skipped_list = downloader.run()
```

+ `download_traffic`: A float denoting the total size (in bytes) of images downloaded.
+ `succeeded_list`: A list of ImageInfo containing successfully downloaded images.
+ `failed_list`: A list of ImageInfo containing images failed to be downloaded.
  + Images not downloaded due to reaching `capacity` defined in CapacityCountConfig will be classified to this list.
+ `skipped_list`: A list of ImageInfo containing images skipped.
  + Images filtered out by the function of `image_info_filter`, not downloaded due to the restriction of `image_num` in CapacityCountConfig, and skipped due to such images already exist when `overwrite_images` in DownloadConfig is set to `False` will be classified to this list.

`succeeded_list`, `failed_list` and `skipped_list` can be saved or loaded with `save_image_infos()` or `load_image_infos()` for future uses.
