from typing import Any, Callable, Optional as OptionalType

from uhmactually.core import (
    Validator,
    ValidationError,
    ValidationResult,
)
from uhmactually.validators.registry import validator


@validator
class AllowNoneValidator(Validator):
    """Validator that checks if a value can be None."""

    def __init__(self, allow_none: bool = False):
        """
        Initialize the validator.

        Args:
            allow_none: Whether to allow None values. Default is False.
        """
        self.allow_none = allow_none

    def validate(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Validate that a value can be None if allowed.

        Args:
            func: The function being validated.
            value: The value to validate.
            field_name: The name of the field being validated.

        Returns:
            A ValidationResult object.
        """
        result = ValidationResult()

        if value is None and not self.allow_none:
            result.add_error(
                ValidationError(
                    f"None value is not allowed for field '{field_name}'",
                    field_name,
                    value,
                )
            )

        return result

    def default(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Default validation method that runs all the time.
        For AllowNoneValidator, this does the same validation as the validate method.

        Args:
            func: The function being validated.
            value: The value to validate.
            field_name: The name of the field being validated.

        Returns:
            A ValidationResult object.
        """
        return self.validate(func, value, field_name)


@validator
class OptionalValidator(Validator):
    """Validator that checks if a field is optional."""

    def __init__(self, optional: bool = False):
        """
        Initialize the validator.

        Args:
            optional: Whether the field is optional. Default is False.
        """
        self.optional = optional

    def validate(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Validate that a field is provided if not optional.

        Args:
            func: The function being validated.
            value: The value to validate.
            field_name: The name of the field being validated.

        Returns:
            A ValidationResult object.
        """
        result = ValidationResult()

        # If the field is optional, we don't need to validate anything
        if self.optional:
            return result

        # If the field is not optional and the value is None, add an error
        if value is None:
            result.add_error(
                ValidationError(
                    f"Field '{field_name}' is required and cannot be None",
                    field_name,
                    value,
                )
            )

        return result

    def default(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Default validation method that runs all the time.
        For OptionalValidator, this does the same validation as the validate method.

        Args:
            func: The function being validated.
            value: The value to validate.
            field_name: The name of the field being validated.

        Returns:
            A ValidationResult object.
        """
        return self.validate(func, value, field_name)


# Decorator factories
def allow_none(allow: bool = True):
    """Decorator to validate that a value can be None."""
    return AllowNoneValidator.create_decorator(allow)


def optional(is_optional: bool = True):
    """Decorator to validate that a field is optional."""
    return OptionalValidator.create_decorator(is_optional)
