from rich.panel import Panel
from rich.text import Text
from rich import print as rich_print
from jxa_builder.core.constants import IS_RICH
from jxa_builder.utils.logger import logger


def print_error(error_msg: str, title: str = 'Error'):
  if IS_RICH:
    rich_print(
        Panel(Text(error_msg),
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


def terminate_with_error(error_msg: str,
                         *,
                         title: str = 'Error',
                         incl_traceback: bool = True,
                         exit_code: int = 1):
  """Prints a given error message, log it and exit with specified error code"""
  print_error(error_msg, title)
  logger.fatal(error_msg, exc_info=incl_traceback)
  exit(exit_code)