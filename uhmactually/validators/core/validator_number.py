from typing import Any, Callable, Optional, Union, TypeVar, Generic, Type

from uhmactually.core import (
    Validator,
    ValidationError,
    ValidationResult,
)


# Type variable for numeric types
N = TypeVar("N", int, float)


# Number validation helpers
def min_value(value: N, min_value: N, inclusive: bool = True) -> None:
    """
    Validate that a number is at least a minimum value.

    Args:
        value: The value to validate.
        min_value: The minimum value.
        inclusive: Whether the minimum value is inclusive. Default is True.

    Raises:
        ValidationError: If the number is less than the minimum value.
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"Expected a number, got {type(value).__name__}",
            None,
            value,
        )

    if inclusive:
        if value < min_value:
            raise ValidationError(
                f"Value {value} is less than the minimum value of {min_value}",
                None,
                value,
            )
    else:
        if value <= min_value:
            raise ValidationError(
                f"Value {value} is less than or equal to the minimum value of {min_value} (exclusive)",
                None,
                value,
            )


def max_value(value: N, max_value: N, inclusive: bool = True) -> None:
    """
    Validate that a number does not exceed a maximum value.

    Args:
        value: The value to validate.
        max_value: The maximum value.
        inclusive: Whether the maximum value is inclusive. Default is True.

    Raises:
        ValidationError: If the number exceeds the maximum value.
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"Expected a number, got {type(value).__name__}",
            None,
            value,
        )

    if inclusive:
        if value > max_value:
            raise ValidationError(
                f"Value {value} exceeds the maximum value of {max_value}",
                None,
                value,
            )
    else:
        if value >= max_value:
            raise ValidationError(
                f"Value {value} is greater than or equal to the maximum value of {max_value} (exclusive)",
                None,
                value,
            )


def in_range(
    value: N,
    min_value: N,
    max_value: N,
    min_inclusive: bool = True,
    max_inclusive: bool = True,
) -> None:
    """
    Validate that a number is within a range.

    Args:
        value: The value to validate.
        min_value: The minimum value.
        max_value: The maximum value.
        min_inclusive: Whether the minimum value is inclusive. Default is True.
        max_inclusive: Whether the maximum value is inclusive. Default is True.

    Raises:
        ValidationError: If the number is not within the specified range.
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"Expected a number, got {type(value).__name__}",
            None,
            value,
        )

    min_check = value >= min_value if min_inclusive else value > min_value
    max_check = value <= max_value if max_inclusive else value < max_value

    if not min_check:
        min_op = ">=" if min_inclusive else ">"
        raise ValidationError(
            f"Value {value} must be {min_op} {min_value}",
            None,
            value,
        )

    if not max_check:
        max_op = "<=" if max_inclusive else "<"
        raise ValidationError(
            f"Value {value} must be {max_op} {max_value}",
            None,
            value,
        )


class MinValidator(Validator, Generic[N]):
    """Validator that checks if a number is at least a minimum value."""

    def __init__(self, min_value: N, inclusive: bool = True):
        """
        Initialize the validator.

        Args:
            min_value: The minimum value.
            inclusive: Whether the minimum value is inclusive. Default is True.
        """
        self.min_value = min_value
        self.inclusive = inclusive

    def validate(
        self,
        func: Callable,
        value: Any,
        field_name: str,
        source_info: str = None,
        parent_object: Any = None,
    ) -> ValidationResult:
        """
        Validate that a number is at least the minimum value.

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

        # Ensure value is a number
        if not isinstance(value, (int, float)):
            result.add_error(
                ValidationError(
                    f"Expected a number for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                    source_info,
                    parent_object,
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
                        source_info,
                        parent_object,
                    )
                )
        else:
            if value <= self.min_value:
                result.add_error(
                    ValidationError(
                        f"Value {value} is less than or equal to the minimum value of {self.min_value} (exclusive)",
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
        For MinValidator, this does nothing by default.

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


class MaxValidator(Validator, Generic[N]):
    """Validator that checks if a number is at most a maximum value."""

    def __init__(self, max_value: N, inclusive: bool = True):
        """
        Initialize the validator.

        Args:
            max_value: The maximum value.
            inclusive: Whether the maximum value is inclusive. Default is True.
        """
        self.max_value = max_value
        self.inclusive = inclusive

    def validate(
        self,
        func: Callable,
        value: Any,
        field_name: str,
        source_info: str = None,
        parent_object: Any = None,
    ) -> ValidationResult:
        """
        Validate that a number does not exceed the maximum value.

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

        # Ensure value is a number
        if not isinstance(value, (int, float)):
            result.add_error(
                ValidationError(
                    f"Expected a number for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                    source_info,
                    parent_object,
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
                        source_info,
                        parent_object,
                    )
                )
        else:
            if value >= self.max_value:
                result.add_error(
                    ValidationError(
                        f"Value {value} is greater than or equal to the maximum value of {self.max_value} (exclusive)",
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
        For MaxValidator, this does nothing by default.

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


class RangeValidator(Validator):
    """Validator that checks if a number is within a range."""

    def __init__(
        self,
        min_value: N,
        max_value: N,
        min_inclusive: bool = True,
        max_inclusive: bool = True,
    ):
        """
        Initialize the validator.

        Args:
            min_value: The minimum value.
            max_value: The maximum value.
            min_inclusive: Whether the minimum value is inclusive. Default is True.
            max_inclusive: Whether the maximum value is inclusive. Default is True.
        """
        self.min_value = min_value
        self.max_value = max_value
        self.min_inclusive = min_inclusive
        self.max_inclusive = max_inclusive

    def validate(
        self,
        func: Callable,
        value: Any,
        field_name: str,
        source_info: str = None,
        parent_object: Any = None,
    ) -> ValidationResult:
        """
        Validate that a number is within the specified range.

        Args:
            func: The function being validated.
            value: The value to validate.
            field_name: The name of the field being validated.
            source_info: Information about where the field is defined.

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
                    source_info,
                    parent_object,
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
                    source_info,
                    parent_object,
                )
            )

        if not max_check:
            max_op = "<=" if self.max_inclusive else "<"
            result.add_error(
                ValidationError(
                    f"Value {value} must be {max_op} {self.max_value}",
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
        For RangeValidator, this does nothing by default.

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
def min_value_check(min_value, inclusive: bool = True, value=None):
    """
    Check if a number is at least a minimum value.

    Args:
        value: The number to check.
        min_value: The minimum value.
        inclusive: Whether the minimum value is inclusive. Default is True.

    Raises:
        ValidationError: If the number is less than the minimum value.
    """
    # Try to determine field name from call stack
    if value is None:
        field_name = None
        import inspect

        frame = inspect.currentframe().f_back
        if frame:
            # Get the function that called this function
            func_name = frame.f_code.co_name
            func_instance = frame.f_locals.get("self")
            # If the function name is a property name in a ValidatedModel class, use it as field_name
            if func_name != "<module>":
                field_name = func_name
                value = func_instance._data[func_name]

                if value is None:
                    raise ValidationError(
                        "Value is None",
                        None,
                        value,
                    )
                print(f"value analysed: {value}")
            else:
                raise ValidationError(
                    "No field name found",
                    None,
                    value,
                )
        else:
            raise ValidationError(
                "No call stack found",
                None,
                value,
            )

    validator = MinValidator(min_value, inclusive)

    result = validator.validate(min_value_check, value, field_name or "value")
    if not result.is_valid:
        raise ValidationError(result.errors[0].message, field_name, value)


def max_value_check(max_value, inclusive: bool = True, value=None):
    """
    Check if a number is at most a maximum value.

    Args:
        value: The number to check.
        max_value: The maximum value.
        inclusive: Whether the maximum value is inclusive. Default is True.

    Raises:
        ValidationError: If the number exceeds the maximum value.
    """
    # Try to determine field name from call stack
    if value is None:
        field_name = None
        import inspect

        frame = inspect.currentframe().f_back
        if frame:
            # Get the function that called this function
            func_name = frame.f_code.co_name
            func_instance = frame.f_locals.get("self")
            # If the function name is a property name in a ValidatedModel class, use it as field_name
            if func_name != "<module>":
                field_name = func_name
                value = func_instance._data[func_name]

                if value is None:
                    raise ValidationError(
                        "Value is None",
                        None,
                        value,
                    )
                print(f"value analysed: {value}")
            else:
                raise ValidationError(
                    "No field name found",
                    None,
                    value,
                )
        else:
            raise ValidationError(
                "No call stack found",
                None,
                value,
            )

    validator = MaxValidator(max_value, inclusive)
    result = validator.validate(max_value_check, value, field_name or "value")
    if not result.is_valid:
        raise ValidationError(result.errors[0].message, field_name, value)


def in_range_check(
    min_value,
    max_value,
    min_inclusive: bool = True,
    max_inclusive: bool = True,
    value=None,
):
    """
    Check if a number is within a range.

    Args:
        value: The number to check.
        min_value: The minimum value.
        max_value: The maximum value.
        min_inclusive: Whether the minimum value is inclusive. Default is True.
        max_inclusive: Whether the maximum value is inclusive. Default is True.

    Raises:
        ValidationError: If the number is not within the range.
    """
    # Try to determine field name from call stack
    if value is None:
        field_name = None
        import inspect

        frame = inspect.currentframe().f_back
        if frame:
            # Get the function that called this function
            func_name = frame.f_code.co_name
            func_instance = frame.f_locals.get("self")
            # If the function name is a property name in a ValidatedModel class, use it as field_name
            if func_name != "<module>":
                field_name = func_name
                value = func_instance._data[func_name]

                if value is None:
                    raise ValidationError(
                        "Value is None",
                        None,
                        value,
                    )
                print(f"value analysed: {value}")
            else:
                raise ValidationError(
                    "No field name found",
                    None,
                    value,
                )
        else:
            raise ValidationError(
                "No call stack found",
                None,
                value,
            )

    validator = RangeValidator(min_value, max_value, min_inclusive, max_inclusive)
    result = validator.validate(in_range_check, value, field_name or "value")
    if not result.is_valid:
        raise ValidationError(result.errors[0].message, field_name, value)
