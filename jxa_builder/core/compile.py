from typing import Literal
import subprocess
from os import path as p
from jxa_builder.utils.printit import terminate_with_error


def compile(input_path: str,
            output_path: str,
            comp_mode: Literal['app', 'script', 'bundle'] = 'script'):

  input_path = p.abspath(input_path)
  output_path = p.abspath(output_path)
  if p.isdir(output_path):
    output_path = p.join(output_path, p.basename(p.splitext(input_path)[0]))

  if comp_mode == 'app':
    ext = '.app'
  elif comp_mode == 'script':
    ext = '.scpt'
  elif comp_mode == 'bundle':
    ext = '.scptd'
  else:
    raise ValueError('Invalid compilation mode: {comp_mode}')
  command = [
      'osacompile', '-l', 'JavaScript', '-o', output_path + ext, input_path
  ]
  try:
    subprocess.run(command, check=True, text=True)
  except subprocess.CalledProcessError as e:
    terminate_with_error(f'Error running osacompile: {e}')


if __name__ == '__main__':
  print('Compiling...')
  # compile('jxa_builder/../tests/test_jxa/index.js',
  #         'jxa_builder/../tests/build')
