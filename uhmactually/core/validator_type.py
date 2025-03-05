from uhmactually.validator import (
    Validator,
    validator,
    ValidationInput,
    ValidationResult,
)
from typing import Callable, Type
import inspect


@validator
class TypeValidator(Validator):
    def validate(self, input: ValidationInput, **kwargs) -> ValidationResult:
        value = input.value
        type = kwargs.get("type")
        print(value, type)
        if isinstance(value, type):
            return self.success(value)
        return self.fail(f"Value must be of type {type}")

    def default(self, input: ValidationInput) -> ValidationResult:
        method = input.definition

        inspect_type = inspect.signature(method).return_annotation
        print(inspect_type)

        if inspect_type == inspect.Signature.empty:
            return self.success(input.value)
        # else fail if not derived from expected type
        elif not issubclass(type(input.value), inspect_type):
            return self.fail(f"Value must be of type {inspect_type}")
        else:
            return self.success(input.value)


def typed(type: Type) -> Callable:
    """Decorator to validate that a number is at least min_value."""

    def decorator(func):
        # Use the validate decorator to mark this as a validation field
        from uhmactually.validator import validate

        # Apply the validator
        decorated = TypeValidator().generate_decorator(type=type)(func)

        return decorated

    return decorator
