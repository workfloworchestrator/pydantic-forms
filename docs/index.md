# Pydantic Forms

A Python package that lets you add smart forms to [FastAPI](https://fastapi.tiangolo.com/) and [Flask](https://palletsprojects.com/p/flask/). Forms respond with a JSON schema that contains all the information a React frontend (with [uniforms](https://uniforms.tools/)) needs to render the form and handle validation.

Forms can also be composed into wizards — multiple consecutive forms that share state — so you can build complex flows. Forms and validation logic are defined using [Pydantic](https://docs.pydantic.dev/) models.

## Frontend rendering

This package only emits JSON Schema; rendering is the frontend's job. For a working end-to-end example that wires this backend up to a React frontend, see [`workfloworchestrator/pydantic-forms-ui`](https://github.com/workfloworchestrator/pydantic-forms-ui).

## Installation

```shell
pip install pydantic-forms
```

## Development

Install the project with development dependencies:

```shell
python3 -m venv venv
source venv/bin/activate
pip install flit
flit install --deps develop --symlink --python venv/bin/python
```

Run the test suite:

```shell
pytest tests/unit_tests
```

## Building these docs

```shell
pip install -e ".[doc]"
mkdocs serve
```
