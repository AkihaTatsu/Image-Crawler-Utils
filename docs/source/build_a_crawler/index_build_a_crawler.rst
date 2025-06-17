Build a Custom Crawler
======================

Image Crawler Utils is designed to keep a balance between running a preset crawling task and building a custom image crawler as simply as possible.

Mostly, you only need to construct a Parser by inheriting the :class:`Parser <image_crawler_utils.Parser>` or :class:`KeywordParser <image_crawler_utils.Parser>` class. However, you should follow several requirements set by :class:`CrawlerSettings <image_crawler_utils.CrawlerSettings>`, :class:`ImageInfo <image_crawler_utils.ImageInfo>`, etc. Read :doc:`build_a_parser` for more details.

Besides, you may make use of several other classes and functions provided in the submodules of ``image_crawler_utils``. Read :doc:`useful_tools` for more details.

.. toctree::
   :maxdepth: 4

   build_a_parser
   useful_tools
