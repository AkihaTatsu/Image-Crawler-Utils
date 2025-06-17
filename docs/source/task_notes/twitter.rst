Twitter / X Tasks
=================

Twitter / X-related Parsers can be imported from :mod:`image_crawler_utils.stations.twitter`. Check out its documentation for more details.

Get Twitter / X Cookies
~~~~~~~~~~~~~~~~~~~~~~~

Please refer to the documentation of :func:`get_twitter_cookies() <image_crawler_utils.stations.twitter.get_twitter_cookies>` for detailed information.

You can save Twitter / X cookies for later use instead of calling this function every run.

Twitter / X Tips
~~~~~~~~~~~~~~~~

+ The main station URL of Twitter / X is: https://x.com/

.. note::
    Parsers of Twitter / X will not use the ``page_num`` parameter, as no gallery pages exist in Twitter / X.

    ``image_num`` will be used by Parsers of Twitter / X, but actual image number may exceed this parameter.
    
    + Twitter / X Parsers will only determine whether the number of images has exceeded ``image_num`` after a Twitter / X searching result page is fully scanned, or a batch of Twitter / X searching result pages are fully scanned.

.. important::

    If you want to download restricted contents, please configure your account settings before using Parsers.

About TwitterKeywordMediaParser
-------------------------------

For the meaning of parameters and attributes, check out the documentation of :class:`TwitterKeywordMediaParser <image_crawler_utils.stations.twitter.TwitterKeywordMediaParser>`.

If you want to set advanced searching options, check out the documentation of :class:`TwitterSearchSettings <image_crawler_utils.stations.twitter.TwitterSearchSettings>`. It can be passed in to the ``twitter_search_settings`` parameter.

About TwitterUserMediaParser
----------------------------

For the meaning of parameters and attributes, check out the documentation of :class:`TwitterUserMediaParser <image_crawler_utils.stations.twitter.TwitterUserMediaParser>`.

Example Program of TwitterKeywordMediaParser
--------------------------------------------

This example will download images with keyword (hashtags) "#クオン", "#イラスト" and "#うたわれるもの" which are sent before 2024/01/01 and only includes tweets with media into the ``Twitter`` folder. After you logging in to Twitter / X, the cookies will be saved at `Twitter_cookies.json` for later use.

.. literalinclude:: ../../../examples/twitter_keyword_example.py

Example Program of TwitterUserMediaParser
-----------------------------------------

This example will download media images of user "idonum" from 2023/1/1 to 2024/1/1 into the ``Twitter_user_idonum`` folder. After you logging in to Twitter / X, the cookies will be saved at ``Twitter_cookies.json`` for later use.

.. literalinclude:: ../../../examples/twitter_user_example.py

Example ImageInfo of Twitter / X
--------------------------------

This example image information (Twitter status 1622634960543973376) is from `this Twitter / X status (tweet) <https://x.com/InarikoNkoNa/status/1622634960543973376>`_. Its :class:`ImageInfo <image_crawler_utils.ImageInfo>` structure in JSON is like:

.. collapse:: CLICK HERE TO DISPLAY

    .. literalinclude:: ../JSONs/Twitter 1622634960543973376.json

---------
