from typing import Optional, Literal, Dict, Callable
from typing_extensions import Annotated
import os
from os import path as p
import json
from pydantic import (BaseModel, ConfigDict, ValidationError,
                      StringConstraints, field_validator)
from pydantic.alias_generators import to_camel, to_snake
from jxa_builder.core.constants import PACKAGE_JSON_FILE, JXA_JSON_FILE
from jxa_builder.utils.remove_empty_values import remove_empty_values
from jxa_builder.utils.logger import logger
from jxa_builder.utils.printit import terminate_with_error
from jxa_builder.core.models import JxaProjectConfig, SEM_VER


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
      terminate_with_error(error_msg)
    if not isinstance(json_dict, dict):
      terminate_with_error(
          f'Invalid type in "{file_path}": Expected an object, got {type(json_dict)}'
      )
  return json_dict


ErrorsNumber = int
OriginalName = str


def validate_dict_with_model(
    json_obj: Dict[str, any],
    *,
    error_msg_header: Optional[Callable[[ErrorsNumber], str]] = None,
    prop_alt_name: Optional[Callable[[OriginalName], str]] = None,
):
  try:
    logger.debug(f'Validating: {json_obj}')
    JxaProjectConfig(**json_obj)
  except ValidationError as e:
    errors = e.errors()
    error_msg = ''
    if error_msg_header:
      error_msg += error_msg_header(len(errors))
    else:
      error_msg += f'\n{len(errors)} validation error(s)'
    for error in e.errors():
      prop = error['loc'][0]
      if prop_alt_name:
        prop = prop_alt_name(prop)
      error_msg += f'\n{prop}'
      if error['type'] == 'extra_forbidden':
        error_msg += f'''\n  Unrecognized property (input value: '{error["input"]}')'''
      elif error['type'] == 'string_pattern_mismatch' and error['ctx'][
          'pattern'] == SEM_VER:
        error_msg += f'''\n  Input should be a valid semantic version (input value: '{error["input"]}')'''
      elif error['type'] == 'value_error':
        error_msg += f'''\n  {error["msg"][error["msg"].find(', ')+2:]} (input value: '{error["input"]}')'''
      else:
        error_msg += f'''\n  {error["msg"]} (input value: '{error["input"]}')'''

    terminate_with_error(error_msg)


def cmd_args_override(cmd_overrides: Dict[str, any]) -> Dict[str, any]:
  if cmd_overrides:
    cmd_overrides = {to_camel(k): v for k, v in cmd_overrides.items()}
    cmd_overrides = remove_empty_values(cmd_overrides)
    to_kebab = lambda s: s.replace('_', '-')
    validate_dict_with_model(
        cmd_overrides,
        error_msg_header=lambda n:
        f'{n} validation error(s) in command line arguments',
        prop_alt_name=lambda s: f'--{to_kebab(to_snake(s))}',
    )
  return cmd_overrides


def get_project_config(
    project_dir: str,
    override_func: Optional[Callable[..., Dict[str, any]]] = None
) -> 'JxaProjectConfig':
  logger.debug(f'Getting project config of: {project_dir}')
  if not p.exists(project_dir):
    terminate_with_error(f'"{project_dir}" does not exist')
  if not p.isdir(project_dir):
    terminate_with_error(f'"{project_dir}" is not a directory')

  package_json_file = p.join(project_dir, PACKAGE_JSON_FILE)
  jxa_json_file = p.join(project_dir, JXA_JSON_FILE)
  project_config = JxaProjectConfig()

  # package.json
  package_json = get_json_obj(package_json_file)
  name = package_json.get('name')
  version = package_json.get('version')
  main = package_json.get('main')
  package_json = {'appName': name, 'version': version, 'main': main}
  package_json = remove_empty_values(package_json)
  if package_json:
    validate_dict_with_model(
        package_json,
        error_msg_header=lambda n:
        f'{n} validation error(s) in "{package_json_file}"',
    )
    project_config = project_config.model_copy(update=package_json)

  # package.json jxa property
  package_json = get_json_obj(package_json_file)
  package_json = remove_empty_values(package_json)
  package_json_jxa = package_json.get('jxa', {})
  if not isinstance(package_json_jxa, dict):
    terminate_with_error(
        f'Invalid type in "{package_json_file}": The "jxa" must be an object.')
  if package_json_jxa:
    validate_dict_with_model(
        package_json_jxa,
        error_msg_header=lambda n:
        f'{n} validation error(s) in "{package_json_file}"',
        prop_alt_name=lambda s: f'jxa.{s}',
    )
    project_config = project_config.model_copy(update=package_json_jxa)

    # jxa.json
    jxa_json = get_json_obj(jxa_json_file)
    jxa_json = remove_empty_values(jxa_json)
    if jxa_json:
      validate_dict_with_model(
          jxa_json,
          error_msg_header=lambda n:
          f'{n} validation error(s) in "{jxa_json_file}"',
      )
      project_config = project_config.model_copy(update=jxa_json)

    # overrides
    if override_func:
      overrides = override_func()
      if overrides:
        project_config = project_config.model_copy(update=overrides)
  return project_config
