import os
from os import path as p
import shutil
import subprocess
import json
from typing import Literal
from jxa_builder.core.constants import SYSTEM_TMP_DIR
from jxa_builder.utils.printit import terminate_with_error

# TODO: include traceback using incl_traceback=True


def manage_outputs(action: Literal['install', 'uninstall'],
                   locations_file: str):
  """
  Manage outputs (install/uninstall) by reading locations.json file.
  It will ask for administrator privileges if needed.
  
  Common body for both install and uninstall commands
  """
  system_tmp = SYSTEM_TMP_DIR
  perm_problem = False
  shell_command = ''
  output_dir = ''
  if p.exists(locations_file):
    try:
      with open(locations_file, 'r') as f:
        locations: dict[str, str] = json.load(f)
    except Exception as e:
      terminate_with_error(f'Cannot read {locations_file}: {e}')
    for target, install_path in locations.items():
      if not output_dir:
        output_dir = p.dirname(target)
      dest_file = p.join(install_path, p.basename(target))
      if target != dest_file:
        try:
          if p.exists(dest_file):
            shutil.rmtree(dest_file) if p.isdir(dest_file) else os.remove(
                dest_file)
          if action == 'install':
            os.makedirs(install_path, exist_ok=True)
            shutil.copytree(target,
                            install_path) if p.isdir(target) else shutil.copy(
                                target, install_path)
        ## - To perform action that needs sudo it will use constructed shell command
        ##   that is invoked by JXA's doShellScript with administrator privileges,
        ##   so convinient Touch ID can be used to authenticate (sudo still works too).
        ## - The shell command is used instead of running the python script itself
        ##   to avoid Operatin not permitted error (with admin privils home dir cannot be accessed).
        ## - Files to be installed are first copied to the system temporary directory
        ##   beacuse of the same reason as above.
        ##   More info: https://stackoverflow.com/a/68694914
        except PermissionError as e:
          perm_problem = True
          shell_command += f'[ -e "{dest_file}" ] && rm -r "{dest_file}";'
          if action == 'install':
            target = p.join(system_tmp, p.basename(target))
            shell_command += f'mkdir -p "{install_path}" && mv "{target}" "{install_path}";'

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
      if action == 'install':
        try:
          shutil.copytree(output_dir, system_tmp, dirs_exist_ok=True)
        except Exception as e:
          terminate_with_error(
              f'Cannot copy output directory to temporary directory (system): {e}'
          )
      try:
        subprocess.run(['osascript', '-l', 'JavaScript', '-e', jxa_command],
                       text=True)
      except subprocess.CalledProcessError as e:
        terminate_with_error(f'Cannot run {action} action: {e}')
      if action == 'install':
        if p.exists(system_tmp):
          try:
            shutil.rmtree(system_tmp)
          except Exception as e:
            terminate_with_error(
                f'Cannot delete temporary directory (system): {e}')
  else:
    terminate_with_error(f'Locations file: {locations_file} not found')
