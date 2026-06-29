from typing import Literal

from pydantic_settings import BaseSettings


class PydanticFormsSettings(BaseSettings):
    REQUIRED_FIELD_HANDLING: Literal["default", "extended"] = (
        "default"  # "default": how pydantic determines requires fields. "extended": default + extra detection for
    )


pydantic_form_settings = PydanticFormsSettings()
