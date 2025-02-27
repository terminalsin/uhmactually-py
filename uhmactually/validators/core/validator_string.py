import re
from typing import Any, Callable, Optional, Pattern, Union

from uhmactually.core import (
    Validator,
    ValidationError,
    ValidationResult,
)


# String validation helpers
def min_length(value: str, min_length: int) -> None:
    """
    Validate that a string has at least a minimum length.

    Args:
        value: The value to validate.
        min_length: The minimum length.

    Raises:
        ValidationError: If the string is shorter than the minimum length.
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"Expected a string, got {type(value).__name__}",
            None,
            value,
        )

    if len(value) < min_length:
        raise ValidationError(
            f"String length {len(value)} is less than the minimum length of {min_length}",
            None,
            value,
        )


def max_length(value: str, max_length: int) -> None:
    """
    Validate that a string does not exceed a maximum length.

    Args:
        value: The value to validate.
        max_length: The maximum length.

    Raises:
        ValidationError: If the string is longer than the maximum length.
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"Expected a string, got {type(value).__name__}",
            None,
            value,
        )

    if len(value) > max_length:
        raise ValidationError(
            f"String length {len(value)} exceeds the maximum length of {max_length}",
            None,
            value,
        )


def length_between(value: str, min_length: int, max_length: int) -> None:
    """
    Validate that a string length is between a minimum and maximum.

    Args:
        value: The value to validate.
        min_length: The minimum length.
        max_length: The maximum length.

    Raises:
        ValidationError: If the string length is not within the specified range.
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"Expected a string, got {type(value).__name__}",
            None,
            value,
        )

    if len(value) < min_length:
        raise ValidationError(
            f"String length {len(value)} is less than the minimum length of {min_length}",
            None,
            value,
        )

    if len(value) > max_length:
        raise ValidationError(
            f"String length {len(value)} exceeds the maximum length of {max_length}",
            None,
            value,
        )


def matches_pattern(value: str, pattern: Union[str, Pattern]) -> None:
    """
    Validate that a string matches a regular expression pattern.

    Args:
        value: The value to validate.
        pattern: The regular expression pattern to match.

    Raises:
        ValidationError: If the string does not match the pattern.
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"Expected a string, got {type(value).__name__}",
            None,
            value,
        )

    if isinstance(pattern, str):
        pattern = re.compile(pattern)

    if not pattern.match(value):
        raise ValidationError(
            f"String '{value}' does not match the pattern '{pattern.pattern}'",
            None,
            value,
        )


def contains(value: str, substring: str, case_sensitive: bool = True) -> None:
    """
    Validate that a string contains a substring.

    Args:
        value: The value to validate.
        substring: The substring to check for.
        case_sensitive: Whether the check should be case-sensitive. Default is True.

    Raises:
        ValidationError: If the string does not contain the substring.
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"Expected a string, got {type(value).__name__}",
            None,
            value,
        )

    if case_sensitive:
        if substring not in value:
            raise ValidationError(
                f"String '{value}' does not contain the substring '{substring}'",
                None,
                value,
            )
    else:
        if substring.lower() not in value.lower():
            raise ValidationError(
                f"String '{value}' does not contain the substring '{substring}' (case-insensitive)",
                None,
                value,
            )


def starts_with(value: str, prefix: str, case_sensitive: bool = True) -> None:
    """
    Validate that a string starts with a prefix.

    Args:
        value: The value to validate.
        prefix: The prefix to check for.
        case_sensitive: Whether the check should be case-sensitive. Default is True.

    Raises:
        ValidationError: If the string does not start with the prefix.
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"Expected a string, got {type(value).__name__}",
            None,
            value,
        )

    if case_sensitive:
        if not value.startswith(prefix):
            raise ValidationError(
                f"String '{value}' does not start with '{prefix}'",
                None,
                value,
            )
    else:
        if not value.lower().startswith(prefix.lower()):
            raise ValidationError(
                f"String '{value}' does not start with '{prefix}' (case-insensitive)",
                None,
                value,
            )


def ends_with(value: str, suffix: str, case_sensitive: bool = True) -> None:
    """
    Validate that a string ends with a suffix.

    Args:
        value: The value to validate.
        suffix: The suffix to check for.
        case_sensitive: Whether the check should be case-sensitive. Default is True.

    Raises:
        ValidationError: If the string does not end with the suffix.
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"Expected a string, got {type(value).__name__}",
            None,
            value,
        )

    if case_sensitive:
        if not value.endswith(suffix):
            raise ValidationError(
                f"String '{value}' does not end with '{suffix}'",
                None,
                value,
            )
    else:
        if not value.lower().endswith(suffix.lower()):
            raise ValidationError(
                f"String '{value}' does not end with '{suffix}' (case-insensitive)",
                None,
                value,
            )


class MinLengthValidator(Validator):
    """Validator that checks if a string has at least a minimum length."""

    def __init__(self, min_length: int):
        """
        Initialize the validator.

        Args:
            min_length: The minimum length.
        """
        self.min_length = min_length

    def validate(
        self,
        func: Callable,
        value: Any,
        field_name: str,
        source_info: str = None,
        parent_object: Any = None,
    ) -> ValidationResult:
        """
        Validate that a string has at least a minimum length.

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

        # Ensure value is a string
        if not isinstance(value, str):
            result.add_error(
                ValidationError(
                    f"Expected a string for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                    source_info,
                    parent_object,
                )
            )
            return result

        # Check if the string has at least the minimum length
        if len(value) < self.min_length:
            result.add_error(
                ValidationError(
                    f"String length {len(value)} is less than the minimum length of {self.min_length}",
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
        For MinLengthValidator, this does nothing by default.

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


class MaxLengthValidator(Validator):
    """Validator that checks if a string does not exceed a maximum length."""

    def __init__(self, max_length: int):
        """
        Initialize the validator.

        Args:
            max_length: The maximum length.
        """
        self.max_length = max_length

    def validate(
        self,
        func: Callable,
        value: Any,
        field_name: str,
        source_info: str = None,
        parent_object: Any = None,
    ) -> ValidationResult:
        """
        Validate that a string does not exceed a maximum length.

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

        # Ensure value is a string
        if not isinstance(value, str):
            result.add_error(
                ValidationError(
                    f"Expected a string for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                    source_info,
                    parent_object,
                )
            )
            return result

        # Check if the string does not exceed the maximum length
        if len(value) > self.max_length:
            result.add_error(
                ValidationError(
                    f"String length {len(value)} exceeds the maximum length of {self.max_length}",
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
        For MaxLengthValidator, this does nothing by default.

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


class LengthRangeValidator(Validator):
    """Validator that checks if a string length is within a range."""

    def __init__(self, min_length: int, max_length: int):
        """
        Initialize the validator.

        Args:
            min_length: The minimum length.
            max_length: The maximum length.
        """
        self.min_length = min_length
        self.max_length = max_length

    def validate(
        self,
        func: Callable,
        value: Any,
        field_name: str,
        source_info: str = None,
        parent_object: Any = None,
    ) -> ValidationResult:
        """
        Validate that a string length is within a range.

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

        # Ensure value is a string
        if not isinstance(value, str):
            result.add_error(
                ValidationError(
                    f"Expected a string for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                    source_info,
                    parent_object,
                )
            )
            return result

        # Check if the string length is within the range
        if len(value) < self.min_length:
            result.add_error(
                ValidationError(
                    f"String length {len(value)} is less than the minimum length of {self.min_length}",
                    field_name,
                    value,
                    source_info,
                    parent_object,
                )
            )
        elif len(value) > self.max_length:
            result.add_error(
                ValidationError(
                    f"String length {len(value)} exceeds the maximum length of {self.max_length}",
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
        For LengthRangeValidator, this does nothing by default.

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


class PatternValidator(Validator):
    """Validator that checks if a string matches a pattern."""

    def __init__(self, pattern: Union[str, Pattern]):
        """
        Initialize the validator.

        Args:
            pattern: The regular expression pattern to match.
        """
        self.pattern = pattern if isinstance(pattern, Pattern) else re.compile(pattern)

    def validate(
        self,
        func: Callable,
        value: Any,
        field_name: str,
        source_info: str = None,
        parent_object: Any = None,
    ) -> ValidationResult:
        """
        Validate that a string matches a pattern.

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

        # Ensure value is a string
        if not isinstance(value, str):
            result.add_error(
                ValidationError(
                    f"Expected a string for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                    source_info,
                    parent_object,
                )
            )
            return result

        # Check if the string matches the pattern
        if not self.pattern.match(value):
            result.add_error(
                ValidationError(
                    f"String '{value}' does not match the pattern '{self.pattern.pattern}'",
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
        For PatternValidator, this does nothing by default.

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


class ContainsValidator(Validator):
    """Validator that checks if a string contains a substring."""

    def __init__(self, substring: str, case_sensitive: bool = True):
        """
        Initialize the validator.

        Args:
            substring: The substring to check for.
            case_sensitive: Whether the check should be case-sensitive. Default is True.
        """
        self.substring = substring
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
        Validate that a string contains a substring.

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

        # Ensure value is a string
        if not isinstance(value, str):
            result.add_error(
                ValidationError(
                    f"Expected a string for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                    source_info,
                    parent_object,
                )
            )
            return result

        # Check if the string contains the substring
        if self.case_sensitive:
            if self.substring not in value:
                result.add_error(
                    ValidationError(
                        f"String '{value}' does not contain the substring '{self.substring}'",
                        field_name,
                        value,
                        source_info,
                        parent_object,
                    )
                )
        else:
            if self.substring.lower() not in value.lower():
                result.add_error(
                    ValidationError(
                        f"String '{value}' does not contain the substring '{self.substring}' (case-insensitive)",
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
        For ContainsValidator, this does nothing by default.

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


class StartsWithValidator(Validator):
    """Validator that checks if a string starts with a prefix."""

    def __init__(self, prefix: str, case_sensitive: bool = True):
        """
        Initialize the validator.

        Args:
            prefix: The prefix to check for.
            case_sensitive: Whether the check should be case-sensitive. Default is True.
        """
        self.prefix = prefix
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
        Validate that a string starts with a prefix.

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

        # Ensure value is a string
        if not isinstance(value, str):
            result.add_error(
                ValidationError(
                    f"Expected a string for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                    source_info,
                    parent_object,
                )
            )
            return result

        # Check if the string starts with the prefix
        if self.case_sensitive:
            if not value.startswith(self.prefix):
                result.add_error(
                    ValidationError(
                        f"String '{value}' does not start with '{self.prefix}'",
                        field_name,
                        value,
                        source_info,
                        parent_object,
                    )
                )
        else:
            if not value.lower().startswith(self.prefix.lower()):
                result.add_error(
                    ValidationError(
                        f"String '{value}' does not start with '{self.prefix}' (case-insensitive)",
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
        For StartsWithValidator, this does nothing by default.

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


class EndsWithValidator(Validator):
    """Validator that checks if a string ends with a suffix."""

    def __init__(self, suffix: str, case_sensitive: bool = True):
        """
        Initialize the validator.

        Args:
            suffix: The suffix to check for.
            case_sensitive: Whether the check should be case-sensitive. Default is True.
        """
        self.suffix = suffix
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
        Validate that a string ends with a suffix.

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

        # Ensure value is a string
        if not isinstance(value, str):
            result.add_error(
                ValidationError(
                    f"Expected a string for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                    source_info,
                    parent_object,
                )
            )
            return result

        # Check if the string ends with the suffix
        if self.case_sensitive:
            if not value.endswith(self.suffix):
                result.add_error(
                    ValidationError(
                        f"String '{value}' does not end with '{self.suffix}'",
                        field_name,
                        value,
                        source_info,
                        parent_object,
                    )
                )
        else:
            if not value.lower().endswith(self.suffix.lower()):
                result.add_error(
                    ValidationError(
                        f"String '{value}' does not end with '{self.suffix}' (case-insensitive)",
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
        For EndsWithValidator, this does nothing by default.

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
def min_length_check(value, min_length: int):
    """
    Check if a string has at least a minimum length.

    Args:
        value: The string to check.
        min_length: The minimum length.

    Raises:
        ValidationError: If the string is shorter than the minimum length.
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

    validator = MinLengthValidator(min_length)
    result = validator.validate(min_length_check, value, field_name or "value")
    if not result.is_valid:
        raise ValidationError(result.errors[0].message, field_name, value)


def max_length_check(value, max_length: int):
    """
    Check if a string has at most a maximum length.

    Args:
        value: The string to check.
        max_length: The maximum length.

    Raises:
        ValidationError: If the string is longer than the maximum length.
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

    validator = MaxLengthValidator(max_length)
    result = validator.validate(max_length_check, value, field_name or "value")
    if not result.is_valid:
        raise ValidationError(result.errors[0].message, field_name, value)


def length_between_check(min_length: int, max_length: int):
    """
    Create a validator function that checks if a string length is between a minimum and maximum.

    Args:
        min_length: The minimum length.
        max_length: The maximum length.

    Returns:
        A function that validates the length range of a string.
    """
    validator = LengthRangeValidator(min_length, max_length)

    def validate_length_range(value):
        """Validate that a string length is within a range."""
        result = validator.validate(validate_length_range, value, "value")
        if not result.is_valid:
            raise ValidationError(result.errors[0].message, None, value)

    return validate_length_range


def pattern_check(value, pattern: str, flags: int = 0):
    """
    Check if a string matches a regular expression pattern.

    Args:
        value: The string to check.
        pattern: The regular expression pattern to match against.
        flags: Regular expression flags. Default is 0.

    Raises:
        ValidationError: If the string does not match the pattern.
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

    validator = PatternValidator(pattern, flags)
    result = validator.validate(pattern_check, value, field_name or "value")
    if not result.is_valid:
        raise ValidationError(result.errors[0].message, field_name, value)


def contains_check(value, substring: str, case_sensitive: bool = True):
    """
    Check if a string contains a substring.

    Args:
        value: The string to check.
        substring: The substring to check for.
        case_sensitive: Whether the check should be case-sensitive. Default is True.

    Raises:
        ValidationError: If the string does not contain the substring.
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

    validator = ContainsValidator(substring, case_sensitive)
    result = validator.validate(contains_check, value, field_name or "value")
    if not result.is_valid:
        raise ValidationError(result.errors[0].message, field_name, value)


def starts_with_check(value, prefix: str, case_sensitive: bool = True):
    """
    Check if a string starts with a prefix.

    Args:
        value: The string to check.
        prefix: The prefix to check for.
        case_sensitive: Whether the check should be case-sensitive. Default is True.

    Raises:
        ValidationError: If the string does not start with the prefix.
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

    validator = StartsWithValidator(prefix, case_sensitive)
    result = validator.validate(starts_with_check, value, field_name or "value")
    if not result.is_valid:
        raise ValidationError(result.errors[0].message, field_name, value)


def ends_with_check(value, suffix: str, case_sensitive: bool = True):
    """
    Create a validator function that checks if a string ends with a suffix.

    Args:
        value: The string to check.
        suffix: The suffix to check for.
        case_sensitive: Whether the check should be case-sensitive. Default is True.

    Raises:
        ValidationError: If the string does not end with the suffix.
    """
    validator = EndsWithValidator(suffix, case_sensitive)

    def validate_ends_with(value):
        """Validate that a string ends with a suffix."""
        result = validator.validate(validate_ends_with, value, "value")
        if not result.is_valid:
            raise ValidationError(result.errors[0].message, None, value)

    return validate_ends_with
