from os import path as p
import re
import glob
from dataclasses import dataclass
from pydantic import ValidationError
from typing import List, Set
from jxa_builder.core.get_project_config import get_project_config
from jxa_builder.utils.printit import log_print_error
from jxa_builder.core.models import Module


def get_dependency_modules(package_path: str) -> List[Module]:
  """Recursively get all dependencies"""
  dependencies = []
  if not p.exists(p.join(package_path)):
    log_print_error(f'Error, "{package_path}" does not exist')
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
    log_print_error(f'Error, while reading source "{source}": {e}')
    exit(1)
  code = re.sub(r'//.*\n', '', code)
  code = re.sub(r'/\*[\s\S]*?\*/', '', code)
  libraries: Set[str] = set(re.findall(r'Library\(["\'](.+?)["\']\)', code))

  # TODO: use glob module
  for lib in libraries:
    source_dir = p.dirname(source)
    ## Resolve relative paths
    while lib.startswith('../'):
      lib = lib[3:]
      source_dir = p.dirname(source_dir)
    # lib_path = p.join(source_dir, lib)

    # TODO: add global node_modules search path
    deps_search_paths = [
        source_dir,
        p.join(source_dir, 'dependencies'),
        p.join(package_path, 'node_modules')
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
            Module(
                name=lib,
                source=lib_source,
                # version=lib_version,
                version='',
                dependant_source=source))
        dependencies += get_dependency_modules(lib_source)
        break  # found
      else:
        if deps_search_path == deps_search_paths[-1]:  # last iteration
          log_print_error(
              f'Error, Could not find library "{lib}": "{lib_path}"\nMake sure it\'s actually installed if using a package manager (e.g. "npm install")'
          )
          exit(1)
  return dependencies
