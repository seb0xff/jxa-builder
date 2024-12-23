import re
import os
from os import path as p
import shutil
from typing import Optional
from jxa_builder.utils.recase import recase
from jxa_builder.utils.printit import log_print_error


def modify_app_internals(app_path: str, icon_path: Optional[str] = None):
  resources_path = p.join(app_path, 'Contents', 'Resources')
  macos_path = p.join(app_path, 'Contents', 'MacOS')
  info_plist_path = p.join(app_path, 'Contents', 'Info.plist')

  bundle_executable = recase(p.basename(app_path), 'pascal')

  try:
    with open(info_plist_path, 'r') as file:
      info_plist = file.read()
  except Exception as e:
    log_print_error(f'Cannot read the Info.plist: {e}')
    exit(1)

  default_bundle_executable = re.search(
      r'(<key>CFBundleExecutable</key>\s+<string>)(\w+?)(</string>)',
      info_plist).group(2)

  ## Replace bundle executable name
  info_plist = re.sub(
      r'(<key>CFBundleExecutable</key>\s+<string>)\w+?(</string>)',
      f'\\g<1>{bundle_executable}\\g<2>', info_plist)

  ## Replace bundle icon name
  info_plist = re.sub(
      r'(<key>CFBundleIconFile</key>\s+<string>)\w+?(</string>)',
      f'\\g<1>{bundle_executable}.icns\\g<2>', info_plist)

  try:
    with open(info_plist_path, 'w') as f:
      f.write(info_plist)
  except Exception as e:
    log_print_error(f'Cannot write to the Info.plist: {e}')
    exit(1)

  ## Rename bundle executable accordingly
  try:
    if p.exists(p.join(macos_path, default_bundle_executable)):
      os.rename(p.join(macos_path, default_bundle_executable),
                p.join(macos_path, bundle_executable))
  except Exception as e:
    log_print_error(f'Cannot rename the bundle executable: {e}')
    exit(1)

  ## Rename app resource files accordingly
  try:
    os.rename(p.join(resources_path, f'{default_bundle_executable}.icns'),
              p.join(resources_path, f'{bundle_executable}.icns'))
    os.rename(p.join(resources_path, f'{default_bundle_executable}.rsrc'),
              p.join(resources_path, f'{bundle_executable}.rsrc'))
  except Exception as e:
    log_print_error(f'Cannot rename the app resource files: {e}')
    exit(1)

  ## Copy icon to the app resources
  if icon_path:
    try:
      shutil.copy2(
          icon_path,
          p.join(app_path, 'Contents', 'Resources',
                 f'{bundle_executable}.icns'))
    except Exception as e:
      log_print_error(f'Cannot copy the icon to the app resources: {e}')
      exit(1)
