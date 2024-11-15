import datetime
import os, sys
import tqdm
from tqdm import notebook
from typing import Optional
from colorama import Fore, Back, Style

import logging, getpass

from image_crawler_utils.configs import DebugConfig



##### Log utils


def print_logging_msg(
        level: str, 
        msg: str,
        debug_config: DebugConfig=DebugConfig(
            show_debug=True,
            show_info=True,
            show_warning=True,
            show_error=True,
            show_critical=True,
        ), 
    ):
    """
    Print time and message according to its logging level.
    If debug_config is used and the logging level is not allowed to show, the message will not be output.
    """
    
    def _is_ipython_kernel():
        if 'IPython' not in sys.modules:
            return False
        from IPython import get_ipython
        return getattr(get_ipython(), 'kernel', None) is not None

    custom_tqdm = notebook if _is_ipython_kernel() else tqdm
    time_str = f'{Fore.CYAN}[{datetime.datetime.now().strftime("%H:%M:%S")}]{Style.RESET_ALL}'
    
    if level.lower() == 'debug' and debug_config.show_debug:
        custom_tqdm.tqdm.write(f"{time_str} {Fore.BLUE}[DEBUG]{Style.RESET_ALL}: {msg}")
    elif level.lower() == 'info' and debug_config.show_info:
        custom_tqdm.tqdm.write(f"{time_str} {Fore.GREEN}[INFO]{Style.RESET_ALL}: {msg}")
    elif (level.lower() == 'warning' or level.lower() == 'warn') and debug_config.show_warning:
        custom_tqdm.tqdm.write(f"{time_str} {Fore.YELLOW}[WARNING]{Style.RESET_ALL}: {msg}")
    elif level.lower() == 'error' and debug_config.show_error:
        custom_tqdm.tqdm.write(f"{time_str} {Fore.RED}[ERROR]{Style.RESET_ALL}: {msg}")
    elif level.lower() == 'critical' and debug_config.show_critical:
        custom_tqdm.tqdm.write(f"{time_str} {Back.RED}{Fore.WHITE}[CRITICAL]{Style.RESET_ALL}: {msg}")


class Log:
    def __init__(
            self, 
            log_file: Optional[str]=None,
            debug_config: DebugConfig=DebugConfig(),
            logging_level=logging.DEBUG,
        ):
        """
        Logging messages.

        Parameters:
            log_file (str): Output name for the logging file. NO SUFFIX APPENDED. Set to None (Default) is not to output any file.
            debug_config (image_crawler_utils.config.DebugConfig): Set the OUTPUT MESSAGE TO CONSOLE level. Default is not to output any message.
            logging_level: Set the logging level of the LOGGING FILE. Select from: logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR and logging.CRITICAL .
        """

        self.debug_config = debug_config
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

    # Check whether logging to file
    def is_logging_to_file(self):
        return self.file_handler is not None
    
    # Output .log path
    def logging_file_info(self):
        if self.is_logging_to_file():
            return self.filename
        else:
            return None

    # Five levels of logging
    # msg will be recorded in logging file
    # output_msg will be printed on console instead of msg if it isn't None.
    def debug(self, msg, output_msg=None):
        self.logger.debug(msg)
        print_logging_msg("debug", output_msg if output_msg is not None else msg, debug_config=self.debug_config)
        return msg

    def info(self, msg, output_msg=None):
        self.logger.info(msg)
        print_logging_msg("info", output_msg if output_msg is not None else msg, debug_config=self.debug_config)
        return msg

    def warning(self, msg, output_msg=None):
        self.logger.warning(msg)
        print_logging_msg("warning", output_msg if output_msg is not None else msg, debug_config=self.debug_config)
        return msg

    def error(self, msg, output_msg=None):
        self.logger.error(msg)
        print_logging_msg("error", output_msg if output_msg is not None else msg, debug_config=self.debug_config)
        return msg

    def critical(self, msg, output_msg=None):
        self.logger.critical(msg)
        print_logging_msg("critical", output_msg if output_msg is not None else msg, debug_config=self.debug_config)
        return msg
    