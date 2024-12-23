from os import path as p, environ
import importlib.util

IS_RICH = environ.get(
    'JXA_BUILDER_CLASSIC_DISPLAY_MODE',
    'false').lower() not in ('true', '1',
                             'yes') and importlib.util.find_spec('rich_click')
PROG_NAME = 'jxa-builder'
BUILD_DIR = 'build'
OUTPUT_DIR = p.join(BUILD_DIR, 'output')
PREPROCESSED_DIR = p.join(BUILD_DIR, 'preprocessed')
DEPS_DIR = 'dependencies'
NODE_DIR = 'node_modules'
SYSTEM_ROOT_DIR_ABS = p.abspath(p.sep)
SYSTEM_TMP_DIR_ABS = p.join(SYSTEM_ROOT_DIR_ABS, 'private', 'tmp', PROG_NAME)
USER_DIR_ABS = p.expanduser('~')
SYSTEM_LIBS_DIR_ABS = p.join(SYSTEM_ROOT_DIR_ABS, 'Library',
                             'Script Libraries')
USER_LIBS_DIR_ABS = p.join(USER_DIR_ABS, 'Library', 'Script Libraries')
APP_LIBS_DIR = p.join('Contents', 'Resources', 'Script Libraries')
APPS_DIR_ABS = p.join('/', 'Applications')
LOCATIONS_FILE = p.join(BUILD_DIR, 'locations.json')
JXA_JSON_FILE = 'jxa.json'
PACKAGE_JSON_FILE = 'package.json'
LOG_FILE_ABS = p.join(USER_DIR_ABS, 'Library', 'Logs', f'{PROG_NAME}.log')
