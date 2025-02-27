import re
from typing import Any, Callable, Optional, Pattern as RegexPattern

from uhmactually.core import (
    Validator,
    ValidationError,
    ValidationResult,
)
from uhmactually.validators.registry import validator


@validator
class ContainsValidator(Validator):
    """Validator that checks if a string contains a substring."""

    def __init__(self, substring: str = "", case_sensitive: bool = True):
        """
        Initialize the validator.

        Args:
            substring: The substring to check for.
            case_sensitive: Whether the check should be case-sensitive. Default is True.
        """
        self.substring = substring
        self.case_sensitive = case_sensitive

    def validate(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Validate that a string contains the specified substring.

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

        # Ensure value is a string
        if not isinstance(value, str):
            result.add_error(
                ValidationError(
                    f"Expected a string for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                )
            )
            return result

        # Check if the string contains the substring
        if self.case_sensitive:
            if self.substring not in value:
                result.add_error(
                    ValidationError(
                        f"String '{value}' does not contain '{self.substring}'",
                        field_name,
                        value,
                    )
                )
        else:
            if self.substring.lower() not in value.lower():
                result.add_error(
                    ValidationError(
                        f"String '{value}' does not contain '{self.substring}' (case-insensitive)",
                        field_name,
                        value,
                    )
                )

        return result

    def default(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        return ValidationResult()


@validator
class BeginsWithValidator(Validator):
    """Validator that checks if a string begins with a prefix."""

    def __init__(self, prefix: str = "", case_sensitive: bool = True):
        """
        Initialize the validator.

        Args:
            prefix: The prefix to check for.
            case_sensitive: Whether the check should be case-sensitive. Default is True.
        """
        self.prefix = prefix
        self.case_sensitive = case_sensitive

    def validate(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Validate that a string begins with the specified prefix.

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

        # Ensure value is a string
        if not isinstance(value, str):
            result.add_error(
                ValidationError(
                    f"Expected a string for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                )
            )
            return result

        # Check if the string begins with the prefix
        if self.case_sensitive:
            if not value.startswith(self.prefix):
                result.add_error(
                    ValidationError(
                        f"String '{value}' does not begin with '{self.prefix}'",
                        field_name,
                        value,
                    )
                )
        else:
            if not value.lower().startswith(self.prefix.lower()):
                result.add_error(
                    ValidationError(
                        f"String '{value}' does not begin with '{self.prefix}' (case-insensitive)",
                        field_name,
                        value,
                    )
                )

        return result

    def default(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        return ValidationResult()


@validator
class PatternValidator(Validator):
    """Validator that checks if a string matches a regular expression pattern."""

    def __init__(self, pattern: str = "(.*?)", flags: int = 0):
        """
        Initialize the validator.

        Args:
            pattern: The regular expression pattern to match against.
            flags: Regular expression flags (e.g., re.IGNORECASE). Default is 0.
        """
        self.pattern = pattern
        self.flags = flags
        self.compiled_pattern = re.compile(pattern, flags)

    def validate(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Validate that a string matches the specified pattern.

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

        # Ensure value is a string
        if not isinstance(value, str):
            result.add_error(
                ValidationError(
                    f"Expected a string for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                )
            )
            return result

        # Check if the string matches the pattern
        if not self.compiled_pattern.match(value):
            result.add_error(
                ValidationError(
                    f"String '{value}' does not match pattern '{self.pattern}'",
                    field_name,
                    value,
                )
            )

        return result

    def default(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        return ValidationResult()


@validator
class MinLengthValidator(Validator):
    """Validator that checks if a string has a minimum length."""

    def __init__(self, min_length: int = 0):
        """
        Initialize the validator.

        Args:
            min_length: The minimum length required.
        """
        self.min_length = min_length

    def validate(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Validate that a string has at least the minimum length.

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

        # Ensure value is a string
        if not isinstance(value, str):
            result.add_error(
                ValidationError(
                    f"Expected a string for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                )
            )
            return result

        # Check if the string has at least the minimum length
        if len(value) < self.min_length:
            result.add_error(
                ValidationError(
                    f"String '{value}' has length {len(value)}, which is less than the minimum length of {self.min_length}",
                    field_name,
                    value,
                )
            )

        return result

    def default(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        return ValidationResult()


@validator
class MaxLengthValidator(Validator):
    """Validator that checks if a string has a maximum length."""

    def __init__(self, max_length: int = float("inf")):
        """
        Initialize the validator.

        Args:
            max_length: The maximum length allowed.
        """
        self.max_length = max_length

    def validate(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Validate that a string does not exceed the maximum length.

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

        # Ensure value is a string
        if not isinstance(value, str):
            result.add_error(
                ValidationError(
                    f"Expected a string for field '{field_name}', got {type(value).__name__}",
                    field_name,
                    value,
                )
            )
            return result

        # Check if the string does not exceed the maximum length
        if len(value) > self.max_length:
            result.add_error(
                ValidationError(
                    f"String '{value}' has length {len(value)}, which exceeds the maximum length of {self.max_length}",
                    field_name,
                    value,
                )
            )

        return result

    def default(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        return ValidationResult()


# Decorator factories
def contains(substring: str, case_sensitive: bool = True):
    """Decorator to validate that a string contains a substring."""
    return ContainsValidator.create_decorator(substring, case_sensitive)


def begins_with(prefix: str, case_sensitive: bool = True):
    """Decorator to validate that a string begins with a prefix."""
    return BeginsWithValidator.create_decorator(prefix, case_sensitive)


def pattern(pattern: str, flags: int = 0):
    """Decorator to validate that a string matches a regular expression pattern."""
    return PatternValidator.create_decorator(pattern, flags)


def min_length(min_length: int):
    """Decorator to validate that a string has a minimum length."""
    return MinLengthValidator.create_decorator(min_length)


def max_length(max_length: int):
    """Decorator to validate that a string has a maximum length."""
    return MaxLengthValidator.create_decorator(max_length)
