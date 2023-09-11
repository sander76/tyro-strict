"""Core public API."""
from types import UnionType
from typing import (
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    get_args,
)
from pydantic import BaseModel

from typing import Annotated
from tyro import cli, conf
from pydantic import create_model
from pydantic.fields import FieldInfo

T = TypeVar("T", bound=BaseModel)


def _is_subcommand(attribute: str, field_info: FieldInfo) -> bool:
    if not isinstance(field_info.annotation, UnionType):
        return False
    args = get_args(field_info.annotation)
    if not all(issubclass(arg, BaseModel) for arg in args):
        return False
    if not field_info.is_required():
        raise ValueError("Should be required values.")
    return True


def _make_subcommand(field_info: FieldInfo) -> tuple:
    """Rewrite as a subcommand.

    A strict subcommand is in a form of two or more optional BaseModels which will
    be re-annotated using the `tyro` annotations for strict subcommands.

    Args:
        field_info: field_info

    Returns:
        A tuple containing type and default value for recreation of the object.

    """
    args = get_args(field_info.annotation)

    mdls = []
    for arg in args:
        mdl = make_strict(arg)
        mdls.append(Annotated[mdl, conf.subcommand(prefix_name=False)])

    _type = conf.OmitSubcommandPrefixes[Union[tuple(mdls)]]  # type: ignore
    return (_type, ...)


def _is_object(field_info: FieldInfo) -> bool:
    if field_info.annotation is None:
        raise AttributeError("Expecting annotation information.")
    if issubclass(field_info.annotation, BaseModel):
        return True
    return False


def _make_positional(field_info: FieldInfo) -> tuple:
    """We are assuming a positional is always a python primitive

    like an int/str etc.
    """
    return (conf.Positional[field_info.annotation], ...)  # type: ignore


def make_strict(model: Type[T]) -> Type[T]:
    sub_command_found = False
    field_definitions: dict[str, tuple] = {}
    for key, value in model.model_fields.items():
        if _is_subcommand(key, value):
            if sub_command_found:
                raise ValueError("Cannot have two subcommands.")
            else:
                sub_command_found = True
            field_definitions[key] = _make_subcommand(value)
        elif _is_object(value):
            raise ValueError("Nested objects not allowed.")
        elif value.is_required():
            field_definitions[key] = _make_positional(value)
        else:
            field_definitions[key] = (value.annotation, value.default)

    new_model = create_model(
        model.__name__,
        **field_definitions,
        __base__=model,
    )  # type: ignore
    return new_model


def strict_cli(
    model: Type[BaseModel],
    args: Optional[Sequence[str]] = None,
) -> BaseModel:
    new_model = make_strict(model)
    return cli(new_model, args=args)
