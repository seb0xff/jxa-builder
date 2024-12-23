from os import getcwd
from jxa_builder.utils.click_importer import click
import jxa_builder.utils.logger as logger
from logging import DEBUG


def set_debug(_, __, value):
  if value:
    logger.shell_handler.setLevel(DEBUG)


debug_option = click.option(
    '--debug',
    is_flag=True,
    help='Whether to run in debug mode',
    callback=set_debug,
    expose_value=False,
)

project_dir_option = click.option(
    '--project-dir',
    default=getcwd(),
    show_default='current directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help=
    'Working directory. Place where the project is located. Defaults to the current directory'
)
