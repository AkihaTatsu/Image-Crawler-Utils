<h1 align="center">
教程
</h1>
<p align="center">
<a href="tutorials.md">English</a> | 简体中文
</p>

本教程将帮助你构建一个爬取程序，并使用特定关键词从Danbooru下载图像。建议开始之前先完成[README文档](README_zh.md)的阅读。

**警告：不要加载来源不明的`.pkl`文件！** 

**目录**

- [建立爬取程序设置（CrawlerSettings()）](#建立爬取程序设置crawlersettings)
  - [配置（Configs）](#配置configs)
    - [CapacityCountConfig()](#capacitycountconfig)
    - [DebugConfig()](#debugconfig)
    - [DownloadConfig()](#downloadconfig)
    - [配置的保存与读取](#配置的保存与读取)
- [设置解析器（Parser）](#设置解析器parser)
  - [获取Cookies](#获取cookies)
    - [Cookies()类](#cookies类)
  - [设置DanbooruKeywordParser()](#设置danboorukeywordparser)
    - [关键词的标准语法](#关键词的标准语法)
  - [ImageInfo()的列表](#imageinfo的列表)
- [运行Downloader()](#运行downloader)
---

## 建立爬取程序设置（CrawlerSettings()）

CrawlerSettings类包含为解析器（Parser）和下载器（Downloader）提供的基本信息和配置。可以从`image_crawler_utils`中导入该类。

CrawlerSettings参数的默认值如下所示：

```Python
from image_crawler_utils import CrawlerSettings
from image_crawler_utils.configs import DebugConfig

crawler_settings = CrawlerSettings(
    # 限制下载数量和流量的配置
    image_num: int | None=None,
    capacity: float | None=None,
    page_num: int | None=None,
    # 下载参数的配置
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
    # 控制在控制台上显示信息的配置
    debug_config=DebugConfig.level("info"),
    # 日志设置
    detailed_console_log: bool=False,
    # 自行使用时的额外参数
    extra_configs={
        "arg_name": config, 
        "arg_name2": config2, 
        ...
    },
)
```

+ 大部分参数的具体意义可参考[配置（Configs）](#配置configs)章节：
  + `image_num`
  + `capacity`
  + `page_num`
    + 其意义请参考[CapacityCountConfig()](#capacitycountconfig)章节，这类参数控制爬取时图片和页面的数量，以及图片的总大小。
    + 留空将会使用CapacityCountConfig中对应参数的默认值。
    + 也可以在设置一个CapacityCountConfig类之后，直接将其传入CrawlerSettings类的`capacity_count_config`参数中；这会覆盖以上参数的设置，如：
      
      ```Python
      from image_crawler_utils import CrawlerSettings
      from image_crawler_utils.configs import CapacityCountConfig

      crawler_settings = CrawlerSettings(
          capacity_count_config=CapacityCountConfig(
              image_num=200,
          )
          # 由于设置了CapacityCountConfig，该参数不会被使用
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
    + 其意义请参考[DownloadConfig()](#downloadconfig)章节，这类参数控制与下载网页和图像相关的设置。
    + 留空将会使用DownloadConfig中对应参数的默认值。
    + 也可以在设置一个DownloadConfig类之后，直接将其传入CrawlerSettings类的`download_config`参数中；这会覆盖以上参数的设置。
  + `debug_config`：应当为`image_crawler_utils.configs.DebugConfig`类，该参数控制消息在控制台上的显示级别。请参考[DebugConfig()](#debugconfig)章节。
+ `detailed_console_log`：向控制台输出详细版本的日志。
  + 当输出到控制台时，总是使用`msg`（输出到文件的日志信息）即使`output_msg`存在（参见[类与函数（English）#Log](classes_and_functions.md#log)一章）。
+ `extra_configs`：一个可选的`dict`参数，在目前支持的网站和爬取任务中没有被使用。此参数为开发自定义的图像爬取程序而保留。

由于控制台上显示的消息经过简化、通常不够完整，建议在运行爬取程序时添加日志文件。在设置完成CrawlerSettings后，使用`.set_logging_file()`添加一个日志文件句柄到当前爬取程序设置：

```Python
import logging

# crawler_settings = CrawlerSettings()

crawler_settings.set_logging_file(
    log_file: str,
    logging_level: int=logging.DEBUG,
)

# 样例
crawler_settings.set_logging_file("test.log")
```

+ `log_file`：日志文件名，例如`test.log`。
+ `logging_level`：记录到*文件*的日志级别。
  + 日志级别可以通过`import logging`后进行设定，包括`logging.DEBUG`、`logging.INFO`、`logging.WARNING`、`logging.ERROR`、`logging.CRITICAL`5个级别。每个级别会要求日志文件记录该级别及更高级别的消息。默认为`logging.DEBUG`级别。
  + **注意：** 该日志级别与控制台的消息显示级别是相互独立的！
    + 后者由`debug_config`参数控制，同时该参数也反过来不会影响日志文件的记录。

可以使用`.display_all_configs()`展示并检查当前CrawlerSettings的所有参数配置。

此类提供了以下属性函数：

+ `.connectivity_test(url: str)`可以检查是否能正常连接当前URL。日志消息会根据你的设定被记录在控制台上或文件内。
  + 若连接成功，返回`True`；若连接失败，返回`False`。
+ `.browser_test(url: str, headless: bool=True)`会检查浏览器是否能根据当前设置正常运行。日志消息会根据你的设定被记录在控制台上或文件内。
  + 若正常运行，返回`True`；若出现错误，返回`False`。
  + 将`headless`设为`False`会弹出一个浏览器窗口，展示整个加载页面的过程。
+ `.save_to_pkl(pkl_file: str | None=None)`可以将整个类保存到一个`.pkl`文件中。
  + 将`pkl_file`参数留空会让其文件名设置为原类在base64序列化后的字符串经过sha256加密得到的结果；一般可以确保每个不同的CrawlerSettings类对应不同的文件名。
  + 运行成功后将会返回元组`(保存的.pkl文件名, 保存的.pkl文件的绝对路径)`，或者运行失败后返回`None`。

可以通过以下函数生成新的CrawlerSettings类：

+ `.copy()`可以复制一个已有的CrawlerSettings，并修改其中的部分参数。
  + **注意：** 不建议通过直接修改CrawlerSettings属性的方式来对其进行更新。
  + 该函数内可以填入要在复制的CrawlerSettings中需要修改的参数，例如：
    
    ```Python
    new_settings = old_crawler_settings.copy(
        image_num=30,
    )
    ```

+ `CrawlerSettings.load_from_pkl()`可以从`.pkl`文件中读取并生成一个CrawlerSettings类。
  + 该函数第一个参数为`.pkl`文件名（必须包含后缀），第二个参数`log`控制日志输出到控制台和记录到文件的级别。

一个保存或读取CrawlerSettings的例子如下所示：

```Python
from image_crawler_utils import CrawlerSettings

crawler_settings = CrawlerSettings(download_config=DownloadConfig(image_num=20))

# 保存一个CrawlerSettings
crawler_settings.save_to_pkl("crawler_settings.pkl")

# 从文件中读取一个CrawlerSettings
new_crawler_settings = CrawlerSettings.load_from_pkl("crawler_settings.pkl")

# 复制一个CrawlerSettings，并修改其download_config
copied_crawler_settings = crawler_settings.copy(
    image_num=30,
)
```

### 配置（Configs）

#### CapacityCountConfig()

一个CapacityCountConfig的结构为：

```Python
from image_crawler_utils.configs import CapacityCountConfig

CapacityCountConfig(
    image_num: int | None=None,
    capacity: float | None=None,
    page_num: int | None=None,
)

# 样例
capacity_count_config = CapacityCountConfig(
    image_num=60,
    capacity=1024,
    page_num=2,
)
```

+ `image_num`：控制从网站解析、或者从图片列表中要下载的图片数量。
  + 默认为`None`，即没有任何限制。
  + 大部分时候只用于Downloader以控制下载图片的数量，但部分Parser也会使用此参数。详细信息请参考[网站任务说明（English）](notes_for_tasks.md)。
+ `capacity`：要下载的图片总大小。
  + 默认为`None`，即没有任何限制。
  + 当图片总大小达到此参数设定的大小时，新的下载线程不再会被添加，但已经开始的下载线程不会中断。这意味着实际下载的图片大小会略微超过此限制。
+ `page_num`：从网站下载的页面数量。一般用于有集中展示页的网站。
  + 默认为`None`，即没有任何限制。
  + [Twitter / X](https://x.com/)等网站不使用集中展示页或JSON-API页面（Image Crawler Utils通过滚动页面的方式来获得Twitter / X图片），此时该参数不被使用。详细信息请参考[网站任务说明（English）](notes_for_tasks.md)。

#### DebugConfig()

DebugConfig只控制在控制台上显示的消息的种类。对于记录到`.log`文件的设置，请使用`image_crawler_utils.CrawlerSettings.set_logging_file()`。

一个DebugConfig的结构为：

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

+ `show_debug`：显示调试级别的消息。
  + 默认为`False`。
  + 该级别包含运行爬取程序的详细消息，特别是网站的连接状况。
  + 将`show_debug`设置为`False`不会阻止任何`.display_all_configs()`显示其调试信息。
+ `show_info`：显示信息级别的消息。
  + 默认为`True`。
  + 该级别包含提示爬取程序进度的基本消息。
+ `show_warning`：显示警告级别的消息。
  + 默认为`True`。
  + 该级别包含基本不影响最终结果的错误消息，主要为未能成功连接至网页。
+ `show_error`：显示错误级别的消息。
  + 默认为`True`。
  + 该级别包含可能影响最终结果，但不中断爬取程序的错误消息。
+ `show_critical`：显示严重错误级别的消息。
  + 默认为`True`。
  + 该级别包含导致爬取程序中断的错误消息。通常一个Python错误会同时发生。

如果希望显示高于某级别的信息，使用`.set_level()`。

+ 其参数可以为`"debug"`、`"info"`、`"warning"`、`"error"`、`"critical"`或者`"silenced"`。
+ 设置一个日志级别会允许显示该级别及更高级别的消息。例如，`.set_level("warning")`将只会显示`"warning"`、`"error"`以及`"critical"`级别的消息。
+ 设置为`silenced`级别会停止显示除进度条之外的任何消息。

可以使用`DebugConfig.level("some_level")`直接生成一个拥有特定日志级别的DebugConfig（可以直接使用于部分参数中，如`CrawlerSettings(debug_config=DebugConfig.level("debug"))`）。

同时，如果你已经定义了一个`debug_config = DebugConfig()`，可以使用`debug_config.set_level("some_level")`来更改其日志级别。

#### DownloadConfig()

一个DownloadConfig的结构为：

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

# 样例
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

+ `headers`：设置请求的请求头。
  + 获取网页和下载图片都会使用此参数。
  + 请求头应当为`None`、一个`dict`或者返回一个`dict`的函数。
    + 如果希望每次请求使用不同的请求头，你可以设置`headers`为一个函数；此函数不应当接受任何参数（可以使用`lambda`实现）并返回一个`dict`。
  + 只有当请求为`requests`所发出（类似于`requests.get()`）时，此参数才会被使用。对于浏览器加载的网页，此参数会被忽略。
  + 通常此参数包含请求的UA（User Agent）信息。`image_crawler_utils.user_agent`中的`UserAgent`提供了可供选择的部分预定义请求头。
    + **注意：** 并非所有UA都会被爬取的网站所支持！详细信息请参考[网站任务说明（English）](notes_for_tasks.md)。

      ```Python
      from image_crawler_utils.user_agent import UserAgent
      
      download_config = DownloadConfig(
          # 使用一个随机的Chrome请求头
          headers=lambda: UserAgent.random_agent_with_name("chrome")
      )
      ```

+ `proxies`：爬取程序所使用的代理。
  + 获取网页和下载图片都会使用此参数。
  + 代理应当为`None`、一个`dict`或者返回一个`dict`的函数。
    + 设为`None`（默认）会让爬取程序使用系统代理。
    + 如果希望每次请求使用不同的代理，你可以设置`proxies`为一个函数；此函数不应当接受任何参数（可以使用`lambda`实现）并返回一个`dict`。
  + `requests`和浏览器都会使用此代理，但其结构应当符合`requests`所使用的格式，例如：
    + HTTP代理：`{'http': '127.0.0.1:7890'}`
    + HTTPS代理：`{'https': '127.0.0.1:7890'}`
    + SOCKS代理：`{'https': 'socks5://127.0.0.1:7890'}`
    + 如果你输入了`'https'`代理，`'http'`代理相应地会自动生成。
    + **注意：** 当前不支持使用用户名和密码。
+ `thread_delay`：在每个线程开始前的等待时间（秒）。
  + 获取网页和下载图片都会使用此参数。
  + 部分解析器可能会使用不同的参数来控制等待时间。详细信息请参考[网站任务说明（English）](notes_for_tasks.md)。
+ `fail_delay`：每次请求失败后的等待时间（秒）。
  + 获取网页和下载图片都会使用此参数。
  + 部分解析器可能会使用不同的参数来控制失败后的等待时间。详细信息请参考[网站任务说明（English）](notes_for_tasks.md)。
+ `randomize_delay`：让`thread_delay`和`fail_delay`变为在0与其实际值之间取值。
  + 例如，`thread_delay=5.0`及`randomize_delay=False`会让`thread_delay`实际上在每次调用时于0和5.0之间随机任取一个值。
+ `thread_num`：总线程数量。
  + 获取网页和下载图片都会使用此参数。
  + 部分解析器不使用多线程的方式获取页面，此时该参数不会被使用。详细信息请参考[网站任务说明（English）](notes_for_tasks.md)。
+ `timeout`：连接超时的时间。在`timeout`秒内请求无响应，则请求失败。
  + 获取网页和下载图片都会使用此参数。
  + 设为`None`则不限制超时时间。
+ `max_download_time`：当下载图片时于`max_download_time`秒内没有新的数据，则下载失败。
  + 只有下载图片会使用此参数。
  + 默认为`None`，即没有任何限制。
+ `retry_times`：获取网页 / 下载图片的尝试次数。
  + 获取网页和下载图片都会使用此参数。
+ `overwrite_images`：下载时是否覆盖已有图片。
  + 只有下载图片会使用此参数。

#### 配置的保存与读取

绝大部分配置可以用`save_dataclass()`和`load_dataclass()`进行保存与读取。两个函数均支持以下2种文件类型：`.json`和`.pkl`。

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

# 样例
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

+ `save_dataclass()`会将dataclass保存到一个文件中。
  + 设置`file_type`参数为`json`或`pkl`会强制函数将dataclass（配置）保存为该格式，或留空此参数会使得函数根据`file_name`决定保存的类型。
    + 即，`save_dataclass(dataclass, 'foo.json')`和`save_dataclass(dataclass, 'foo', 'json')`是等效的。
    + 当你的dataclass（配置）不包含无法JSON序列化的对象（例如一个函数）时，建议使用`.json`；同时，序列化数据文件`.pkl`支持大多数数据结构，但其文件不具有可读性。
    + `encoding`只有在保存为`.json`文件时启用。
  + 在运行成功后，函数将会返回元组`(保存的文件名, 保存的文件的绝对路径)`，或者运行失败后返回`None`。
+ `load_dataclass()`会从指定文件中加载dataclass（配置）到`dataclass_to_load`参数对应的变量中。
  + 设置`file_type`参数为`json`或`pkl`会强制函数将加载的文件视为此类型，或留空此参数会使得函数根据`file_name`决定文件类型。
    + 即，`load_dataclass(dataclass, 'foo.json')`和`load_dataclass(dataclass, 'foo.json', 'json')`是等效的。
    + `encoding`只有在以`.json`文件形式读取时启用。
  + `dataclass_to_load`中需要载入的变量应当和文件中保存的dataclass（配置）为同一个类。
  + 在运行成功后，函数将会返回加载文件内容后的`dataclass_to_load`，或者运行失败后返回`None`。
+ 参数`log`控制日志输出到控制台和记录到文件的级别。可以使用`log=crawler_settings.log`使其日志级别与你设置的CrawlerSettings相同。

## 设置解析器（Parser）

一个解析器能够从网站中解析图片信息。

对某个特定网站的解析器在`image_crawler_utils.stations.某个特定网站`中提供；例如，导入Danbooru的关键词解析器应当使用`from image_crawler_utils.stations.booru import DanbooruKeywordParser`。

在创建解析器时就应当完成其配置，并在调整设置完成后使用`image_info_list = Parser.run()`获得图片信息的列表，该列表可以传递给下载器（Downloader）。

以下为从Danbooru解析具有关键词`kuon_(utawarerumono)`和`rating:safe`的图片的例子：

```Python
from image_crawler_utils.stations.booru import DanbooruKeywordParser

parser = DanbooruKeywordParser(
    crawler_settings=crawler_settings,  # 需要提前完成定义
    standard_keyword_string="kuon_(utawarerumono) AND rating:safe",
)
image_info_list = parser.run()
```

一个Parser类可以使用`.save_to_pkl()`进行保存，同时用该类对应的`.load_from_pkl()`进行读取（如`DanbooruKeywordParser.load_from_pkl()`），例如：

```Python
from image_crawler_utils.stations.booru import DanbooruKeywordParser

parser = DanbooruKeywordParser(
    crawler_settings=crawler_settings,  # 需要预先定义
    standard_keyword_string="kuon_(utawarerumono) AND rating:safe",
)
# 保存一个DanbooruKeywordParser
parser.save_to_pkl('parser.pkl')

# 读取一个DanbooruKeywordParser
new_parser = DanbooruKeywordParser.load_from_pkl('parser.pkl')
```

使用`.display_all_configs()`检查当前Parser的所有参数。

### 获取Cookies

某些网站需要cookies以取得结果。此处提供了部分函数以获得包含登录信息的cookies。

例如，获得Pixiv的cookies可以使用`image_crawler_utils.stations.pixiv`中的`get_pixiv_cookies`：

```Python
from image_crawler_utils.stations.pixiv import get_pixiv_cookies

cookies = get_pixiv_cookies(
    pixiv_id="mail@address",
    password="password",
    proxies={"proxy_type": "proxy_address"}, 
    timeout=30.0,
    headless=False, 
    waiting_seconds=60.0, 
)
```

+ `pixiv_id`：账号的Pixiv ID或邮箱地址。留空以手动输入。
+ `password`：账号的密码。留空以手动输入。
+ `proxies`：打开登录界面的代理。使用的格式与[DownloadConfig](#downloadconfig)中的格式相同。
+ `timeout`：等待网页元素加载的时间（秒）。如果在`timeout`秒内元素未能加载，则记录错误并返回`None`。默认为30。
+ `headless`：一个`bool`类，决定是否使用无头模式（不显示窗口），默认为`False`。**强烈建议不要设置为`True`**，否则会无法通过可能的验证码或邮箱验证。
+ `waiting_seconds`：在`headless=True`的情况下，如果在`waiting_seconds`秒内未能登录，则记录错误并返回`None`。默认为60。

`get_pixiv_cookies()`使用浏览器生成一个页面以完成登录。如果需要进行确认（如reCAPTCHA检查，邮件确认等），你必须手动完成此步骤。

#### Cookies()类

`get_pixiv_cookies()`的结果是一个`image_crawler_utils.Cookies`类，这个结果可以被用于解析器和下载器中。

Cookies类可以从`image_crawler_utils`中导入。一个Cookies可以通过`Cookies.create_by()`创建，并接受以下4种形式：

+ `str`：这种cookies可以通过部分浏览器的开发者模式（F12）等方式获得。

  ```Python
  from image_crawler_utils import Cookies
  
  cookies = Cookies.create_by("your_cookies_string")
  ```

+ `dict`：这种cookies可以通过`requests`相关的函数和类、或者其他类似于`get_dict()`的cookie函数等方式获得。

  ```Python
  import requests
  from image_crawler_utils import Cookies
  
  session = requests.Session()
  # 将cookies添加到session的过程
  requests_cookies = session.cookies.get_dict()  # A list
  cookies = Cookies.create_by(requests_cookies)
  ```

+ `list[dict]`：这种cookies可以通过selenium相关的函数和类等方式获得。

  ```Python
  from selenium.webdriver import Chrome
  from image_crawler_utils import Cookies
  
  chrome_driver_path = '/path/to/chromedriver'
  chrome_browser = webdriver.Chrome(executable_path=chrome_driver_path)
  chrome_browser.get('https://foo.bar.com')
  # 一些其他过程
  selenium_cookies = chrome_browser.get_cookies()  # 一个dict
  cookies = Cookies.create_by(selenium_cookies)
  ```

+ `list[nodriver.cdp.network.Cookie]`：这种cookies可以通过nodriver相关的函数和类等方式获得。

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

此类包含了为不同情况所准备的数个属性：

+ `.cookies_string`：以`str`类型表示的cookies。
+ `.cookies_dict`：以`dict`类型表示的cookies，可以在`requests`相关的环境下使用：

  ```Python
  import requests
  
  session = requests.Session()
  session.cookies.update(cookies.cookies_dict)
  ```

+ `.cookies_selenium`：以`list[dict]`类型表示的cookies，可以在selenium相关的环境下使用。
  + **注意：** 如果你通过`str`或`dict`创建了一个Cookies，则`.cookies_selenium`**不能**被直接用在selenium的webdriver中（信息存在部分缺失）。这种情况下应当使用`.update_selenium_cookies()`。
+ `.cookies_nodriver`：以`list[nodriver.cdp.network.Cookie]`类型表示的cookies，可以在nodriver相关的环境下使用。
+ `.update_selenium_cookies()`：更新selenium的webdriver中的cookies。其输入应当为一个selenium形式的cookies（一个`list[dict]`），该函数会返回一个新的selenium形式的cookies，其中包含了Cookies类中存储的信息。如果你通过`str`或`dict`创建了一个Cookies类，此函数可以用于向selenium的webdriver添加cookies。
  + 没有domain的cookies会被赋值为输入cookies中出现次数最多的domain。

    ```Python
    from selenium.webdriver import Chrome
    from image_crawler_utils import Cookies
    
    chrome_driver_path = '/path/to/chromedriver'
    chrome_browser = webdriver.Chrome(executable_path=chrome_driver_path)
    chrome_browser.get('https://foo.bar.com')
    
    # 更新selenium的cookies
    new_cookies = cookies.update_selenium_cookies(driver.get_cookies())
    for new_cookie in new_cookies:
        driver.add_cookie(new_cookie)
    chrome_browser.get('https://foo.bar.com')
    ```

+ `.update_nodriver_cookies()`：更新nodriver的实例中的cookies。其输入应当为一个nodriver形式的cookies（一个`list[nodriver.cdp.network.Cookie]`），该函数会返回一个新的nodriver形式的cookies，其中包含了Cookies类中存储的信息。
  + 对于nodriver，其可以通过`browser.cookies.get_all()`生成cookies，这里`browser`是一个`nodriver.Browser`实例。
  + 如果你通过`str`或`dict`创建了一个Cookies类，**不要**直接使用此函数为nodriver实例设置cookies。请使用下文中提到的`update_nodriver_browser_cookies()`代替。
  + 没有domain的cookies会被赋值为输入cookies中出现次数最多的domain。
+ `.is_none()`：一个布尔值，表示当前Cookies类是否为空。
  + 如果Cookies是直接创建的（例如`cookies = Cookies()`），则`.is_none()`会返回`True`，否则返回`False`。

`image_crawler_utils`中提供了专门用于将通过`str`或`dict`创建的Cookies添加到nodriver实例中的`update_nodriver_browser_cookies()`函数。

```Python
import nodriver
from image_crawler_utils.utils import set_up_nodriver_browser
from image_crawler_utils import Cookies, update_nodriver_browser_cookies

async def nodriver_func(cookies: Cookies):
    browser = await set_up_nodriver_browser()
    tab = await browser.get('https://foo.bar.com')

    # 更新nodriver的cookies
    await update_nodriver_browser_cookies(browser, cookies)  # 这是一个异步函数
    browser.get('https://foo.bar.com')

foo_cookies: Cookies = # 从其他来源创建的cookies
nodriver.loop().run_until_complete(nodriver_func(cookies=foo_cookies))
```

一个Cookies类可以使用`.save_to_json()`进行保存，同时用`Cookies.load_from_json()`进行读取，例如：

```Python
from image_crawler_utils import Cookies
cookies = Cookies.create_by(foo_cookies)

# 保存一个Cookies
cookies.save_to_json('cookies.json', encoding='UTF-8')

# 读取一个Cookies
new_cookies = Cookies.load_from_json('cookies.json', encoding='UTF-8')
```

两个Cookies类可以进行相加；如果二者中存在拥有相同的`name`属性的cookie，则后者中该`name`对应的cookie会被忽略。

### 设置DanbooruKeywordParser()

Danbooru与其他使用booru框架的网站有许多共同特征，从而其解析器有数个共通的参数。在开始前请先阅读[Danbooru的备忘单](https://danbooru.donmai.us/wiki_pages/help:cheatsheet)。

DanbooruKeywordParser参数的详细列表如下所示：

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

# 样例
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

+ `crawler_settings`：此解析器使用的CrawlerSettings。
+ `station_url`：网站主页的URL。
  + 当多个网站使用相同的框架时，此参数有效。例如，[yande.re](https://yande.re/)和[konachan.com](https://konachan.com/)同时使用Moebooru建立其网站，此参数必须被指定以处理不同的网站。
  + 对于类似[Pixiv](https://www.pixiv.net/)的、不存在其他网站使用其框架的网站，此参数已被提前初始化，不需要使用。
+ `standard_keyword_string`：使用标准语法的关键词查询字符串。详细信息参见[关键词的标准语法](#关键词的标准语法)章节。
+ `keyword_string`：如果你希望直接指定搜索时的关键词，将`keyword_string`设置为一个自定义的非空字符串。该参数会**覆盖**`standard_keyword_string`。
  + 例如，将DanbooruKeywordParser中的`keyword_string`设置为`"kuon_(utawarerumono) rating:safe"`意味着将在Danbooru中直接以此字符串搜索；其标准语法关键词字符串的等价为`"kuon_(utawarerumono) AND rating:safe"`。
  + `standard_keyword_string`和`keyword_string`不能同时为`None`或为空（只含有空格），否则一个严重错误将会发生！
+ `cookies`：从网站上获取信息时使用的cookies。
  + 可以为`image_crawler_utils.Cookies`、`list`、`dict`、`str`或`None`。
    + 对于各类的使用方法的详细信息，请参考[Cookies()类](#cookies类)章节。
    + `None`意味着没有cookies，其等效于`Cookies()`。
    + 将此参数留空与设置为`None` / `Cookies()`相同。
+ `replace_url_with_source_level`：一个控制解析器尝试从图像源链接而非Danbooru链接进行下载的等级。
  + 有3个可用等级，且默认等级为`"None"`：
    + `"All"`或`"all"`（**不建议**）：只要图像有源URL，尝试优先从此URL下载。
    + `"File"`或`"file"`：如果源URL形似一个文件（例如`https://foo.bar/image.png`），或源URL为若干个特殊的网址（例如Pixiv或Twitter / X的推文）之一，则尝试优先从此URL下载。
    + `"None"`或`"none"`：不尝试优先从任何源URL下载。
  + 源URL和Danbooru的URL都将存储在ImageInfo类中，并在下载时均会被检查使用。这个参数只控制下载时使用URL的优先级。
  + 设置为除`"None"` / `"none"`之外的等级可以减少Danbooru服务器经受的压力，但会花费更长的时间（由于源URL可能无法直接连接，或已经失效）。
+ `use_keyword_include`：如果此参数设置为`True`，DanbooruKeywordParser会尝试寻找具有小于等于2个关键词 / 标签（Danbooru对无账号搜索的限制）的、包含所有要查找图片的关键词 / 标签子组，并从中选择对应页面数量最少的子组。
  + 只有在`standard_keyword_string`被启用时有效。如果指定了`keyword_string`，此参数被忽略。
  + 例如，如果`standard_keyword_string`被设置为`"kuon_(utawarerumono) AND rating:safe OR utawarerumono"`，则解析器会分别以`"kuon_(utawarerumono) OR utawarerumono"`和`"rating:safe OR utawarerumono"`进行搜索，并选择有着最少页面数的一组作为关键词字符串用于之后的搜索中。
  + 如果不存在有着小于等于2个关键词 / 标签的子组（例如`"kuon_(utawarerumono) OR rating:safe OR utawarerumono"`），则解析器会尝试寻找有着最少关键词 / 标签数量的子组。这经常会**造成错误**，因此在设定此参数为`True`之前，建议先对关键词字符串做一次快速检查。

#### 关键词的标准语法

由于不同的站点会使用不同的关键词搜索语法，Image Crawler Utils使用一组标准化的语法来解析关键词字符串。

+ 逻辑符号：
  + `AND` / `&`表示搜索同时包含两个关键词 / 标签的图片。
  + `OR` / `|`表示搜索包含其中至少一个关键词 / 标签的图片。
  + `NOT` / `!`表示搜索不含该关键词 / 标签的图片。
  + `[`和`]`与通常表达式中的括号作用相同，提升被包含的关键词 / 标签的优先级。
    + 此处**强烈**建议使用`[`和`]`以避免歧义。
    + **注意：** `(`和`)`被视作关键词 / 标签的一部分，而非一个逻辑符号。
  + 逻辑符号的优先级遵循C语言优先级，即：**OR < AND < NOT < [ = ]**
+ 转义字符：用`\`加上以上除`(`、`)`之外的任意一个符号（如`\&`）即可表示其符号本身，同时`\\`可表示`\`。
  + **注意：** Python本身可能不认为类似`\[`、`\]`的字符组合是合法的转义字符，因此需要视情况将原字符串进行相应调整。
+ 如果两个关键词 / 标签之间没有任何逻辑符号连接，则其将会被视为用`_`连接的同一个关键词。例如，`kuon (utawarerumono)`等效于`kuon_(utawarerumono)`。
+ 关键词的通配符：`*`可以替换为任何一个字符串（包括空字符串）。
  + `*key`表示所有以`key`结束的关键词。例如，`*dress`可以匹配到`dress`和`chinadress`。
  + `key*`表示所有以`key`开始的关键词。例如，`dress*`可以匹配到`dress`和`dress_shirt`。
  + `*key*`表示所有包含`key`的关键词。例如，`*dress*`可以匹配到`dress`、`chinadress`和`dress_shirt`。
  + `ke*y`表示所有以`ke`开始、以`y`结束的关键词。例如，`satono*(umamusume)`可以匹配到`satono_diamond_(umamusume)`和`satono_crown_(umamusume)`。
  + 这些通配符可以组合使用，例如`*ke*y`。

例如：`*dress AND NOT [kuon (utawarerumono) OR chinadress]`表示搜索所有包含以`dress`结尾的关键词、同时不包含`kuon_(utawarerumono)`和`chinadress`关键词的图片。

**注意：** 部分网站不支持前述的所有语法，或在关键词搜索上存在限制。进阶使用请参考[网站任务说明（English）](notes_for_tasks.md)。

### ImageInfo()的列表

`Parser.run()`返回一个ImageInfo的列表。`image_crawler_utils`中定义的ImageInfo是图片下载的基本单元，包含以下四个属性：

+ `url`：下载图片时**最优先**使用的URL。
+ `name`：保存时图片的文件名。
+ `info`：一个`dict`，包含图片相关的信息。
  + `info`不会直接影响下载器。只有在你设定了Downloader类中的`image_info_filter`参数时，该项会起作用。
  + 不同的站点可能具有不同的`info`结构，这些结构分别由其解析器定义。详细信息请参考[网站任务说明（English）](notes_for_tasks.md)。
  + **注意：** 如果你定义属于自己的`info`结构，请尽量**保证**该结构可以被JSON序列化（例如，`dict`中元素的取值应当为`int`、`float`、`str`、`list`、`dict`等）以使得其可以配合`save_image_infos()`和`load_image_infos()`使用。
+ `backup_urls`：当从`url`下载失败时，尝试从`backup_urls`的列表中的URL进行下载。

可以使用`image_crawler_utils`中的`save_image_infos()`和`load_image_infos()`将ImageInfo的列表保存到一个JSON文件中或从中进行加载。

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

# 样例
save_image_infos(image_info_list, "image_info_list.json")
new_image_info_list = load_image_infos("image_info_list.json")
```

+ `save_image_infos()`在运行成功后将会返回元组`(保存的.json文件名, 保存的.json文件的绝对路径)`，或者运行失败后返回`None`。
  + `image_info_list`：一个可迭代的`image_crawler_utils.ImageInfo`的列表（如`list`或`set`）。
  + `json_file`：JSON文件的名称。
  + `encoding`：文件编码的类型。默认为`UTF-8`。
  + `display_progress`：显示一个`rich`进度条。默认为`True`。
  + `log`：一个控制日志输出的`image_crawler_utils.log.Log`类。
+ `load_image_infos()`在运行成功后将会返回一个ImageInfo的列表，或者运行失败后返回`None`。
  + `json_file`：JSON文件的名称。
  + `encoding`：文件编码的类型。默认为`UTF-8`。
  + `display_progress`：显示一个`rich`进度条。默认为`True`。
  + `log`：一个控制日志输出的`image_crawler_utils.log.Log`类。
+ 参数`log`控制日志输出到控制台和记录到文件的级别。可以使用`log=crawler_settings.log`使其日志级别与你设置的CrawlerSettings相同。

此处给出由DanbooruKeywordParser对Danbooru上[ID为4994142的图片](https://danbooru.donmai.us/posts/4994142)生成的ImageInfo保存为JSON的样例：

<details>
<summary><b>用JSON表示的ImageInfo结构</b></summary>

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

如果你希望获得此图片的标签（假定其对应的`image_info`属于ImageInfo类），应当使用`image_info.info["tags"]`而不是`image_info["info"]["tags"]`或者`image_info.info.tags`。

## 运行Downloader()

一个下载器（Downloader）可以从带有图片信息的ImageInfo列表中下载图片。

你可以从`image_crawler_utils`中导入Downloader类。Downloader中的参数列表如下所示：

```Python
from image_crawler_utils import Downloader

Downloader(
    crawler_settings: CrawlerSettings=CrawlerSettings(),
    image_info_list: Iterable[ImageInfo],
    store_path: str | Iterable[str]='./',
    image_info_filter: Callable | bool=True,
    cookies: Cookies | list | dict | str | None=Cookies(),
)

# 样例
from image_crawler_utils.stations.booru import filter_keyword_booru

downloader = Downloader(
    crawler_settings=crawler_settings,
    image_info_list=image_info_list,
    store_path='path/folder/',
    image_info_filter=lambda info: filter_keyword_booru(info, "kuon_(utawarerumono)"),
    cookies='some_cookies_string',
)
```

+ `crawler_settings`：此下载器使用的CrawlerSettings。
+ `image_info_list`：ImageInfo的列表。
+ `store_path`：存储与图像的路径，或每张图片存储路径的列表。
  + 默认为当前工作目录。
  + 如果设置为列表，则其长度应当和`image_info_list`相同。
+ `image_info_filter`：一个函数，用以筛选ImageInfo的列表。
  + `image_info_filter`使用的函数应当只接受1个ImageInfo类型的参数，且只返回`True`（下载此图片）或`False`（不下载此图片），例如：
  
    ```Python
    def filter_func(image_info: ImageInfo) -> bool:
        # 符合要求
        return True
        # 不符合要求
        return False
    ```
  
  + 如果函数有其他参数，使用`lambda`来排除其他参数：
  
    ```Python
    image_info_filter=lambda info: filter_func(info, param1, param2, ...)
    ```
  
  + 如果你希望下载ImageInfo列表中所有的图片，将`image_info_filter`设置为`True`。
  + **提示：** 如果你希望在网站上进行带有复杂约束条件、以至于网站不一定支持的图片搜索（例如，搜索有着大量关键词、以及带对比例和大小等约束的图片），可以先简化为搜索若干个关键词，再使用自定义的`image_info_filter`函数进行筛选。
+ `cookies`：从网站上获取图片时使用的cookies。
  + 可以为`image_crawler_utils.Cookies`、`list`、`dict`、`str`或`None`。
    + 对于各类的使用方法的详细信息，请参考[Cookies()类](#cookies类)章节。
    + `None`意味着没有cookies，其等效于`Cookies()`。
    + 将此参数留空与设置为`None` / `Cookies()`相同。
  + **提示：** 如果部分图片所在的URL必须要一个账号才能连接，你可以添加相应的cookies到Downloader中。例如，如果你已经事先将Pixiv和Twitter / X的cookies保存在`Pixiv_cookies.json`和`Twitter_cookies.json`中，则可以使用`cookies=Cookies.load_from_json("Pixiv_cookies.json") + Cookies.load_from_json("Twitter_cookies.json")`将两个cookies都添加到Downloader中。

在Downloader类被创建后，使用`.display_all_configs()`以展示所有参数和配置。

一个Downloader类可以使用`.save_to_pkl()`进行保存，同时用`Downloader.load_from_pkl()`进行读取，例如：

```Python
from image_crawler_utils import Downloader
downloader = # 需要提前创建

# 保存一个Downloader
downloader.save_to_pkl('downloader.pkl')

# 加载一个Downloader
new_downloader = Downloader.load_from_pkl('downloader.pkl')
```

`downloader.run()`会将所有图片下载到`store_path`定义的路径中。`downloader.run()`返回的元组`(float, list[ImageInfo], list[ImageInfo], list[ImageInfo])`的各元素为：

```Python
download_traffic, succeeded_list, failed_list, skipped_list = downloader.run()
```

+ `download_traffic`：当前下载图片的总大小（Bytes）。
+ `succeeded_list`：一个ImageInfo的列表，包含所有下载成功的图片。
+ `failed_list`：一个ImageInfo的列表，包含所有下载失败的图片。
  + 由于已下载图片总大小达到CapacityCountConfig中`capacity`的值导致未能下载的剩余图片会被归类到此列表中。
+ `skipped_list`：一个ImageInfo的列表，包含所有跳过下载的图片。
  + 被`image_info_filter`所筛出不下载的图片，由于CapacityCountConfig中`image_num`的限制而未能下载的图片，以及由于DownloadConfig中`overwrite_images`被设置为`False`且目标图片已经存在导致跳过的图片都会被归类到此列表中。

`succeeded_list`、`failed_list`和`skipped_list`可以用`save_image_infos()`或`load_image_infos()`进行保存和读取以便将来使用。
