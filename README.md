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

Documentation regarding the usage of Forms can be found
[here](https://github.com/workfloworchestrator/orchestrator-core/blob/main/docs/architecture/application/forms-frontend.md)

### Installation (Development standalone)
Install the project and its dependencies to develop on the code.

#### Step 1 - install uv:

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Step 2 - install the development code:
```shell
uv sync --all-extras
```

This creates a `.venv` in the project and installs the package in editable mode.


### Running tests
Run the unit-test suite to verify a correct setup.

#### Step 3 - Run tests
```shell
uv run --all-extras pytest tests/unit_tests
```

or with xdist:

```shell
uv run --all-extras pytest -n auto tests/unit_tests
```

If you do not encounter any failures in the test, you should be able to develop features in the pydantic-forms.

### Installation (Development editable into project that uses pydantic-forms)

If you are working on a project that already uses the `pydantic-forms` and you want to test your new form features
against it, you can install the development checkout into that project's virtual environment. It will replace the
PyPI dependency with an editable install of the development version.

#### Step 1 - install uv:

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2 - install pydantic-forms into your own project

```shell
uv pip install --python /path/to/a/project/venv/bin/python -e .
```

# Increasing the version number for a (pre) release.

When your PR is accepted you will get a version number.

You can do the necessary change with a clean, e.g. every change committed, branch:

```shell
bumpversion patch --new-version 0.0.1
```

Note: specifying it like this, instead of relying on bumpversion itself to increase the version, allows you to
set a "RC1" version if needed.

# Debugging Form behaviour

If you want/need the traceback of pydantic in a Form response you can add an env variable:

`
LOG_LEVEL_PYDANTIC_FORMS=DEBUG
`

This will add the traceback to the `JSONResponse`. If the loglevel is set to DEBUG the library will also add the
traceback to the logger.
