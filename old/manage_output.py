from dataclasses import dataclass
import os
from os import path as p
import shutil
import subprocess
import json
from typing import Literal


def manage_outputs(action: Literal['install', 'uninstall'],
                   locations_file: str,
                   exit_after: bool = False):
  system_tmp = p.join('/private', 'tmp', 'jxa-builder')
  perm_problem = False
  shell_command = ''
  output_dir = ''
  if p.exists(locations_file):
    try:
      with open(locations_file, 'r') as f:
        locations: dict[str, str] = json.load(f)
    except Exception as e:
      print(f'Error, while reading {locations_file}: {e}')
      exit(1)
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
          print(
              f'Error, while copying output directory to the temporary (system) directory: {e}'
          )
          exit(1)
      try:
        process = subprocess.run(
            ['osascript', '-l', 'JavaScript', '-e', jxa_command], text=True)
      except subprocess.CalledProcessError as e:
        print(f'Error, while running {action}: {e}')
        exit(1)
      if action == 'install':
        if p.exists(system_tmp):
          try:
            shutil.rmtree(system_tmp)
          except Exception as e:
            print(f'Error, while deleting temporary (system) directory: {e}')
            exit(1)
  else:
    print(f'Error, {locations_file} not found')
    exit(1)
  if exit_after:
    exit(0)
