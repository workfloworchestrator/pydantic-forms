from enum import Enum
from typing import Any, Callable, Dict, Generator, List, Tuple, Type, TypedDict, TypeVar, Union

try:
    # python3.10 introduces types.UnionType for the new union and optional type defs.
    from types import UnionType

    union_types = [Union, UnionType]
except ImportError:
    union_types = [Union]
from pydantic.main import BaseModel

UUIDstr = str
State = Dict[str, Any]
JSON = Any


class strEnum(str, Enum):
    def __str__(self) -> str:
        return self.value

    @classmethod
    def values(cls) -> List:
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
    headers: List[str]
    labels: List[str]
    columns: List[List[Union[str, int, bool, float]]]


InputForm = Type[BaseModel]
AcceptData = List[Union[Tuple[str, AcceptItemType], Tuple[str, AcceptItemType, Dict]]]

T = TypeVar("T", bound=BaseModel)

FormGenerator = Generator[Type[T], T, State]
SimpleInputFormGenerator = Callable[..., InputForm]
InputFormGenerator = Callable[..., FormGenerator]
InputStepFunc = Union[SimpleInputFormGenerator, InputFormGenerator]
StateSimpleInputFormGenerator = Callable[[State], InputForm]
StateInputFormGenerator = Callable[[State], FormGenerator]
StateInputStepFunc = Union[StateSimpleInputFormGenerator, StateInputFormGenerator]
SubscriptionMapping = Dict[str, List[Dict[str, str]]]
