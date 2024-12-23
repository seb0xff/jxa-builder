#!/usr/bin/env python3
from __future__ import annotations
import os
import shutil
from typing import Literal, TypeVar, Generic, Iterable, Optional, Union, cast, Annotated, get_type_hints, Protocol, runtime_checkable, List, Dict, Sequence, Tuple
from types import SimpleNamespace
from dataclasses import dataclass
from recase import recase
from pprint import pprint
from pydantic import BaseModel, BaseSettings, PostgresDsn
from pydantic.env_settings import SettingsSourceCallable
from os import path as p
import json

RICH = os.environ.get('JXA_BUILDER_CLASSIC_DISPLAY_MODE',
                      'false').lower() not in ('true', '1', 'yes')
if RICH:
  import rich_click as click
else:
  import click

cmd_config_dict = {}


def cmd_test(settings: BaseSettings) -> Dict[str, any]:
  print(settings.__dict__)
  include = ['project_dir', 'debug']
  return {k: v for k, v in cmd_config_dict.items() if k in include}


class GeneralConfig(BaseSettings):
  project_dir: str = os.getcwd()
  debug: bool = False
  verbose: bool = False

  class Config:

    @classmethod
    def customise_sources(
        cls,
        init_settings: SettingsSourceCallable,
        env_settings: SettingsSourceCallable,
        file_secret_settings: SettingsSourceCallable,
    ) -> Tuple[SettingsSourceCallable, ...]:
      # return command_line, env_settings, jxa_json, jxa_from_package_json, init_settings
      return init_settings, cmd_test


class jxa_json:

  def __init__(self, path: str):
    self.path = path

  def __call__(self, settings: BaseSettings) -> Dict[str, any]:
    config_path = p.join(self.path, 'jxa.json')
    # config_path = p.join(settings.project_dir, 'jxa.json')
    if not p.exists(config_path):
      return {}

    if p.exists(config_path):
      try:
        with open(config_path) as f:
          jxa = json.load(f).items()
          if not jxa:
            return {}
          # return {recase(k, 'snake'): v for k, v in jxa}
          return {recase(k, 'snake'): v for k, v in jxa}
          # jxa.pop('project_dir')
          # jxa['project_dir'] = 'test'
          # return jxa
      except json.JSONDecodeError:
        print(f'Error, the file "{config_path}" is not a valid JSON document.')
        exit(1)
      except Exception as e:
        print(f'Error, while reading "{config_path}": {e}')
        exit(1)
    else:
      return {}


def jxa_from_package_json(settings: BaseSettings) -> Dict[str, any]:
  # config_path = p.join(settings.project_dir, 'package.json')
  config_path = p.join(os.getcwd(), 'package.json')
  if not p.exists(config_path):
    return {}

  if p.exists(config_path):
    try:
      with open(config_path) as f:
        jxa = json.load(f).get('jxa', {}).items()
        if not jxa:
          return {}
        return {recase(k, 'snake'): v for k, v in jxa}
    except json.JSONDecodeError:
      print(f'Error, the file "{config_path}" is not a valid JSON document.')
      exit(1)
    except Exception as e:
      print(f'Error, while reading "{config_path}": {e}')
      exit(1)
  else:
    return {}


def command_line(settings: BaseSettings) -> Dict[str, any]:
  skip = ['project_dir', 'debug']
  return {k: v for k, v in cmd_config_dict.items() if k not in skip}


class BuildConfig(BaseSettings):

  def __init__(self, project_dir, **kwargs):
    self.project_dir = project_dir
    super().__init__(**kwargs)

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

  # paths: List[str] = []

  class Config:

    @classmethod
    def customise_sources(
        cls,
        init_settings: SettingsSourceCallable,
        env_settings: SettingsSourceCallable,
        file_secret_settings: SettingsSourceCallable,
    ) -> Tuple[SettingsSourceCallable, ...]:
      # return command_line, env_settings, jxa_json, jxa_from_package_json, init_settings
      return init_settings, env_settings, jxa_json(
          cmd_config_dict['project_dir'])


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
  global cmd_config_dict
  cmd_config_dict = kwargs
  from pydantic.error_wrappers import ValidationError

  try:
    b = BuildConfig()
    g = GeneralConfig()
  except ValidationError as e:
    print(e)
    exit(1)
  # print(cmd_config_dict['project_dir'])
  # print(b.comp_mode)
  print(g.project_dir)


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
cli()

# from pydantic.error_wrappers import ValidationError
# try:
#   b = BuildConfig()
#   bb = BuildConfig()
# except ValidationError as e:
#   print(e)
#   exit(1)

# print(b.comp_mode)
