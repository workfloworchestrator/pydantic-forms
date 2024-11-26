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

#### Step 1 - install flit:

```shell
python3 -m venv venv
source venv/bin/activate
pip install flit
```

#### Step 2 - install the development code:
```shell
flit install --deps develop --symlink --python venv/bin/python
```

!!! danger
    Make sure to use the flit binary that is installed in your environment. You can check the correct
    path by running
    ```shell
    which flit
    ```

To be sure that the packages will be installed against the correct venv you can also prepend the python interpreter
that you want to use:

```shell
flit install --deps develop --symlink --python venv/bin/python
```


### Running tests
Run the unit-test suite to verify a correct setup.

#### Step 2 - Run tests
```shell
pytest tests/unit_tests
```

or with xdist:

```shell
pytest -n auto tests/unit_tests
```

If you do not encounter any failures in the test, you should be able to develop features in the pydantic-forms.

### Installation (Development symlinked into project that use pydantic-forms)

If you are working on a project that already uses the `pydantic-forms` and you want to test your new form features
against it, you can use some `flit` magic to symlink the dev version of the forms to your project. It will
automatically replace the pypi dep with a symlink to the development version
of the core and update/downgrade all required packages in your own project.

#### Step 1 - install flit:

```shell
python - m venv venv
source venv/bin/activate
pip install flit
```

### Step 2 - symlink pydantic-forms to your own project

```shell
flit install --deps develop --symlink --python /path/to/a/project/venv/bin/python
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
