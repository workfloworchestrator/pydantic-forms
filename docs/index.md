# Pydantic Forms

Pydantic Forms lets FastAPI or Flask applications collect user input as forms, defined as
[Pydantic](https://docs.pydantic.dev/) models. A form definition is turned into a JSON schema that a frontend
can render, validate the submitted input against the model, and return the validated data.

Forms can also be wizards: a generator function `yield`s one form page at a time, using the result of each page to
decide what the next page looks like.

It's used by [orchestrator-core](https://workfloworchestrator.org/orchestrator-core/) to render the input forms of
its workflows.
