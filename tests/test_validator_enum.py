import pytest
from enum import Enum, auto
from typing import List, Set, Tuple, Union

from uhmactually.core import (
    ValidationError,
    ValidatedModel,
    validate,
)
from uhmactually.validators import (
    one_of,
    not_in,
    is_enum,
)


# Test Enum
class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class Status(Enum):
    PENDING = auto()
    ACTIVE = auto()
    INACTIVE = auto()


# Test Models
class EnumValidatorModel(ValidatedModel):
    """A model with enum validators."""

    @one_of(["apple", "banana", "cherry"])
    def fruit(self) -> str:
        pass

    @one_of({"red", "green", "blue"})
    def color_name(self) -> str:
        pass

    @one_of(("small", "medium", "large"))
    def size(self) -> str:
        pass

    @one_of(["YES", "NO"], case_sensitive=False)
    def case_insensitive_choice(self) -> str:
        pass

    @is_enum(Color)
    def color(self) -> str:
        pass

    @is_enum(Status)
    def status(self) -> int:
        pass


class NotInValidatorModel(ValidatedModel):
    """A model with not_in validators."""

    @not_in(["forbidden", "restricted", "banned"])
    def allowed_word(self) -> str:
        pass

    @not_in(["FORBIDDEN", "RESTRICTED", "BANNED"], case_sensitive=False)
    def case_insensitive_allowed(self) -> str:
        pass


# Parametrized Tests for EnumValidator with lists
@pytest.mark.parametrize(
    "fruit,should_pass",
    [
        # Valid cases
        ("apple", True),
        ("banana", True),
        ("cherry", True),
        # Invalid cases
        ("orange", False),
        ("", False),
        (None, True),  # None is skipped in validation
    ],
)
def test_one_of_list_validator(fruit, should_pass):
    """Test one_of validator with a list of allowed values."""
    if should_pass:
        model = EnumValidatorModel(
            fruit=fruit,
            color_name="red",
            size="small",
            case_insensitive_choice="YES",
            color=Color.RED.value,
            status=Status.ACTIVE.value,
        )
        assert model.fruit() == fruit
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            EnumValidatorModel(
                fruit=fruit,
                color_name="red",
                size="small",
                case_insensitive_choice="YES",
                color=Color.RED.value,
                status=Status.ACTIVE.value,
            )
        assert "is not in the set of allowed values" in str(excinfo.value)


# Parametrized Tests for EnumValidator with sets
@pytest.mark.parametrize(
    "color_name,should_pass",
    [
        # Valid cases
        ("red", True),
        ("green", True),
        ("blue", True),
        # Invalid cases
        ("yellow", False),
        ("", False),
        (None, True),  # None is skipped in validation
    ],
)
def test_one_of_set_validator(color_name, should_pass):
    """Test one_of validator with a set of allowed values."""
    if should_pass:
        model = EnumValidatorModel(
            fruit="apple",
            color_name=color_name,
            size="small",
            case_insensitive_choice="YES",
            color=Color.RED.value,
            status=Status.ACTIVE.value,
        )
        assert model.color_name() == color_name
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            EnumValidatorModel(
                fruit="apple",
                color_name=color_name,
                size="small",
                case_insensitive_choice="YES",
                color=Color.RED.value,
                status=Status.ACTIVE.value,
            )
        assert "is not in the set of allowed values" in str(excinfo.value)


# Parametrized Tests for EnumValidator with tuples
@pytest.mark.parametrize(
    "size,should_pass",
    [
        # Valid cases
        ("small", True),
        ("medium", True),
        ("large", True),
        # Invalid cases
        ("x-large", False),
        ("", False),
        (None, True),  # None is skipped in validation
    ],
)
def test_one_of_tuple_validator(size, should_pass):
    """Test one_of validator with a tuple of allowed values."""
    if should_pass:
        model = EnumValidatorModel(
            fruit="apple",
            color_name="red",
            size=size,
            case_insensitive_choice="YES",
            color=Color.RED.value,
            status=Status.ACTIVE.value,
        )
        assert model.size() == size
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            EnumValidatorModel(
                fruit="apple",
                color_name="red",
                size=size,
                case_insensitive_choice="YES",
                color=Color.RED.value,
                status=Status.ACTIVE.value,
            )
        assert "is not in the set of allowed values" in str(excinfo.value)


# Parametrized Tests for EnumValidator with case insensitivity
@pytest.mark.parametrize(
    "choice,should_pass",
    [
        # Valid cases - exact match
        ("YES", True),
        ("NO", True),
        # Valid cases - different case
        ("yes", True),
        ("no", True),
        ("Yes", True),
        ("No", True),
        # Invalid cases
        ("maybe", False),
        ("", False),
        (None, True),  # None is skipped in validation
    ],
)
def test_one_of_case_insensitive_validator(choice, should_pass):
    """Test one_of validator with case-insensitive comparison."""
    if should_pass:
        model = EnumValidatorModel(
            fruit="apple",
            color_name="red",
            size="small",
            case_insensitive_choice=choice,
            color=Color.RED.value,
            status=Status.ACTIVE.value,
        )
        assert model.case_insensitive_choice() == choice
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            EnumValidatorModel(
                fruit="apple",
                color_name="red",
                size="small",
                case_insensitive_choice=choice,
                color=Color.RED.value,
                status=Status.ACTIVE.value,
            )
        assert "is not in the set of allowed values" in str(excinfo.value)


# Parametrized Tests for EnumValidator with Enum class
@pytest.mark.parametrize(
    "color_value,should_pass",
    [
        # Valid cases
        (Color.RED.value, True),
        (Color.GREEN.value, True),
        (Color.BLUE.value, True),
        ("red", True),
        ("green", True),
        ("blue", True),
        # Invalid cases
        ("yellow", False),
        ("", False),
        (None, True),  # None is skipped in validation
    ],
)
def test_is_enum_validator(color_value, should_pass):
    """Test is_enum validator with an Enum class."""
    if should_pass:
        model = EnumValidatorModel(
            fruit="apple",
            color_name="red",
            size="small",
            case_insensitive_choice="YES",
            color=color_value,
            status=Status.ACTIVE.value,
        )
        assert model.color() == color_value
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            EnumValidatorModel(
                fruit="apple",
                color_name="red",
                size="small",
                case_insensitive_choice="YES",
                color=color_value,
                status=Status.ACTIVE.value,
            )
        assert "is not in the set of allowed values" in str(excinfo.value)


# Parametrized Tests for NotInValidator
@pytest.mark.parametrize(
    "word,should_pass",
    [
        # Valid cases
        ("allowed", True),
        ("permitted", True),
        ("", True),
        # Invalid cases
        ("forbidden", False),
        ("restricted", False),
        ("banned", False),
        (None, True),  # None is skipped in validation
    ],
)
def test_not_in_validator(word, should_pass):
    """Test not_in validator with a list of disallowed values."""
    if should_pass:
        model = NotInValidatorModel(
            allowed_word=word,
            case_insensitive_allowed="allowed",
        )
        assert model.allowed_word() == word
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            NotInValidatorModel(
                allowed_word=word,
                case_insensitive_allowed="allowed",
            )
        assert "is in the set of disallowed values" in str(excinfo.value)


# Parametrized Tests for NotInValidator with case insensitivity
@pytest.mark.parametrize(
    "word,should_pass",
    [
        # Valid cases
        ("allowed", True),
        ("permitted", True),
        ("", True),
        # Invalid cases - exact match
        ("FORBIDDEN", False),
        ("RESTRICTED", False),
        ("BANNED", False),
        # Invalid cases - different case
        ("forbidden", False),
        ("Restricted", False),
        ("banned", False),
        (None, True),  # None is skipped in validation
    ],
)
def test_not_in_case_insensitive_validator(word, should_pass):
    """Test not_in validator with case-insensitive comparison."""
    if should_pass:
        model = NotInValidatorModel(
            allowed_word="allowed",
            case_insensitive_allowed=word,
        )
        assert model.case_insensitive_allowed() == word
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            NotInValidatorModel(
                allowed_word="allowed",
                case_insensitive_allowed=word,
            )
        assert "is in the set of disallowed values" in str(excinfo.value)


# Test error messages
def test_one_of_error_message():
    """Test that EnumValidator produces the expected error message."""
    with pytest.raises(ValidationError) as excinfo:
        EnumValidatorModel(
            fruit="orange",  # Invalid
            color_name="red",
            size="small",
            case_insensitive_choice="YES",
            color=Color.RED.value,
            status=Status.ACTIVE.value,
        )
    error_message = str(excinfo.value)
    assert (
        "Value 'orange' is not in the set of allowed values: 'apple', 'banana', 'cherry'"
        in error_message
    )


def test_not_in_error_message():
    """Test that NotInValidator produces the expected error message."""
    with pytest.raises(ValidationError) as excinfo:
        NotInValidatorModel(
            allowed_word="forbidden",  # Invalid
            case_insensitive_allowed="allowed",
        )
    error_message = str(excinfo.value)
    assert (
        "Value 'forbidden' is in the set of disallowed values: 'forbidden', 'restricted', 'banned'"
        in error_message
    )


# Test validation results
def test_enum_validation_results():
    """Test that validation results contain the expected errors."""
    # Create a model with valid values
    model = EnumValidatorModel(
        fruit="apple",
        color_name="red",
        size="small",
        case_insensitive_choice="YES",
        color=Color.RED.value,
        status=Status.ACTIVE.value,
    )

    # Manually set invalid values to bypass initialization validation
    model._data["fruit"] = "orange"
    model._data["color_name"] = "yellow"

    # Validate the model
    result = model.validate()

    # Check that validation failed
    assert not result.is_valid

    # Check that the expected errors are present
    errors = result.errors
    assert len(errors) == 2

    # Check error fields
    error_fields = [error.field for error in errors]
    assert "fruit" in error_fields
    assert "color_name" in error_fields
