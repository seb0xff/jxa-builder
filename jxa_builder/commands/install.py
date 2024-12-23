from os import getcwd, path as p
from jxa_builder.utils.click_importer import click
from jxa_builder.core.manage_outputs import manage_outputs
from ._shared_options import debug_option
from jxa_builder.core.constants import LOCATIONS_FILE


@click.command(help='Copy compiled files to appropriate locations.')
@click.option('--path',
              type=click.Path(exists=True),
              default=getcwd(),
              help='Path to the project directory or the locations.json file')
@click.option('--deps-only',
              is_flag=True,
              default=False,
              help='Whether to install only the dependencies')
@debug_option
def install(path: str, deps_only: bool):
  """path: Path to the project directory or locations file"""
  print(f"{path}")
  if p.isfile(path):
    manage_outputs('install', path, deps_only=deps_only)
  elif p.isdir(path):
    manage_outputs('install',
                   p.join(path, LOCATIONS_FILE),
                   deps_only=deps_only)
