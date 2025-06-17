.. Image Crawler Utils documentation master file, created by
   sphinx-quickstart on Sun Jun 15 12:20:18 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Image Crawler Utils Documentation
=================================

A **rather customizable** image crawler structure, designed to download images with their information using multi-threading method. This GIF depicts a sample run:

.. image::  ../example.gif

Besides, several classes and functions have been implemented to help better build a custom image crawler for yourself.

**Please follow the rules of robots.txt, and set a low number of threads with high number of delay time when crawling images. Frequent requests and massive download traffic may result in IP addresses being banned or accounts being suspended.**

Installation
------------

It is recommended to install it by

::

    pip install image-crawler-utils

* Requires ``Python >= 3.9``.

.. important::
    
    `nodriver <https://github.com/ultrafunkamsterdam/nodriver>`_ are used to parse information from certain websites. It is suggested to install the latest version of `Google Chrome <https://www.google.com/chrome/>`_ first to ensure the crawler will be correctly running.

Guides
------

It is recommended to start Image Crawler Utils with the :doc:`get_started` chapter.

For those using the preset crawling tasks, check out the :doc:`task_notes/index_tasks` chapter.

For those planning to construct a custom crawler, check out the :doc:`build_a_crawler/index_build_a_crawler` chapter.

.. toctree::
    :maxdepth: 2
    :caption: Quick Start

    get_started
    guides/crawler_settings
    guides/parser_example
    guides/downloader

.. toctree::
    :maxdepth: 2
    :caption: Advanced Usage

    task_notes/index_tasks
    build_a_crawler/index_build_a_crawler

.. toctree::
    :maxdepth: 2
    :caption: Modules

    modules
