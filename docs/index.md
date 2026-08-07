# Introduction

pydantic-forms is a library that lets APIs (e.g. FastAPI) collect user input through forms defined as
[Pydantic](https://docs.pydantic.dev/) models. A form definition is turned into a JSON schema that a frontend
can render. The submitted input can be validated against and transformed by the model.

Forms can also be chained together to create "form wizards", using the result of each form page to
decide what the next page looks like.

This library is a spinoff from [orchestrator-core](https://workfloworchestrator.org/orchestrator-core/) in which it was
originally developed, and where it is still used to render the input forms of its workflows.
