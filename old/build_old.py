#!/usr/bin/env python3

from dataclasses import dataclass
import os
from os import path as p
import re
import sys
import shutil
import subprocess
import json
import argparse
from typing import Literal, Optional, TypeVar, Generic, Type

T = TypeVar('T')


@dataclass
class Option(Generic[T]):
  json: str
  cmd: str
  # vals: Optional[Type[T]] = None
  vals: T = None


# TODO: add flag whether to install app too for install command
# TODO: remove unnecessary makedirs calls
# TODO: break into multiple files
# TODO: add utils file with file system related functions
# TODO: reconsider the use of print && exit when error occurs
# TODO: make use of this class and make it static
# TODO: add png to icns conversion


# TODO: move this, args parser and JxaConfig to a separate file
class Literals:
  working_dir = Option('', '--working-dir', bool)
  comp_mode = Option('compilationMode', '--comp-mode', Literal['app', 'script',
                                                               'bundle'])
  deps_comp_mode = Option('dependenciesCompilationMode', '--deps-comp-mode',
                          ['script', 'bundle'])
  deps_install_mode = Option('dependenciesInstallationMode',
                             '--deps-install-mode', ['app', 'user', 'system'])
  version = Option('version', '--version')
  main_file = Option('main', '--main-file')
  app_name = Option('appName', '--app-name')
  app_icon = Option('appIcon', '--app-icon')
  package_name = Option('packageName', '')
  install_after = Option('installAfter', '--install-after')
  debug_info = Option('debugInfo', '--debug-info')
  deps_only = Option('dependenciesOnly', '--dependencies-only')


# print(Literals.comp_mode.vals)
# a = str

## Parse arguments
parser = argparse.ArgumentParser(
    description='Javascript for Automation build system')
parser.add_argument(
    Literals.working_dir.cmd,
    type=str,
    default=os.getcwd(),
    help=
    'Working directory. Place where the project is located. Defaults to the current directory'
)
parser.add_argument(
    Literals.comp_mode.cmd,
    type=str,
    choices=Literals.comp_mode.vals,
    help=
    'Whether to compile the main source to a standalone app (e.g. applet/droplet) or a script'
)
parser.add_argument(
    Literals.deps_comp_mode.cmd,
    type=str,
    choices=Literals.deps_comp_mode.vals,
    help='Whether dependencies should be compiled as scripts or bundles')
parser.add_argument(
    Literals.deps_install_mode.cmd,
    type=str,
    choices=Literals.deps_install_mode.vals,
    help=
    'Where to install dependencies. If the main file is compiled to a standalone app one can embed them inside. Otherwise they can be installed for a current user, or system wide'
)
parser.add_argument(Literals.version.cmd,
                    type=str,
                    help='Version of the project')
parser.add_argument(Literals.main_file.cmd, type=str, help='Main source file')
parser.add_argument(
    Literals.app_name.cmd,
    type=str,
    help='App name, (has effect only when compiling to a standalone app)')
parser.add_argument(
    Literals.app_icon.cmd,
    type=str,
    help=
    'By default the builder searches for "icon.icns" or "<app-name>.icns" in the working directory. If both icons are not found and this option is left empty, the default icon is used (has effect only when compiling to a standalone app)'
)
parser.add_argument(
    Literals.debug_info.cmd,
    action='store_true',
    help=
    'Whether to add some useful information. (mainly used for testing purposes)'
)
subparsers = parser.add_subparsers()
install_parser = subparsers.add_parser('install')
install_parser.add_argument(
    Literals.deps_only.cmd,
    default=False,
    action='store_true',
    help=
    'Whether to install the app and it\'s dependencies or only the dependencies'
)
uninstall_parser = subparsers.add_parser('uninstall')

# TODO: for ./ and ../ search only in these folders
# TODO: find common prefix while installing


# TODO: move this to a separate file
def manage_outputs(action: Literal['install', 'uninstall'],
                   exit_after: bool = False):
  system_tmp = p.join('/private', 'tmp', 'jxa-builder')
  perm_problem = False
  shell_command = ''
  if p.exists(p.join(build_dir, 'outputs.json')):
    try:
      with open(p.join(build_dir, 'outputs.json'), 'r') as f:
        outputs: dict[str, str] = json.load(f)
    except Exception as e:
      print(f'Error, while reading outputs.json: {e}')
      exit(1)
    # for name, install_path in list(outputs.items())[::-1]:
    for target, install_path in outputs.items():
      dest_file = p.join(install_path, p.basename(target))
      if target != dest_file:
        try:
          if p.exists(dest_file):
            shutil.rmtree(dest_file) if p.isdir(dest_file) else os.remove(
                dest_file)
          if action == 'install':
            os.makedirs(install_path, exist_ok=True)
            shutil.copytree(target,
                            install_path) if p.isdir(target) else shutil.copy(
                                target, install_path)
        ## - To perform action that needs sudo it will use constructed shell command
        ##   that is invoked by JXA's doShellScript with administrator privileges,
        ##   so convinient Touch ID can be used to authenticate (sudo still works too).
        ## - The shell command is used instead of running the python script itself
        ##   to avoid Operatin not permitted error (with admin privils you can't access home dir).
        ## - Files to be installed are first copied to the system temporary directory
        ##   beacuse of the same reason as above.
        ##   More info: https://stackoverflow.com/a/68694914
        except PermissionError as e:
          perm_problem = True
          shell_command += f'[ -e "{dest_file}" ] && rm -r "{dest_file}";'
          if action == 'install':
            target = p.join(system_tmp, p.basename(target))
            shell_command += f'mkdir -p "{install_path}" && mv "{target}" "{install_path}";'

    if perm_problem:
      jxa_command = f'''
      const app = Application.currentApplication();
      app.includeStandardAdditions = true;
      app.doShellScript('{shell_command}', {{
        administratorPrivileges: true,
        alteringLineEndings: false,
        withPrompt: "Administration privileges are needed to perform the task.\\nPlease enter your password:",
      }});
      '''
      if action == 'install':
        try:
          shutil.copytree(output_dir, system_tmp, dirs_exist_ok=True)
        except Exception as e:
          print(
              f'Error, while copying output directory to the temporary (system) directory: {e}'
          )
          exit(1)
      try:
        process = subprocess.run(
            ['osascript', '-l', 'JavaScript', '-e', jxa_command], text=True)
      except subprocess.CalledProcessError as e:
        print(f'Error, while running {action}: {e}')
        exit(1)
      if action == 'install':
        if p.exists(system_tmp):
          try:
            shutil.rmtree(system_tmp)
          except Exception as e:
            print(f'Error, while deleting temporary (system) directory: {e}')
            exit(1)
  else:
    print('Error, outputs.json not found')
    exit(1)
  if exit_after:
    exit(0)


install_parser.set_defaults(func=lambda: manage_outputs('install', True))
uninstall_parser.set_defaults(func=lambda: manage_outputs('uninstall', True))

args = parser.parse_args()
debug_info = args.debug_info
debug_info = False
# working_dir = args.working_dir
working_dir = '/Users/sebastian/Documents/src/js/DoubleClickConsoleEdit'
build_dir = p.join(working_dir, 'build')
tmp_dir = p.join(build_dir, 'tmp')
output_dir = p.join(build_dir, 'output')
# if hasattr(args, 'func'):
#   args.func()

manage_outputs('uninstall', True)


@dataclass
class CompilationUnit:
  input_path: str
  output_path: str


@dataclass
class Module:
  name: str
  source: str
  version: str
  dependant_source: str


class JxaConfig:

  def __init__(self, path: str):
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
    # print(json_config)
    ## Read config values from arguments if in the working directory and set defaults
    ## Hierarchical order: arguments > jxa.json > package.json
    self.comp_mode: Literal['app', 'script', 'bundle'] = (
        (args.comp_mode if is_arg_provided(Literals.comp_mode.cmd)
         and isWorkingDir else json_config.get(Literals.comp_mode.json, ''))
        or 'app').strip()
    self.deps_comp_mode: Literal['script', 'bundle'] = (
        (args.deps_comp_mode if is_arg_provided(Literals.deps_comp_mode.cmd)
         and isWorkingDir else json_config.get(Literals.deps_comp_mode.json,
                                               '')) or 'script').strip()
    self.deps_install_mode: Literal['app', 'user', 'system'] = (
        (args.deps_install_mode if is_arg_provided('--dep-install-mode') and
         isWorkingDir else json_config.get('dependencyInstallationMode', ''))
        or 'app').strip()
    self.version: str = ((args.version if is_arg_provided('--version')
                          and isWorkingDir else json_config.get('version', ''))
                         or '1.0.0').strip()
    self.main_file: str = ((args.main_file if is_arg_provided('--main-file')
                            and isWorkingDir else json_config.get('main', ''))
                           or 'index.js').strip()
    self.app_name: str = ((args.app_name if is_arg_provided('--app-name') and
                           isWorkingDir else json_config.get('appName', ''))
                          or 'app').strip()
    self.app_icon: str = ((args.app_icon if is_arg_provided('--app-icon') and
                           isWorkingDir else json_config.get('appIcon', ''))
                          or '').strip()
    if not self.app_icon and p.exists(
        p.join(working_dir, self.app_name + '.icns')):
      self.app_icon = p.join(working_dir, self.app_name + '.icns')
    elif not self.app_icon and p.exists(p.join(working_dir, 'icon.icns')):
      self.app_icon = p.join(working_dir, 'icon.icns')
    self.install_after: bool = (
        (args.install_after if is_arg_provided('--install-after')
         and isWorkingDir else json_config.get('installAfter', '')) or False)
    self.package_name = (package_json.get('name', '') or '').strip()


jxa_config = JxaConfig(working_dir)
# if debug_info:
#   for key, value in vars(jxa_config).items():
#     print(f'{key}: {value}')
# print(jxa_config.deps_comp_mode)
# exit()

main_module = Module('', '', '', '')
if jxa_config.comp_mode == 'app':
  main_module.name = jxa_config.app_name
if main_module.name == '':
  jxa_config.package_name
main_module.source = jxa_config.main_file
main_module.version = jxa_config.version


## Recursively get all dependencies
def get_dependency_modules(package_path) -> list[Module]:
  dependencies = []
  jxa_config = JxaConfig(package_path)
  if jxa_config.__dict__ and p.isdir(package_path):
    source = p.join(package_path, jxa_config.main_file)
  elif p.isdir(package_path):
    source = p.join(package_path, 'index.js')
  else:
    source = package_path

  if not p.exists(source):
    print(f'Error, could not find source "{source}"')
    exit(1)

  ## Get library names from the source
  try:
    with open(source, 'r') as f:
      code = f.read()
  except Exception as e:
    print(f'Error, while reading source "{source}": {e}')
    exit(1)
  code = re.sub(r'//.*\n', '', code)
  code = re.sub(r'/\*[\s\S]*?\*/', '', code)
  libraries: set[str] = set(re.findall(r'Library\(["\'](.+?)["\']\)', code))

  for lib in libraries:
    source_dir = p.dirname(source)
    ## Resolve relative paths
    # TODO: replace with glob
    while lib.startswith('../'):
      lib = lib[3:]
      source_dir = p.dirname(source_dir)
    lib_path = p.join(source_dir, lib)

    # TODO: add global node_modules search path
    deps_search_paths = [
        source_dir, 'dependencies',
        p.join(package_path, 'node_modules')
    ]
    for deps_search_path in deps_search_paths:
      lib_path = p.join(deps_search_path, lib)
      if p.exists(lib_path):
        lib_jxa_config = JxaConfig(lib_path)
        lib_source = p.join(
            lib_path,
            lib_jxa_config.main_file) if lib_jxa_config.__dict__ else p.join(
                lib_path, 'index.js')
        lib_version = lib_jxa_config.version if lib_jxa_config.__dict__ else ''
        dependencies.append(Module(lib, lib_source, lib_version, source))
        dependencies += get_dependency_modules(lib_path)
        break
      elif p.exists(lib_path + '.js'):
        lib_source = lib_path + '.js'
        dependencies.append(Module(lib, lib_source, '', source))
        dependencies += get_dependency_modules(lib_source)
        break
      else:
        if deps_search_path == deps_search_paths[-1]:  # last iteration
          print(f'Error, Could not find library "{lib}"')
          print(
              'Make sure it\'s actually installed if using a package manager (e.g. "npm install")'
          )
          exit(1)
  return dependencies


# dependency_modules = get_dependency_modules(working_dir)
# print(dependency_modules)
# exit()

## Mirror sources to a temporary directory
## Change library names in dependant sources to include versions
## Finally add them to the compilation units list
try:
  shutil.rmtree(tmp_dir, ignore_errors=True)
except Exception as e:
  print(f'Error, while deleting temporary directory: {e}')
  exit(1)
try:
  shutil.rmtree(output_dir, ignore_errors=True)
except Exception as e:
  print(f'Error, while deleting output directory: {e}')
  exit(1)

mirror_main_folder = p.join(
    tmp_dir,
    p.dirname(main_module.source).replace(working_dir + p.sep, ''))
mirror_main_source = p.join(mirror_main_folder, p.basename(main_module.source))
try:
  os.makedirs(p.dirname(mirror_main_source), exist_ok=True)
except Exception as e:
  print(f'Error, while creating temporary directory: {e}')
  exit(1)
try:
  shutil.copy2(main_module.source, p.dirname(mirror_main_source))
except Exception as e:
  print(f'Error, while copying main source to temporary directory: {e}')
  exit(1)
main = CompilationUnit(mirror_main_source, p.join(output_dir,
                                                  main_module.name))
libs: list[CompilationUnit] = []
for dep in dependency_modules:
  mirror_dependant_folder = p.join(
      tmp_dir,
      p.dirname(dep.dependant_source).replace(working_dir + p.sep, ''))
  mirror_dependant_source = p.join(mirror_dependant_folder,
                                   p.basename(dep.dependant_source))
  mirror_folder = p.join(
      tmp_dir,
      p.dirname(dep.source).replace(working_dir + p.sep, ''))
  mirror_source = p.join(mirror_folder, p.basename(dep.source))
  try:
    os.makedirs(mirror_folder, exist_ok=True)
  except Exception as e:
    print(f'Error, while creating temporary directory for dependency: {e}')
    exit(1)
  try:
    shutil.copy2(dep.source, mirror_folder)
  except Exception as e:
    print(
        f'Error, while copying dependency source to temporary directory: {e}')
    exit(1)
  try:
    with open(mirror_dependant_source, 'r') as f:
      code = f.read()
  except Exception as e:
    print(f'Error, while reading dependant source: {e}')
    exit(1)
  name_ver = dep.name + dep.version if re.match(r'.*\d+\.\d+\.\d+.*',
                                                dep.version) else dep.name
  ## Dots are not allowed in library names
  name_ver = name_ver.replace('.', '_')
  code = re.sub(f'(Library\\(["\'])(?:.+/)*{dep.name}(["\']\\))',
                f'\\g<1>{name_ver}\\g<2>', code)
  try:
    with open(mirror_dependant_source, 'w') as f:
      f.write(code)
  except Exception as e:
    print(f'Error, while writing dependant source: {e}')
    exit(1)
  libs.append(CompilationUnit(mirror_source, name_ver))

## Make pascal case from space separated, snake or kebab case string
bundle_executable = ''.join(
    word[0].capitalize() + word[1:]
    for word in re.split(r'[\s_-]+', p.basename(main.output_path)))

if jxa_config.comp_mode == 'app':
  main_ext = 'app'
elif jxa_config.comp_mode == 'script':
  main_ext = 'scpt'

main.output_path = f'{main.output_path}.{main_ext}'

## Set library installation path
if jxa_config.deps_install_mode == 'app':
  if jxa_config.comp_mode != 'app':
    print(
        'Error, library installation mode is set to "app", but the main file is not compiled to an app'
    )
    exit(1)
  if jxa_config.install_after:
    main.output_path = p.join('/Applications', p.basename(main.output_path))
  lib_dest = p.join(main.output_path, 'Contents', 'Resources',
                    'Script Libraries')
elif jxa_config.deps_install_mode == 'user':
  lib_dest = p.join(p.expanduser('~'), 'Library', 'Script Libraries')
elif jxa_config.deps_install_mode == "system":
  lib_dest = p.join('/Library', 'Script Libraries')
else:
  print(
      f'Error, unknown library installation mode "{jxa_config.deps_install_mode}"'
  )
  exit(1)

if jxa_config.deps_comp_mode == 'script':
  lib_ext = 'scpt'
elif jxa_config.deps_comp_mode == 'bundle':
  lib_ext = 'scptd'
else:
  print(
      f'Error, unknown library compilation mode "{jxa_config.deps_comp_mode}"')
  exit(1)

for lib in libs:
  lib.output_path = p.join(lib_dest, f'{lib.output_path}.{lib_ext}')

## Create fresh output directory
if p.exists(output_dir):
  shutil.rmtree(output_dir)
if not p.exists(output_dir):
  try:
    os.makedirs(output_dir)
  except:
    print(f'Error, while creating output directory: {e}')
    exit(1)

## Compile
outputs: dict[str, str] = {}
for item in [main] + libs:
  ## Instead of installing directly to the output path,
  ## install to the output directory.
  ## Optionally, move the outputs to the final destinations
  ## using "--install_after" flag or "install" command
  # TODO: try to move this logic to compilation unit
  outputs[p.join(output_dir,
                 p.basename(item.output_path))] = p.dirname(item.output_path)
  item.output_path = p.join(output_dir, p.basename(item.output_path))

  command = [
      'osacompile', '-l', 'JavaScript', '-o', item.output_path, item.input_path
  ]
  try:
    subprocess.run(command, check=True, text=True)
  except subprocess.CalledProcessError as e:
    print(f'Error running osacompile: {e}')
    exit(1)

try:
  with open(p.join(build_dir, 'outputs.json'), 'w') as f:
    f.write(json.dumps(outputs, indent=2))
except Exception as e:
  print(f'Error, while writing outputs.json: {e}')
  exit(1)

## TODO: move this to a separate file
## Modify Info.plist and app resources
if jxa_config.comp_mode == "app":
  try:
    with open(p.join(main.output_path, 'Contents', 'Info.plist'), 'r') as file:
      info_plist = file.read()
  except Exception as e:
    print(f'Error, while reading Info.plist: {e}')
    exit(1)

  default_bundle_executable = re.search(
      r'(<key>CFBundleExecutable</key>\s+<string>)(\w+?)(</string>)',
      info_plist).group(2)

  ## Replace bundle executable name
  info_plist = re.sub(
      r'(<key>CFBundleExecutable</key>\s+<string>)\w+?(</string>)',
      f'\\g<1>{bundle_executable}\\g<2>', info_plist)

  ## Replace bundle icon name
  info_plist = re.sub(
      r'(<key>CFBundleIconFile</key>\s+<string>)\w+?(</string>)',
      f'\\g<1>{bundle_executable}.icns\\g<2>', info_plist)

  try:
    with open(p.join(main.output_path, 'Contents', 'Info.plist'), 'w') as file:
      file.write(info_plist)
  except Exception as e:
    print(f'Error, while writing Info.plist: {e}')
    exit(1)

  ## Rename bundle executable accordingly
  try:
    if p.exists(
        p.join(main.output_path, 'Contents', 'MacOS',
               default_bundle_executable)):
      os.rename(
          p.join(main.output_path, 'Contents', 'MacOS',
                 default_bundle_executable),
          p.join(main.output_path, 'Contents', 'MacOS', bundle_executable))
  except Exception as e:
    print(f'Error, while renaming bundle executable: {e}')
    exit(1)

  ## Rename app resource files accordingly
  try:
    os.rename(
        p.join(main.output_path, 'Contents', 'Resources',
               f'{default_bundle_executable}.icns'),
        p.join(main.output_path, 'Contents', 'Resources',
               f'{bundle_executable}.icns'))
    os.rename(
        p.join(main.output_path, 'Contents', 'Resources',
               f'{default_bundle_executable}.rsrc'),
        p.join(main.output_path, 'Contents', 'Resources',
               f'{bundle_executable}.rsrc'))
  except Exception as e:
    print(f'Error, while renaming app resource files: {e}')
    exit(1)

  ## Copy icon to the app resources
  # TODO: make sure relative paths work
  if jxa_config.app_icon != '':
    try:
      shutil.copy2(
          jxa_config.app_icon,
          p.join(main.output_path, 'Contents', 'Resources',
                 f'{bundle_executable}.icns'))
    except Exception as e:
      print(f'Error, while copying icon to the app resources: {e}')
      exit(1)
