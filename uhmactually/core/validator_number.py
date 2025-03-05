from uhmactually.validator import (
    Validator,
    validator,
    ValidationInput,
    ValidationResult,
)
from typing import Callable


@validator
class MinNumberValidator(Validator):
    def validate(self, input: ValidationInput, **kwargs) -> ValidationResult:
        value = input.value
        min_value = kwargs.get("min_value")
        print(value, min_value)
        if value >= min_value:
            return self.success(value)
        return self.fail(f"Value must be at least {min_value}")

    def default(self, input: ValidationInput) -> ValidationResult:
        return self.success(input.value)


def min(min_value: int) -> Callable:
    """Decorator to validate that a number is at least min_value."""

    def decorator(func):
        # Use the validate decorator to mark this as a validation field
        from uhmactually.validator import validate

        # Apply the validator
        decorated = MinNumberValidator().generate_decorator(min_value=min_value)(func)

        return decorated

    return decorator


@validator
class MaxNumberValidator(Validator):
    def validate(self, input: ValidationInput, **kwargs) -> ValidationResult:
        value = input.value
        max_value = kwargs.get("max_value")
        if value <= max_value:
            return self.success(value)
        return self.fail(f"Value must be at most {max_value}")

    def default(self, input: ValidationInput) -> ValidationResult:
        return self.success(input.value)


def max(max_value: int) -> Callable:
    """Decorator to validate that a number is at most max_value."""

    def decorator(func):
        # Apply the validator
        decorated = MaxNumberValidator().generate_decorator(max_value=max_value)(func)

        return decorated

    return decorator
