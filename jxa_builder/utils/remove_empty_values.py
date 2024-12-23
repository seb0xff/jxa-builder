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
  """
  if not isinstance(d, Dict):
    raise ValueError(f'Expected a dictionary, got {type(d)}')
  return {
      k: remove_empty_values(v, exclude=exclude) if isinstance(v, Dict) else v
      for k, v in d.items() if v or v == 0 or v in exclude
  }
