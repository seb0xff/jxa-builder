import os
from os import path as p
import shutil
from jxa_builder.core.get_dependency_modules import get_dependency_modules
from jxa_builder.core.get_project_config import get_project_config
from jxa_builder.core.constants import DEPS_DIR, NODE_DIR
from jxa_builder.utils.click_importer import click
from jxa_builder.utils.printit import log_print_error
from jxa_builder.commands._shared_options import debug_option, project_dir_option


@click.command(
    help=
    'Copy nodejs dependencies to the dependencies directory. It is useful when the target needs to be built on a machine without nodejs installed.'
)
@project_dir_option
@debug_option
def freeze_nodejs_deps(project_dir: str):
  jxa_config = get_project_config(project_dir)

  dependency_modules = get_dependency_modules(project_dir)

  if freeze_nodejs_deps:
    for dep in dependency_modules:
      try:
        if NODE_DIR in dep.source and p.exists(dep.source):
          node_modules = p.join(jxa_config.project_dir, NODE_DIR)
          for root, dirs, _ in os.walk(node_modules):
            for d in dirs:
              if d == dep.name:
                shutil.copytree(p.join(root, d),
                                p.join(jxa_config.project_dir, DEPS_DIR,
                                       dep.name),
                                dirs_exist_ok=True)
                break
          if not p.exists(p.join(jxa_config.project_dir, DEPS_DIR)):
            os.makedirs(p.join(jxa_config.project_dir, DEPS_DIR))
      except Exception as e:
        log_print_error(f'Cannot copy nodejs dependency: {dep}: {e}')
        exit(1)
