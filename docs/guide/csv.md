# Loading CSV data

{func}`~sevaht_utility.parsing.csv_load` streams rows from a CSV source into
either plain dictionaries or typed dataclass instances. Rows are produced
lazily, so even very large files are handled a row at a time, and blank lines
are skipped.

## Reading from different sources

The `source` can be anything in {data}`~sevaht_utility.parsing.TextProvider`: a
single string, a {class}`~pathlib.Path`, an already-open text stream, or a list
of lines. All four behave identically:

```python
from io import StringIO
from pathlib import Path
from sevaht_utility.parsing import csv_load

csv_load("name,score\nAda,95")          # one string
csv_load(["name,score", "Ada,95"])      # list of lines
csv_load(Path("people.csv"))            # a file path
csv_load(StringIO("name,score\nAda,95"))  # an open stream
```

Each returns a lazy iterator; wrap it in `list(...)` to materialize, or iterate
it directly. The examples below use lists of lines for brevity.

## Dictionaries

With no `dataclass`, the first row is the header and each later row becomes a
`dict[str, str]` (values are left as strings):

```python
list(csv_load(["name,score", "Ada,95", "Linus,88"]))
# [{'name': 'Ada', 'score': '95'}, {'name': 'Linus', 'score': '88'}]
```

## Dataclasses with typed fields

Pass a `dataclass` and each row is constructed into an instance, with every
cell converted to the field's annotated type:

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    score: int

list(csv_load(["name,score", "Ada,95"], dataclass=Person))
# [Person(name='Ada', score=95)]
```

## Converting cell values

### Built-in types and unions

`str`, `int`, `float`, and `bool` are converted out of the box. A union is tried
left to right, so annotate a column that holds mixed data accordingly. With
`int | str`, numeric cells become `int` and the rest stay `str`:

```python
@dataclass
class Item:
    id: int | str
    quantity: int

list(csv_load(["id,quantity", "7,3", "abc,5"], dataclass=Item))
# [Item(id=7, quantity=3), Item(id='abc', quantity=5)]
```

### Booleans

A `bool` field accepts `1`, `true`, or `yes` (case-insensitively) as true;
everything else is false (see {func}`~sevaht_utility.parsing.parse_bool`):

```python
@dataclass
class Flag:
    name: str
    enabled: bool

list(csv_load(["name,enabled", "wifi,Yes", "bt,0"], dataclass=Flag))
# [Flag(name='wifi', enabled=True), Flag(name='bt', enabled=False)]
```

### Custom types with `from_string`

Give a type a `from_string` classmethod and it is used automatically to convert
that field's cells:

```python
@dataclass
class Temperature:
    celsius: float

    @classmethod
    def from_string(cls, value: str) -> "Temperature":
        return cls(float(value.removesuffix("C")))

@dataclass
class Reading:
    label: str
    temp: Temperature

list(csv_load(["label,temp", "noon,21.5C"], dataclass=Reading))
# [Reading(label='noon', temp=Temperature(celsius=21.5))]
```

### Registering a converter for a type you do not own

When you cannot add `from_string` to a type (it is third-party, or you want
different behavior per load), register a converter on a
{class}`~sevaht_utility.parsing.StringParser` and pass it via
{class}`~sevaht_utility.parsing.CsvLoadOptions`:

```python
from sevaht_utility.parsing import CsvLoadOptions, StringParser

parser = StringParser()
parser.set_converter(complex, converter=complex)  # built-in complex()

@dataclass
class Signal:
    name: str
    value: complex

list(csv_load(["name,value", "a,1+2j"], dataclass=Signal,
              options=CsvLoadOptions(string_parser=parser)))
# [Signal(name='a', value=(1+2j))]
```

## Computing fields per row

### Derived fields with `InitVar` and `__post_init__`

Use `InitVar` for cells that feed `__post_init__` but are not stored directly,
and `field(init=False, ...)` for values computed from them. Each `InitVar` is
matched to a column like any other field:

```python
from dataclasses import dataclass, field, InitVar

@dataclass
class Scores:
    name: str
    total: int = field(init=False, default=0)
    first: InitVar[int] = 0
    second: InitVar[int] = 0

    def __post_init__(self, first: int, second: int) -> None:
        self.total = first + second

list(csv_load(["name,first,second", "Ada,3,4"], dataclass=Scores))
# [Scores(name='Ada', total=7)]
```

### A custom factory with `init_function`

Supply `init_function` to build each row yourself instead of calling the
constructor directly. Its parameter names are matched to columns and its
annotations drive conversion. Pair it with `dataclass=` so the result is typed:

```python
@dataclass
class Person:
    name: str
    score: int

def make_person(name: str, score: int) -> Person:
    return Person(name=name.title(), score=score + 100)  # bonus points

list(csv_load(["name,score", "ada,95"], dataclass=Person,
              init_function=make_person))
# [Person(name='Ada', score=195)]
```

In dict mode (no `dataclass`), an `init_function` returns a dict; its annotated
parameters still drive conversion, which lets you add derived keys:

```python
def to_record(name: str, score: int) -> dict[str, object]:
    return {"name": name, "score": score, "passed": score >= 50}

list(csv_load(["name,score", "Ada,40"], init_function=to_record))
# [{'name': 'Ada', 'score': 40, 'passed': False}]
```

### Default values for absent columns

Fields with defaults need not appear in the CSV; missing columns simply keep
their default:

```python
@dataclass
class Config:
    host: str
    port: int = 8080

list(csv_load(["host", "example.com"], dataclass=Config))
# [Config(host='example.com', port=8080)]
```

## Reader options

{class}`~sevaht_utility.parsing.CsvLoadOptions` and
{class}`~sevaht_utility.parsing.DataMapping` cover the *how* and the *what* of a
load, respectively.

### A different delimiter

Set `delimiter` for tab- or pipe-separated data:

```python
list(csv_load(["a\tb", "1\t2"], options=CsvLoadOptions(delimiter="\t")))
# [{'a': '1', 'b': '2'}]
```

### Data with no header row

Provide `column_names` to name the columns positionally; every row is then
treated as data:

```python
from sevaht_utility.parsing import DataMapping

list(csv_load(["1,2,3", "4,5,6"],
              mapping=DataMapping(column_names=["a", "b", "c"])))
# [{'a': '1', 'b': '2', 'c': '3'}, {'a': '4', 'b': '5', 'c': '6'}]
```

### Requiring every column to be used

By default, columns that match no field are ignored. Set
`allow_column_subset=False` to raise
{exc}`~sevaht_utility.parsing.UnconsumedColumnsError` instead when a column goes
unused:

```python
mapping = DataMapping(field_to_column_name={"x": "a"})
options = CsvLoadOptions(allow_column_subset=False)
list(csv_load(["a,b", "1,2"], mapping=mapping, options=options))
# UnconsumedColumnsError: 1 columns were not consumed: b
```

(edge-case-names)=

## Mapping columns to fields for edge-case names

By default a column feeds the field with the same name. When the header text
does not line up with your field names, describe the mapping with a
{class}`~sevaht_utility.parsing.DataMapping`. When several rules could apply the
precedence is, highest first:

1. `field_to_column_index`
2. `field_to_column_name`
3. field / parameter names
4. dataclass field metadata
5. raw column names (dict mode)

### Differently-cased headers

Real exports often use `camelCase` or `PascalCase` headers while your fields
are `snake_case`. Set `name_style` and both sides are normalized before
matching (see {doc}`naming`).

Both the source columns *and* the destination field names are converted to
`name_style` before they are compared. Normalizing the destination names is the
important part: it means your dataclass can keep idiomatic PEP 8 `snake_case`
members regardless of how the file is cased. You do not rename your fields to
match the header — you name them properly and let the comparison happen in a
common style.

```python
from sevaht_utility.naming import NameStyle

@dataclass
class Person:
    full_name: str
    score_value: int

rows = ["fullName,scoreValue", "Ada,95"]
list(csv_load(rows, dataclass=Person,
              mapping=DataMapping(name_style=NameStyle.CAMEL_CASE)))
# [Person(full_name='Ada', score_value=95)]
```

### A header that differs per field (metadata)

When only one field has an awkward header, annotate just that field. By default
the metadata key is `csv_key` (configurable via
{class}`~sevaht_utility.parsing.CsvLoadOptions`):

```python
@dataclass
class Row:
    identifier: int = field(metadata={"csv_key": "ID"})
    label: str = ""

list(csv_load(["ID,label", "7,hello"], dataclass=Row))
# [Row(identifier=7, label='hello')]
```

### Arbitrary header text

For headers that share nothing with the field names, map them explicitly with
`field_to_column_name`:

```python
@dataclass
class Account:
    user_id: int
    balance: float

mapping = DataMapping(field_to_column_name={"user_id": "acct#", "balance": "$$$"})
list(csv_load(["acct#,$$$", "42,9.99"], dataclass=Account, mapping=mapping))
# [Account(user_id=42, balance=9.99)]
```

### Duplicate or ambiguous headers

When two columns share a name (or normalize to the same name), matching by name
is ambiguous and raises
{exc}`~sevaht_utility.parsing.AmbiguousColumnNamesError`. Disambiguate by
pinning fields to explicit zero-based column indices, the highest-precedence
rule:

```python
@dataclass
class Pair:
    first_a: int
    second_a: int

mapping = DataMapping(
    field_to_column_name={"first_a": "a", "second_a": "a"},
    field_to_column_index={"first_a": 0, "second_a": 1},
)
list(csv_load(["a,a,b", "1,2,3"], dataclass=Pair, mapping=mapping))
# [Pair(first_a=1, second_a=2)]
```

This is the recommended escape hatch for the run-together acronym names that
{func}`~sevaht_utility.naming.split_into_words` intentionally leaves merged: map
the column directly rather than relying on the splitter.

See the {doc}`API reference <../reference/parsing>` for the full set of options
and the exceptions each mismatch raises.
