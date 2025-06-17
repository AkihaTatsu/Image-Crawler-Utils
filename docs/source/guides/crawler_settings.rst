Guide: CrawlerSettings Class
============================

A :class:`CrawlerSettings <image_crawler_utils.CrawlerSettings>` class contains basic information and configurations for Parsers and Downloaders. It can be imported from the :class:`image_crawler_utils` package.

You should always prepare a CrawlerSettings before starting the crawling.

Detailed Information
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: image_crawler_utils.CrawlerSettings
    :no-index:
    :members:
    :show-inheritance:
    :undoc-members:
    :inherited-members:

Configs, and how to Save and Load them
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When setting up a CrawlerSettings class, the parameters ``capacity_count_config``, ``download_config`` and ``debug_config`` can be respectively filled with classes :class:`CapacityCountConfig <image_crawler_utils.configs.CapacityCountConfig>`, :class:`DownloadConfig <image_crawler_utils.configs.DownloadConfig>` and :class:`DebugConfig <image_crawler_utils.configs.DebugConfig>`. You can also save or load them for later uses.

.. autoclass:: image_crawler_utils.configs.CapacityCountConfig
    :no-index:
    :members:
    :show-inheritance:
    :undoc-members:
    :inherited-members:

.. autoclass:: image_crawler_utils.configs.DownloadConfig
    :no-index:
    :members:
    :show-inheritance:
    :undoc-members:
    :inherited-members:

.. autoclass:: image_crawler_utils.configs.DebugConfig
    :no-index:
    :members:
    :show-inheritance:
    :undoc-members:
    :inherited-members:

Saving and Loading Configs
--------------------------

Use the 2 functions below to save and load these Configs.

.. autofunction:: image_crawler_utils.utils.save_dataclass
    :no-index:

.. autofunction:: image_crawler_utils.utils.load_dataclass
    :no-index:
