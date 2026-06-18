# sevaht-utility

General-purpose utilities, including typed CSV loading.

## Documentation

Full documentation lives in `docs/` and is published to GitHub Pages:
<https://sevaht.github.io/sevaht-utility/>.

Highlights:

- **Naming** — detect the words in an identifier in any casing convention and
  convert it to another (`snake_case`, `kebab-case`, `camelCase`, `PascalCase`).
- **CSV** — stream rows into dicts or typed dataclasses, with flexible
  column-to-field mapping for awkward headers.

### Building the docs locally

```console
$ uv run --group docs sphinx-build -b html docs docs/_build/html
```

Then open `docs/_build/html/index.html`. (Publishing to GitHub Pages requires
enabling Pages with the "GitHub Actions" source in the repository settings.)
