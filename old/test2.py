#!/usr/bin/env python3
import os
import shutil
from typing import Literal, TypeVar, Generic, Iterable, Optional, Union, cast, Annotated, get_type_hints, Protocol, runtime_checkable, List, Dict, Sequence, Tuple
from types import SimpleNamespace
from dataclasses import dataclass
import argparse
from pprint import pprint
from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic.alias_generators import to_camel, to_snake
from pydantic_settings import PydanticBaseSettingsSource, BaseSettings
from os import path as p
import json

RICH = os.environ.get('JXA_BUILDER_CLASSIC_DISPLAY_MODE',
                      'false').lower() not in ('true', '1', 'yes')
if RICH:
  import rich_click as click
else:
  import click


class JxaConfig(BaseModel):
  model_config: ConfigDict = ConfigDict(
      alias_generator=to_camel,
      populate_by_name=True,
      str_strip_whitespace=True,
      extra='forbid',
  )
  comp_mode: Literal['app', 'script'] = 'app'
  deps_comp_mode: Literal['script', 'bundle'] = 'script'
  deps_install_mode: Literal['app', 'user', 'system'] = 'app'
  version: str = '1.0.0'
  main: str = 'index.js'
  app_name: str = 'out'
  app_icon: Optional[str] = None
  install_after: bool = False
  deps_only: bool = False
  package_name: Optional[str] = None


class Paths:

  def __init__(self, project_dir: str):
    self.project_dir = project_dir
    self.build_dir = p.join(self.project_dir, 'build')
    self.output_dir = p.join(self.build_dir, 'output')
    self.preprocessed_dir = p.join(self.build_dir, 'preprocessed')
    self.system_root_dir = p.abspath(p.sep)
    self.system_tmp_dir = p.join(self.system_root_dir, 'private', 'tmp',
                                 'jxa-builder')
    self.system_lib_dir = p.join(self.system_root_dir, 'Library',
                                 'Script Libraries')
    self.user_lib_dir = p.join(p.expanduser('~'), 'Library',
                               'Script Libraries')
    self.locations_file = p.join(self.build_dir, 'locations.json')
    self.jxa_file = p.join(self.project_dir, 'jxa.json')
    self.package_json_file = p.join(self.project_dir, 'package.json')

  def __repr__(self):
    return f"Paths(project_dir={self.project_dir!r}, build_dir={self.build_dir!r}, output_dir={self.output_dir!r}, preprocessed_dir={self.preprocessed_dir!r}, system_root_dir={self.system_root_dir!r}, system_lib_dir={self.system_lib_dir!r}, user_lib_dir={self.user_lib_dir!r}, locations_file={self.locations_file!r}, jxa_file={self.jxa_file!r}, package_json_file={self.package_json_file})"


CmdArgs = Dict[str, any]


def get_jxa_config(paths_or_args: Union[Paths, CmdArgs]) -> JxaConfig:

  if isinstance(paths_or_args, Paths):
    paths = paths_or_args
    cmd_args = {}
  else:
    paths = Paths(paths_or_args['project_dir'])
    cmd_args = paths_or_args

  jxa_dict = {}

  if p.exists(paths.package_json_file):
    try:
      with open(paths.package_json_file) as f:
        jxa_json = json.load(f).get('jxa', {})
        if jxa_json:
          jxa_dict.update({to_snake(k): v for k, v in jxa_json.items()})
    except json.JSONDecodeError:
      print(
          f'Error, the file "{paths.package_json_file}" is not a valid JSON document.'
      )
      exit(1)
    except Exception as e:
      print(f'Error, while reading "{paths.package_json_file}": {e}')
      exit(1)

  if p.exists(paths.jxa_file):
    try:
      with open(paths.jxa_file) as f:
        jxa_json = json.load(f)
        if jxa_json:
          jxa_dict.update({to_snake(k): v for k, v in jxa_json.items()})
    except json.JSONDecodeError:
      print(
          f'Error, the file "{paths.jxa_file}" is not a valid JSON document.')
      exit(1)
    except Exception as e:
      print(f'Error, while reading "{paths.jxa_file}": {e}')
      exit(1)

  if cmd_args:
    cmd_ignore = ('project_dir', 'debug', 'verbose')
    jxa_dict.update({
        k: v
        for k, v in cmd_args.items() if v is not None and k not in cmd_ignore
    })

  return JxaConfig(**jxa_dict)


@click.group(
    help=
    'Javascript for Automation build system.\n\nTo turn on classic display mode set JXA_BUILDER_CLASSIC_DISPLAY_MODE env variable to true.'
)
def cli():
  pass


@click.command()
@click.option(
    '--project-dir',
    default=os.getcwd(),
    show_default='current directory',
    help=
    'Working directory. Place where the project is located. Defaults to the current directory'
)
@click.option(
    '--comp-mode',
    type=click.Choice(['app', 'script']),
    # default='app',
    show_default='app',
    help=
    'Whether to compile the main source to a standalone app (e.g. applet/droplet) or a script'
)
@click.option(
    '--deps-comp-mode',
    type=click.Choice(['script', 'bundle']),
    # default='script',
    show_default='script',
    help=
    'Dependencies compilation mode. Whether dependencies should be compiled as scripts or bundles'
)
@click.option(
    '--deps-install-mode',
    type=click.Choice(['app', 'user', 'system']),
    # default='app',
    show_default='app',
    help=
    'Where to install dependencies. If the main file is compiled to a standalone app one can embed them inside. Otherwise they can be installed for a current user, or system wide'
)
@click.option(
    '--version',
    # default='1.0.0',
    show_default='1.0.0',
    help='Version of the project')
@click.option(
    '--main',
    # default='index.js',
    show_default='index.js',
    help='Main source file')
@click.option(
    '--app-name',
    # default='out',
    show_default='out',
    help='App name, (has effect only when compiling to a standalone app)')
@click.option(
    '--app-icon',
    help=
    'By default the builder searches for "icon.icns" or "<app-name>.icns" in the working directory. If both icons are not found and this option is left empty, the default icon is used (has effect only when compiling to a standalone app)'
)
@click.option(
    '--debug',
    is_flag=True,
    help=
    'Whether to add some useful information. (mainly used for testing purposes)'
)
@click.option('--install-after',
              is_flag=True,
              help='Whether to run "install" command after building')
@click.option(
    '--deps-only',
    is_flag=True,
    help=
    'Whether to install the app and its dependencies or only the dependencies')
@click.option('--package-name', help='Package name')
def compile(**kwargs):
  try:
    b = get_jxa_config(kwargs)
  except ValidationError as e:
    print(e)
    exit(1)
  print(b)


@click.command()
@click.option('--locations-file',
              default='./build/locations.json',
              help='Locations file')
@click.option('--deps-only',
              is_flag=True,
              help='Whether to install only the dependencies')
def install(locations_file: str, dependencies_only: bool):
  click.echo(f"{locations_file}, {dependencies_only}")


@click.command()
@click.option('--locations-file',
              default='./build/locations.json',
              help='Locations file')
def uninstall(locations_file: Optional[str]):
  click.echo(f"{locations_file}")


cli.add_command(compile)
cli.add_command(install)
cli.add_command(uninstall)

# if __name__ == "__main__":
# cli()
#   print(dir)

# cli()
from typing import Callable, Dict, Optional


def a(a: int, b: int) -> int:
  return a + b


def f(c: Callable[..., any]) -> any:
  return c()


print(f(lambda: a(1, 2)))
