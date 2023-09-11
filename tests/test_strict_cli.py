from pydantic import BaseModel
from tyro import cli
from tyro_strict.strict_cli import strict_cli
import pytest


def test_simple_model__make_strict__success():
    class SimpleModel(BaseModel):
        name: str
        """Should become positional."""

    model = strict_cli(SimpleModel, args=["myname"])

    assert isinstance(model, SimpleModel)
    assert model.name == "myname"


def test_model_with_sub_command__make_strict__success():
    class SubCommandOne(BaseModel):
        name: str = "subcommand_one"

    class SubCommandTwo(BaseModel):
        name: str = "subcommand_two"

    class ModelWithSubcommand(BaseModel):
        sub_command: SubCommandOne | SubCommandTwo

    model = strict_cli(ModelWithSubcommand, args=["sub-command-one"])
    assert isinstance(model.sub_command, SubCommandOne)

    model = strict_cli(ModelWithSubcommand, args=["sub-command-two"])
    assert isinstance(model.sub_command, SubCommandTwo)


def test_model_with_sub_commands_and_positionals__make_strict__success():
    class SubCommandOne(BaseModel):
        name: str

    class SubCommandTwo(BaseModel):
        name: str

    class ModelWithSubcommand(BaseModel):
        sub_command: SubCommandOne | SubCommandTwo

    model = strict_cli(ModelWithSubcommand, args=["sub-command-one", "myname"])
    assert isinstance(model.sub_command, SubCommandOne)
    assert model.sub_command.name == "myname"


def test_model_with_subcommand_and_default__should_raise():
    class SubCommandOne(BaseModel):
        name: str = "subcommand_one"

    class SubCommandTwo(BaseModel):
        name: str = "subcommand_two"

    class ModelWithSubcommand(BaseModel):
        sub_command: SubCommandOne | SubCommandTwo = (
            SubCommandOne()
        )  # <-- default is not allowed.

    with pytest.raises(ValueError):
        strict_cli(ModelWithSubcommand)


def test_model_with_two_subcommands__make_strict__should_raise():
    class SubCommandOne(BaseModel):
        name: str = "subcommand_one"

    class SubCommandTwo(BaseModel):
        name: str = "subcommand_two"

    class ModelWithSubcommand(BaseModel):
        sub_command: SubCommandOne | SubCommandTwo
        sub_command_two: SubCommandOne | SubCommandTwo

    with pytest.raises(ValueError):
        strict_cli(ModelWithSubcommand)


def test_model_with_sub_basemodel__make_strict__should_raise():
    class SubModel(BaseModel):
        name: str

    class NestedModel(BaseModel):
        name: str
        model: SubModel

    with pytest.raises(ValueError):
        strict_cli(NestedModel, args=["myname", "-h"])


def test_nested_subcommand():
    class NestedSubcommandOne(BaseModel):
        name: str

    class NestedSubcommandTwo(BaseModel):
        name: str

    class SubCommandOne(BaseModel):
        sub_command: NestedSubcommandOne | NestedSubcommandTwo

    class SubCommandTwo(BaseModel):
        name: str

    class ModelWithSubcommand(BaseModel):
        sub_command: SubCommandOne | SubCommandTwo

    model = strict_cli(
        ModelWithSubcommand,
        args=["sub-command-one", "nested-subcommand-one", "myname"],
    )
    assert isinstance(model.sub_command, SubCommandOne)
    assert isinstance(model.sub_command.sub_command, NestedSubcommandOne)


def test_pydantic_model_with_sub_commands_and_positionals__success():
    class SubCommandOne(BaseModel):
        name: str

    class SubCommandTwo(BaseModel):
        name: str

    class ModelWithSubcommand(BaseModel):
        sub_command: SubCommandOne | SubCommandTwo

    model = cli(
        ModelWithSubcommand,
        args=["sub-command:sub-command-two", "--sub-command.name", "myname"],
    )
    assert isinstance(model.sub_command, SubCommandTwo)
    assert model.sub_command.name == "myname"
