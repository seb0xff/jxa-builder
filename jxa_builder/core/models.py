from dataclasses import dataclass
from os import path as p
from typing import Optional, Literal, Union
from typing_extensions import Annotated, Self
from pydantic import (BaseModel, ConfigDict, StringConstraints, ValidationInfo,
                      Field, field_validator, model_validator)


@dataclass
class CompilationUnit:
  input_path: str
  output_path: str
  installation_path: str


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


#TODO: add bundle support
class JxaProjectConfig(BaseModel):
  model_config: ConfigDict = ConfigDict(
      str_strip_whitespace=True,
      extra='forbid',
      validate_default=True,
  )
  project_dir: str = Field(..., description="The project directory")
  comp_mode: Literal['app',
                     'script'] = Field('app',
                                       description="The compilation mode")
  deps_install_mode: Literal['app', 'user', 'system'] = Field(
      'app', description="The dependencies installation mode")
  version: Annotated[str, StringConstraints(pattern=SEM_VER)] = Field(
      '1.0.0', description="The version")
  app_name: str = Field('out', description="The application name")
  main: str = Field('index.js', description="The main script")
  app_icon: Optional[str] = Field(None, description="The application icon")

  @field_validator('project_dir')
  @classmethod
  def resolve_project_dir(cls, value: str) -> str:
    project_dir = p.abspath(value)
    if not p.exists(project_dir):
      raise ValueError(f'Path "{project_dir}" does not exist')
    if not p.isdir(project_dir):
      raise ValueError(f'Path "{project_dir}" is not a directory')

    return project_dir

  @field_validator('main')
  @classmethod
  def resolve_main_path(cls, value: str, info: ValidationInfo) -> str:
    project_dir = info.data['project_dir']
    main = p.join(project_dir, value)
    if not p.exists(main):
      raise ValueError(f'Path "{main}" does not exist')
    if not p.isfile(main):
      raise ValueError(f'Path "{main}" is not a file')

    return main

  @field_validator('app_icon')
  @classmethod
  def resolve_icon_path(cls, value: Optional[str],
                        info: ValidationInfo) -> Optional[str]:
    project_dir = info.data['project_dir']
    if value:
      app_icon = p.join(project_dir, value)
      if not p.exists(app_icon):
        raise ValueError(f'Path "{app_icon}" does not exist')
      if not p.isfile(app_icon):
        raise ValueError(f'Path "{app_icon}" is not a file')
    elif p.exists(p.join(project_dir, 'icon.icns')):
      app_icon = p.join(project_dir, 'icon.icns')
    elif p.exists(p.join(project_dir, info.data['app_name'] + '.icns')):
      app_icon = p.join(project_dir, 'icon.icns')
    else:
      app_icon = None

    return app_icon

  @model_validator(mode='after')
  def validate_model(self) -> Self:
    if self.deps_install_mode == 'app' and not self.comp_mode == 'app':
      raise ValueError(
          'Dependencies installation mode "app" is only available for compilation mode "app"'
      )
