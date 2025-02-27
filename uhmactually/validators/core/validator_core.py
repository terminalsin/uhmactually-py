from typing import Any, Callable, Optional, TypeVar, Generic, Union
import inspect
from uhmactually.core import (
    Validator,
    ValidationError,
    ValidationResult,
)


# Optional validation helper
def optional(value: Any) -> None:
    """
    Validate that a value can be None.
    This is a no-op function that allows None values.

    Args:
        value: The value to validate.

    Raises:
        ValidationError: This function never raises ValidationError.
    """
    # This function allows None values, so it does nothing
    pass


def allow_none(value: Any = None, allow: bool = True) -> None:
    """
    Validate that a field allows None values.

    Args:
        value: The value to validate.
        allow: Whether the field allows None values. Default is True.

    Raises:
        ValidationError: If the field does not allow None values and the value is None.
    """
    if not allow and value is None:
        raise ValidationError(
            f"None value is not allowed",
            None,
            value,
        )


class OptionalValidator(Validator):
    """Validator that allows a value to be None."""

    def __init__(self, is_optional: bool = False):
        self.is_optional = is_optional

    def validate(
        self,
        func: Callable,
        value: Any,
        field_name: str,
        source_info: str = None,
        parent_object: Any = None,
    ) -> ValidationResult:
        """
        Validate that a value can be None.
        This validator always passes.

        Args:
            func: The function being validated.
            value: The value to validate.
            field_name: The name of the field being validated.
            source_info: Information about where the field is defined.
            parent_object: The object containing this field.

        Returns:
            A ValidationResult object.
        """
        if self.is_optional:
            # This validator allows None values, so it always passes
            return ValidationResult()
        elif value is None:
            raise ValidationError(
                f"Value is not optional by default and was found to be None",
                field_name,
                value,
            )
        else:
            return ValidationResult()

    def default(
        self,
        func: Callable,
        value: Any,
        field_name: str,
        source_info: str = None,
        parent_object: Any = None,
    ) -> ValidationResult:
        """
        Default validation method that runs all the time.
        For OptionalValidator, this does nothing.

        Args:
            func: The function being validated.
            value: The value to validate.
            field_name: The name of the field being validated.
            source_info: Information about where the field is defined.
            parent_object: The object containing this field.

        Returns:
            A ValidationResult object.
        """
        # Default implementation does nothing
        if value is None:
            raise ValidationError(
                f"Value is not optional by default and was found to be None",
                field_name,
                value,
            )
        else:
            return ValidationResult()


# Helper function wrapper for optional validator
def optional_check(value):
    """
    Check if a value is not None.

    Args:
        value: The value to check.

    Raises:
        ValidationError: If the value is None.
    """
    # Try to determine field name from call stack
    field_name = None
    import inspect

    frame = inspect.currentframe().f_back
    if frame:
        # Get the function that called this function
        func_name = frame.f_code.co_name
        # If the function name is a property name in a ValidatedModel class, use it as field_name
        if func_name != "<module>":
            field_name = func_name

    validator = OptionalValidator()
    result = validator.validate(optional_check, value, field_name or "value")
    if not result.is_valid:
        raise ValidationError(result.errors[0].message, field_name, value)


# Decorator factories
def optional(is_optional: bool = True):
    """Decorator to validate that a field is optional."""
    print("optional decorator", is_optional)
    return lambda func: OptionalValidator(is_optional).validate
