from __future__ import annotations
from typing import Optional, Union, Type
from collections.abc import Iterable
from types import TracebackType

from rich.progress import (
    Progress, 
    ProgressColumn, 
    Task, 
    filesize,
    SpinnerColumn,
    MofNCompleteColumn,
    DownloadColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    FileSizeColumn,
)
from rich.text import Text
from rich.console import Group
from rich.live import Live
from rich.panel import Panel



class CountColumn(ProgressColumn):
    """
    A :py:class:`rich.progress.ProgressColumn` class, which displays current progress number in integer.

    Args:
        table_column: Table column of the ProgressColumn.
        has_unit (bool): Set to :py:data:`True` will shorten the number with a unit. Default is :py:data:`False`, meaning the number will be displayed directly.

            + For example, "10" will be displayed as "10" will "12120" be displayed as "12.1×10³".
    """

    def __init__(
        self, 
        table_column = None,
        has_unit: bool=False,
    ):
        super().__init__(table_column)
        self.has_unit = has_unit


    def render(self, task: "Task") -> Text:
        """
        Show count completed.
        """

        complete_count = task.completed
        if self.has_unit:
            unit, suffix = filesize.pick_unit_and_suffix(
                int(complete_count),
                ["", "×10³", "×10⁶", "×10⁹", "×10¹²"],
                1000,
            )
            count_str = f"{(complete_count / unit):.1f}{suffix}" if len(suffix) > 0 else int(complete_count)
        else:
            count_str = int(complete_count)
        return Text(f"{count_str}", style="progress.filesize")



class TimeColumnLeft(ProgressColumn):
    """
    A :py:class:`rich.progress.ProgressColumn` class, which displays elapsed time and remaining time in "[00:08<00:03," format. It is suggested to put it to the left of :py:class:`SpeedColumnRight`.

    Args:
        table_column: Table column of the ProgressColumn.
        has_total (bool): Set to :py:data:`True` if involved tasks has a total number. When set to :py:data:`False`, remaining time will not be displayed. Default is :py:data:`False`.
        time_format (str): A string that controls the time format. Default is "%H:%M:%S".

            + '%H' will be replaced with hours.
            + '%M' will be replaced minutes.
            + '%S' will be replaced seconds.
            + '%L' will be replaced miliseconds.

        is_compact_time_format (bool): When set to :py:data:`True` (default), the ``time_format`` will be truncated to start from '%M' when time is lower than 1 hour.

            + For example, "%H:%M:%S.%L" will be truncated to "%M:%S.%L" when time is lower than 1 hour.
    """

    def __init__(
        self,
        table_column=None,
        has_total: bool=True,
        time_format: str='%H:%M:%S',
        is_compact_time_format: bool=True,
    ):
        
        super().__init__(table_column)
        self.time_format = time_format
        self.has_total = has_total
        self.is_compact_time_format = is_compact_time_format


    def __seconds_to_format(self, seconds: Optional[Union[int, float]]) -> str:
        if seconds is None:
            hours, mins, secs, miliseconds = 0, 0, 0, 0
            hour_str, min_str, sec_str, milisec_str = '-', '--', '--', '---'
        else:
            miliseconds = int((seconds - int(seconds)) * 1000)
            use_seconds = int(seconds)  # Omit miliseconds!
            hours = use_seconds // 3600
            mins = use_seconds // 60 - hours * 60
            secs = use_seconds - hours * 3600 - mins * 60
            hour_str, min_str, sec_str, milisec_str = str(hours), str(mins), str(secs), str(miliseconds)
            min_str = '0' * (1 - mins // 10) + min_str
            sec_str = '0' * (1 - secs // 10) + sec_str
            milisec_str = '0' * (2 - miliseconds // 10) + milisec_str
        if self.is_compact_time_format:
            compact_time_format = self.time_format[(self.time_format.find("%M") if hours == 0 else 0):]
            return compact_time_format.replace("%H", hour_str).replace("%M", min_str).replace("%S", sec_str).replace("%L", milisec_str)
        else:
            return self.time_format.replace("%H", hour_str).replace("%M", min_str).replace("%S", sec_str).replace("%L", milisec_str)


    def render(self, task: "Task") -> Text:
        """
        Renders elapsed time and remaining time.
        """
        
        # Elapsed time and remaining time
        
        if self.has_total:  # Has total, can calc remaining time
            elapsed = task.finished_time if task.finished else task.elapsed
            elapsed_text = Text(self.__seconds_to_format(elapsed), style="progress.elapsed")

            remaining = task.time_remaining
            remaining_text = Text(self.__seconds_to_format(remaining), style="progress.remaining")

            time_text = elapsed_text + Text('<', style="default") + remaining_text
        else:  # Cannot calc remaining time
            elapsed = task.stop_time if task.stop_time is not None else task.get_time() - task.start_time
            elapsed_text = Text(self.__seconds_to_format(elapsed), style="progress.elapsed")
            time_text = elapsed_text

        final_text = (Text(' [', style='default')
                      + time_text 
                      + Text(',', style='default'))
        return final_text
    


class SpeedColumnRight(ProgressColumn):
    """
    A :py:class:`rich.progress.ProgressColumn` class, which displays speed in "1.23 MB/s]" format. It is suggested to put it to the right of :py:class:`TimeColumnLeft`.
    
    Args:
        table_column: Table column of the ProgressColumn.
        is_file (bool): Set to :py:data:`True` if involved tasks deal with files. When set to :py:data:`True`, the units will use 'KB', 'MB', etc. Default is :py:data:`False`.
    """

    def __init__(
        self,
        table_column=None,
        is_file: bool=False,
    ):
        
        super().__init__(table_column)
        self.is_file = is_file


    def render(self, task: "Task") -> Text:
        """
        Renders speed.
        """

        # Speed
        speed = task.finished_speed or task.speed
        if speed is None:
            data_speed = "?"
        else:
            if self.is_file:
                # A file, using ?MB/s format
                data_speed = f"{filesize.decimal(int(speed))}/s"
            else:
                # Not a file, using ?it/s format
                unit, suffix = filesize.pick_unit_and_suffix(
                    int(speed),
                    ["", "×10³", "×10⁶", "×10⁹", "×10¹²"],
                    1000,
                )
                data_speed = f"{(speed / unit):.1f}{suffix} it/s"
        data_speed_text = Text(data_speed, style="progress.data.speed")
        final_text = (data_speed_text
                      + Text(']', style='default'))
        return final_text
    


class CustomProgress(Progress):
    """
    A wrapped Progress class with specific format-controlling parameters.

    If you add ProgressColumns to CustomProgress like normal :class:`rich.progress.Progress` class, it will be placed between ``BarColumn`` & ``TaskProgressColumn`` (i.e. the progress bar and percentage) and ``TimeColumnLeft``.
        + These ProgressColumns classes will be omitted if ``text_only`` is set to :py:data:`True`.

    Args:
        text_only (bool): If set to :py:data:`True`, Progress bars will only display descriptions. Default is :py:data:`False`.

            + When set to :py:data:`True`, all other columns except ``rich.progress.TextColumn("[progress.description]{task.description}[reset]")`` will be omitted!

        has_spinner (bool): If set to :py:data:`True`, a spinner will be added to the left. Default is :py:data:`False`.
        spinner_name (str): The type of the spinner, which can be referred from https://jsfiddle.net/sindresorhus/2eLtsbey/embedded/result/. Default is :py:data:"dots".
        has_total (bool): Set to :py:data:`True` if involved tasks have total numbers. Default is :py:data:`False`.
        is_file (bool): Set to :py:data:`True` if involved tasks deal with files. Default is :py:data:`False`.
        time_format (str): A string that controls the time format. Default is "%H:%M:%S".

            + '%H' will be replaced with hours.
            + '%M' will be replaced minutes.
            + '%S' will be replaced seconds.
            + '%L' will be replaced miliseconds.

        is_compact_time_format (bool): When set to :py:data:`True` (default), the ``time_format`` will be truncated to start from '%M' when time is lower than 1 hour.

            + For example, "%H:%M:%S.%L" will be truncated to "%M:%S.%L" when time is lower than 1 hour.

        is_sub_process (bool): Set to :py:data:`True` if it is a subprocess of a certain :class:`ProgressGroup`. Default is :py:data:`False`.

        console (Console, None): Optional Console instance. Defaults to an internal Console instance writing to stdout.
        auto_refresh (bool, None): Enable auto refresh. If disabled, you will need to call ``refresh()``.
        refresh_per_second (Optional[float], None): Number of times per second to refresh the progress information or None to use default (10). Defaults to None.
        speed_estimate_period: (float, None): Period (in seconds) used to calculate the speed estimate. Defaults to 30.
        transient: (bool, None): Clear the progress on exit. Defaults to False.
        redirect_stdout: (bool, None): Enable redirection of stdout, so ``print`` may be used. Defaults to True.
        redirect_stderr: (bool, None): Enable redirection of stderr. Defaults to True.
        get_time: (Callable, None): A callable that gets the current time, or None to use Console.get_time. Defaults to None.
        disable (bool, None): Disable progress display. Defaults to False
        expand (bool, None): Expand tasks table to fit width. Defaults to False.
    """

    def __init__(
        self,
        *columns,

        text_only: bool=False,
        has_spinner: bool=False,
        spinner_name: str="dots",
        has_total: bool=True,
        is_file: bool=False,
        time_format: str='%H:%M:%S',
        is_compact_time_format: bool=True,
        is_sub_process: bool=False,

        console=None,
        auto_refresh=True,
        refresh_per_second=20,
        speed_estimate_period=30,
        transient=False,
        redirect_stdout=True,
        redirect_stderr=True,
        get_time=None,
        disable=False,
        expand=False,
    ):

        if text_only:
            column_list = [TextColumn("[progress.description]{task.description}[reset]")]
        else:
            column_list = ([SpinnerColumn(spinner_name=spinner_name)] if has_spinner else []) + [
                TextColumn("[progress.description]{task.description}[reset]"),
            ] + ([BarColumn(bar_width=None), TaskProgressColumn(),] if has_total else []) + [
                *columns,
            ] + ([DownloadColumn() if is_file else MofNCompleteColumn()] if has_total
                 else [FileSizeColumn() if is_file else CountColumn()]) + [
                TimeColumnLeft(
                    has_total=has_total,
                    time_format=time_format,
                    is_compact_time_format=is_compact_time_format,
                ),
                SpeedColumnRight(
                    is_file=is_file,
                ),
            ]
        super().__init__(
            *column_list,
            console=console,
            auto_refresh=auto_refresh,
            refresh_per_second=refresh_per_second,
            speed_estimate_period=speed_estimate_period,
            transient=transient,
            redirect_stdout=redirect_stdout,
            redirect_stderr=redirect_stderr,
            get_time=get_time,
            disable=disable,
            expand=expand,
        )
        self.is_sub_process = is_sub_process


    def finish_task(self, task: Task, hide=True):
        """
        Finish a task within the CustomProgress. Unless this CustomProgress is a preset attribute of :class`ProgressGroup` or its ``is_sub_process`` is set to :py:data:`True`, running this function will stop the whole Progress; otherwise it will just stop the task.

        Args:
            task (rich.progress.Task): The Task class that is created under this CustomProgress.
            hide (bool): Set to :py:data:`True` (default) to hide the progress bar of this task.
        """

        if self.is_sub_process:
            self.update(task, visible=not hide)
        else:
            self.live.transient = hide
            self.stop()



class ProgressGroup:
    """
    A Group of Progress, which can simplify building multiple Progress bars.

    Args:
        progress_list (list[rich.progress.Progress]): An iterable list of :class:`rich.progress.Progress` classes which will be added to the ProgressGroup when created. Default is ``[]`` (an empty :py:class:`list`).
        has_panel (bool): When set to :py:data:`True` (default), a :py:class:`rich.panel.Panel` will be wrapped around all of the progress bars.
        panel_title (str): When set to a :py:class:`str`, the title will be displayed at the top middle of the panel.

            + Works only if ``has_panel`` is set to :py:data:`True`.

        panel_subtitle (str): When set to a :py:class:`str`, the title will be displayed at the bottom middle of the panel.

            + Works only if ``has_panel`` is set to :py:data:`True`.

        refresh_per_second (int): Refreshing the progress bars for ``refresh_per_second`` times in a second. Default is 10.
    """

    def __init__(
        self,
        progress_list: Iterable[Progress]=[],
        has_panel: bool=True,
        panel_title: Optional[str]=None,
        panel_subtitle: Optional[str]=None,
        refresh_per_second: int=10,
    ):

        self.main_file_bar = CustomProgress(is_file=True, refresh_per_second=refresh_per_second, is_sub_process=True)
        self.main_count_bar = CustomProgress(refresh_per_second=refresh_per_second, is_sub_process=True)
        self.main_no_total_file_bar = CustomProgress(has_total=False, is_file=True, refresh_per_second=refresh_per_second, is_sub_process=True)
        self.main_no_total_count_bar = CustomProgress(has_total=False, is_file=False, refresh_per_second=refresh_per_second, is_sub_process=True)

        self.main_text_only_bar = CustomProgress(text_only=True)
        
        self.sub_file_bar = CustomProgress(is_file=True, transient=True, refresh_per_second=refresh_per_second, is_sub_process=True)
        self.sub_count_bar = CustomProgress(is_file=False, transient=True, refresh_per_second=refresh_per_second, is_sub_process=True)
        self.sub_no_total_file_bar = CustomProgress(has_total=False, is_file=True, transient=True, refresh_per_second=refresh_per_second, is_sub_process=True)
        self.sub_no_total_count_bar = CustomProgress(has_total=False, is_file=False, transient=True, refresh_per_second=refresh_per_second, is_sub_process=True)

        self.sub_text_only_bar = CustomProgress(text_only=True, transient=True)

        self.progress_list = progress_list

        self.group = Group(
            self.main_count_bar,
            self.main_file_bar,
            self.main_no_total_file_bar,
            self.main_no_total_count_bar,
            self.main_text_only_bar,
            self.sub_file_bar,
            self.sub_count_bar,
            self.sub_no_total_file_bar,
            self.sub_no_total_count_bar,
            self.sub_text_only_bar,
            *self.progress_list,
        )
        if has_panel:
            self.live = Live(Panel(self.group, 
                                   title=panel_title,
                                   subtitle=panel_subtitle),
                             refresh_per_second=refresh_per_second)
        else:
            self.live = Live(self.group, refresh_per_second=refresh_per_second)


    def start(self) -> None:
        """
        Start the ProgressGroup. That is, start the ``ProgressGroup().live`` attribute.
        """

        self.live.start(refresh=self.live._renderable is not None)


    def stop(self) -> None:
        """
        Stop the ProgressGroup. That is, stop the ``ProgressGroup().live`` attribute.
        """

        self.live.stop()


    def __enter__(self) -> ProgressGroup:
        self.start()
        return self
    

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.stop()
