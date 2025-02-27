from typing import (
    Any,
    Callable,
    List,
    Set,
    Tuple,
    Union,
    TypeVar,
    Generic,
    Optional,
    Type,
)
from enum import Enum

from uhmactually.core import (
    Validator,
    ValidationError,
    ValidationResult,
)
from uhmactually.validators.registry import validator

# Type variable for values
T = TypeVar("T")


@validator
class EnumValidator(Validator, Generic[T]):
    """Validator that checks if a value is in a set of allowed values."""

    def __init__(
        self,
        allowed_values: Union[List[T], Set[T], Tuple[T, ...], Enum] = Any,
        case_sensitive: bool = True,
    ):
        """
        Initialize the validator.

        Args:
            allowed_values: The set of allowed values. Can be a list, set, tuple, or Enum class.
            case_sensitive: Whether string comparisons should be case-sensitive. Default is True.
        """
        if allowed_values == Any:
            self.allowed_values = Any
        elif isinstance(allowed_values, type) and issubclass(allowed_values, Enum):
            self.allowed_values = [item.value for item in allowed_values]
        else:
            self.allowed_values = list(allowed_values)
        self.case_sensitive = case_sensitive

    def validate(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Validate that a value is in the set of allowed values.

        Args:
            func: The function being validated.
            value: The value to validate.
            field_name: The name of the field being validated.

        Returns:
            A ValidationResult object.
        """
        result = ValidationResult()

        # Skip validation if value is None or if allowed_values is Any
        if value is None or self.allowed_values == Any:
            return result

        # For case-insensitive string comparison
        if not self.case_sensitive and isinstance(value, str):
            if not any(
                isinstance(allowed, str) and allowed.lower() == value.lower()
                for allowed in self.allowed_values
            ):
                allowed_str = ", ".join(repr(v) for v in self.allowed_values)
                result.add_error(
                    ValidationError(
                        f"Value '{value}' is not in the set of allowed values: {allowed_str} (case-insensitive)",
                        field_name,
                        value,
                    )
                )
        # For regular comparison
        elif value not in self.allowed_values:
            allowed_str = ", ".join(repr(v) for v in self.allowed_values)
            result.add_error(
                ValidationError(
                    f"Value '{value}' is not in the set of allowed values: {allowed_str}",
                    field_name,
                    value,
                )
            )

        return result

    def default(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        return ValidationResult()


@validator
class NotInValidator(Validator, Generic[T]):
    """Validator that checks if a value is not in a set of disallowed values."""

    def __init__(
        self,
        disallowed_values: Union[List[T], Set[T], Tuple[T, ...]] = [],
        case_sensitive: bool = True,
    ):
        """
        Initialize the validator.

        Args:
            disallowed_values: The set of disallowed values.
            case_sensitive: Whether string comparisons should be case-sensitive. Default is True.
        """
        self.disallowed_values = list(disallowed_values)
        self.case_sensitive = case_sensitive

    def validate(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Validate that a value is not in the set of disallowed values.

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

        # For case-insensitive string comparison
        if not self.case_sensitive and isinstance(value, str):
            if any(
                isinstance(disallowed, str) and disallowed.lower() == value.lower()
                for disallowed in self.disallowed_values
            ):
                disallowed_str = ", ".join(repr(v) for v in self.disallowed_values)
                result.add_error(
                    ValidationError(
                        f"Value '{value}' is in the set of disallowed values: {disallowed_str} (case-insensitive)",
                        field_name,
                        value,
                    )
                )
        # For regular comparison
        elif value in self.disallowed_values:
            disallowed_str = ", ".join(repr(v) for v in self.disallowed_values)
            result.add_error(
                ValidationError(
                    f"Value '{value}' is in the set of disallowed values: {disallowed_str}",
                    field_name,
                    value,
                )
            )

        return result

    def default(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        return ValidationResult()


# Decorator factories
def one_of(
    allowed_values: Union[List[T], Set[T], Tuple[T, ...], Enum],
    case_sensitive: bool = True,
):
    """Decorator to validate that a value is in a set of allowed values."""
    return EnumValidator.create_decorator(allowed_values, case_sensitive)


def not_in(
    disallowed_values: Union[List[T], Set[T], Tuple[T, ...]],
    case_sensitive: bool = True,
):
    """Decorator to validate that a value is not in a set of disallowed values."""
    return NotInValidator.create_decorator(disallowed_values, case_sensitive)


def is_enum(enum_class: Type[Enum]):
    """Decorator to validate that a value is a valid enum value."""
    return EnumValidator.create_decorator(enum_class)
