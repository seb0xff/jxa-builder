from dataclasses import dataclass
from os import path as p
from typing import Optional, Literal, Union, Callable
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


@dataclass
class LoadedPropInfo:
  value: any
  origin: str
  original_name: Optional[str] = None


class JxaProjectConfig(BaseModel):
  model_config: ConfigDict = ConfigDict(
      # alias_generator=to_camel,
      str_strip_whitespace=True,
      extra='forbid',
      validate_default=True,
  )
  project_dir: str = Field(..., description="The project directory")
  comp_mode: Literal['app', 'script',
                     'bundle'] = Field('app',
                                       description="The compilation mode")
  deps_comp_mode: Literal['script', 'bundle'] = Field(
      'script', description="The dependencies compilation mode")
  deps_install_mode: Literal['app', 'user', 'system'] = Field(
      'app', description="The dependencies installation mode")
  version: Annotated[str, StringConstraints(pattern=SEM_VER)] = Field(
      '1.0.0', description="The version")
  app_name: str = Field('out', description="The application name")
  main: str = Field('index.js', description="The main script")
  app_icon: Optional[str] = Field(None, description="The application icon")

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
