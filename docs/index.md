# sevaht-utility

General-purpose Python utilities.

The library is small and focused. The most-used pieces are:

- **{mod}`sevaht_utility.naming`** — detect the words inside an identifier in any
  casing convention and convert it to another. See {doc}`guide/naming`.
- **{mod}`sevaht_utility.parsing`** — stream CSV rows into dicts or typed
  dataclasses, with flexible column-to-field mapping. See {doc}`guide/csv`.
- **{mod}`sevaht_utility.hinting`** — runtime inspection of type hints.
- **{mod}`sevaht_utility.log_utility`** — opinionated logging setup.

## Installation

```console
$ pip install sevaht-utility
```

Requires Python 3.12 or newer and has no runtime dependencies.

## Quick start

```python
from dataclasses import dataclass
from sevaht_utility.naming import convert_name, NameStyle
from sevaht_utility.parsing import csv_load, DataMapping

# Convert between casing styles.
convert_name("getHTTPResponseCode", style=NameStyle.SNAKE_CASE)
# -> 'get_http_response_code'

# Load CSV whose camelCase headers should feed snake_case fields.
@dataclass
class Person:
    full_name: str
    score_value: int

rows = ["fullName,scoreValue", "Ada,95"]
list(csv_load(rows, dataclass=Person, mapping=DataMapping(name_style=NameStyle.CAMEL_CASE)))
# -> [Person(full_name='Ada', score_value=95)]
```

```{toctree}
:hidden:
:caption: Guides

guide/naming
guide/csv
```

```{toctree}
:hidden:
:caption: API reference

reference/naming
reference/parsing
reference/hinting
reference/log_utility
```
