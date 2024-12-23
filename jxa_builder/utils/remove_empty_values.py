from typing import Dict, Iterable, Optional


def remove_empty_values(
    d: Dict[str, any], *,
    exclude: Optional[Iterable] = (0, False)) -> Dict[str, any]:
  """Recursively remove empty values from a dictionary.
  Includes expressions that evaluate to False (e.g. [], (), {}, '', None, etc.), except values in `exclude`.

  Elements in iterables are not removed.

  Args:
      d (Dict[str, any]): The dictionary to remove empty values from.
      exclude (Optional[Iterable], optional): Values to exclude from removal. Defaults to (0, False).
  
  Example:
  ```python
  x = remove_empty_values({
      'a': 0,
      'b': None,
      'c': '',
      'd': {},
      'e': True,
      'f': ({}, 0, None, ()),
      'g': {
          'a': 1,
          'b': (),
          'c': {
              'a': [],
              'b': False
          }
      }
  })
  print(x)
  # {
  #    'a': 0,
  #    'e': True,
  #    'f': ({}, 0, None, ()),
  #    'g': {
  #        'a': 1,
  #        'c': {
  #            'b': False
  #        }
  #    }
  # }
  ```
  """
  return {
      k: remove_empty_values(v, exclude=exclude) if isinstance(v, dict) else v
      for k, v in d.items() if v or v == 0 or v in exclude
  }
