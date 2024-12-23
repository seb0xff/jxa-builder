from typing import Optional
from os import getcwd, path as p
from jxa_builder.utils.click_importer import click
from jxa_builder.core.manage_outputs import manage_outputs
from ._shared_options import debug_option, project_dir_option
from jxa_builder.core.constants import LOCATIONS_FILE


@click.command()
@click.argument('src-path', type=click.Path(exists=True), default=getcwd())
# @project_dir_option
# @click.option('--locations-file',
#               default='./build/locations.json',
#               help='Locations file')
@click.option('--deps-only',
              is_flag=True,
              help='Whether to install only the dependencies')
@debug_option
def install(src_path: str, deps_only: bool):
  """SRC_PATH: Path to the project directory or locations file"""
  print(f"{src_path}")
  if p.isfile(src_path):
    manage_outputs('install', src_path)
  elif p.isdir(src_path):
    manage_outputs('install', p.join(src_path, LOCATIONS_FILE))
