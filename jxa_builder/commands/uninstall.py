from os import getcwd, path as p
from jxa_builder.utils.click_importer import click
from jxa_builder.core.manage_outputs import manage_outputs
from ._shared_options import debug_option
from jxa_builder.core.constants import LOCATIONS_FILE


@click.command()
@click.option('--path',
              type=click.Path(exists=True),
              default=getcwd(),
              help='Path to the project directory or the locations.json file')
@debug_option
def uninstall(path: str):
  """path: Path to the project directory or locations file"""
  print(f"{path}")
  if p.isfile(path):
    manage_outputs('uninstall', path, False)
  elif p.isdir(path):
    manage_outputs('uninstall', p.join(path, LOCATIONS_FILE), False)
