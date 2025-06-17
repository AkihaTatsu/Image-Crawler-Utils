Useful Classes and Functions
============================

Most tools for building your custom image crawlers are provided in the submodules of :class:`image_crawler_utils`. Check out the :doc:`../modules` for detailed information.

Logging
~~~~~~~

Logging in Image Crawler Utils is packed in :class:`Log <image_crawler_utils.log.Log>` class, which uses :external:ref:`rich`-style output for logging onto console and :py:mod:`logging` library for logging into files.

Logging parameters is mostly set when creating :class:`CrawlerSettings <image_crawler_utils.CrawlerSettings>`. You can refer to the :doc:`../guides/crawler_settings` for more details. To log information in most Parsers and Downloaders, you can write it like

.. code-block:: python

    self.crawler_settings.log.info("LOGGING INFO")

To determine which logging level should be used, check out the documentation of Log class:

.. autoclass:: image_crawler_utils.log.Log
    :no-index:
    :members:
    :show-inheritance:
    :undoc-members:

Progress Bars
~~~~~~~~~~~~~

Image Crawler Utils currently use :external:ref:`progress` of :external:ref:`rich` to display progress bars, with several classes like :class:`CustomProgress <image_crawler_utils.progress_bar.CustomProgress>` designed for simple implementation.

CustomProgress Class
--------------------

If you want to display only one progress bar, check out the documentation of :class:`CustomProgress <image_crawler_utils.progress_bar.CustomProgress>`:

.. autoclass:: image_crawler_utils.progress_bar.CustomProgress
    :no-index:
    :members:
    :show-inheritance:
    :inherited-members:

Examples of CustomProgress
^^^^^^^^^^^^^^^^^^^^^^^^^^

An example of using CustomProgress is like:

.. code-block:: python

    from image_crawler_utils.progress_bar import CustomProgress

    # Create a Progress instance with spinner which vanishes after finishing
    with CustomProgress(has_spinner=True, transient=True) as progress:
        # Set the task for current progress bar
        task_1 = progress.add_task(description="foo", total=100)
        # Multiple tasks can be created for one Progress instance, 
        # which will be displayed as a different progress bar
        task_2 = progress.add_task(description="bar", total=50)

        try:
            for i in range(50):
                '''Do something'''
                # Update the progress bar for 2 progress
                progress.update(task_1, advance=2, description="foo_new")
                progress.update(task_2)  # Default: advance=1
        
        except:
            # If an error happens and you need to finish the progress immediately,
            # use CustomProgress.finish_task()
            progress.finish_task(task_1)
            progress.finish_task(task_2)

    # If you do not wish to use ``with`` structure,
    # you can switch to the code below:
    progress = CustomProgress()
    progress.start()
    '''Do something like above'''
    progress.stop()

ProgressGroup Class
-------------------

If you want to display multiple progress bars at once, it is recommended to use :class:`ProgressGroup <image_crawler_utils.progress_bar.ProgressGroup>`.

.. warning::
    
    DO NOT try to start another :py:class:`Progress <rich.progress.Progress>` instance (like :class:`CustomProgress <image_crawler_utils.progress_bar.CustomProgress>`) while a progress bar instance is already running! An error will be raised.

.. autoclass:: image_crawler_utils.progress_bar.ProgressGroup
    :no-index:
    :members:
    :show-inheritance:
    :undoc-members:

The ProgressGroup provided several preset :py:class:`Progress <rich.progress.Progress>` instances, which will be displayed from top to bottom in the order below:

============================ ========= ========= ======= =========
        Attribute            transient has_total is_file text_only
============================ ========= ========= ======= =========
     ``.main_file_bar``        False     True     True     False  
    ``.main_count_bar``        False     True     False    False  
``.main_no_total_file_bar``    False     False    True     False  
``.main_no_total_count_bar``   False     False    False    False  
  ``.main_text_only_bar``      False       /        /      True   
     ``.sub_file_bar``         True      True     True     False  
     ``.sub_count_bar``        True      True     False    False  
 ``.sub_no_total_file_bar``    True      False    True     False  
``.sub_no_total_count_bar``    True      False    False    False  
   ``.sub_text_only_bar``      True        /        /      True   
============================ ========= ========= ======= =========

You can add you own :py:class:`Progress <rich.progress.Progress>` instances in the ``progress_list``, which will be displayed below all of the preset Progress instances.

As one :py:class:`Progress <rich.progress.Progress>` instance can have multiple tasks (i.e. multiple progress bars), it is suggested to use the preset Progress instances first to create your progress bars.

Examples of ProgressGroup
^^^^^^^^^^^^^^^^^^^^^^^^^

An example of using ProgressGroup is like:

.. code-block:: python

    from image_crawler_utils.progress_bar import ProgressGroup, CustomProgress

    # Use a custom progress bar which vanishes after finishing
    custom_progress = CustomProgress(transient=True)

    # Create a progress group
    with ProgressGroup(
        # Add the custom Progress instance into the progress group
        progress_list=[custom_progress]
        # Set the panel title
        panel_title="Downloading"
    ) as progress_group:
        # Use the preset .main_count_bar
        main_progress = progress_group.main_count_bar
        task_main = main_bar.add_task(total=10, description="Foo")

        for i in range(10):
            # The task_sub progress bar will be displayed
            # below the task_main progress bar
            task_sub = progress_group.progress_list[0].add_task(total=5, description="Bar")

            for j in range(5):
                '''Do something'''
                # Update the task_sub progress bar
                progress_group.progress_list[0].update(task_sub)

            # Update the task_main progress bar
            progress_group.main_count_bar.update(task_main)

    # If you do not wish to use ``with`` structure,
    # you can switch to the code below:
    progress_group = ProgressGroup()
    progress_group.start()
    '''Do something like above'''
    progress_group.stop()

User Agents
~~~~~~~~~~~

Currently, Image Crawler Utils use `ua-generator <https://github.com/iamdual/ua-generator/tree/master>`_ for generating random user agents. Checkout its documentation for more details.

Other Tools
~~~~~~~~~~~

The :mod:`image_crawler_utils.utils` provided a wide variety of functions and classes for different uses. 

.. automodule:: image_crawler_utils.utils
    :no-index:
    :members:
    :show-inheritance:
    :undoc-members:
    