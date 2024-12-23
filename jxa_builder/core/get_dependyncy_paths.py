from typing import List, Set, Iterable
from os import path as p
import re
from jxa_builder.utils.printit import log_print_error


def get_dependency_paths(
    source_path: str, extra_search_paths: Iterable = ()) -> List[str]:
  # Get library names from the source
  try:
    with open(source_path, 'r') as f:
      source = f.read()
  except Exception as e:
    log_print_error(f'Error, while reading source "{source_path}": {e}')
    exit(1)
  source = re.sub(r'//.*\n', '', source)
  source = re.sub(r'/\*[\s\S]*?\*/', '', source)
  libraries_rel: Set[str] = set(
      re.findall(r'Library\(["\'](.+?)["\']\)', source))

  libraries_abs: List[str] = []

  deps_search_paths = (
      p.dirname(source_path),
      p.dirname(source_path) + '/../node_modules',
      *extra_search_paths,
  )

  for lib_rel in libraries_rel:
    for deps_search_path in deps_search_paths:
      deps_search_abs = p.abspath(deps_search_path)
      lib_abs = p.abspath(p.join(deps_search_abs, lib_rel))

      if p.exists(lib_abs):
        libraries_abs.append(lib_abs)
        break  # found
      elif p.exists(lib_abs + '.js'):
        libraries_abs.append(lib_abs + '.js')
        break  # found
      else:
        if deps_search_abs == p.abspath(
            deps_search_paths[-1]):  # last iteration
          log_print_error(
              f'Could not find library "{lib_rel}": "{lib_abs}"\nMake sure it\'s actually installed if using a package manager (e.g. "npm install")'
          )
          exit(1)

  return libraries_abs


if __name__ == '__main__':
  print(
      get_dependency_paths(
          '/Users/sebastian/Documents/src/js/DoubleClickConsoleEdit/src/index.js'
      ))
