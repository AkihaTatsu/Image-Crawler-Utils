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
    Renders completed counts.
    """

    def render(self, task: "Task") -> Text:
        """
        Show count completed.
        """

        complete_count = task.completed
        unit, suffix = filesize.pick_unit_and_suffix(
            int(complete_count),
            ["", "×10³", "×10⁶", "×10⁹", "×10¹²"],
            1000,
        )
        count_str = f"{(complete_count / unit):.1f}{suffix}" if len(suffix) > 0 else int(complete_count)
        return Text(f"{count_str}", style="progress.filesize")



class TimeColumnLeft(ProgressColumn):

    def __init__(
        self,
        table_column=None,
        has_total: bool=True,
        time_format: str='%H:%M:%S',
        is_compact_time_format: bool=True,
    ):
        """
        Renders elapsed time and remaining time.

        Parameters:
            table_column: Table column of the ProgressColumn.
            has_total (bool): Has a total number in current progress.
            time_format (str): Format of time.
                - '%H' means hours.
                - '%M' means minutes.
                - '%S' means seconds.
                - '%L' means miliseconds.
            is_compact_time_format (bool): If set to True, the `time_format` will be truncated to start from '%M' when time is lower than 1 hour.
        """
        
        super().__init__(table_column)
        self.time_format = time_format
        self.has_total = has_total
        self.is_compact_time_format = is_compact_time_format


    def seconds_to_format(self, seconds: Optional[Union[int, float]]) -> str:
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
            elapsed_text = Text(self.seconds_to_format(elapsed), style="progress.elapsed")

            remaining = task.time_remaining
            remaining_text = Text(self.seconds_to_format(remaining), style="progress.remaining")

            time_text = elapsed_text + Text('<', style="default") + remaining_text
        else:  # Cannot calc remaining time
            elapsed = task.stop_time if task.stop_time is not None else task.get_time() - task.start_time
            elapsed_text = Text(self.seconds_to_format(elapsed), style="progress.elapsed")
            time_text = elapsed_text

        final_text = (Text(' [', style='default')
                      + time_text 
                      + Text(',', style='default'))
        return final_text
    


class SpeedColumnRight(ProgressColumn):

    def __init__(
        self,
        table_column=None,
        is_file: bool=False,
    ):
        """
        Renders speed.
        
        Parameters:
            table_column: Table column of the ProgressColumn.
            is_file (bool): The progress is for a file.
        """
        
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
        refresh_per_second=10,
        speed_estimate_period=30,
        transient=False,
        redirect_stdout=True,
        redirect_stderr=True,
        get_time=None,
        disable=False,
        expand=False,
    ):
        """
        A wrapped Progress class with specific format-controlling parameters.

        Parameters:
            text_only (bool): Set Progress to a text-only format.
            has_spinner (bool): Has a spinner at the beginning.
            spinner_name (str): Name of the spinner.
            has_total (bool): Its tasks have total numbers.
            is_file (bool): Its tasks are dealing with files.
            time_format (str): Format of time.
                - '%H' means hours.
                - '%M' means minutes.
                - '%S' means seconds.
                - '%L' means miliseconds.
            is_compact_time_format (bool): If set to True, the format will be truncated to start from '%M' when time is lower than 1 hour.
            is_sub_process (bool): Current progress is a subprocess of a certain ProgressGroup.

            console (Console, optional): Optional Console instance. Defaults to an internal Console instance writing to stdout.
            auto_refresh (bool, optional): Enable auto refresh. If disabled, you will need to call `refresh()`.
            refresh_per_second (Optional[float], optional): Number of times per second to refresh the progress information or None to use default (10). Defaults to None.
            speed_estimate_period: (float, optional): Period (in seconds) used to calculate the speed estimate. Defaults to 30.
            transient: (bool, optional): Clear the progress on exit. Defaults to False.
            redirect_stdout: (bool, optional): Enable redirection of stdout, so ``print`` may be used. Defaults to True.
            redirect_stderr: (bool, optional): Enable redirection of stderr. Defaults to True.
            get_time: (Callable, optional): A callable that gets the current time, or None to use Console.get_time. Defaults to None.
            disable (bool, optional): Disable progress display. Defaults to False
            expand (bool, optional): Expand tasks table to fit width. Defaults to False.
        """

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
        if self.is_sub_process:
            self.update(task, visible=not hide)
        else:
            self.live.transient = hide
            self.stop()



class ProgressGroup:

    def __init__(
        self,
        progress_list: Iterable[Progress]=[],
        has_panel: bool=True,
        panel_title: Optional[str]=None,
        panel_subtitle: Optional[str]=None,
        refresh_per_second: int=10,
    ):
        """
        A Group of Progress, which can simplify building multiple Progress bars.

        Parameters:
            has_panel (bool): Has a Panel over its Progress bars.
            panel_title (str): Title of the Panel.
            panel_subtitle (str): Title of the Panel.
            refresh_per_second (int): Refresh times per second.
        """

        self.main_file_bar = CustomProgress(is_file=True, refresh_per_second=refresh_per_second, is_sub_process=True)
        self.main_count_bar = CustomProgress(refresh_per_second=refresh_per_second, is_sub_process=True)
        self.main_no_total_file_bar = CustomProgress(has_total=False, is_file=True, refresh_per_second=refresh_per_second, is_sub_process=True)
        self.main_no_total_count_bar = CustomProgress(has_total=False, is_file=False, refresh_per_second=refresh_per_second, is_sub_process=True)

        self.sub_file_bar = CustomProgress(is_file=True, transient=True, refresh_per_second=refresh_per_second, is_sub_process=True)
        self.sub_count_bar = CustomProgress(is_file=False, transient=True, refresh_per_second=refresh_per_second, is_sub_process=True)
        self.sub_no_total_file_bar = CustomProgress(has_total=False, is_file=True, transient=True, refresh_per_second=refresh_per_second, is_sub_process=True)
        self.sub_no_total_count_bar = CustomProgress(has_total=False, is_file=False, transient=True, refresh_per_second=refresh_per_second, is_sub_process=True)

        self.main_text_only_bar = CustomProgress(text_only=True)
        self.sub_text_only_bar = CustomProgress(text_only=True, transient=True)

        self.progress_list = progress_list

        self.group = Group(
            self.main_count_bar,
            self.main_file_bar,
            self.main_no_total_file_bar,
            self.main_no_total_count_bar,
            self.sub_file_bar,
            self.sub_count_bar,
            self.sub_no_total_file_bar,
            self.sub_no_total_count_bar,
            self.main_text_only_bar,
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
        Start the ProgressGroup.
        """

        self.live.start(refresh=self.live._renderable is not None)


    def stop(self) -> None:
        """
        Stop the ProgressGroup.
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
