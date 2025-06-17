import os, sys
from typing import Optional, Union
from collections.abc import Mapping

import logging, getpass
import re
import rich
from rich import markup
import rich.default_styles
from rich.logging import RichHandler

from .configs import DebugConfig



##### Initialization


logging.basicConfig(
    level=logging.NOTSET,
    handlers=[],
)

__rich_handler = RichHandler(
    log_time_format='[%X]',
    show_path=False,
)
__rich_handler.setFormatter(logging.Formatter('%(message)s'))
__rich_handler.setLevel(logging.NOTSET)
__rich_logger = logging.getLogger("Console")
__rich_logger.addHandler(__rich_handler)


##### Log utils


def print_logging_msg(
        msg: str,
        level: str='',
        debug_config: DebugConfig=DebugConfig.level("debug"),
        exc_info=None,
        stack_info: bool=False,
        stacklevel: int=1,
        extra: Mapping[str, object] | None=None,
    ):
    """
    Print time and message according to its logging level.
    If debug_config is used and the logging level is not allowed to show, the message will not be output.
    
    Args:
        level (str): Level of messages.
            - Should be one of "debug", "info", "warning", "error", "critical".
            - Set it to other string or leave it blank will always output msg string without any prefix.
        msg (str): The message string to output.
        debug_config (image_crawler_utils.configs.DebugConfig): DebugConfig that controls output level. Default set to debug-level (output all).
        exc_info: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
        stack_info: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
        stacklevel: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
        extra: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
    """
    
    if level.lower() == 'debug':
        if debug_config.show_debug:
            __rich_logger.debug(msg, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra)
    elif level.lower() == 'info':
        if debug_config.show_info:
            __rich_logger.info(msg, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra)
    elif level.lower() == 'warning' or level.lower() == 'warn':
        if debug_config.show_warning:
            __rich_logger.warning(msg, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra)
    elif level.lower() == 'error':
        if debug_config.show_error:
            __rich_logger.error(msg, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra)
    elif level.lower() == 'critical':
        if debug_config.show_critical:
            __rich_logger.critical(msg, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra)
    else:
        rich.print(msg, stack_info=stack_info, stacklevel=stacklevel, extra=extra)


##### Class


class Log:
    """
    Class provided for logging messages onto the console and into the file.

    Args:
        log_file (str): Output name for the logging file. NO SUFFIX APPENDED. Set to None (Default) is not to output any file.
        debug_config (image_crawler_utils.configs.DebugConfig): Set the OUTPUT MESSAGE TO CONSOLE level. Default is not to output any message.
        logging_level (str, int): Set the logging level of the LOGGING FILE.
            - Select from: logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR and logging.CRITICAL
        detailed_console_log (bool): When logging info to the console, always log ``msg`` (the messages logged into files) even if ``output_msg`` exists.
    """

    def __init__(
            self, 
            log_file: Optional[str]=None,
            debug_config: DebugConfig=DebugConfig(),
            logging_level: Union[str, int]=logging.DEBUG,
            detailed_console_log: bool=False,
        ):

        self.debug_config = debug_config
        self.detailed_console_log = detailed_console_log

        self.logger = logging.getLogger(getpass.getuser())
        self.logger.setLevel(logging_level)

        self.formatter = logging.Formatter('%(asctime)-12s %(levelname)-8s %(message)-12s')

        # Don't write to console; We have better output method.
        self.empty_stream_handler = logging.StreamHandler(stream=sys.stdout)
        self.empty_stream_handler.setLevel(logging.CRITICAL + 1)
        self.logger.addHandler(self.empty_stream_handler)

        # Write to file
        self.file_handler = None

        if log_file is not None:
            path, filename = os.path.split(log_file)
            self.filename = f"{filename}.log".replace(".log.log", ".log")

            if len(path) > 0 and not os.path.exists(path):
                os.makedirs(path)
            self.log_file = os.path.join(path, self.filename)
            self.file_handler = logging.FileHandler(
                filename=self.log_file,
                encoding='UTF-8'
            )
            self.file_handler.setFormatter(self.formatter)
            self.file_handler.setLevel(logging_level)
            self.logger.addHandler(self.file_handler)


    # Escape styles before logging
    def __escape_style(self, msg: str) -> str:
        r"""
        If [inside] is not a style, then turn [ into escaped character \[
        """

        pos_list = [[0, 0]]
        possible_render_str_list = re.findall(r'\[[^\[\]]*?\]', msg)
        for possible_render_str in possible_render_str_list:
            if possible_render_str[1:-1] not in rich.default_styles.DEFAULT_STYLES.keys():
                pos = msg.find(possible_render_str)
                if pos >= 1 and msg[pos - 1] == '\\':
                    if pos >= 2 and msg[pos - 2] == '\\':
                        pos_list.append([pos, pos + len(possible_render_str)])
                else:
                    pos_list.append([pos, pos + len(possible_render_str)])
        pos_list.append([len(msg), len(msg)])

        new_msg = ''.join(msg[pos_list[i - 1][1]:pos_list[i][0]] + markup.escape(msg[pos_list[i][0]:pos_list[i][1]]) for i in range(1, len(pos_list)))
        return new_msg


    # Check whether logging to file
    def logging_file_handler(self):
        """
        Return the file handler if logging into file, or None if not.
        """

        return self.file_handler is not None
    

    # Output .log path
    def logging_file_path(self):
        """
        Output the absolute path of logging file if exists, or None if not.
        """

        if self.logging_file_handler():
            return os.path.abspath(self.log_file)
        else:
            return None


    # Five levels of logging
    # msg will be recorded in logging file
    # output_msg will be printed on console instead of msg if it isn't None.
    def debug(
            self,
            msg: str,
            output_msg: Optional[str]=None,
            exc_info=None,
            stack_info: bool=False,
            stacklevel: int=1,
            extra: Mapping[str, object] | None=None,
        ):
        """
        Output debug messages of many detailed information about running the crawler, especially connections with websites.

        Args:
            msg (str): Logging message.
            output_msg (str, None): Message to be output to console. Set to None will output the string in ``msg`` parameter.
            exc_info: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
            stack_info: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
            stacklevel: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
            extra: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
        """

        to_file_msg = markup.render(self.__escape_style(msg)) if extra is not None and "markup" in extra.keys() and extra["markup"] == True else msg
        self.logger.debug(to_file_msg)
        print_logging_msg(
            output_msg if (output_msg is not None and not self.detailed_console_log) else msg,
            "debug",
            self.debug_config,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
        )
        return msg


    def info(
            self,
            msg: str,
            output_msg: Optional[str]=None,
            exc_info=None,
            stack_info: bool=False,
            stacklevel: int=1,
            extra: Mapping[str, object] | None=None,
        ):
        """
        Output info messages of basic information indicating the progress of the crawler.

        Args:
            msg (str): Logging message.
            output_msg (str, None): Message to be output to console. Set to None will output the string in ``msg`` parameter.
            exc_info: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
            stack_info: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
            stacklevel: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
            extra: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
        """
        
        to_file_msg = markup.render(self.__escape_style(msg)) if extra is not None and "markup" in extra.keys() and extra["markup"] == True else msg
        self.logger.info(to_file_msg)
        print_logging_msg(
            output_msg if (output_msg is not None and not self.detailed_console_log) else msg,
            "info",
            self.debug_config,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
        )
        return msg


    def warning(
            self,
            msg: str,
            output_msg: Optional[str]=None,
            exc_info=None,
            stack_info: bool=False,
            stacklevel: int=1,
            extra: Mapping[str, object] | None=None,
        ):
        """
        Output warning messages of errors that basically do not affect the final results, mostly connection failures with the websites.

        Args:
            msg (str): Logging message.
            output_msg (str, None): Message to be output to console. Set to None will output the string in ``msg`` parameter.
            exc_info: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
            stack_info: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
            stacklevel: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
            extra: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
        """
        
        to_file_msg = markup.render(self.__escape_style(msg)) if extra is not None and "markup" in extra.keys() and extra["markup"] == True else msg
        self.logger.warning(to_file_msg)
        print_logging_msg(
            output_msg if (output_msg is not None and not self.detailed_console_log) else msg,
            "warning",
            self.debug_config,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
        )
        return msg


    def error(
            self,
            msg: str,
            output_msg: Optional[str]=None,
            exc_info=None,
            stack_info: bool=False,
            stacklevel: int=1,
            extra: Mapping[str, object] | None=None,
        ):
        """
        Output error messages of errors that may affect the final results but do not interrupt the crawler.

        Args:
            msg (str): Logging message.
            output_msg (str, None): Message to be output to console. Set to None will output the string in ``msg`` parameter.
            exc_info: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
            stack_info: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
            stacklevel: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
            extra: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
        """
        
        to_file_msg = markup.render(self.__escape_style(msg)) if extra is not None and "markup" in extra.keys() and extra["markup"] == True else msg
        self.logger.error(to_file_msg)
        print_logging_msg(
            output_msg if (output_msg is not None and not self.detailed_console_log) else msg,
            "error",
            self.debug_config,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
        )
        return msg


    def critical(
            self,
            msg: str,
            output_msg: Optional[str]=None,
            exc_info=None,
            stack_info: bool=False,
            stacklevel: int=1,
            extra: Mapping[str, object] | None=None,
        ):
        """
        Output critical messages of errors that interrupt the crawler. Usually a Python error will be raised when critical errors happen.

        Args:
            msg (str): Logging message.
            output_msg (str, None): Message to be output to console. Set to None will output the string in ``msg`` parameter.
            exc_info: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
            stack_info: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
            stacklevel: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
            extra: Please refer to the :py:mod:`logging` and :py:mod:`rich.logging` documentation.
        """
        
        to_file_msg = markup.render(self.__escape_style(msg)) if extra is not None and "markup" in extra.keys() and extra["markup"] == True else msg
        self.logger.critical(to_file_msg)
        print_logging_msg(
            output_msg if (output_msg is not None and not self.detailed_console_log) else msg,
            "critical",
            self.debug_config,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
        )
        return msg
    