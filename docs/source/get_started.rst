Get Started
===========

After successfully installing Image Crawler Utils, you can test the library with this example program:

.. literalinclude:: ../../examples/danbooru_example.py

If no error is thrown, the program should download several pictures into the ``Danbooru`` folder in the same directory of your program, with an ``image_info_list.json`` containing their information.

As described in the code, the program is divided into 3 parts:

1. The :doc:`CrawlerSettings <guides/crawler_settings>` part, which controls all parameters later used. You need to set up a :class:`CrawlerSettings <image_crawler_utils.CrawlerSettings>` class before running the crawler.
#. The :doc:`Parser <guides/parser_example>` part, which crawls the information of images from certain websites. The required :class:`Parser <image_crawler_utils.Parser>` class (like :class:`DanbooruKeywordParser <image_crawler_utils.stations.booru.DanbooruKeywordParser>` here) should be selected and extra parameters need to be filled before running the Parser.
#. The :doc:`Downloader <guides/downloader>` part, which downloads all images from the list of :class:`ImageInfo <image_crawler_utils.ImageInfo>` generated from the Parser part.

Check out the respective documents for detailed guides.
