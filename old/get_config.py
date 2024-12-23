from dataclasses import dataclass
import os
from os import path as p
import re
import sys
import shutil
import subprocess
import json
import argparse
from typing import Literal, Union, TypeVar, Generic, TypedDict, Optional
from recase import recase

T = TypeVar('T')


@dataclass
class Option(Generic[T]):
  name: str
  choices: list[T] = None
  default: T = None
  action: Literal['store', 'store_const', 'store_true', 'store_false',
                  'append', 'count', 'help'] = 'store'
  # required: bool = False
  is_config: bool = True
  help: str = ''
  sub_options: list['Option'] = None


options = list([
    Option(
        'workingDir',
        '--working-dir',
        default=os.getcwd(),
        is_config=False,
        help=
        'Working directory. Place where the project is located. Defaults to the current directory'
    ),
    Option(
        'compilationMode',
        '--comp-mode', ['app', 'script', 'bundle'],
        'app',
        help=
        'Whether to compile the main source to a standalone app (e.g. applet/droplet) or a script'
    ),
    Option(
        'dependenciesCompilationMode',
        '--deps-comp-mode', ['script', 'bundle'],
        'script',
        help=
        'Dependencies compilation mode. Whether dependencies should be compiled as scripts or bundles'
    ),
    Option(
        'dependenciesInstallationMode',
        '--deps-install-mode', ['app', 'user', 'system'],
        'app',
        help=
        'Where to install dependencies. If the main file is compiled to a standalone app one can embed them inside. Otherwise they can be installed for a current user, or system wide'
    ),
    Option('version', '--version', [], '', 'Version of the project'),
    Option('mainFile', '--main-file', [], '', 'Main source file'),
    Option('appName', '--app-name', [], '',
           'App name, (has effect only when compiling to a standalone app)'),
    Option(
        'appIcon', '--app-icon', [], '',
        'By default the builder searches for "icon.icns" or "<app-name>.icns" in the working directory. If both icons are not found and this option is left empty, the default icon is used (has effect only when compiling to a standalone app)'
    ),
    Option(
        'debugInfo', '--debug-info', [], False,
        'Whether to add some useful information. (mainly used for testing purposes)'
    ),
    Option('installAfter', '--install-after', [], False,
           'Whether to run "install" command after building'),
    Option(
        'dependenciesOnly', '--deps-only', [], False,
        'Whether to install the app and it\'s dependencies or only the dependencies'
    ),
    Option('packageName', '', [], '', ''),
])


class ConfigParser:

  def add(self,
          *options: str,
          choices: list[T] = None,
          default: T = None,
          action: Literal['store', 'store_const', 'store_true', 'store_false',
                          'append', 'count', 'help'] = 'store',
          help: str = ''):
    pass

  def t(self, **kwargs):
    if kwargs.get('choices'):
      kwargs['choices'] = list(map(lambda x: str(x), kwargs['choices']))

  def __init__(self, path: str):
    parser = argparse.ArgumentParser(
        description='Javascript for Automation build system')
    subparsers = parser.add_subparsers()
    for option in options:
      # setattr(self, option.name, option.default) #type=str #action='store_true'
      if option.sub_options:
        subparser = subparsers.add_parser(option.cmd)
        for sub_option in option.sub_options:
          subparser.add_argument(sub_option.cmd,
                                 choices=sub_option.choices,
                                 default=sub_option.default,
                                 action=sub_option.action,
                                 help=sub_option.help)
      else:
        parser.add_argument(option.cmd,
                            choices=option.choices,
                            default=option.default,
                            action=option.action,
                            help=option.help)

    args = parser.parse_args()
    print(args)

    c = ConfigParser('').t()
    exit()
    debug_info = args.debug_info
    working_dir = args.working_dir
    build_dir = p.join(working_dir, 'build')
    tmp_dir = p.join(build_dir, 'tmp')
    output_dir = p.join(build_dir, 'output')
    system_tmp = p.join('/private', 'tmp', 'jxa-builder')

    if path.endswith('.js'):
      return

    package_json_path = p.join(path, 'package.json')
    jxa_json_path = p.join(path, 'jxa.json')
    if not p.exists(package_json_path) and not p.exists(jxa_json_path):
      return

    def is_arg_provided(arg: str):
      for a in sys.argv:
        if a.startswith(arg):
          return True
      return False

    package_json = {}
    jxa_from_package_json = {}
    if p.exists(package_json_path):
      try:
        with open(package_json_path) as f:
          package_json = json.load(f)
          jxa_from_package_json = package_json.get('jxa', {})
      except Exception as e:
        print(f'Error, while reading "{package_json_path}": {e}')
        exit(1)

    jxa_json = {}
    if p.exists(jxa_json_path):
      try:
        with open(jxa_json_path) as f:
          jxa_json = json.load(f)
      except Exception as e:
        print(f'Error, while reading "{jxa_json_path}": {e}')
        exit(1)

    ## Fetch config values
    json_config = {**package_json, **jxa_from_package_json, **jxa_json}
    isWorkingDir = path == working_dir
