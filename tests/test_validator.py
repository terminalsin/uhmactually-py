import pytest
from typing import Optional, List, Any, Type, Union, get_type_hints
import re
import inspect

from uhmactually.validator import (
    ValidatedModel,
    Validator,
    ValidationInput,
    ValidationResult,
    ValidationException,
    validator,
    validate,
    fail,
    success,
)


# --------------------------------
# Test Validator Implementations
# --------------------------------


@validator
class EmailValidator(Validator):
    """Validates that a value is a valid email address according to RFC 5322."""

    def validate(self, input: ValidationInput) -> ValidationResult:
        value = input.value
        if value is None:
            raise ValidationException(
                message="Email cannot be None",
                field_name=input.field_name,
                received={"value": value},
                expected={"type": "string"},
            )

        if not isinstance(value, str):
            raise ValidationException(
                message=f"Expected string, got {type(value).__name__}",
                field_name=input.field_name,
                received={"value": value, "type": type(value).__name__},
                expected={"type": "string"},
            )

        # Check for empty email
        if not value.strip():
            raise ValidationException(
                message="Email cannot be empty",
                field_name=input.field_name,
                received={"value": value},
                expected={"non-empty": True},
            )

        # Start with basic check for @ symbol
        if "@" not in value:
            raise ValidationException(
                message="Invalid email format: missing @ symbol",
                field_name=input.field_name,
                received={"value": value},
                expected={"format": "valid email containing @ symbol"},
            )

        # Check for multiple @ symbols
        if value.count("@") > 1:
            raise ValidationException(
                message="Invalid email format: multiple @ symbols",
                field_name=input.field_name,
                received={"value": value},
                expected={"format": "valid email with exactly one @ symbol"},
            )

        # Split the email into local and domain parts
        try:
            local_part, domain_part = value.rsplit("@", 1)
        except ValueError:
            raise ValidationException(
                message="Invalid email format",
                field_name=input.field_name,
                received={"value": value},
                expected={"format": "valid email"},
            )

        # Check for empty parts
        if not local_part:
            raise ValidationException(
                message="Invalid email format: local part cannot be empty",
                field_name=input.field_name,
                received={"value": value},
                expected={"format": "local part must not be empty"},
            )
        if not domain_part:
            raise ValidationException(
                message="Invalid email format: domain part cannot be empty",
                field_name=input.field_name,
                received={"value": value},
                expected={"format": "domain part must not be empty"},
            )

        # Validate local part (max 64 characters)
        if len(local_part) > 64:
            raise ValidationException(
                message="Invalid email format: local part exceeds 64 characters",
                field_name=input.field_name,
                received={"value": value, "local_part_length": len(local_part)},
                expected={"max_length": 64},
            )

        # Check for invalid start/end periods in local part
        if local_part.startswith(".") or local_part.endswith("."):
            raise ValidationException(
                message="Invalid email format: local part cannot start or end with a period",
                field_name=input.field_name,
                received={"value": value},
                expected={"format": "local part without leading/trailing periods"},
            )

        # Check for consecutive periods in local part
        if ".." in local_part:
            raise ValidationException(
                message="Invalid email format: local part cannot contain consecutive periods",
                field_name=input.field_name,
                received={"value": value},
                expected={"format": "local part without consecutive periods"},
            )

        # Check for unbalanced or misplaced quotes in local part
        quote_count = local_part.count('"')
        if quote_count % 2 != 0 or quote_count > 0:
            # For simplicity, we're rejecting all quoted local parts
            raise ValidationException(
                message="Invalid email format: quoted local parts not supported",
                field_name=input.field_name,
                received={"value": value},
                expected={"format": "local part without quotes"},
            )

        # Check for invalid characters in local part
        invalid_chars = ' ()<>@,;:\\"/[]'
        for char in invalid_chars:
            if char in local_part:
                raise ValidationException(
                    message=f"Invalid email format: local part contains invalid character '{char}'",
                    field_name=input.field_name,
                    received={"value": value},
                    expected={
                        "format": f"local part without invalid character '{char}'"
                    },
                )

        # Validate domain part (max 255 characters)
        if len(domain_part) > 255:
            raise ValidationException(
                message="Invalid email format: domain part exceeds 255 characters",
                field_name=input.field_name,
                received={"value": value, "domain_part_length": len(domain_part)},
                expected={"max_length": 255},
            )

        # Domain part must have at least one period (for TLD)
        if "." not in domain_part:
            raise ValidationException(
                message="Invalid email format: domain must have a TLD",
                field_name=input.field_name,
                received={"value": value},
                expected={"format": "domain with TLD"},
            )

        # Domain cannot start or end with hyphen or period
        if (
            domain_part.startswith(".")
            or domain_part.startswith("-")
            or domain_part.endswith(".")
            or domain_part.endswith("-")
        ):
            raise ValidationException(
                message="Invalid email format: domain cannot start or end with hyphen or period",
                field_name=input.field_name,
                received={"value": value},
                expected={
                    "format": "domain without leading/trailing hyphens or periods"
                },
            )

        # Check for consecutive periods in domain
        if ".." in domain_part:
            raise ValidationException(
                message="Invalid email format: domain cannot contain consecutive periods",
                field_name=input.field_name,
                received={"value": value},
                expected={"format": "domain without consecutive periods"},
            )

        # Check for IP address literal format
        if domain_part.startswith("[") and domain_part.endswith("]"):
            raise ValidationException(
                message="Invalid email format: IP address literals not supported",
                field_name=input.field_name,
                received={"value": value},
                expected={"format": "domain name without IP address literals"},
            )

        # Check for underscore in domain
        if "_" in domain_part:
            raise ValidationException(
                message="Invalid email format: underscore not allowed in domain names",
                field_name=input.field_name,
                received={"value": value},
                expected={"format": "domain name without underscores"},
            )

        # Check for non-ASCII characters
        if not all(ord(c) < 128 for c in value):
            raise ValidationException(
                message="Invalid email format: non-ASCII characters not supported",
                field_name=input.field_name,
                received={"value": value},
                expected={"format": "email with ASCII characters only"},
            )

        # Basic pattern check as a final validation
        if not re.match(
            r"^[a-zA-Z0-9.!#$%&\'*+\-/=?^_`{|}~]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$",
            value,
        ):
            raise ValidationException(
                message="Invalid email format",
                field_name=input.field_name,
                received={"value": value},
                expected={"format": "valid email address format"},
            )

        # Normalize to lowercase
        return success(value.lower())

    def default(self, input: ValidationInput) -> ValidationResult:
        """By default, email validator does nothing unless explicitly applied."""
        return success(input.value)


@validator
class LengthValidator(Validator):
    """Validates that a string is within the specified length range."""

    def __init__(self):
        super().__init__()
        self.min_length = 0
        self.max_length = None

    def set_limits(self, min_length: int = 0, max_length: Optional[int] = None):
        """Configure the length limits for this validator."""
        self.min_length = min_length
        self.max_length = max_length
        return self

    def validate(self, input: ValidationInput) -> ValidationResult:
        value = input.value
        if value is None:
            return fail("Value cannot be None")

        if not isinstance(value, str):
            return fail(f"Expected string, got {type(value).__name__}")

        if len(value) < self.min_length:
            return fail(f"Value must be at least {self.min_length} characters long")

        if self.max_length is not None and len(value) > self.max_length:
            return fail(f"Value must be at most {self.max_length} characters long")

        return success()


@validator
class NumberValidator(Validator):
    """Validates that a number is within the specified range."""

    def __init__(self):
        super().__init__()
        self.min_value = None
        self.max_value = None

    def set_limits(
        self,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
    ):
        """Configure the number range limits for this validator."""
        self.min_value = min_value
        self.max_value = max_value
        return self

    def validate(self, input: ValidationInput) -> ValidationResult:
        value = input.value

        # Skip methods and functions during validation
        if inspect.ismethod(value) or inspect.isfunction(value):
            return success(value)

        if value is None:
            return fail(
                "Value cannot be None",
                additional_context={
                    "field_name": input.field_name,
                    "received": {"value": value},
                    "expected": {"type": "number"},
                },
            )

        if not isinstance(value, (int, float)):
            return fail(
                f"Expected number, got {type(value).__name__}",
                additional_context={
                    "field_name": input.field_name,
                    "received": {"value": value, "type": type(value).__name__},
                    "expected": {"type": "number"},
                },
            )

        if self.min_value is not None and value < self.min_value:
            return fail(
                f"Value must be at least {self.min_value}",
                additional_context={
                    "field_name": input.field_name,
                    "received": {"value": value},
                    "expected": {"min_value": self.min_value},
                },
            )

        if self.max_value is not None and value > self.max_value:
            return fail(
                f"Value must be at most {self.max_value}",
                additional_context={
                    "field_name": input.field_name,
                    "received": {"value": value},
                    "expected": {"max_value": self.max_value},
                },
            )

        return success(value)

    def default(self, input: ValidationInput) -> ValidationResult:
        """By default, number validator does nothing unless explicitly applied."""
        # Skip validation for methods and functions
        if inspect.ismethod(input.value) or inspect.isfunction(input.value):
            return success(input.value)

        return success(input.value)


@validator
class TypeValidator(Validator):
    """A validator that checks if a value matches its type annotation."""

    def validate(self, input: ValidationInput) -> ValidationResult:
        value = input.value
        expected_type = input.get_type()

        # Skip validation if no type annotation
        if expected_type is None:
            return success()

        # Handle Optional types (Union[Type, None])
        if hasattr(expected_type, "__origin__") and expected_type.__origin__ is Union:
            # Check if None is one of the allowed types
            if type(None) in expected_type.__args__:
                # It's an Optional type, so None is allowed
                if value is None:
                    return success()

                # For non-None values, check against the other type
                other_types = [t for t in expected_type.__args__ if t is not type(None)]
                if len(other_types) == 1:
                    expected_type = other_types[0]

        # Skip validation if the expected_type is Any
        if expected_type is Any:
            return success()

        # Validate that the value is an instance of the expected type
        if not isinstance(value, expected_type):
            actual_type = type(value).__name__
            expected_name = getattr(expected_type, "__name__", str(expected_type))
            return fail(f"Expected type {expected_name}, got {actual_type}")

        return success()

    def default(self, input: ValidationInput) -> ValidationResult:
        """
        Type validator runs by default on fields with type annotations.
        It only validates fields that have been set or have a value.
        """
        # Skip validation for methods without an actual value
        if inspect.ismethod(input.value) or inspect.isfunction(input.value):
            return success()

        return self.validate(input)


# Create specific length validators with different parameters
username_length = LengthValidator().set_limits(min_length=3, max_length=50)
password_length = LengthValidator().set_limits(min_length=8, max_length=128)


# Create shorthand email decorator for convenience
def email(method):
    validator = EmailValidator()
    method._validators = getattr(method, "_validators", []) + [validator]
    return method


username = username_length.generate_decorator()
password = password_length.generate_decorator()

# --------------------------------
# Test Models
# --------------------------------


def password(method):
    """Validates that a password field is of the proper length."""
    validator = LengthValidator()
    validator.set_limits(min_length=8)
    method._validators = getattr(method, "_validators", []) + [validator]
    return method


def number(min_value=None, max_value=None):
    """
    Validates that a number is within the specified range.

    Args:
        min_value: Optional minimum value allowed
        max_value: Optional maximum value allowed
    """

    def decorator(method):
        validator = NumberValidator()
        validator.set_limits(min_value=min_value, max_value=max_value)
        method._validators = getattr(method, "_validators", []) + [validator]
        return method

    return decorator


class User(ValidatedModel):
    """A simple user model for testing validation."""

    @email
    @validate
    def email(self, value) -> str:
        """User's email address."""
        if value is None:
            raise ValueError("Email cannot be None")
        return value

    @username
    @validate
    def username(self, value) -> str:
        """User's username."""
        # Custom validation - no spaces allowed
        if " " in value:
            raise ValueError("Username cannot contain spaces")
        return value

    @validate
    @password
    def password(self) -> str:
        """User's password."""
        # Access the password directly from self
        # In a real implementation, this might hash the password
        if self.password == "password":
            raise ValueError("Password cannot be 'password'")
        return self.password

    # Optional field with no validator, but with a type annotation
    # Should be implicitly validated by the TypeValidator
    @validate
    def display_name(self, value) -> Optional[str]:
        """User's display name (optional)."""
        # If no display name is provided, use the username
        if value is None or value == "":
            return getattr(self, "username", "Anonymous")
        return value

    # Field with no type annotation - should not be type-checked
    @validate
    def preferences(self, value):
        """User preferences can be any type."""
        return value


# --------------------------------
# Test Cases
# --------------------------------


class TestValidation:
    """Test cases for the validation framework."""

    def test_valid_user(self):
        """Test that a valid user passes validation."""
        user = User(
            email="test@example.com",
            username="testuser",
            password="securepassword123",
            display_name="Test User",
            preferences={"theme": "dark", "notifications": True},
        )

        # If validation fails, an exception will be raised
        # So if we get here, validation passed
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password == "securepassword123"
        assert user.display_name == "Test User"
        assert user.preferences == {"theme": "dark", "notifications": True}

    @pytest.mark.parametrize(
        "email",
        [
            # Missing @ symbol
            "invalidemail",
            "plainaddress",
            # Multiple @ symbols
            "user@domain@example.com",
            "multiple@@example.com",
            # Invalid characters in local part
            "user name@example.com",
            "user<name@example.com",
            "user>name@example.com",
            "user[name@example.com",
            "user]name@example.com",
            "user(name@example.com",
            "user)name@example.com",
            "user\\name@example.com",
            'user"name@example.com',
            "user;name@example.com",
            "user:name@example.com",
            "user,name@example.com",
            # Invalid characters in domain part
            "user@domain_name.com",
            "user@domain-",
            "user@-domain.com",
            "user@domain..com",
            "user@domain.com.",
            "user@.domain.com",
            # Empty parts
            "@domain.com",
            "user@",
            # Domain without proper TLD
            "user@domain",
            "user@.com",
            "user@com.",
            # Local part exceeds maximum length (64 characters)
            "a" * 65 + "@example.com",
            # Domain part exceeds maximum length (255 characters)
            "user@" + "a" * 250 + ".com",
            # Improperly quoted local parts
            '"user@example.com',
            'user"@example.com',
            # Invalid use of dots
            ".user@example.com",
            "user.@example.com",
            "us..er@example.com",
            # IP address format issues
            "user@[1.2.3.4]",
            "user@[IPv6:1:2:3:4:5:6:7:8]",
            # Unicode characters where they're not allowed
            "用户@example.com",
            "user@例子.com",
            # IDN not properly encoded
            "user@ドメイン.com",
            # Extremely long email
            "user." + "very" * 50 + "long@example.com",
        ],
    )
    def test_invalid_emails(self, email: str):
        """Test that invalid email addresses are rejected."""
        try:
            # Attempt to create the user with the invalid email
            user = User(email=email, username="testuser", password="securepassword123")

            # If we get here, validation didn't raise an exception, which is unexpected
            # Let's print some debug info
            pytest.fail(f"Validation should have failed for email: {email}")
        except ValidationException:
            # This is the expected behavior
            pass

    def test_email_normalization(self):
        """Test that email addresses are normalized to lowercase."""
        user = User(
            email="Test@Example.COM", username="testuser", password="securepassword123"
        )

        assert user.email == "test@example.com"

    def test_default_display_name(self):
        """Test that display_name defaults to username if not provided."""
        user = User(
            email="test@example.com",
            username="testuser",
            password="securepassword123",
            display_name=None,
        )

        assert user.display_name == "testuser"

    def test_invalid_email(self):
        """Test that invalid email addresses are rejected."""
        with pytest.raises(ValidationException) as excinfo:
            User(
                email="invalid-email", username="testuser", password="securepassword123"
            )

        # Check that the exception contains helpful information
        assert "email" in excinfo.value.field_name
        assert "@" in str(excinfo.value)

    def test_username_too_short(self):
        """Test that usernames that are too short are rejected."""
        with pytest.raises(ValidationException) as excinfo:
            User(
                email="test@example.com",
                username="ab",  # Too short (min is 3)
                password="securepassword123",
            )

        assert "username" in excinfo.value.field_name
        assert "3" in str(excinfo.value)

    def test_password_too_short(self):
        """Test that passwords that are too short are rejected."""
        with pytest.raises(ValidationException) as excinfo:
            User(
                email="test@example.com",
                username="testuser",
                password="short",  # Too short (min is 8)
            )

        assert "password" in excinfo.value.field_name
        assert "8" in str(excinfo.value)

    def test_custom_validation_error(self):
        """Test that custom validation logic in the model works."""
        with pytest.raises(ValidationException) as excinfo:
            User(
                email="test@example.com",
                username="test user",  # Contains a space
                password="securepassword123",
            )

        assert "username" in excinfo.value.field_name
        assert "space" in str(excinfo.value)

    def test_password_custom_validation(self):
        """Test that custom validation logic for the password field works."""
        with pytest.raises(ValidationException) as excinfo:
            User(
                email="test@example.com",
                username="testuser",
                password="password",  # 'password' is not allowed
            )

        assert "password" in excinfo.value.field_name

    def test_type_validation(self):
        """Test that type validation works automatically on typed fields."""
        with pytest.raises(ValidationException) as excinfo:
            User(
                email="test@example.com",
                username="testuser",
                password="securepassword123",
                display_name=123,  # Should be a string
            )

        assert "display_name" in excinfo.value.field_name
        assert "str" in str(excinfo.value)
        assert "int" in str(excinfo.value)

    def test_untyped_field_allows_any_type(self):
        """Test that fields without type annotations accept any type."""
        # This should work without error since preferences has no type annotation
        user = User(
            email="test@example.com",
            username="testuser",
            password="securepassword123",
            preferences=123,  # Any type is allowed
        )

        assert user.preferences == 123

    def test_error_format(self):
        """Test that validation errors are formatted correctly."""
        try:
            User(
                email="invalid-email", username="testuser", password="securepassword123"
            )
            pytest.fail("Expected ValidationException for invalid email")
        except ValidationException as e:
            error_str = str(e)
            # Check for Rust-style formatting elements
            assert "error[E0001]" in error_str
            assert "received:" in error_str
            assert "expected schema:" in error_str


class TestNumberValidation:
    """Tests for the NumberValidator."""

    def test_setup(self):
        """Test that the validator is properly initialized."""

        class TestModel(ValidatedModel):
            @validate
            @number(min_value=10, max_value=100)
            def age(self, value) -> int:
                return value

        model = TestModel()
        assert hasattr(model.age, "_validators")
        assert any(isinstance(v, NumberValidator) for v in model.age._validators)

    def test_valid_numbers(self):
        """Test that valid numbers pass validation."""

        class TestModel(ValidatedModel):
            @validate
            @number(min_value=10, max_value=100)
            def age(self, value) -> int:
                return value

        model = TestModel()
        model.age = 10
        assert model.age == 10
        model.age = 50
        assert model.age == 50
        model.age = 100
        assert model.age == 100

    def test_below_minimum(self):
        """Test that numbers below the minimum fail validation."""

        class TestModel(ValidatedModel):
            @validate
            @number(min_value=10, max_value=100)
            def age(self, value) -> int:
                return value

        model = TestModel()
        try:
            model.age = 5
            pytest.fail("Should have raised ValidationException")
        except ValidationException as e:
            assert "Value must be at least 10" in str(e)

    def test_above_maximum(self):
        """Test that numbers above the maximum fail validation."""

        class TestModel(ValidatedModel):
            @validate
            @number(min_value=10, max_value=100)
            def age(self, value) -> int:
                return value

        model = TestModel()
        try:
            model.age = 150
            pytest.fail("Should have raised ValidationException")
        except ValidationException as e:
            assert "Value must be at most 100" in str(e)

    def test_non_number_value(self):
        """Test that non-number values fail validation."""

        class TestModel(ValidatedModel):
            @validate
            @number(min_value=10, max_value=100)
            def age(self, value) -> int:
                return value

        model = TestModel()
        try:
            model.age = "twenty"
            pytest.fail("Should have raised ValidationException")
        except ValidationException as e:
            assert "Expected number, got str" in str(e)

    def test_only_min_constraint(self):
        """Test validation with only a minimum constraint."""

        class TestModel(ValidatedModel):
            @validate
            @number(min_value=10)
            def score(self, value) -> float:
                return value

        model = TestModel()
        model.score = 10
        assert model.score == 10
        model.score = 1000
        assert model.score == 1000
        try:
            model.score = 5
            pytest.fail("Should have raised ValidationException")
        except ValidationException as e:
            assert "Value must be at least 10" in str(e)

    def test_only_max_constraint(self):
        """Test validation with only a maximum constraint."""

        class TestModel(ValidatedModel):
            @validate
            @number(max_value=100)
            def temperature(self, value) -> float:
                return value

        model = TestModel()
        model.temperature = -50
        assert model.temperature == -50
        model.temperature = 100
        assert model.temperature == 100
        try:
            model.temperature = 101
            pytest.fail("Should have raised ValidationException")
        except ValidationException as e:
            assert "Value must be at most 100" in str(e)

    def test_no_constraints(self):
        """Test validation with no constraints."""

        class TestModel(ValidatedModel):
            @validate
            @number()
            def value(self, value) -> float:
                return value

        model = TestModel()
        model.value = -1000
        assert model.value == -1000
        model.value = 0
        assert model.value == 0
        model.value = 1000
        assert model.value == 1000
        try:
            model.value = "not a number"
            pytest.fail("Should have raised ValidationException")
        except ValidationException as e:
            assert "Expected number, got str" in str(e)
