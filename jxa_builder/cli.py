#!/usr/bin/env python3
import os
import shutil
from typing import Literal, TypeVar, Generic, Iterable, Optional, Union, cast, get_type_hints, Protocol, runtime_checkable, List, Dict, Sequence, Tuple
from types import SimpleNamespace
from pprint import pprint
from os import path as p
from jxa_builder.utils.click_importer import click

from jxa_builder.commands.build import build
from jxa_builder.commands.install import install
from jxa_builder.commands.uninstall import uninstall


@click.group(
    # invoke_without_command=True,
    help=
    'Javascript for Automation build system.\n\nTo turn on classic display mode set JXA_BUILDER_CLASSIC_DISPLAY_MODE env variable to true.'
)
def cli():
  pass


cli.add_command(build)
cli.add_command(install)
cli.add_command(uninstall)

if __name__ == "__main__":
  cli()
