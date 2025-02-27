import pytest
from enum import Enum

from uhmactually.core import (
    ValidationError,
    ValidatedModel,
    validate,
)
from uhmactually.validators import (
    one_of_check,
    is_enum_check,
)


# Test Enum
class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


# Test Model with stacked decorators
class StackedDecoratorsModel(ValidatedModel):
    """A model with stacked decorators."""

    # Test stacking validate before other decorators
    @validate
    def fruit(self, value=None) -> str:
        if value is not None:
            one_of_check(value, ["apple", "banana", "cherry"])
        return value

    # Test stacking validate after other decorators
    @validate
    def color(self, value=None) -> str:
        if value is not None:
            is_enum_check(value, Color)
        return value

    # Test stacking validate between other decorators
    @validate
    def size(self, value=None) -> str:
        if value is not None:
            one_of_check(value, ["small", "medium", "large"])
        return value

    # Another field with a different validator
    @validate
    def color2(self, value=None) -> str:
        if value is not None:
            is_enum_check(value, Color)
        return value


def test_validate_before_other_decorator():
    """Test validate decorator stacked before other decorators."""
    # Valid case
    model = StackedDecoratorsModel(
        fruit="apple",
        color=Color.RED.value,
        size="small",
        color2=Color.GREEN.value,
    )
    assert model.fruit() == "apple"
    assert model.validate().is_valid

    # Invalid case
    with pytest.raises(ValidationError) as excinfo:
        StackedDecoratorsModel(
            fruit="orange",  # Invalid
            color=Color.RED.value,
            size="small",
            color2=Color.GREEN.value,
        )
    assert "is not in the set of allowed values" in str(excinfo.value)


def test_validate_after_other_decorator():
    """Test validate decorator stacked after other decorators."""
    # Valid case
    model = StackedDecoratorsModel(
        fruit="apple",
        color=Color.RED.value,
        size="small",
        color2=Color.GREEN.value,
    )
    assert model.color() == Color.RED.value
    assert model.validate().is_valid

    # Invalid case
    with pytest.raises(ValidationError) as excinfo:
        StackedDecoratorsModel(
            fruit="apple",
            color="yellow",  # Invalid
            size="small",
            color2=Color.GREEN.value,
        )
    assert "is not in the set of allowed values" in str(excinfo.value)


def test_validate_between_other_decorators():
    """Test validate decorator stacked between other decorators."""
    # Valid case
    model = StackedDecoratorsModel(
        fruit="apple",
        color=Color.RED.value,
        size="small",
        color2=Color.GREEN.value,
    )
    assert model.size() == "small"
    assert model.validate().is_valid

    # Invalid case - should fail the one_of validation
    with pytest.raises(ValidationError) as excinfo:
        StackedDecoratorsModel(
            fruit="apple",
            color=Color.RED.value,
            size="extra-large",  # Invalid
            color2=Color.GREEN.value,
        )
    assert "is not in the set of allowed values" in str(excinfo.value)
