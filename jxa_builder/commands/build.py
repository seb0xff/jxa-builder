import os
from os import path as p
import re
import shutil
import subprocess
import json
from dataclasses import asdict
from jxa_builder.core.models import Module, CompilationUnit, LoadedPropInfo
from jxa_builder.core.get_dependency_modules import get_dependency_modules
from jxa_builder.core.get_project_config import get_project_config
from jxa_builder.core.modify_app_internals import modify_app_internals
from jxa_builder.core.constants import OUTPUT_DIR, LOCATIONS_FILE, PREPROCESSED_DIR, APPS_DIR_ABS, APP_LIBS_DIR, USER_LIBS_DIR_ABS, SYSTEM_LIBS_DIR_ABS
from jxa_builder.utils.logger import logger
from jxa_builder.utils.click_importer import click
from jxa_builder.utils.printit import log_print_error
from jxa_builder.utils.recase import recase
from jxa_builder.commands._shared_options import debug_option, project_dir_option


# TODO: generate these options from the project config model
@click.command()
@project_dir_option
@click.option(
    '--comp-mode',
    type=click.Choice(['app', 'script']),
    show_default='app',
    help=
    'Whether to compile the main source to a standalone app (e.g. applet/droplet) or a script'
)
@click.option(
    '--deps-install-mode',
    type=click.Choice(['app', 'user', 'system']),
    show_default='app',
    help=
    'Where to install dependencies. If the main file is compiled to a standalone app one can embed them inside. Otherwise they can be installed for a current user, or system wide'
)
@click.option('--version', show_default='1.0.0', help='Version of the project')
@click.option('--main', show_default='index.js', help='Main source file')
@click.option(
    '--app-name',
    show_default='out',
    help='App name, (has effect only when compiling to a standalone app)')
@click.option(
    '--app-icon',
    help=
    'By default the builder searches for "icon.icns" or "<app-name>.icns" in the project directory. If none of them is found and this option is left empty, the default icon is used (has effect only when compiling to a standalone app)'
)
@debug_option
def build(**kwargs):
  project_dir = kwargs['project_dir']
  jxa_config = get_project_config(
      project_dir, {
          k: LoadedPropInfo(v, '', '--' + recase(k, 'kebab'))
          for k, v in kwargs.items()
      })

  main_module = Module(
      name=jxa_config.app_name if jxa_config.comp_mode == 'app' else 'main',
      source=p.join(project_dir, jxa_config.main),
      version=jxa_config.version)

  dependency_modules = get_dependency_modules(project_dir)

  preprocessed_dir = p.join(project_dir, PREPROCESSED_DIR)
  output_dir = p.join(project_dir, OUTPUT_DIR)
  locations_file = p.join(project_dir, LOCATIONS_FILE)

  if p.exists(preprocessed_dir):
    try:
      shutil.rmtree(preprocessed_dir)
    except Exception as e:
      log_print_error(f'Cannot delete the preprocessed directory: {e}')
      exit(1)

  if p.exists(output_dir):
    try:
      shutil.rmtree(output_dir)
    except Exception as e:
      log_print_error(f'Cannot delete the output directory: {e}')
      exit(1)

  if p.exists(output_dir):
    shutil.rmtree(output_dir)
  if not p.exists(output_dir):
    try:
      os.makedirs(output_dir)
    except:
      log_print_error
      (f'Cannot create the output directory: {e}')
      exit(1)

  mirror_main_folder = p.join(
      preprocessed_dir,
      p.dirname(main_module.source).replace(project_dir + p.sep, ''))
  mirror_main_source = p.join(mirror_main_folder,
                              p.basename(main_module.source))

  try:
    os.makedirs(p.dirname(mirror_main_source), exist_ok=True)
  except Exception as e:
    log_print_error
    (f'Cannot create the temporary directory: {e}')
    exit(1)
  try:
    shutil.copy2(main_module.source, p.dirname(mirror_main_source))
  except Exception as e:
    log_print_error
    (f'Cannot copy the main source to the temporary directory: {e}')
    exit(1)

  comp_units: list[CompilationUnit] = []

  if jxa_config.comp_mode == 'app':
    main_suffix = '.app'
  elif jxa_config.comp_mode == 'script':
    main_suffix = '.scpt'
  comp_units.append(
      CompilationUnit(mirror_main_source,
                      p.join(output_dir, main_module.name) + main_suffix,
                      p.join(APPS_DIR_ABS, main_module.name) + main_suffix))

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
      log_print_error
      (f'Cannot create the temporary directory for a dependency: {e}')
      exit(1)
    try:
      shutil.copy2(dep.source, mirror_folder)
    except Exception as e:
      log_print_error
      ('Cannot copy a dependency source to the temporary directory: {e}')
      exit(1)
    try:
      with open(mirror_dependant_source, 'r') as f:
        code = f.read()
    except Exception as e:
      log_print_error
      (f'Cannot read a dependant source: {e}')
      exit(1)
    name_ver = dep.name + dep.version
    name_ver = name_ver.replace('.', '_')  # Dots are not allowed in lib name
    code = re.sub(f'(Library\\(["\'])(?:.+/)*{dep.name}(["\']\\))',
                  f'\\g<1>{name_ver}\\g<2>', code)
    try:
      with open(mirror_dependant_source, 'w') as f:
        f.write(code)
    except Exception as e:
      log_print_error
      (f'Cannot write a dependant source: {e}')
      exit(1)

    ## Installation paths
    if jxa_config.deps_install_mode == 'app':
      if jxa_config.comp_mode != 'app':
        log_print_error
        ('Error, library installation mode is set to "app", but the main file is not compiled to an app'
         )
        exit(1)
      lib_dest = p.join(comp_units[0].installation_path, APP_LIBS_DIR)
    elif jxa_config.deps_install_mode == 'user':
      lib_dest = USER_LIBS_DIR_ABS
    elif jxa_config.deps_install_mode == "system":
      lib_dest = SYSTEM_LIBS_DIR_ABS
    comp_units.append(
        CompilationUnit(mirror_source, f'{p.join(output_dir, name_ver)}.scpt',
                        f'{p.join(lib_dest, name_ver)}.scpt'))

  with open(locations_file, 'w') as f:
    f.write(json.dumps([asdict(d) for d in comp_units], indent=2))

  logger.debug(f'Gathered compilation units: {comp_units}')
  logger.info('Compiling...')
  for unit in comp_units:
    command = [
        'osacompile', '-l', 'JavaScript', '-o', unit.output_path,
        unit.input_path
    ]
    try:
      subprocess.run(command, check=True, text=True)
    except subprocess.CalledProcessError as e:
      log_print_error(f'Something bad happened during compilation: {e}')
      exit(1)

  if jxa_config.comp_mode == 'app':
    logger.info('Modifying app internals...')
    modify_app_internals(comp_units[0].output_path, jxa_config.app_icon)
