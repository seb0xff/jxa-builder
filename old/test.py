#!/usr/bin/env python3
import os
import shutil
from typing import Literal, TypeVar, Generic, Iterable, Optional, Union, cast
from dataclasses import dataclass
import argparse
from recase import recase
from pprint import pprint

T = TypeVar('T')


class NoDefault:
  """Sentinel value representing a missing default value."""


@dataclass
class Property(Generic[T]):
  """
  name - property name
  choices - possible values
  cmd_names - additional command line options to the --<name>-in-kebab-case
  default - default value, NoDefault means that the value is required
  action - action
  source - where to get the value from
  help - help message
  """
  name: str
  choices: Optional[Iterable[T]] = None
  cmd_names: Optional[Iterable[str]] = None
  default: Union[T, None, NoDefault] = None
  action: Literal['store', 'store_const', 'store_true', 'store_false',
                  'append', 'count', 'help'] = 'store'
  source: Literal['args', 'config', 'both'] = 'both'
  help: Optional[str] = None


root = list([
    Property(
        name='workingDir',
        default=os.getcwd(),
        source='args',
        help=
        'Working directory. Place where the project is located. Defaults to the current directory'
    ),
    Property(
        name='compilationMode',
        choices=['app', 'script', 'bundle'],
        default='app',
        help=
        'Whether to compile the main source to a standalone app (e.g. applet/droplet) or a script'
    ),
    Property(
        name='dependenciesCompilationMode',
        choices=['script', 'bundle'],
        default='script',
        help=
        'Dependencies compilation mode. Whether dependencies should be compiled as scripts or bundles'
    ),
    Property(
        name='dependenciesInstallationMode',
        choices=['app', 'user', 'system'],
        default='app',
        help=
        'Where to install dependencies. If the main file is compiled to a standalone app one can embed them inside. Otherwise they can be installed for a current user, or system wide'
    ),
    Property(name='version', default='1.0.0', help='Version of the project'),
    Property(name='mainFile', default='index.js', help='Main source file'),
    Property(
        name='appName',
        default='out',
        help='App name, (has effect only when compiling to a standalone app)'),
    Property(
        name='appIcon',
        default='',
        help=
        'By default the builder searches for "icon.icns" or "<app-name>.icns" in the working directory. If both icons are not found and this option is left empty, the default icon is used (has effect only when compiling to a standalone app)'
    ),
    Property(
        name='debugInfo',
        default=False,
        action='store_true',
        help=
        'Whether to add some useful information. (mainly used for testing purposes)'
    ),
    Property(name='installAfter',
             default=False,
             action='store_true',
             help='Whether to run "install" command after building'),
    Property(
        name='dependenciesOnly',
        default=False,
        action='store_true',
        help=
        'Whether to install the app and it\'s dependencies or only the dependencies'
    ),
    Property(name='packageName'),
])


class Config:

  def __init__(self, name: str = None, description: str = None):
    self._name: str = name or ''
    self._parser = argparse.ArgumentParser(description=description)
    # self._subparsers = self._parser.add_subparsers(dest='command')
    self._subparsers = self._parser.add_subparsers()

  def add_property(self, *props: Property) -> 'Config':
    for prop in props:
      args = [f'--{recase(prop.name, "kebab")}', *(prop.cmd_names or [])]

      kwargs = {}
      if prop.action != 'store_true':
        kwargs['choices'] = prop.choices
      kwargs['default'] = prop.default
      kwargs['required'] = prop.default is NoDefault
      kwargs['action'] = prop.action
      kwargs['help'] = prop.help

      self._parser.add_argument(*args, **kwargs)
    return self

  def add_subconfig(self, config: 'Config') -> 'Config':
    assert isinstance(config, Config)
    assert config._name.strip()
    sub = self._subparsers.add_parser(config._name)
    config._parser = sub
    return config

  def parse(self, base: type[T] = None) -> T:
    args = self._parser.parse_args()
    return args

  def unparse(self) -> dict[str, any]:
    pass


conf = Config(description='Javascript for Automation build system')
conf.add_property(*root)


def get_config(self, *props: Property) -> 'Config':
  for prop in props:
    args = [f'--{recase(prop.name, "kebab")}', *(prop.cmd_names or [])]

    kwargs = {}
    if prop.action != 'store_true':
      kwargs['choices'] = prop.choices
    kwargs['default'] = prop.default
    kwargs['required'] = prop.default is NoDefault
    kwargs['action'] = prop.action
    kwargs['help'] = prop.help

    self._parser.add_argument(*args, **kwargs)
  return self
