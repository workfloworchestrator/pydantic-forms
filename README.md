# Pydantic forms

[![pypi_version](https://img.shields.io/pypi/v/pydantic-forms?color=%2334D058&label=pypi%20package)](https://pypi.org/project/pydantic-forms)
[![Supported python versions](https://img.shields.io/pypi/pyversions/pydantic-forms.svg?color=%2334D058)](https://pypi.org/project/pydantic-forms)
[![Downloads](https://static.pepy.tech/badge/pydantic-forms/month)](https://pepy.tech/project/pydantic-forms)
[![codecov](https://codecov.io/gh/workfloworchestrator/pydantic-forms/branch/main/graph/badge.svg?token=AJMOSWPHQX)](https://codecov.io/gh/workfloworchestrator/pydantic-forms)

A Python package that lets you add smart forms to [FastAPI](https://fastapi.tiangolo.com/)
and [Flask](https://palletsprojects.com/p/flask/). Forms will respond with a JSON scheme that
contains all info needed in a React frontend with uniforms to render the forms and handle all validation tasks.

Forms can also consist out of a wizard, so you can create complex form flows consisting out of multiple
consecutive forms. The forms and the validation logic are defined by
using [Pydantic](https://pydantic-docs.helpmanual.io/) models.

Documentation regarding the usage of Forms can be found at
[workfloworchestrator.org/pydantic-forms](https://workfloworchestrator.org/pydantic-forms/).

### Installation (Development standalone)

This project uses [uv](https://docs.astral.sh/uv/). Install the project and its dependencies to develop on the code:

```shell
uv sync --all-extras
```

This creates a `.venv`, installs `pydantic-forms` in editable mode, and installs the `dev` dependency group
(which chains in `test` and `doc`) plus the `fastapi` and `orjson` extras. There is no need to create or
activate a virtualenv yourself -- prefix commands with `uv run` and uv will use the right interpreter.

### Running tests
Run the unit-test suite to verify a correct setup.

```shell
uv run pytest tests/unit_tests
```

or with xdist:

```shell
uv run pytest -n auto tests/unit_tests
```

If you do not encounter any failures in the test, you should be able to develop features in the pydantic-forms.

### Installation (Development version used by a project that depends on pydantic-forms)

If you are working on a project that already uses `pydantic-forms` and you want to test your new form features
against it, point that project at your local checkout. Run this **from the other project**:

```shell
uv add --editable /path/to/pydantic-forms
```

This replaces the PyPI dependency with an editable install of your working copy and records it under
`[tool.uv.sources]` in that project's `pyproject.toml`. Undo it with:

```shell
uv remove pydantic-forms && uv add pydantic-forms
```

# Increasing the version number for a (pre) release.

When your PR is accepted you will get a version number.

You can do the necessary change with a clean, e.g. every change committed, branch:

```shell
uv version 0.0.1
```

Note: specifying the version explicitly, instead of relying on `uv version --bump patch` to increase it, allows
you to set a "RC1" version if needed -- e.g. `uv version 0.0.1rc1`.

# Debugging Form behaviour

If you want/need the traceback of pydantic in a Form response you can add an env variable:

`
LOG_LEVEL_PYDANTIC_FORMS=DEBUG
`

This will add the traceback to the `JSONResponse`. If the loglevel is set to DEBUG the library will also add the
traceback to the logger.
