import os
from os import path as p
import shutil
import subprocess
import json
from typing import Literal, List
from jxa_builder.core.constants import SYSTEM_TMP_DIR_ABS, APPS_DIR_ABS
from jxa_builder.core.models import CompilationUnit
from jxa_builder.utils.printit import log_print_error, log_print_warning
from jxa_builder.utils.logger import logger

#TODO: Make it completely independent to the build command
# Instead of the locations file, gather deps in folders (the preprocessed folder)


def manage_outputs(action: Literal['install', 'uninstall'],
                   locations_file: str,
                   deps_only: bool = False):
  """
  Manage outputs (install/uninstall) by reading locations.json file.
  It will ask for administrator privileges if needed.
  
  Common func body for both install and uninstall commands
  """
  system_tmp = SYSTEM_TMP_DIR_ABS
  perm_problem = False
  shell_command = ''
  output_dir = ''
  if p.exists(locations_file):
    try:
      with open(locations_file, 'r') as f:
        locations: List[CompilationUnit] = json.load(
            f, object_hook=lambda d: CompilationUnit(**d))
    except Exception as e:
      log_print_error(f'Cannot read {locations_file}: {e}')
      exit(1)
    if deps_only:
      locations = [
          loc for loc in locations
          if p.dirname(loc.installation_path) != APPS_DIR_ABS
      ]
    for loc in locations:
      target = loc.output_path
      dest_file = loc.installation_path
      dest_file_dir = p.dirname(dest_file)
      if not output_dir:
        output_dir = p.dirname(target)
      if target != dest_file:
        try:
          if p.exists(dest_file) and p.exists(target):
            shutil.rmtree(dest_file) if p.isdir(dest_file) else os.remove(
                dest_file)
          if action == 'install' and p.exists(target):
            os.makedirs(dest_file_dir, exist_ok=True)
            shutil.copytree(
                target, dest_file_dir,
                dirs_exist_ok=True) if p.isdir(target) else shutil.copy(
                    target, dest_file_dir)
        ## - To perform action that needs sudo it will use constructed shell command
        ##   that is invoked by JXA's doShellScript with administrator privileges,
        ##   so convinient Touch ID can be used to authenticate (however sudo also works).
        ## - The shell command is used instead of running the python script itself
        ##   to avoid Operatin not permitted error (with admin privils home dir cannot be accessed).
        ## - Files to be installed are first copied to the system temporary directory
        ##   beacuse of the same reason as above.
        ##   More info: https://stackoverflow.com/a/68694914
        except Exception as e:
          # except PermissionError as e:
          target = p.join(system_tmp, p.basename(target))
          perm_problem = True
          ## The assembled command is executed later, so all the checks need to be done again
          shell_command += f'[ -e "{dest_file}" ] && [ -e "{target}" ] && rm -r "{dest_file}" || true;'  ## true to make exit code 0
          if action == 'install':
            shell_command += f'[ -e "{target}" ] && (mkdir -p "{dest_file_dir}" && mv "{target}" "{dest_file_dir}");'

    if perm_problem:
      jxa_command = f'''
      const app = Application.currentApplication();
      app.includeStandardAdditions = true;
      app.doShellScript('{shell_command}', {{
        administratorPrivileges: true,
        alteringLineEndings: false,
        withPrompt: "Administration privileges are needed to perform the task.\\nPlease enter your password:",
      }});
      '''
      logger.debug(f'JXA command: {jxa_command}')
      if action == 'install':
        try:
          shutil.copytree(output_dir, system_tmp, dirs_exist_ok=True)
        except Exception as e:
          log_print_error(
              f'Cannot copy output directory to temporary directory (system): {e}'
          )
          exit(1)
      try:
        subprocess.run(['osascript', '-l', 'JavaScript', '-e', jxa_command],
                       text=True)
      except subprocess.CalledProcessError as e:
        log_print_error(f'Cannot run {action} action: {e}')
        exit(1)
      if action == 'install':
        if p.exists(system_tmp):
          try:
            shutil.rmtree(system_tmp)
          except Exception as e:
            log_print_warning(
                f'Cannot delete temporary directory (system): {e}')

  else:
    log_print_error(f'Locations file: {locations_file} not found')
    exit(1)
