from typing import Any, Callable, Optional, Union, TypeVar, Generic

from uhmactually.core import (
    Validator,
    ValidationError,
    ValidationResult,
)
from uhmactually.validators.registry import validator

# Type variable for numeric types
N = TypeVar("N", int, float)


@validator
class MinValidator(Validator, Generic[N]):
    """Validator that checks if a number is at least a minimum value."""

    def __init__(self, min_value: N = -float("inf"), inclusive: bool = True):
        """
        Initialize the validator.

        Args:
            min_value: The minimum value allowed.
            inclusive: Whether the minimum value is inclusive. Default is True.
        """
        self.min_value = min_value
        self.inclusive = inclusive

    def validate(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Validate that a number is at least the minimum value.

        Args:
            func: The function being validated.
            value: The value to validate.
            field_name: The name of the field being validated.

        Returns:
            A ValidationResult object.
        """
        result = ValidationResult()

        # Skip validation if value is None
        if value is None:
            return result

        # Ensure value is a number
        if not isinstance(value, (int, float)):
            result.add_error(
                ValidationError(
                    f"Expected a number for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                )
            )
            return result

        # Check if the number is at least the minimum value
        if self.inclusive:
            if value < self.min_value:
                result.add_error(
                    ValidationError(
                        f"Value {value} is less than the minimum value of {self.min_value}",
                        field_name,
                        value,
                    )
                )
        else:
            if value <= self.min_value:
                result.add_error(
                    ValidationError(
                        f"Value {value} is less than or equal to the minimum value of {self.min_value} (exclusive)",
                        field_name,
                        value,
                    )
                )

        return result

    def default(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        return ValidationResult()


@validator
class MaxValidator(Validator, Generic[N]):
    """Validator that checks if a number is at most a maximum value."""

    def __init__(self, max_value: N = float("inf"), inclusive: bool = True):
        """
        Initialize the validator.

        Args:
            max_value: The maximum value allowed.
            inclusive: Whether the maximum value is inclusive. Default is True.
        """
        self.max_value = max_value
        self.inclusive = inclusive

    def validate(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Validate that a number does not exceed the maximum value.

        Args:
            func: The function being validated.
            value: The value to validate.
            field_name: The name of the field being validated.

        Returns:
            A ValidationResult object.
        """
        result = ValidationResult()

        # Skip validation if value is None
        if value is None:
            return result

        # Ensure value is a number
        if not isinstance(value, (int, float)):
            result.add_error(
                ValidationError(
                    f"Expected a number for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                )
            )
            return result

        # Check if the number does not exceed the maximum value
        if self.inclusive:
            if value > self.max_value:
                result.add_error(
                    ValidationError(
                        f"Value {value} exceeds the maximum value of {self.max_value}",
                        field_name,
                        value,
                    )
                )
        else:
            if value >= self.max_value:
                result.add_error(
                    ValidationError(
                        f"Value {value} is greater than or equal to the maximum value of {self.max_value} (exclusive)",
                        field_name,
                        value,
                    )
                )

        return result

    def default(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        return ValidationResult()


@validator
class RangeValidator(Validator):
    """Validator that checks if a number is within a range."""

    def __init__(
        self,
        min_value: Union[int, float] = -float("inf"),
        max_value: Union[int, float] = float("inf"),
        min_inclusive: bool = True,
        max_inclusive: bool = True,
    ):
        """
        Initialize the validator.

        Args:
            min_value: The minimum value allowed.
            max_value: The maximum value allowed.
            min_inclusive: Whether the minimum value is inclusive. Default is True.
            max_inclusive: Whether the maximum value is inclusive. Default is True.
        """
        self.min_value = min_value
        self.max_value = max_value
        self.min_inclusive = min_inclusive
        self.max_inclusive = max_inclusive

    def validate(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Validate that a number is within the specified range.

        Args:
            func: The function being validated.
            value: The value to validate.
            field_name: The name of the field being validated.

        Returns:
            A ValidationResult object.
        """
        result = ValidationResult()

        # Skip validation if value is None
        if value is None:
            return result

        # Ensure value is a number
        if not isinstance(value, (int, float)):
            result.add_error(
                ValidationError(
                    f"Expected a number for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                )
            )
            return result

        # Check if the number is within the range
        min_check = (
            value >= self.min_value if self.min_inclusive else value > self.min_value
        )
        max_check = (
            value <= self.max_value if self.max_inclusive else value < self.max_value
        )

        if not min_check:
            min_op = ">=" if self.min_inclusive else ">"
            result.add_error(
                ValidationError(
                    f"Value {value} must be {min_op} {self.min_value}",
                    field_name,
                    value,
                )
            )

        if not max_check:
            max_op = "<=" if self.max_inclusive else "<"
            result.add_error(
                ValidationError(
                    f"Value {value} must be {max_op} {self.max_value}",
                    field_name,
                    value,
                )
            )

        return result

    def default(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        return ValidationResult()


# Decorator factories
def min_value(min_value: Union[int, float], inclusive: bool = True):
    """Decorator to validate that a number is at least a minimum value."""
    return MinValidator.create_decorator(min_value, inclusive)


def max_value(max_value: Union[int, float], inclusive: bool = True):
    """Decorator to validate that a number does not exceed a maximum value."""
    return MaxValidator.create_decorator(max_value, inclusive)


def in_range(
    min_value: Union[int, float],
    max_value: Union[int, float],
    min_inclusive: bool = True,
    max_inclusive: bool = True,
):
    """Decorator to validate that a number is within a range."""
    return RangeValidator.create_decorator(
        min_value, max_value, min_inclusive, max_inclusive
    )
