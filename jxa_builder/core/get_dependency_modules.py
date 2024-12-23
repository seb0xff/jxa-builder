from os import path as p
import re
from typing import List, Set
from jxa_builder.core.get_project_config import get_project_config
from jxa_builder.core.constants import DEPS_DIR, NODE_DIR
from jxa_builder.utils.printit import log_print_error
from jxa_builder.core.models import Module
from jxa_builder.utils.logger import logger


def get_dependency_modules(package_path: str) -> List[Module]:
  """Recursively get all dependencies"""
  dependencies = []
  if not p.exists(package_path):
    log_print_error(f'"{package_path}" does not exist')
    exit(1)
  if p.isdir(package_path):
    jxa_config = get_project_config(package_path)
    source = p.join(package_path, jxa_config.main)
  elif p.isfile(package_path):
    source = package_path

  ## Get library names from the source
  try:
    with open(source, 'r') as f:
      code = f.read()
  except Exception as e:
    log_print_error(f'Cannot read a source "{source}": {e}')
    exit(1)
  code = re.sub(r'//.*\n', '', code)
  code = re.sub(r'/\*[\s\S]*?\*/', '', code)
  libraries: Set[str] = set(re.findall(r'Library\(["\'](.+?)["\']\)', code))

  for lib in libraries:
    lib_path = p.join(p.dirname(source), lib)
    lib_path = p.abspath(p.realpath(lib_path))
    source_dir = p.dirname(lib_path)
    lib = p.basename(lib_path)

    # TODO: add global node_modules search path
    deps_search_paths = [
        source_dir,
        p.join(package_path, DEPS_DIR),
        p.join(package_path, NODE_DIR)
    ]
    for deps_search_path in deps_search_paths:
      lib_path = p.join(deps_search_path, lib)

      if p.exists(lib_path):
        lib_jxa_config = get_project_config(lib_path)
        lib_source = p.join(lib_path, lib_jxa_config.main)
        lib_version = lib_jxa_config.version
        dependencies.append(
            Module(name=lib,
                   source=lib_source,
                   version=lib_version,
                   dependant_source=source))
        dependencies += get_dependency_modules(lib_path)
        break  # found
      elif p.exists(lib_path + '.js'):
        lib_source = lib_path + '.js'
        dependencies.append(
            Module(name=lib,
                   source=lib_source,
                   version='',
                   dependant_source=source))
        dependencies += get_dependency_modules(lib_source)
        break  # found
      else:
        if deps_search_path == deps_search_paths[-1]:  # last iteration
          log_print_error(
              f'Could not find library "{lib}": "{lib_path}"\nIf you use a package manager, make sure it\'s actually installed(e.g. "npm list ")'
          )
          exit(1)
  logger.debug(f'Gathered dependencies: {dependencies}')
  return dependencies
