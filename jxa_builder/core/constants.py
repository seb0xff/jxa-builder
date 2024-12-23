from os import path as p, environ

IS_RICH = environ.get('JXA_BUILDER_CLASSIC_DISPLAY_MODE',
                      'false').lower() not in ('true', '1', 'yes')
APP_NAME = 'jxa-builder'
BUILD_DIR = 'build'
OUTPUT_DIR = p.join(BUILD_DIR, 'output')
PREPROCESSED_DIR = p.join(BUILD_DIR, 'preprocessed')
SYSTEM_ROOT_DIR = p.abspath(p.sep)
SYSTEM_TMP_DIR = p.join(SYSTEM_ROOT_DIR, 'private', 'tmp', APP_NAME)
SYSTEM_LIBS_DIR = p.join(SYSTEM_ROOT_DIR, 'Library', 'Script Libraries')
USER_DIR = p.expanduser('~')
USER_LIBS_DIR = p.join(USER_DIR, 'Library', 'Script Libraries')
LOCATIONS_FILE = p.join(BUILD_DIR, 'locations.json')
JXA_JSON_FILE = 'jxa.json'
PACKAGE_JSON_FILE = 'package.json'
LOG_FILE = p.join(USER_DIR, 'Library', 'Logs', f'{APP_NAME}.log')
