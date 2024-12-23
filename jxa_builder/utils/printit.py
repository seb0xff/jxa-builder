from jxa_builder.core.constants import IS_RICH
from jxa_builder.utils.logger import logger
if IS_RICH:
  from rich.panel import Panel
  from rich.text import Text
  from rich import print as rich_print


def print_error(error_msg: str, title: str = 'Error'):
  if IS_RICH:
    rich_print(
        Panel(Text.from_markup(error_msg),
              title=title,
              title_align='left',
              border_style="red"))
  else:
    print(error_msg)


def print_warning(warning_msg: str, title: str = 'Warning'):
  if IS_RICH:
    rich_print(
        Panel(Text(warning_msg),
              title=title,
              title_align='left',
              border_style="yellow"))
  else:
    print(warning_msg)


def log_print_error(
    error_msg: str,
    title: str = 'Error',
    incl_traceback: bool = True,
):
  print_error(error_msg, title)
  if IS_RICH:
    error_msg = Text.from_markup(error_msg).plain
  logger.fatal(error_msg, exc_info=incl_traceback, stacklevel=2)


def log_print_warning(warning_msg: str, title: str = 'Warning'):
  print_warning(warning_msg, title)
  if IS_RICH:
    warning_msg = Text(warning_msg).plain
  logger.warning(warning_msg, stacklevel=2)
