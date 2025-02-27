import pytest
from typing import Union

from uhmactually.core import (
    ValidationError,
    ValidatedModel,
    validate,
)
from uhmactually.validators import (
    min_value_check,
    max_value_check,
    in_range_check,
)


# Test Models
class NumberValidatorModel(ValidatedModel):
    """A model with number validators."""

    @validate
    def non_negative(self) -> int:
        min_value_check(0)

    @validate
    def positive(self) -> int:
        min_value_check(1, inclusive=False)

    @validate
    def max_hundred(self) -> int:
        max_value_check(100)

    @validate
    def less_than_hundred(self) -> int:
        max_value_check(99, inclusive=False)

    @validate
    def zero_to_ten(self) -> int:
        in_range_check(0, 10)

    @validate
    def exclusive_range(self) -> float:
        in_range_check(0, 10, min_inclusive=False, max_inclusive=False)


class FloatValidatorModel(ValidatedModel):
    """A model with float validators."""

    @validate
    def non_negative(self) -> float:
        min_value_check(0.0)

    @validate(is_optional=True)
    def max_one(self) -> float:
        max_value_check(1.0)

    @validate
    def zero_to_one(self) -> float:
        in_range_check(0.0, 1.0)

    @validate
    def exclusive_zero_to_one(self) -> float:
        in_range_check(0.0, 1.0, min_inclusive=False, max_inclusive=False)


# Parametrized Tests for MinValidator with integers
@pytest.mark.parametrize(
    "non_negative,should_pass",
    [
        # Valid cases
        (0, True),
        (1, True),
        (100, True),
        # Invalid cases
        (-1, False),
        (-100, False),
        (None, False),  # None is skipped in validation
    ],
)
def test_min_value_validator(non_negative, should_pass):
    """Test min_value validator with integers."""
    if should_pass:
        model = NumberValidatorModel(
            non_negative=non_negative,
            positive=2,
            max_hundred=50,
            less_than_hundred=50,
            zero_to_ten=5,
            exclusive_range=5.5,
        )
        assert model.non_negative() == non_negative
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            NumberValidatorModel(
                non_negative=non_negative,
                positive=2,
                max_hundred=50,
                less_than_hundred=50,
                zero_to_ten=5,
                exclusive_range=5.5,
            )
        assert "is less than the minimum value" in str(
            excinfo.value
        ) or "Value is not optional by" in str(excinfo.value)


# Parametrized Tests for MinValidator with exclusive minimum
@pytest.mark.parametrize(
    "positive,should_pass",
    [
        # Valid cases
        (2, True),
        (10, True),
        (100, True),
        # Invalid cases
        (1, False),  # Exactly the minimum (exclusive)
        (0, False),
        (-1, False),
        (None, False),  # None is skipped in validation
    ],
)
def test_min_value_exclusive_validator(positive, should_pass):
    """Test min_value validator with exclusive minimum."""
    if should_pass:
        model = NumberValidatorModel(
            non_negative=0,
            positive=positive,
            max_hundred=50,
            less_than_hundred=50,
            zero_to_ten=5,
            exclusive_range=5.5,
        )
        assert model.positive() == positive
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            NumberValidatorModel(
                non_negative=0,
                positive=positive,
                max_hundred=50,
                less_than_hundred=50,
                zero_to_ten=5,
                exclusive_range=5.5,
            )
        assert "exclusive" in str(excinfo.value) or "Value is not optional by" in str(
            excinfo.value
        )


# Parametrized Tests for MaxValidator with integers
@pytest.mark.parametrize(
    "max_hundred,should_pass",
    [
        # Valid cases
        (0, True),
        (50, True),
        (100, True),  # Exactly the maximum
        # Invalid cases
        (101, False),
        (1000, False),
        (None, False),  # None is skipped in validation
    ],
)
def test_max_value_validator(max_hundred, should_pass):
    """Test max_value validator with integers."""
    if should_pass:
        model = NumberValidatorModel(
            non_negative=0,
            positive=2,
            max_hundred=max_hundred,
            less_than_hundred=50,
            zero_to_ten=5,
            exclusive_range=5.5,
        )
        assert model.max_hundred() == max_hundred
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            NumberValidatorModel(
                non_negative=0,
                positive=2,
                max_hundred=max_hundred,
                less_than_hundred=50,
                zero_to_ten=5,
                exclusive_range=5.5,
            )
        assert "exceeds the maximum value" in str(
            excinfo.value
        ) or "Value is not optional by" in str(excinfo.value)


# Parametrized Tests for MaxValidator with exclusive maximum
@pytest.mark.parametrize(
    "less_than_hundred,should_pass",
    [
        # Valid cases
        (0, True),
        (50, True),
        (98, True),
        # Invalid cases
        (99, False),  # Exactly the maximum (exclusive)
        (100, False),
        (101, False),
        (None, False),  # None is skipped in validation
    ],
)
def test_max_value_exclusive_validator(less_than_hundred, should_pass):
    """Test max_value validator with exclusive maximum."""
    if should_pass:
        model = NumberValidatorModel(
            non_negative=0,
            positive=2,
            max_hundred=50,
            less_than_hundred=less_than_hundred,
            zero_to_ten=5,
            exclusive_range=5.5,
        )
        assert model.less_than_hundred() == less_than_hundred
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            NumberValidatorModel(
                non_negative=0,
                positive=2,
                max_hundred=50,
                less_than_hundred=less_than_hundred,
                zero_to_ten=5,
                exclusive_range=5.5,
            )
        assert "exclusive" in str(excinfo.value) or "Value is not optional by" in str(
            excinfo.value
        )


# Parametrized Tests for RangeValidator with integers
@pytest.mark.parametrize(
    "zero_to_ten,should_pass",
    [
        # Valid cases
        (0, True),  # Minimum
        (5, True),  # Middle
        (10, True),  # Maximum
        # Invalid cases
        (-1, False),  # Below minimum
        (11, False),  # Above maximum
        (None, False),  # None is skipped in validation
    ],
)
def test_in_range_validator(zero_to_ten, should_pass):
    """Test in_range validator with integers."""
    if should_pass:
        model = NumberValidatorModel(
            non_negative=0,
            positive=2,
            max_hundred=50,
            less_than_hundred=50,
            zero_to_ten=zero_to_ten,
            exclusive_range=5.5,
        )
        assert model.zero_to_ten() == zero_to_ten
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            NumberValidatorModel(
                non_negative=0,
                positive=2,
                max_hundred=50,
                less_than_hundred=50,
                zero_to_ten=zero_to_ten,
                exclusive_range=5.5,
            )
        if zero_to_ten is not None:
            if zero_to_ten < 0:
                assert ">=" in str(excinfo.value)
            else:
                assert "<=" in str(excinfo.value)


# Parametrized Tests for RangeValidator with exclusive range
@pytest.mark.parametrize(
    "exclusive_range,should_pass",
    [
        # Valid cases
        (0.1, True),
        (5.5, True),
        (9.9, True),
        # Invalid cases
        (0.0, False),  # Exactly the minimum (exclusive)
        (10.0, False),  # Exactly the maximum (exclusive)
        (-1.0, False),  # Below minimum
        (11.0, False),  # Above maximum
        (None, False),  # None is skipped in validation
    ],
)
def test_in_range_exclusive_validator(exclusive_range, should_pass):
    """Test in_range validator with exclusive range."""
    if should_pass:
        model = NumberValidatorModel(
            non_negative=0,
            positive=2,
            max_hundred=50,
            less_than_hundred=50,
            zero_to_ten=5,
            exclusive_range=exclusive_range,
        )
        assert model.exclusive_range() == exclusive_range
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            NumberValidatorModel(
                non_negative=0,
                positive=2,
                max_hundred=50,
                less_than_hundred=50,
                zero_to_ten=5,
                exclusive_range=exclusive_range,
            )
        if exclusive_range is not None:
            if exclusive_range <= 0:
                assert ">" in str(excinfo.value)
            elif exclusive_range >= 10:
                assert "<" in str(excinfo.value)


# Parametrized Tests for MinValidator with floats
@pytest.mark.parametrize(
    "non_negative,should_pass",
    [
        # Valid cases
        (0.0, True),
        (0.1, True),
        (1.0, True),
        # Invalid cases
        (-0.1, False),
        (-1.0, False),
        (None, False),  # None is skipped in validation
    ],
)
def test_min_value_float_validator(non_negative, should_pass):
    """Test min_value validator with floats."""
    if should_pass:
        model = FloatValidatorModel(
            non_negative=non_negative,
            max_one=0.5,
            zero_to_one=0.5,
            exclusive_zero_to_one=0.5,
        )
        assert model.non_negative() == non_negative
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            FloatValidatorModel(
                non_negative=non_negative,
                max_one=0.5,
                zero_to_one=0.5,
                exclusive_zero_to_one=0.5,
            )
        assert "is less than the minimum value" in str(
            excinfo.value
        ) or "Value is not optional by" in str(excinfo.value)


# Parametrized Tests for MaxValidator with floats
@pytest.mark.parametrize(
    "max_one,should_pass",
    [
        # Valid cases
        (0.0, True),
        (0.5, True),
        (1.0, True),  # Exactly the maximum
        # Invalid cases
        (1.1, False),
        (2.0, False),
        (None, False),  # None is skipped in validation
    ],
)
def test_max_value_float_validator(max_one, should_pass):
    """Test max_value validator with floats."""
    if should_pass:
        model = FloatValidatorModel(
            non_negative=0.0,
            max_one=max_one,
            zero_to_one=0.5,
            exclusive_zero_to_one=0.5,
        )
        assert model.max_one() == max_one
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            FloatValidatorModel(
                non_negative=0.0,
                max_one=max_one,
                zero_to_one=0.5,
                exclusive_zero_to_one=0.5,
            )
        assert "exceeds the maximum value" in str(
            excinfo.value
        ) or "Value is not optional by" in str(excinfo.value)


# Parametrized Tests for RangeValidator with floats
@pytest.mark.parametrize(
    "zero_to_one,should_pass",
    [
        # Valid cases
        (0.0, True),  # Minimum
        (0.5, True),  # Middle
        (1.0, True),  # Maximum
        # Invalid cases
        (-0.1, False),  # Below minimum
        (1.1, False),  # Above maximum
        (None, False),  # None is skipped in validation
    ],
)
def test_in_range_float_validator(zero_to_one, should_pass):
    """Test in_range validator with floats."""
    if should_pass:
        model = FloatValidatorModel(
            non_negative=0.0,
            max_one=1.0,
            zero_to_one=zero_to_one,
            exclusive_zero_to_one=0.5,
        )
        assert model.zero_to_one() == zero_to_one
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            FloatValidatorModel(
                non_negative=0.0,
                max_one=1.0,
                zero_to_one=zero_to_one,
                exclusive_zero_to_one=0.5,
            )
        if zero_to_one is not None:
            if zero_to_one < 0:
                assert ">=" in str(excinfo.value)
            else:
                assert "<=" in str(excinfo.value)


# Parametrized Tests for RangeValidator with exclusive float range
@pytest.mark.parametrize(
    "exclusive_zero_to_one,should_pass",
    [
        # Valid cases
        (0.1, True),
        (0.5, True),
        (0.9, True),
        # Invalid cases
        (0.0, False),  # Exactly the minimum (exclusive)
        (1.0, False),  # Exactly the maximum (exclusive)
        (-0.1, False),  # Below minimum
        (1.1, False),  # Above maximum
        (None, False),  # None is skipped in validation
    ],
)
def test_in_range_exclusive_float_validator(exclusive_zero_to_one, should_pass):
    """Test in_range validator with exclusive float range."""
    if should_pass:
        model = FloatValidatorModel(
            non_negative=0.0,
            max_one=1.0,
            zero_to_one=0.5,
            exclusive_zero_to_one=exclusive_zero_to_one,
        )
        assert model.exclusive_zero_to_one() == exclusive_zero_to_one
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            FloatValidatorModel(
                non_negative=0.0,
                max_one=1.0,
                zero_to_one=0.5,
                exclusive_zero_to_one=exclusive_zero_to_one,
            )
        if exclusive_zero_to_one is not None:
            if exclusive_zero_to_one <= 0:
                assert ">" in str(excinfo.value)
            elif exclusive_zero_to_one >= 1:
                assert "<" in str(excinfo.value)


# Test error messages
def test_min_value_error_message():
    """Test that MinValidator produces the expected error message."""
    with pytest.raises(ValidationError) as excinfo:
        NumberValidatorModel(
            non_negative=-1,  # Invalid
            positive=2,
            max_hundred=50,
            less_than_hundred=50,
            zero_to_ten=5,
            exclusive_range=5.5,
        )
    error_message = str(excinfo.value)
    assert "Value -1 is less than the minimum value of 0" in error_message


def test_max_value_error_message():
    """Test that MaxValidator produces the expected error message."""
    with pytest.raises(ValidationError) as excinfo:
        NumberValidatorModel(
            non_negative=0,
            positive=2,
            max_hundred=101,  # Invalid
            less_than_hundred=50,
            zero_to_ten=5,
            exclusive_range=5.5,
        )
    error_message = str(excinfo.value)
    assert "Value 101 exceeds the maximum value of 100" in error_message


def test_in_range_error_message():
    """Test that RangeValidator produces the expected error message."""
    with pytest.raises(ValidationError) as excinfo:
        NumberValidatorModel(
            non_negative=0,
            positive=2,
            max_hundred=50,
            less_than_hundred=50,
            zero_to_ten=11,  # Invalid
            exclusive_range=5.5,
        )
    error_message = str(excinfo.value)
    assert "Value 11 must be <= 10" in error_message


# Test validation results
def test_number_validation_results():
    """Test that validation results contain the expected errors."""
    # Create a model with valid values
    model = NumberValidatorModel(
        non_negative=0,
        positive=2,
        max_hundred=50,
        less_than_hundred=50,
        zero_to_ten=5,
        exclusive_range=0.5,
    )

    # Manually set invalid values to bypass initialization validation
    model._data["non_negative"] = -1
    model._data["max_hundred"] = 101
    model._data["zero_to_ten"] = 11
    model._data["exclusive_range"] = 1.1

    # Validate the model
    print(f"model._data: {model._data}")

    with pytest.raises(ValidationError) as excinfo:
        model.validate()


# Test type validation
def test_number_type_validation():
    """Test that validators check for numeric types."""
    with pytest.raises(ValidationError) as excinfo:
        NumberValidatorModel(
            non_negative="not a number",  # Invalid type
            positive=2,
            max_hundred=50,
            less_than_hundred=50,
            zero_to_ten=5,
            exclusive_range=5.5,
        )
    error_message = str(excinfo.value)
    assert "Expected type int" in error_message
