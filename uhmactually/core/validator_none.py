from uhmactually.validator import (
    Validator,
    validator,
    ValidationInput,
    ValidationResult,
    ValidationException,
)
from typing import Callable


@validator(accept_none=True)
class AllowNoneValidator(Validator):
    def validate(self, input: ValidationInput, **kwargs) -> ValidationResult:
        return self.success(input.value)

    def default(self, input: ValidationInput) -> ValidationResult:
        if input.value is None:
            return self.fail("Value cannot be None")
        return self.success(input.value)


def allow_none(func=None):
    """
    Decorator to validate that a value can be None.
    Can be used as @allow_none or @allow_none()
    """
    from uhmactually.validator import validate

    def decorator(function):
        # Apply the validator
        decorated = AllowNoneValidator().generate_decorator()(function)
        return decorated

    # Direct decoration: @allow_none
    if func is not None:
        return decorator(func)

    # Parameterized decoration: @allow_none()
    return decorator
