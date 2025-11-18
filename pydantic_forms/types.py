from enum import Enum
from types import UnionType
from typing import Any, AsyncGenerator, Callable, Generator, Type, TypeVar, Union

from pydantic.main import BaseModel
from typing_extensions import TypedDict

union_types = [Union, UnionType]

UUIDstr = str
State = dict[str, Any]
JSON = Any


class strEnum(str, Enum):
    def __str__(self) -> str:
        return self.value

    @classmethod
    def values(cls) -> list:
        return [obj.value for obj in cls]


class AcceptItemType(strEnum):
    INFO = "info"
    LABEL = "label"
    WARNING = "warning"
    URL = "url"
    CHECKBOX = "checkbox"
    SUBCHECKBOX = ">checkbox"
    OPTIONAL_CHECKBOX = "checkbox?"
    OPTIONAL_SUBCHECKBOX = ">checkbox?"
    SKIP = "skip"
    VALUE = "value"
    MARGIN = "margin"


class SummaryData(TypedDict, total=False):
    headers: list[str]
    labels: list[str]
    columns: list[list[Union[str, int, bool, float]]]


InputForm = Type[BaseModel]
AcceptData = list[Union[tuple[str, AcceptItemType], tuple[str, AcceptItemType, dict]]]

T = TypeVar("T", bound=BaseModel)

FormGenerator = Generator[Type[T], T, State]  # [YieldType, SendType, ReturnType]
SimpleInputFormGenerator = Callable[..., InputForm]
InputFormGenerator = Callable[..., FormGenerator]
InputStepFunc = Union[SimpleInputFormGenerator, InputFormGenerator]
StateSimpleInputFormGenerator = Callable[[State], InputForm]
StateInputFormGenerator = Callable[[State], FormGenerator]
StateInputStepFunc = Union[StateSimpleInputFormGenerator, StateInputFormGenerator]
SubscriptionMapping = dict[str, list[dict[str, str]]]

FormGeneratorAsync = AsyncGenerator[Union[Type[T], State], T]  # [YieldType, SendType]
StateInputFormGeneratorAsync = Callable[[State], FormGeneratorAsync]
