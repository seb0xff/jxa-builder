from dataclasses import dataclass
from os import path as p
from typing import Optional, Literal, Union
from typing_extensions import Annotated
from pydantic import (BaseModel, ConfigDict, StringConstraints, ValidationInfo,
                      Field, field_validator, computed_field)
from pydantic.alias_generators import to_camel, to_snake


@dataclass
class CompilationUnit:
  input_path: str
  output_path: str


@dataclass
class Module:
  name: str
  source: str
  version: str
  dependant_source: Optional[str] = None


SEM_VER = r'^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'


def _does_path_exist(path: Optional[str] = None,
                     info: Optional[ValidationInfo] = None) -> bool:
  if path:
    path = p.abspath(path)
    package_dir = info.data['project_dir']
    abs_path = p.join(package_dir, path)

    if not p.exists(abs_path):
      raise ValueError(f'Path "{path}" does not exist')
  return path


class JxaProjectConfig(BaseModel):
  model_config: ConfigDict = ConfigDict(
      alias_generator=to_camel,
      str_strip_whitespace=True,
      extra='forbid',
      validate_default=True,
  )
  project_dir: str
  comp_mode: Literal['app', 'script', 'bundle'] = 'app'
  deps_comp_mode: Literal['script', 'bundle'] = 'script'
  deps_install_mode: Literal['app', 'user', 'system'] = 'app'
  version: Annotated[str, StringConstraints(pattern=SEM_VER)] = '1.0.0'
  app_name: str = 'out'
  main: str = 'index.js'
  app_icon: Optional[str] = None

  @field_validator('project_dir')
  @classmethod
  def project_dir_must_exist(cls, value: str) -> str:
    abs_path = p.abspath(value)
    if not p.exists(abs_path):
      raise ValueError(f'Path "{abs_path}" does not exist')
    if not p.isdir(abs_path):
      raise ValueError(f'Path "{abs_path}" is not a directory')
    return abs_path

  @field_validator('main', 'app_icon')
  @classmethod
  def path_must_exist(cls, value: Union[str, None],
                      info: ValidationInfo) -> str:
    if value:
      package_dir = info.data['project_dir']
      abs_path = p.join(package_dir, value)

      if not p.exists(abs_path):
        raise ValueError(f'Path "{abs_path}" does not exist')
      if not p.isfile(abs_path):
        raise ValueError(f'Path "{abs_path}" is not a file')
      return value


try:
  config = JxaProjectConfig(
      projectDir='/Users/sebastian/Documents/src/js/DoubleClickConsoleEdit',
      main='src/index.js',
      appIcon='icon.icns')
  print(config.model_dump_json(indent=2))
except Exception as e:
  print(e)
