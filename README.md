
To add features to the repository follow the following procedure to setup a working development environment.

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
pytest test/unit_tests
```

or with xdist:

```shell
pytest -n auto test/unit_tests
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

### Step 2 - symlink the core to your own project

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
