# Contributing to StructExtract

Thanks for your interest in contributing!

## Setup

```bash
# Clone the repo
git clone https://github.com/<your-fork>/structextract.git
cd structextract

# Install the package in editable mode
pip install -e .

# Install all dependencies (runtime + dev)
pip install -r requirements.txt
```

## Running tests

```bash
pytest tests/
```

All tests are monkeypatched — no real API key is required to run them.

## Code style

No linter is enforced. Please follow these conventions:

- Keep functions small and focused (single responsibility)
- Add type hints to all function signatures
- Prefer explicit over implicit; avoid magic
- Do not add third-party dependencies without discussing in an issue first

## Making changes

1. Branch off `main`: `git checkout -b my-feature`
2. One feature or fix per PR — keep diffs small and reviewable
3. Make sure `pytest tests/` passes before opening a PR
4. Write a clear PR description explaining *what* and *why*

## Reporting issues

Please open an issue on GitHub Issues with:

- A minimal reproducible example
- The document type (txt / pdf / html / md)
- The schema you are using
- The full error traceback (if applicable)
