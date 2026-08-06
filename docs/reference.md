# Reference

Every public module, listed in full. See [Usage](usage.md) and [How it works](how-it-works.md) for the
explanations behind them.

<!--
The options below are repeated per block rather than set once in mkdocs.yml, because this page is also
built as a subproject of workfloworchestrator.github.io. That build uses the parent's mkdocs.yml, and
mkdocstrings options are global per handler, so the parent's settings would otherwise silently apply
here -- and its options cannot be widened to suit this page without changing how the other subprojects
render. Per-block options override the global config, so they hold in both builds.

show_if_no_docstring is the load-bearing one: most field types are Annotated aliases without a
docstring, and the default hides them silently, without even a --strict warning. Removing it drops 24
of the 27 names in validators.__all__; test_reference_documents_every_export guards against that.

filters is tighter than the default "!^_[^_]", which keeps dunders and so documents __all__, __init__
and pydantic's __pydantic_init_subclass__ hooks as if they were API.

Each section supplies its own heading, so show_root_heading/show_root_toc_entry stay off; enabling them
duplicates the heading and nests every member a level deeper, hiding them from the sidebar.
-->

## Forms

::: pydantic_forms.core
    options:
      show_if_no_docstring: true
      filters: ["!^_", "!^logger$"]
      members_order: source
      heading_level: 3
      show_root_heading: false
      show_root_toc_entry: false
      show_source: false

## Async variants

::: pydantic_forms.core.asynchronous
    options:
      show_if_no_docstring: true
      filters: ["!^_", "!^logger$"]
      members_order: source
      heading_level: 3
      show_root_heading: false
      show_root_toc_entry: false
      show_source: false

## Field types

::: pydantic_forms.validators
    options:
      show_if_no_docstring: true
      filters: ["!^_", "!^logger$"]
      members_order: source
      heading_level: 3
      show_root_heading: false
      show_root_toc_entry: false
      show_source: false

## Exceptions

::: pydantic_forms.exceptions
    options:
      show_if_no_docstring: true
      filters: ["!^_", "!^logger$"]
      members_order: source
      heading_level: 3
      show_root_heading: false
      show_root_toc_entry: false
      show_source: false

## Types

::: pydantic_forms.types
    options:
      show_if_no_docstring: true
      filters: ["!^_", "!^logger$"]
      members_order: source
      heading_level: 3
      show_root_heading: false
      show_root_toc_entry: false
      show_source: false

## FastAPI exception handler

::: pydantic_forms.exception_handlers.fastapi
    options:
      show_if_no_docstring: true
      filters: ["!^_", "!^logger$"]
      members_order: source
      heading_level: 3
      show_root_heading: false
      show_root_toc_entry: false
      show_source: false
