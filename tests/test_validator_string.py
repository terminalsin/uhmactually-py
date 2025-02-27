import pytest
import re
from typing import Optional

from uhmactually.core import (
    ValidationError,
    ValidatedModel,
    validate,
)
from uhmactually.validators import (
    contains_check,
    starts_with_check,
    pattern_check,
    min_length_check,
    max_length_check,
)


# Test Models
class StringValidatorModel(ValidatedModel):
    """A model with string validators."""

    @validate
    def contains_test(self, value=None) -> str:
        if value is not None:
            contains_check(value, "test")
        return value

    @validate
    def contains_test_case_insensitive(self, value=None) -> str:
        if value is not None:
            # Note: case_sensitive parameter is not supported in the new approach
            # We would need to implement a custom check for this
            if "test".lower() not in value.lower():
                raise ValidationError(
                    f"String '{value}' does not contain the substring 'TEST' (case-insensitive)",
                    None,
                    value,
                )
        return value

    @validate
    def begins_with_prefix(self, value=None) -> str:
        if value is not None:
            starts_with_check(value, "prefix_")
        return value

    @validate
    def begins_with_prefix_case_insensitive(self, value=None) -> str:
        if value is not None:
            # Note: case_sensitive parameter is not supported in the new approach
            # We would need to implement a custom check for this
            if not value.lower().startswith("prefix_".lower()):
                raise ValidationError(
                    f"String '{value}' does not start with 'PREFIX_' (case-insensitive)",
                    None,
                    value,
                )
        return value

    @validate
    def ssn(self, value=None) -> str:
        if value is not None:
            pattern_check(value, r"^\d{3}-\d{2}-\d{4}$")
        return value

    @validate
    def letters_only(self, value=None) -> str:
        if value is not None:
            # Note: flags parameter is not supported in the new approach
            # We would need to implement a custom check for this
            if not re.match(r"^[a-zA-Z]+$", value):
                raise ValidationError(
                    f"String '{value}' does not match the pattern '^[a-z]+$' (case-insensitive)",
                    None,
                    value,
                )
        return value

    @validate
    def min_five_chars(self, value=None) -> str:
        if value is not None:
            min_length_check(value, 5)
        return value

    @validate
    def max_ten_chars(self, value=None) -> str:
        if value is not None:
            max_length_check(value, 10)
        return value


class CombinedStringValidatorModel(ValidatedModel):
    """A model with combined string validators."""

    @validate
    def password(self, value=None) -> str:
        if value is not None:
            min_length_check(value, 8)
            max_length_check(value, 20)
            pattern_check(
                value,
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$",
            )
        return value

    @validate
    def secure_website(self, value=None) -> str:
        if value is not None:
            starts_with_check(value, "https://")
            contains_check(value, ".com")
        return value


# Parametrized Tests for ContainsValidator
@pytest.mark.parametrize(
    "contains_test,should_pass",
    [
        # Valid cases
        ("This is a test string", True),
        ("test at the beginning", True),
        ("at the end test", True),
        # Invalid cases
        ("This does not contain the word", False),
        ("", False),
        (None, False),  # None is skipped in validation
    ],
)
def test_contains_validator(contains_test, should_pass):
    """Test contains validator with various inputs."""
    if should_pass:
        model = StringValidatorModel(
            contains_test=contains_test,
            contains_test_case_insensitive="Contains TEST somewhere",
            begins_with_prefix="prefix_value",
            begins_with_prefix_case_insensitive="PREFIX_value",
            ssn="123-45-6789",
            letters_only="abcDEF",
            min_five_chars="12345",
            max_ten_chars="1234567890",
        )
        assert model.contains_test() == contains_test
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            StringValidatorModel(
                contains_test=contains_test,
                contains_test_case_insensitive="Contains TEST somewhere",
                begins_with_prefix="prefix_value",
                begins_with_prefix_case_insensitive="PREFIX_value",
                ssn="123-45-6789",
                letters_only="abcDEF",
                min_five_chars="12345",
                max_ten_chars="1234567890",
            )
        assert "does not contain" in str(excinfo.value)


# Parametrized Tests for ContainsValidator with case insensitivity
@pytest.mark.parametrize(
    "contains_test_case_insensitive,should_pass",
    [
        # Valid cases - exact match
        ("This contains TEST exactly", True),
        # Valid cases - different case
        ("This contains test in lowercase", True),
        ("This contains Test with mixed case", True),
        # Invalid cases
        ("This does not contain the word", False),
        ("", False),
        (None, False),  # None is skipped in validation
    ],
)
def test_contains_case_insensitive_validator(
    contains_test_case_insensitive, should_pass
):
    """Test contains validator with case-insensitive comparison."""
    if should_pass:
        model = StringValidatorModel(
            contains_test="This is a test string",
            contains_test_case_insensitive=contains_test_case_insensitive,
            begins_with_prefix="prefix_value",
            begins_with_prefix_case_insensitive="PREFIX_value",
            ssn="123-45-6789",
            letters_only="abcDEF",
            min_five_chars="12345",
            max_ten_chars="1234567890",
        )
        assert model.contains_test_case_insensitive() == contains_test_case_insensitive
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            StringValidatorModel(
                contains_test="This is a test string",
                contains_test_case_insensitive=contains_test_case_insensitive,
                begins_with_prefix="prefix_value",
                begins_with_prefix_case_insensitive="PREFIX_value",
                ssn="123-45-6789",
                letters_only="abcDEF",
                min_five_chars="12345",
                max_ten_chars="1234567890",
            )
        assert "does not contain" in str(excinfo.value)


# Parametrized Tests for BeginsWithValidator
@pytest.mark.parametrize(
    "begins_with_prefix,should_pass",
    [
        # Valid cases
        ("prefix_value", True),
        ("prefix_another_value", True),
        # Invalid cases
        ("no_prefix", False),
        ("wrong_prefix_value", False),
        ("", False),
        (None, False),  # None is skipped in validation
    ],
)
def test_begins_with_validator(begins_with_prefix, should_pass):
    """Test begins_with validator with various inputs."""
    if should_pass:
        model = StringValidatorModel(
            contains_test="This is a test string",
            contains_test_case_insensitive="Contains TEST somewhere",
            begins_with_prefix=begins_with_prefix,
            begins_with_prefix_case_insensitive="PREFIX_value",
            ssn="123-45-6789",
            letters_only="abcDEF",
            min_five_chars="12345",
            max_ten_chars="1234567890",
        )
        assert model.begins_with_prefix() == begins_with_prefix
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            StringValidatorModel(
                contains_test="This is a test string",
                contains_test_case_insensitive="Contains TEST somewhere",
                begins_with_prefix=begins_with_prefix,
                begins_with_prefix_case_insensitive="PREFIX_value",
                ssn="123-45-6789",
                letters_only="abcDEF",
                min_five_chars="12345",
                max_ten_chars="1234567890",
            )
        assert "does not begin with" in str(excinfo.value)


# Parametrized Tests for BeginsWithValidator with case insensitivity
@pytest.mark.parametrize(
    "begins_with_prefix_case_insensitive,should_pass",
    [
        # Valid cases - exact match
        ("PREFIX_value", True),
        # Valid cases - different case
        ("prefix_value", True),
        ("Prefix_value", True),
        # Invalid cases
        ("no_prefix", False),
        ("wrong_prefix_value", False),
        ("", False),
        (None, False),  # None is skipped in validation
    ],
)
def test_begins_with_case_insensitive_validator(
    begins_with_prefix_case_insensitive, should_pass
):
    """Test begins_with validator with case-insensitive comparison."""
    if should_pass:
        model = StringValidatorModel(
            contains_test="This is a test string",
            contains_test_case_insensitive="Contains TEST somewhere",
            begins_with_prefix="prefix_value",
            begins_with_prefix_case_insensitive=begins_with_prefix_case_insensitive,
            ssn="123-45-6789",
            letters_only="abcDEF",
            min_five_chars="12345",
            max_ten_chars="1234567890",
        )
        assert (
            model.begins_with_prefix_case_insensitive()
            == begins_with_prefix_case_insensitive
        )
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            StringValidatorModel(
                contains_test="This is a test string",
                contains_test_case_insensitive="Contains TEST somewhere",
                begins_with_prefix="prefix_value",
                begins_with_prefix_case_insensitive=begins_with_prefix_case_insensitive,
                ssn="123-45-6789",
                letters_only="abcDEF",
                min_five_chars="12345",
                max_ten_chars="1234567890",
            )
        assert "does not begin with" in str(excinfo.value)


# Parametrized Tests for PatternValidator
@pytest.mark.parametrize(
    "ssn,should_pass",
    [
        # Valid cases
        ("123-45-6789", True),
        ("987-65-4321", True),
        # Invalid cases
        ("123-456-789", False),
        ("12-34-5678", False),
        ("123-45-678", False),
        ("abc-de-fghi", False),
        ("", False),
        (None, True),  # None is skipped in validation
    ],
)
def test_pattern_validator(ssn, should_pass):
    """Test pattern validator with various inputs."""
    if should_pass:
        model = StringValidatorModel(
            contains_test="This is a test string",
            contains_test_case_insensitive="Contains TEST somewhere",
            begins_with_prefix="prefix_value",
            begins_with_prefix_case_insensitive="PREFIX_value",
            ssn=ssn,
            letters_only="abcDEF",
            min_five_chars="12345",
            max_ten_chars="1234567890",
        )
        assert model.ssn() == ssn
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            StringValidatorModel(
                contains_test="This is a test string",
                contains_test_case_insensitive="Contains TEST somewhere",
                begins_with_prefix="prefix_value",
                begins_with_prefix_case_insensitive="PREFIX_value",
                ssn=ssn,
                letters_only="abcDEF",
                min_five_chars="12345",
                max_ten_chars="1234567890",
            )
        assert "does not match pattern" in str(excinfo.value)


# Parametrized Tests for PatternValidator with flags
@pytest.mark.parametrize(
    "letters_only,should_pass",
    [
        # Valid cases
        ("abcdef", True),
        ("ABCDEF", True),  # Due to IGNORECASE flag
        ("AbCdEf", True),  # Mixed case
        # Invalid cases
        ("abc123", False),
        ("abc-def", False),
        ("", False),
        (None, True),  # None is skipped in validation
    ],
)
def test_pattern_with_flags_validator(letters_only, should_pass):
    """Test pattern validator with regex flags."""
    if should_pass:
        model = StringValidatorModel(
            contains_test="This is a test string",
            contains_test_case_insensitive="Contains TEST somewhere",
            begins_with_prefix="prefix_value",
            begins_with_prefix_case_insensitive="PREFIX_value",
            ssn="123-45-6789",
            letters_only=letters_only,
            min_five_chars="12345",
            max_ten_chars="1234567890",
        )
        assert model.letters_only() == letters_only
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            StringValidatorModel(
                contains_test="This is a test string",
                contains_test_case_insensitive="Contains TEST somewhere",
                begins_with_prefix="prefix_value",
                begins_with_prefix_case_insensitive="PREFIX_value",
                ssn="123-45-6789",
                letters_only=letters_only,
                min_five_chars="12345",
                max_ten_chars="1234567890",
            )
        assert "does not match pattern" in str(excinfo.value)


# Parametrized Tests for MinLengthValidator
@pytest.mark.parametrize(
    "min_five_chars,should_pass",
    [
        # Valid cases
        ("12345", True),  # Exactly 5 characters
        ("123456", True),  # More than 5 characters
        ("abcdefghij", True),
        # Invalid cases
        ("1234", False),  # Less than 5 characters
        ("", False),
        (None, False),  # None is skipped in validation
    ],
)
def test_min_length_validator(min_five_chars, should_pass):
    """Test min_length validator with various inputs."""
    if should_pass:
        model = StringValidatorModel(
            contains_test="This is a test string",
            contains_test_case_insensitive="Contains TEST somewhere",
            begins_with_prefix="prefix_value",
            begins_with_prefix_case_insensitive="PREFIX_value",
            ssn="123-45-6789",
            letters_only="abcDEF",
            min_five_chars=min_five_chars,
            max_ten_chars="1234567890",
        )
        assert model.min_five_chars() == min_five_chars
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            StringValidatorModel(
                contains_test="This is a test string",
                contains_test_case_insensitive="Contains TEST somewhere",
                begins_with_prefix="prefix_value",
                begins_with_prefix_case_insensitive="PREFIX_value",
                ssn="123-45-6789",
                letters_only="abcDEF",
                min_five_chars=min_five_chars,
                max_ten_chars="1234567890",
            )
        assert "less than the minimum length" in str(excinfo.value)


# Parametrized Tests for MaxLengthValidator
@pytest.mark.parametrize(
    "max_ten_chars,should_pass",
    [
        # Valid cases
        ("", True),  # Empty string
        ("12345", True),  # Less than 10 characters
        ("1234567890", True),  # Exactly 10 characters
        # Invalid cases
        ("12345678901", False),  # More than 10 characters
        ("abcdefghijklmnop", False),
        (None, False),  # None is skipped in validation
    ],
)
def test_max_length_validator(max_ten_chars, should_pass):
    """Test max_length validator with various inputs."""
    if should_pass:
        model = StringValidatorModel(
            contains_test="This is a test string",
            contains_test_case_insensitive="Contains TEST somewhere",
            begins_with_prefix="prefix_value",
            begins_with_prefix_case_insensitive="PREFIX_value",
            ssn="123-45-6789",
            letters_only="abcDEF",
            min_five_chars="12345",
            max_ten_chars=max_ten_chars,
        )
        assert model.max_ten_chars() == max_ten_chars
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            StringValidatorModel(
                contains_test="This is a test string",
                contains_test_case_insensitive="Contains TEST somewhere",
                begins_with_prefix="prefix_value",
                begins_with_prefix_case_insensitive="PREFIX_value",
                ssn="123-45-6789",
                letters_only="abcDEF",
                min_five_chars="12345",
                max_ten_chars=max_ten_chars,
            )
        assert "exceeds the maximum length" in str(excinfo.value)


# Parametrized Tests for Combined String Validators
@pytest.mark.parametrize(
    "password,should_pass",
    [
        # Valid cases
        ("Password1!", True),  # Valid password
        ("Str0ng@P4ssw0rd", True),
        # Invalid cases - too short
        ("Pass1!", False),
        # Invalid cases - too long
        ("ThisPasswordIsWayTooLong1!", False),
        # Invalid cases - missing requirements
        ("password1!", False),  # No uppercase
        ("PASSWORD1!", False),  # No lowercase
        ("Password!", False),  # No digit
        ("Password1", False),  # No special character
        (None, False),  # None is skipped in validation
    ],
)
def test_combined_password_validators(password, should_pass):
    """Test combined validators for password validation."""
    if should_pass:
        model = CombinedStringValidatorModel(
            password=password,
            secure_website="https://example.com",
        )
        assert model.password() == password
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError):
            CombinedStringValidatorModel(
                password=password,
                secure_website="https://example.com",
            )


@pytest.mark.parametrize(
    "secure_website,should_pass",
    [
        # Valid cases
        ("https://example.com", True),
        ("https://test.com/path", True),
        # Invalid cases - wrong protocol
        ("http://example.com", False),
        # Invalid cases - missing .com
        ("https://example.org", False),
        (None, False),  # None is skipped in validation
    ],
)
def test_combined_url_validators(secure_website, should_pass):
    """Test combined validators for URL validation."""
    if should_pass:
        model = CombinedStringValidatorModel(
            password="Password1!",
            secure_website=secure_website,
        )
        assert model.secure_website() == secure_website
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError):
            CombinedStringValidatorModel(
                password="Password1!",
                secure_website=secure_website,
            )


# Test error messages
def test_contains_error_message():
    """Test that ContainsValidator produces the expected error message."""
    with pytest.raises(ValidationError) as excinfo:
        StringValidatorModel(
            contains_test="No substring here",  # Invalid
            contains_test_case_insensitive="Contains TEST somewhere",
            begins_with_prefix="prefix_value",
            begins_with_prefix_case_insensitive="PREFIX_value",
            ssn="123-45-6789",
            letters_only="abcDEF",
            min_five_chars="12345",
            max_ten_chars="1234567890",
        )
    error_message = str(excinfo.value)
    assert "String 'No substring here' does not contain 'test'" in error_message


def test_begins_with_error_message():
    """Test that BeginsWithValidator produces the expected error message."""
    with pytest.raises(ValidationError) as excinfo:
        StringValidatorModel(
            contains_test="This is a test string",
            contains_test_case_insensitive="Contains TEST somewhere",
            begins_with_prefix="wrong_prefix",  # Invalid
            begins_with_prefix_case_insensitive="PREFIX_value",
            ssn="123-45-6789",
            letters_only="abcDEF",
            min_five_chars="12345",
            max_ten_chars="1234567890",
        )
    error_message = str(excinfo.value)
    assert "String 'wrong_prefix' does not begin with 'prefix_'" in error_message


def test_pattern_error_message():
    """Test that PatternValidator produces the expected error message."""
    with pytest.raises(ValidationError) as excinfo:
        StringValidatorModel(
            contains_test="This is a test string",
            contains_test_case_insensitive="Contains TEST somewhere",
            begins_with_prefix="prefix_value",
            begins_with_prefix_case_insensitive="PREFIX_value",
            ssn="invalid-ssn",  # Invalid
            letters_only="abcDEF",
            min_five_chars="12345",
            max_ten_chars="1234567890",
        )
    error_message = str(excinfo.value)
    assert "String 'invalid-ssn' does not match pattern" in error_message


def test_min_length_error_message():
    """Test that MinLengthValidator produces the expected error message."""
    with pytest.raises(ValidationError) as excinfo:
        StringValidatorModel(
            contains_test="This is a test string",
            contains_test_case_insensitive="Contains TEST somewhere",
            begins_with_prefix="prefix_value",
            begins_with_prefix_case_insensitive="PREFIX_value",
            ssn="123-45-6789",
            letters_only="abcDEF",
            min_five_chars="1234",  # Invalid
            max_ten_chars="1234567890",
        )
    error_message = str(excinfo.value)
    assert (
        "String '1234' has length 4, which is less than the minimum length of 5"
        in error_message
    )


def test_max_length_error_message():
    """Test that MaxLengthValidator produces the expected error message."""
    with pytest.raises(ValidationError) as excinfo:
        StringValidatorModel(
            contains_test="This is a test string",
            contains_test_case_insensitive="Contains TEST somewhere",
            begins_with_prefix="prefix_value",
            begins_with_prefix_case_insensitive="PREFIX_value",
            ssn="123-45-6789",
            letters_only="abcDEF",
            min_five_chars="12345",
            max_ten_chars="12345678901",  # Invalid
        )
    error_message = str(excinfo.value)
    assert (
        "String '12345678901' has length 11, which exceeds the maximum length of 10"
        in error_message
    )


# Test validation results
def test_string_validation_results():
    """Test that validation results contain the expected errors."""
    # Create a model with valid values
    model = StringValidatorModel(
        contains_test="This is a test string",
        contains_test_case_insensitive="Contains TEST somewhere",
        begins_with_prefix="prefix_value",
        begins_with_prefix_case_insensitive="PREFIX_value",
        ssn="123-45-6789",
        letters_only="abcDEF",
        min_five_chars="12345",
        max_ten_chars="1234567890",
    )

    # Manually set invalid values to bypass initialization validation
    model._data["contains_test"] = "No substring here"
    model._data["min_five_chars"] = "1234"
    model._data["max_ten_chars"] = "12345678901"

    with pytest.raises(ValidationError) as excinfo:
        # Validate the model
        result = model.validate()

        # Check that validation failed
    assert not result.is_valid

    # Check that the expected errors are present
    errors = result.errors
    assert len(errors) == 3

    # Check error fields
    error_fields = [error.field for error in errors]
    assert "contains_test" in error_fields
    assert "min_five_chars" in error_fields
    assert "max_ten_chars" in error_fields


# Test type validation
def test_string_type_validation():
    """Test that validators check for string types."""
    with pytest.raises(ValidationError) as excinfo:
        StringValidatorModel(
            contains_test=123,  # Invalid type
            contains_test_case_insensitive="Contains TEST somewhere",
            begins_with_prefix="prefix_value",
            begins_with_prefix_case_insensitive="PREFIX_value",
            ssn="123-45-6789",
            letters_only="abcDEF",
            min_five_chars="12345",
            max_ten_chars="1234567890",
        )
    error_message = str(excinfo.value)
    assert "Expected a string" in error_message
