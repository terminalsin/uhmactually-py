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


# Enum validation helpers
def one_of(value: Any, allowed_values: Union[List, Set, Tuple, Enum]) -> None:
    """
    Validate that a value is in a set of allowed values.

    Args:
        value: The value to validate.
        allowed_values: The set of allowed values. Can be a list, set, tuple, or Enum class.

    Raises:
        ValidationError: If the value is not in the set of allowed values.
    """
    # Convert Enum to list of values
    if isinstance(allowed_values, type) and issubclass(allowed_values, Enum):
        allowed_list = [item.value for item in allowed_values]
    else:
        allowed_list = list(allowed_values)

    # Check if the value is in the allowed values
    if value not in allowed_list:
        allowed_str = ", ".join(repr(v) for v in allowed_list)
        raise ValidationError(
            f"Value '{value}' is not in the set of allowed values: {allowed_str}",
            None,
            value,
        )


def not_in(value: Any, disallowed_values: Union[List, Set, Tuple, Enum]) -> None:
    """
    Validate that a value is not in a set of disallowed values.

    Args:
        value: The value to validate.
        disallowed_values: The set of disallowed values. Can be a list, set, tuple, or Enum class.

    Raises:
        ValidationError: If the value is in the set of disallowed values.
    """
    # Convert Enum to list of values
    if isinstance(disallowed_values, type) and issubclass(disallowed_values, Enum):
        disallowed_list = [item.value for item in disallowed_values]
    else:
        disallowed_list = list(disallowed_values)

    # Check if the value is not in the disallowed values
    if value in disallowed_list:
        disallowed_str = ", ".join(repr(v) for v in disallowed_list)
        raise ValidationError(
            f"Value '{value}' is in the set of disallowed values: {disallowed_str}",
            None,
            value,
        )


def is_enum(value: Any, enum_class: Type[Enum]) -> None:
    """
    Validate that a value is a valid enum value.

    Args:
        value: The value to validate.
        enum_class: The enum class to check against.

    Raises:
        ValidationError: If the value is not a valid enum value.
    """
    # Check if the value is a valid enum value
    try:
        enum_class(value)
    except ValueError:
        valid_values = ", ".join(repr(item.value) for item in enum_class)
        raise ValidationError(
            f"Value '{value}' is not a valid {enum_class.__name__} value. Valid values are: {valid_values}",
            None,
            value,
        )


# Type variable for values
T = TypeVar("T")


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

    def validate(
        self,
        func: Callable,
        value: Any,
        field_name: str,
        source_info: str = None,
        parent_object: Any = None,
    ) -> ValidationResult:
        """
        Validate that a value is in the set of allowed values.

        Args:
            func: The function being validated.
            value: The value to validate.
            field_name: The name of the field being validated.
            source_info: Information about where the field is defined.

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
                        source_info,
                        parent_object,
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
                    source_info,
                    parent_object,
                )
            )

        return result

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
        For EnumValidator, this does nothing by default.

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
        return ValidationResult()


class NotInValidator(Validator, Generic[T]):
    """Validator that checks if a value is not in a set of disallowed values."""

    def __init__(
        self,
        disallowed_values: Union[List[T], Set[T], Tuple[T, ...], Enum] = None,
        case_sensitive: bool = True,
    ):
        """
        Initialize the validator.

        Args:
            disallowed_values: The set of disallowed values. Can be a list, set, tuple, or Enum class.
            case_sensitive: Whether string comparisons should be case-sensitive. Default is True.
        """
        if disallowed_values is None:
            self.disallowed_values = []
        elif isinstance(disallowed_values, type) and issubclass(
            disallowed_values, Enum
        ):
            self.disallowed_values = [item.value for item in disallowed_values]
        else:
            self.disallowed_values = list(disallowed_values)
        self.case_sensitive = case_sensitive

    def validate(
        self,
        func: Callable,
        value: Any,
        field_name: str,
        source_info: str = None,
        parent_object: Any = None,
    ) -> ValidationResult:
        """
        Validate that a value is not in the set of disallowed values.

        Args:
            func: The function being validated.
            value: The value to validate.
            field_name: The name of the field being validated.
            source_info: Information about where the field is defined.
            parent_object: The object containing this field.

        Returns:
            A ValidationResult object.
        """
        result = ValidationResult()

        # Skip validation if value is None or if disallowed_values is empty
        if value is None or not self.disallowed_values:
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
                        source_info,
                        parent_object,
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
                    source_info,
                    parent_object,
                )
            )

        return result

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
        For NotInValidator, this does nothing by default.

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
        return ValidationResult()


class EnumClassValidator(Validator):
    """Validator that checks if a value is a valid enum value."""

    def __init__(self, enum_class: Type[Enum]):
        """
        Initialize the validator.

        Args:
            enum_class: The enum class to check against.
        """
        self.enum_class = enum_class

    def validate(
        self,
        func: Callable,
        value: Any,
        field_name: str,
        source_info: str = None,
        parent_object: Any = None,
    ) -> ValidationResult:
        """
        Validate that a value is a valid enum value.

        Args:
            func: The function being validated.
            value: The value to validate.
            field_name: The name of the field being validated.
            source_info: Information about where the field is defined.
            parent_object: The object containing this field.

        Returns:
            A ValidationResult object.
        """
        result = ValidationResult()

        # Skip validation if value is None
        if value is None:
            return result

        # Check if the value is a valid enum value
        try:
            self.enum_class(value)
        except ValueError:
            valid_values = ", ".join(repr(item.value) for item in self.enum_class)
            result.add_error(
                ValidationError(
                    f"Value '{value}' is not a valid {self.enum_class.__name__} value. Valid values are: {valid_values}",
                    field_name,
                    value,
                    source_info,
                    parent_object,
                )
            )

        return result

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
        For EnumClassValidator, this does nothing by default.

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
        return ValidationResult()


# Helper function wrappers for validators
def one_of_check(value, allowed_values):
    """
    Check if a value is in a set of allowed values.

    Args:
        value: The value to check.
        allowed_values: The set of allowed values. Can be a list, set, tuple, or Enum class.

    Raises:
        ValidationError: If the value is not in the set of allowed values.
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

    validator = EnumValidator(allowed_values)
    result = validator.validate(one_of_check, value, field_name or "value")
    if not result.is_valid:
        raise ValidationError(result.errors[0].message, field_name, value)


def not_in_check(value, disallowed_values):
    """
    Check if a value is not in a set of disallowed values.

    Args:
        value: The value to check.
        disallowed_values: The set of disallowed values. Can be a list, set, tuple, or Enum class.

    Raises:
        ValidationError: If the value is in the set of disallowed values.
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

    validator = NotInValidator(disallowed_values)
    result = validator.validate(not_in_check, value, field_name or "value")
    if not result.is_valid:
        raise ValidationError(result.errors[0].message, field_name, value)


def is_enum_check(value, enum_class):
    """
    Check if a value is a valid enum value.

    Args:
        value: The value to check.
        enum_class: The enum class to check against.

    Raises:
        ValidationError: If the value is not a valid enum value.
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

    validator = EnumClassValidator(enum_class)
    result = validator.validate(is_enum_check, value, field_name or "value")
    if not result.is_valid:
        raise ValidationError(result.errors[0].message, field_name, value)
