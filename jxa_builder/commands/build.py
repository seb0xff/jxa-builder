import os
from os import path as p
import re
import shutil
import subprocess
import json
from jxa_builder.utils.click_importer import click
from typing import Optional, List, Set
from jxa_builder.core.get_project_config import get_project_config, cmd_args_override
from jxa_builder.core.constants import BUILD_DIR, OUTPUT_DIR, LOCATIONS_FILE, PREPROCESSED_DIR
from jxa_builder.utils.logger import logger
from jxa_builder.utils.printit import terminate_with_error
from _shared_options import debug_option, project_dir_option
from jxa_builder.core.models import Module, CompilationUnit
from jxa_builder.core.get_dependency_modules import get_dependency_modules


@click.command()
@project_dir_option
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
    'By default the builder searches for "icon.icns" or "<app-name>.icns" in the project directory. If none of them is found and this option is left empty, the default icon is used (has effect only when compiling to a standalone app)'
)
@debug_option
def build(**kwargs):
  project_dir = kwargs.pop('project_dir')
  jxa_config = get_project_config(project_dir,
                                  lambda: cmd_args_override(kwargs))

  main_module = Module(
      name='main',
      #  source=jxa_config.main,
      source=p.join(project_dir, jxa_config.main),
      version=jxa_config.version)
  if jxa_config.comp_mode == 'app':
    main_module.name = jxa_config.app_name

  dependency_modules = get_dependency_modules(project_dir)
  logger.debug(f'Dependencies: {dependency_modules}')

  preprocessed_dir = p.join(project_dir, PREPROCESSED_DIR)
  output_dir = p.join(project_dir, OUTPUT_DIR)
  build_dir = p.join(project_dir, BUILD_DIR)
  # TODO: refactor error messages

  try:
    shutil.rmtree(preprocessed_dir, ignore_errors=True)
  except Exception as e:
    terminate_with_error(f'Error, while deleting temporary directory: {e}')
  try:
    shutil.rmtree(output_dir, ignore_errors=True)
  except Exception as e:
    terminate_with_error(f'Error, while deleting output directory: {e}')

  mirror_main_folder = p.join(
      preprocessed_dir,
      p.dirname(main_module.source).replace(project_dir + p.sep, ''))
  mirror_main_source = p.join(mirror_main_folder,
                              p.basename(main_module.source))
  try:
    os.makedirs(p.dirname(mirror_main_source), exist_ok=True)
  except Exception as e:
    terminate_with_error(f'Error, while creating temporary directory: {e}')
  try:
    shutil.copy2(main_module.source, p.dirname(mirror_main_source))
  except Exception as e:
    terminate_with_error(
        f'Error, while copying main source to temporary directory: {e}')
  main = CompilationUnit(mirror_main_source,
                         p.join(output_dir, main_module.name))
  libs: list[CompilationUnit] = []
  for dep in dependency_modules:
    mirror_dependant_folder = p.join(
        preprocessed_dir,
        p.dirname(dep.dependant_source).replace(project_dir + p.sep, ''))
    mirror_dependant_source = p.join(mirror_dependant_folder,
                                     p.basename(dep.dependant_source))
    mirror_folder = p.join(
        preprocessed_dir,
        p.dirname(dep.source).replace(project_dir + p.sep, ''))
    mirror_source = p.join(mirror_folder, p.basename(dep.source))
    try:
      os.makedirs(mirror_folder, exist_ok=True)
    except Exception as e:
      terminate_with_error(
          f'Error, while creating temporary directory for dependency: {e}')
    try:
      shutil.copy2(dep.source, mirror_folder)
    except Exception as e:
      terminate_with_error(
          f'Error, while copying dependency source to temporary directory: {e}'
      )
    try:
      with open(mirror_dependant_source, 'r') as f:
        code = f.read()
    except Exception as e:
      terminate_with_error(f'Error, while reading dependant source: {e}')
    name_ver = dep.name + dep.version
    name_ver = name_ver.replace('.', '_')  # Dots are not allowed in lib name
    code = re.sub(f'(Library\\(["\'])(?:.+/)*{dep.name}(["\']\\))',
                  f'\\g<1>{name_ver}\\g<2>', code)
    try:
      with open(mirror_dependant_source, 'w') as f:
        f.write(code)
    except Exception as e:
      terminate_with_error(f'Error, while writing dependant source: {e}')
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
      terminate_with_error(
          'Error, library installation mode is set to "app", but the main file is not compiled to an app'
      )
    # if jxa_config.install_after:
    #   main.output_path = p.join('/Applications', p.basename(main.output_path))
    lib_dest = p.join(main.output_path, 'Contents', 'Resources',
                      'Script Libraries')
  elif jxa_config.deps_install_mode == 'user':
    lib_dest = p.join(p.expanduser('~'), 'Library', 'Script Libraries')
  elif jxa_config.deps_install_mode == "system":
    lib_dest = p.join('/Library', 'Script Libraries')
  else:
    terminate_with_error(
        f'Error, unknown library installation mode "{jxa_config.deps_install_mode}"'
    )

  if jxa_config.deps_comp_mode == 'script':
    lib_ext = 'scpt'
  elif jxa_config.deps_comp_mode == 'bundle':
    lib_ext = 'scptd'
  else:
    terminate_with_error(
        f'Error, unknown library compilation mode "{jxa_config.deps_comp_mode}"'
    )

  for lib in libs:
    lib.output_path = p.join(lib_dest, f'{lib.output_path}.{lib_ext}')

  ## Create fresh output directory
  if p.exists(output_dir):
    shutil.rmtree(output_dir)
  if not p.exists(output_dir):
    try:
      os.makedirs(output_dir)
    except:
      terminate_with_error(f'Error, while creating output directory: {e}')

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
        'osacompile', '-l', 'JavaScript', '-o', item.output_path,
        item.input_path
    ]
    try:
      subprocess.run(command, check=True, text=True)
    except subprocess.CalledProcessError as e:
      terminate_with_error(f'Error running osacompile: {e}')

  try:
    with open(p.join(project_dir, LOCATIONS_FILE), 'w') as f:
      f.write(json.dumps(outputs, indent=2))
  except Exception as e:
    terminate_with_error(f'Error, while writing locations file: {e}')

  ## TODO: move this to a separate file
  ## Modify Info.plist and app resources
  if jxa_config.comp_mode == "app":
    try:
      with open(p.join(main.output_path, 'Contents', 'Info.plist'),
                'r') as file:
        info_plist = file.read()
    except Exception as e:
      terminate_with_error(f'Error, while reading Info.plist: {e}')

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
      with open(p.join(main.output_path, 'Contents', 'Info.plist'),
                'w') as file:
        file.write(info_plist)
    except Exception as e:
      terminate_with_error(f'Error, while writing Info.plist: {e}')

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
      terminate_with_error(f'Error, while renaming bundle executable: {e}')

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
      terminate_with_error(f'Error, while renaming app resource files: {e}')

    ## Copy icon to the app resources
    # TODO: make sure relative paths work
    if jxa_config.app_icon:
      try:
        shutil.copy2(
            p.join(project_dir, jxa_config.app_icon),
            p.join(main.output_path, 'Contents', 'Resources',
                   f'{bundle_executable}.icns'))
      except Exception as e:
        terminate_with_error(
            f'Error, while copying icon to the app resources: {e}')
