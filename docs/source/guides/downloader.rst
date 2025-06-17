Guide: Downloader Class
=======================

A :class:`Downloader <image_crawler_utils.Downloader>` will download images with information from the list of ImageInfo.

You can import Downloader from :class:`image_crawler_utils`.

.. autoclass:: image_crawler_utils.Downloader
    :no-index:
    :members:
    :show-inheritance:
    :undoc-members:
    :inherited-members:

Examples of Downloader
~~~~~~~~~~~~~~~~~~~~~~

Mostly, you only need to run:

.. code-block:: python

    downloader = Downloader(
        crawler_settings=defined_CrawlerSettings
        image_info_list=list_of_ImageInfo
        # Set other parameters
    )
    downloader.run()

If you want to collect successfully downloaded list of images or list of images failed to be downloaded, you can use Downloader like:

.. code-block:: python

    download_traffic, succeeded_list, failed_list, skipped_list = downloader.run()

``succeeded_list``, ``failed_list`` and ``skipped_list`` can be saved or loaded with :func:`image_crawler_utils.save_image_infos()` or :func:`image_crawler_utils.load_image_infos()` for future uses.
