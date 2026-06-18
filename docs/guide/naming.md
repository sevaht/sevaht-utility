# Working with identifier names

{mod}`sevaht_utility.naming` answers a single question: *what are the words in
this identifier, and how do I rewrite them in another style?* It understands
`snake_case`, `kebab-case`, `camelCase`, `PascalCase`, and whitespace-separated
names, and it never needs to be told which one you handed it.

## Splitting a name into words

{func}`~sevaht_utility.naming.split_into_words` is the core. It scans the name
once and returns its component words, always lowercased.

```python
from sevaht_utility.naming import split_into_words

split_into_words("someSampleName")    # ['some', 'sample', 'name']
split_into_words("SomeSampleName")    # ['some', 'sample', 'name']
split_into_words("some_sample_name")  # ['some', 'sample', 'name']
split_into_words("some-sample-name")  # ['some', 'sample', 'name']
```

### How boundaries are detected

A new word begins at any of:

1. a **delimiter** — `-`, `_`, or whitespace (the delimiter itself is dropped);
2. a **lower-to-upper** transition — the `S` in `someSample`;
3. the **end of an acronym run** that flows into a lowercase word — see below.

Everything else extends the current word, and digits are treated as ordinary
non-uppercase characters (so `v2` stays one word).

### Acronyms

Run-together capitals are the hard case. A *single* acronym immediately
followed by a capitalized word is split correctly:

```python
split_into_words("HTTPServer")           # ['http', 'server']
split_into_words("userIDName")           # ['user', 'id', 'name']
split_into_words("getHTTPResponseCode")  # ['get', 'http', 'response', 'code']
```

The rule: when a run of two or more capitals is followed by a lowercase
letter, the **last** capital starts the new word (`HTTP` + `Server`), which is
the conventional behavior of most case libraries.

What is *not* attempted is splitting **consecutive** acronyms apart, because
doing so unambiguously requires a dictionary of known acronyms:

```python
split_into_words("XMLHTTPRequest")  # ['xmlhttp', 'request']  (not xml, http)
```

This is a deliberate limitation. When a specific run-together name matters —
for example a CSV header — map it explicitly instead of relying on the
heuristic; see {ref}`edge-case-names`.

## Rebuilding a name in another style

{func}`~sevaht_utility.naming.join_words` recombines words using a
{class}`~sevaht_utility.naming.NameStyle`, and
{func}`~sevaht_utility.naming.convert_name` is the convenient
split-then-join round trip.

```python
from sevaht_utility.naming import convert_name, join_words, NameStyle

convert_name("someSampleName", style=NameStyle.SNAKE_CASE)   # 'some_sample_name'
convert_name("user-id", style=NameStyle.PASCAL_CASE)         # 'UserId'
convert_name("HTTPServer", style=NameStyle.KEBAB_CASE)       # 'http-server'

join_words(["http", "server"], NameStyle.CAMEL_CASE)         # 'httpServer'
```

Because splitting normalizes everything to lowercase words,
`convert_name` is **idempotent** — converting an already-converted name leaves
it unchanged:

```python
once = convert_name("getHTTPResponseCode", style=NameStyle.PASCAL_CASE)
convert_name(once, style=NameStyle.PASCAL_CASE) == once  # True
```

Note that case information about acronyms is lost in the round trip: `HTTP`
becomes the ordinary word `http` and is re-capitalized as `Http`, never
restored to `HTTP`. If you need the original spelling preserved, keep it
out of the conversion.

See the {doc}`API reference <../reference/naming>` for full signatures.
