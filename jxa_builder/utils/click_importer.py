import os
from ..core.constants import IS_RICH

if IS_RICH:
  import rich_click as click
else:
  import click

# def is_rich():
#   return os.environ.get('JXA_BUILDER_CLASSIC_DISPLAY_MODE',
#                         'false').lower() not in ('true', '1', 'yes')

# def get_click():
#   if is_rich():
#     import rich_click as click
#   else:
#     import click
#   return click
