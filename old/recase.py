from typing import Literal


def recase(
    text: str, target_case: Literal['camel', 'constant', 'sentence', 'snake',
                                    'dot', 'kebab', 'path', 'pascal', 'header',
                                    'title']
) -> str:
  symbol_set = {' ', '.', '/', '_', '\\', '-'}
  words = []
  sb = ''
  is_all_caps = text.upper() == text

  for i in range(len(text)):
    char = text[i]
    next_char = text[i + 1] if i + 1 < len(text) else None

    if char in symbol_set:
      continue

    sb += char

    is_end_of_word = next_char is None or (
        next_char.isupper() and not is_all_caps) or next_char in symbol_set

    if is_end_of_word:
      words.append(sb)
      sb = ''

  if target_case == 'camel':
    words = [
        word.capitalize() if i > 0 else word.lower()
        for i, word in enumerate(words)
    ]
    return ''.join(words)
  elif target_case == 'constant':
    return '_'.join([word.upper() for word in words])
  elif target_case == 'sentence':
    words = [word.lower() for word in words]
    words[0] = words[0].capitalize()
    return ' '.join(words)
  elif target_case == 'snake':
    return '_'.join([word.lower() for word in words])
  elif target_case == 'dot':
    return '.'.join([word.lower() for word in words])
  elif target_case == 'kebab':
    return '-'.join([word.lower() for word in words])
  elif target_case == 'path':
    return '/'.join([word.lower() for word in words])
  elif target_case == 'pascal':
    words = [word.capitalize() for word in words]
    return ''.join(words)
  elif target_case == 'header':
    words = [word.capitalize() for word in words]
    return '-'.join(words)
  elif target_case == 'title':
    words = [word.capitalize() for word in words]
    return ' '.join(words)
  else:
    raise ValueError(f'Invalid target case: {target_case}')


# print(recase('HelloWorld_lol.edit.xd-hannoi', 'camel'))
# print(recase('PascalCase_HELLO_WORLD_lolDaDa', 'camel'))
