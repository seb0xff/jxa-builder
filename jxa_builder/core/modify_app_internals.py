import re
import os
from os import path as p
import shutil
from typing import Optional
from jxa_builder.utils import terminate_with_error


def modify_app_internals(app_path: str, icon_path: Optional[str] = None):
  resources_path = p.join(app_path, 'Contents', 'Resources')
  macos_path = p.join(app_path, 'Contents', 'MacOS')
  info_plist_path = p.join(app_path, 'Contents', 'Info.plist')

  # Make pascal case from space separated, snake or kebab case string
  bundle_executable = ''.join(
      word[0].capitalize() + word[1:]
      for word in re.split(r'[\s_-]+', p.basename(app_path)))

  try:
    with open(info_plist_path, 'r') as file:
      info_plist = file.read()
  except Exception as e:
    terminate_with_error(f'Error, while reading Info.plist: {e}')
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
    terminate_with_error(f'Error, while writing Info.plist: {e}')
    exit(1)

  ## Rename bundle executable accordingly
  try:
    if p.exists(p.join(macos_path, default_bundle_executable)):
      os.rename(p.join(macos_path, default_bundle_executable),
                p.join(macos_path, bundle_executable))
  except Exception as e:
    terminate_with_error(f'Error, while renaming bundle executable: {e}')
    exit(1)

  ## Rename app resource files accordingly
  try:
    os.rename(p.join(resources_path, f'{default_bundle_executable}.icns'),
              p.join(resources_path, f'{bundle_executable}.icns'))
    os.rename(p.join(resources_path, f'{default_bundle_executable}.rsrc'),
              p.join(resources_path, f'{bundle_executable}.rsrc'))
  except Exception as e:
    terminate_with_error(f'Error, while renaming app resource files: {e}')
    exit(1)

  ## Copy icon to the app resources
  # TODO: make sure relative paths work
  if icon_path:
    try:
      shutil.copy2(
          icon_path,
          p.join(app_path, 'Contents', 'Resources',
                 f'{bundle_executable}.icns'))
    except Exception as e:
      terminate_with_error(
          f'Error, while copying icon to the app resources: {e}')
      exit(1)
