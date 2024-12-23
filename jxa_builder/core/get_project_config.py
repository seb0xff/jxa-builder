from typing import Optional, Literal, Dict, Callable, List, Dict, Tuple
import os
from os import path as p
import json
from pydantic import ValidationError
from jxa_builder.core.constants import PACKAGE_JSON_FILE, JXA_JSON_FILE
from jxa_builder.utils.remove_empty_values import remove_empty_values
from jxa_builder.utils.logger import logger
from jxa_builder.utils.recase import recase
from jxa_builder.utils.printit import log_print_error
from jxa_builder.core.models import JxaProjectConfig, SEM_VER, LoadedPropInfo
from jxa_builder.core.constants import IS_RICH


def get_json_obj(file_path: str) -> Dict[str, any]:
  if not p.exists(file_path):
    print(f'"{file_path}" does not exist.')
    return {}
  if not p.isfile(file_path):
    print(f'"{file_path}" is not a file.')
    return {}

  with open(file_path) as f:
    try:
      json_dict = json.load(f)
    except json.JSONDecodeError as e:
      error_msg = f'Invalid json syntax in "{file_path}" at line {e.lineno}, column {e.colno}: {e.msg}'
      log_print_error(error_msg)
      exit(1)
    if not isinstance(json_dict, dict):
      log_print_error
      (f'Invalid type in "{file_path}": Expected an object, got {type(json_dict)}'
       )
      exit(1)
  return json_dict


def get_project_config(
    project_dir: str,
    overrides: Optional[Dict[str, LoadedPropInfo]] = None) -> JxaProjectConfig:
  logger.debug(f'Getting project config of: {project_dir}')

  def to_snake_dict(d: Dict[str, any]) -> Dict[str, any]:
    return {recase(k, 'snake'): v for k, v in d.items()}

  properties: Dict[str, LoadedPropInfo] = {
      'project_dir':
      LoadedPropInfo(project_dir, 'function argument', 'project_dir')
  }

  package_json_file = p.join(project_dir, PACKAGE_JSON_FILE)
  jxa_json_file = p.join(project_dir, JXA_JSON_FILE)

  # package.json
  package_json = get_json_obj(package_json_file)
  package_json = {
      'app_name': package_json.get('name'),
      'version': package_json.get('version'),
      'main': package_json.get('main'),
  }
  package_json = remove_empty_values(package_json)
  if package_json:
    properties.update({
        k:
        LoadedPropInfo(v, package_json_file, recase(k, 'camel'))
        for k, v in package_json.items()
    })

  # package.json jxa property
  package_json = get_json_obj(package_json_file)
  package_json = remove_empty_values(package_json)
  package_json_jxa = package_json.get('jxa', {})
  package_json_jxa = to_snake_dict(package_json_jxa)
  if not isinstance(package_json_jxa, dict):
    log_print_error
    (f'Invalid type in "{package_json_file}": The "jxa" must be an object.')
    exit(1)
  if package_json_jxa:
    properties.update({
        k:
        LoadedPropInfo(v, f'{package_json_file} "jxa" property',
                       recase(k, 'camel'))
        for k, v in package_json_jxa.items()
    })

  # jxa.json
  jxa_json = get_json_obj(jxa_json_file)
  jxa_json = remove_empty_values(jxa_json)
  jxa_json = to_snake_dict(jxa_json)
  if jxa_json:
    properties.update({
        k: LoadedPropInfo(v, jxa_json_file, recase(k, 'camel'))
        for k, v in jxa_json.items()
    })

  # overrides
  if overrides:
    cli_dict = {k: v.value for k, v in overrides.items()}
    cli_dict = remove_empty_values(cli_dict)
    cli_dict = to_snake_dict(cli_dict)
    properties.update({
        k:
        LoadedPropInfo(v, overrides[k].origin, overrides[k].original_name)
        for k, v in cli_dict.items()
    })

  try:
    return JxaProjectConfig(**{k: v.value for k, v in properties.items()})
  except ValidationError as e:
    errors = e.errors()
    error_msg = f'\n{len(errors)} validation error(s)'
    for error in e.errors():
      prop = error['loc'][0]
      prop_info = properties[prop]
      error_msg += (f'\n[bold cyan]{prop_info.original_name}[/bold cyan]'
                    if IS_RICH else f'\n{prop_info.original_name}') + (
                        f" in {prop_info.origin}" if prop_info.origin else "")
      if error['type'] == 'extra_forbidden':
        error_msg += f'''\n  Unrecognized property (input value: '{error["input"]}')'''
      elif error['type'] == 'string_pattern_mismatch' and error['ctx'][
          'pattern'] == SEM_VER:
        error_msg += f'''\n  Input should be a valid semantic version (input value: '{error["input"]}')'''
      elif error['type'] == 'value_error':
        error_msg += f'''\n  {error["msg"][error["msg"].find(', ')+2:]} (input value: '{error["input"]}')'''
      else:
        error_msg += f'''\n  {error["msg"]} (input value: '{error["input"]}')'''

    log_print_error(error_msg)
    exit(1)
