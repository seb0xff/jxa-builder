from typing import Optional
from jxa_builder.utils.click_importer import click
from jxa_builder.core.manage_outputs import manage_outputs


@click.command()
@click.option('--locations-file',
              default='./build/locations.json',
              help='Locations file')
def uninstall(locations_file: Optional[str]):
  click.echo(f"{locations_file}")
