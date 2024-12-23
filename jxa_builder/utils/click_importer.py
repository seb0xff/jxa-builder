from ..core.constants import IS_RICH

if IS_RICH:
  import rich_click as click
else:
  import click
