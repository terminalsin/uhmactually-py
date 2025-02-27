import pytest
from typing import List, Optional, Union, Dict, Any, Tuple, Set, FrozenSet, Callable
import random
import string
import json
from datetime import datetime, date, time
from dataclasses import dataclass

from uhmactually.core import (
    ValidationError,
    ValidatedModel,
    validate,
)
from uhmactually.validators import (
    is_type,
    is_instance_of,
)


# Test Models
class User(ValidatedModel):
    """A user model with type validation."""

    @validate
    def username(self) -> str:
        pass

    @validate
    def email(self) -> str:
        pass

    @is_type(int)
    def age(self) -> int:
        pass

    @is_type(Optional[str])
    def bio(self) -> Optional[str]:
        pass


class Address(ValidatedModel):
    """An address model with type validation."""

    @is_type(str)
    def street(self) -> str:
        pass

    @is_type(str)
    def city(self) -> str:
        pass

    @is_type(str)
    def country(self) -> str:
        pass

    @is_type(Optional[str])
    def postal_code(self) -> Optional[str]:
        pass


class UserProfile(ValidatedModel):
    """A user profile model with nested model validation."""

    @is_instance_of(User)
    def user(self) -> User:
        pass

    @is_type(List[Address])
    def addresses(self) -> List[Address]:
        pass

    @is_type(Dict[str, Any])
    def preferences(self) -> Dict[str, Any]:
        pass


class CustomValidationUser(ValidatedModel):
    """A user model with custom validation."""

    @validate
    def username(self, value=None) -> str:
        if value is not None and len(value) < 3:
            raise ValidationError(
                "Username must be at least 3 characters", "username", value
            )
        return value

    @is_type(str)
    def email(self, value=None) -> str:
        if value is not None and "@" not in value:
            raise ValidationError("Invalid email format", "email", value)
        return value


# Advanced test models for more complex type validation
class AdvancedTypes(ValidatedModel):
    """A model with advanced type validations."""

    @is_type(List[int])
    def int_list(self) -> List[int]:
        pass

    @is_type(Dict[str, int])
    def str_int_dict(self) -> Dict[str, int]:
        pass

    @is_type(Union[str, int])
    def str_or_int(self) -> Union[str, int]:
        pass

    @is_type(Tuple[str, int, bool])
    def fixed_tuple(self) -> Tuple[str, int, bool]:
        pass

    @is_type(Set[str])
    def str_set(self) -> Set[str]:
        pass

    @is_type(Optional[List[Dict[str, Any]]])
    def complex_nested(self) -> Optional[List[Dict[str, Any]]]:
        pass


class DateTimeModel(ValidatedModel):
    """A model with date and time validations."""

    @is_type(datetime)
    def timestamp(self) -> datetime:
        pass

    @is_type(date)
    def only_date(self) -> date:
        pass

    @is_type(time)
    def only_time(self) -> time:
        pass


@dataclass
class Point:
    x: float
    y: float


class CustomClassModel(ValidatedModel):
    """A model with custom class validations."""

    @is_type(Point)
    def point(self) -> Point:
        pass

    @is_type(List[Point])
    def points(self) -> List[Point]:
        pass


# Helper functions for generating test data
def random_string(length=10):
    """Generate a random string of fixed length."""
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


def random_email():
    """Generate a random valid email."""
    return f"{random_string(8)}@{random_string(5)}.com"


def random_invalid_email():
    """Generate a random invalid email."""
    return random_string(15)


# Parametrized Tests for Basic Validation
@pytest.mark.parametrize(
    "username,email,age,bio,should_pass",
    [
        # Valid cases
        ("john_doe", "john@example.com", 30, "Software developer", True),
        ("alice", "alice@test.org", 25, None, True),
        ("bob_smith", "bob.smith@company.co.uk", 0, "", True),
        ("x" * 100, "very.long.email@very.long.domain.name", 999, "x" * 1000, True),
        # Invalid cases - wrong types
        (123, "john@example.com", 30, None, False),  # username not str
        ("john", 123, 30, None, False),  # email not str
        ("john", "john@example.com", "thirty", None, False),  # age not int
        ("john", "john@example.com", 30, 123, False),  # bio not str or None
        # Edge cases
        ("", "john@example.com", 30, None, True),  # Empty string is still a string
        (
            "john",
            "",
            30,
            None,
            True,
        ),  # Empty email is still a string (validation only checks type)
        ("john", "john@example.com", -1, None, True),  # Negative age is still an int
    ],
)
def test_user_validation(username, email, age, bio, should_pass):
    """Test user model validation with various inputs."""
    if should_pass:
        user = User(username=username, email=email, age=age, bio=bio)
        assert user.username() == username
        assert user.email() == email
        assert user.age() == age
        assert user.bio() == bio
        assert user.validate().is_valid
    else:
        with pytest.raises(ValidationError):
            User(username=username, email=email, age=age, bio=bio)


# Parametrized Tests for Custom Validation
@pytest.mark.parametrize(
    "username,email,should_pass,expected_error",
    [
        # Valid cases
        ("john_doe", "john@example.com", True, None),
        ("abc", "test@test.com", True, None),
        # Invalid username (too short)
        ("jo", "john@example.com", False, "Username must be at least 3 characters"),
        ("a", "test@test.com", False, "Username must be at least 3 characters"),
        # Invalid email (no @)
        ("john_doe", "johndoe.com", False, "Invalid email format"),
        ("valid_name", "invalid-email", False, "Invalid email format"),
        # Multiple validation errors
        ("jo", "invalid-email", False, None),  # Both username and email are invalid
    ],
)
def test_custom_validation(username, email, should_pass, expected_error):
    """Test custom validation logic with various inputs."""
    if should_pass:
        user = CustomValidationUser(username=username, email=email)
        assert user.username() == username
        assert user.email() == email
        assert user.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            CustomValidationUser(username=username, email=email)

        if expected_error:
            assert expected_error in str(excinfo.value)


# Parametrized Tests for Nested Models
@pytest.mark.parametrize(
    "user_data,addresses_data,preferences,should_pass",
    [
        # Valid case
        (
            {"username": "john", "email": "john@example.com", "age": 30},
            [
                {"street": "123 Main St", "city": "New York", "country": "USA"},
                {
                    "street": "456 Elm St",
                    "city": "San Francisco",
                    "country": "USA",
                    "postal_code": "94107",
                },
            ],
            {"theme": "dark", "notifications": True},
            True,
        ),
        # Invalid user
        (
            {
                "username": 123,
                "email": "john@example.com",
                "age": 30,
            },  # username not str
            [{"street": "123 Main St", "city": "New York", "country": "USA"}],
            {"theme": "dark"},
            False,
        ),
        # Invalid address
        (
            {"username": "john", "email": "john@example.com", "age": 30},
            [{"street": "123 Main St", "city": 123, "country": "USA"}],  # city not str
            {"theme": "dark"},
            False,
        ),
        # Empty lists and dicts
        (
            {"username": "john", "email": "john@example.com", "age": 30},
            [],  # Empty addresses list
            {},  # Empty preferences dict
            True,
        ),
    ],
)
def test_nested_model_validation(user_data, addresses_data, preferences, should_pass):
    """Test nested model validation with various inputs."""
    user = User(**user_data)
    addresses = [Address(**addr) for addr in addresses_data]

    if should_pass:
        profile = UserProfile(user=user, addresses=addresses, preferences=preferences)
        assert profile.user() == user
        assert profile.addresses() == addresses
        assert profile.preferences() == preferences
        assert profile.validate().is_valid
    else:
        with pytest.raises(ValidationError):
            UserProfile(user=user, addresses=addresses, preferences=preferences)


# Fuzzing Tests for User Model
@pytest.mark.parametrize("iterations", [100])
def test_user_model_fuzzing(iterations):
    """Fuzz test the User model with random data."""
    valid_count = 0
    invalid_count = 0

    for _ in range(iterations):
        # Generate random data with different types
        data = {
            "username": random.choice(
                [
                    random_string(),
                    random.randint(1, 1000),
                    random.random(),
                    None,
                    [1, 2, 3],
                    {"key": "value"},
                ]
            ),
            "email": random.choice(
                [
                    random_email(),
                    random_invalid_email(),
                    random.randint(1, 1000),
                    None,
                    [1, 2, 3],
                    {"key": "value"},
                ]
            ),
            "age": random.choice(
                [
                    random.randint(-100, 100),
                    random_string(),
                    random.random(),
                    None,
                    [1, 2, 3],
                    {"key": "value"},
                ]
            ),
            "bio": random.choice(
                [
                    random_string(),
                    None,
                    random.randint(1, 1000),
                    random.random(),
                    [1, 2, 3],
                    {"key": "value"},
                ]
            ),
        }

        try:
            user = User(**data)
            validation_result = user.validate()
            if validation_result.is_valid:
                valid_count += 1
                # Verify that the data was stored correctly
                assert user.username() == data["username"]
                assert user.email() == data["email"]
                assert user.age() == data["age"]
                assert user.bio() == data["bio"]
        except ValidationError:
            invalid_count += 1

    # We should have both valid and invalid cases
    assert valid_count + invalid_count == iterations


# Tests for Advanced Types
@pytest.mark.parametrize(
    "field,valid_values,invalid_values",
    [
        (
            "int_list",
            [[1, 2, 3], [], [0, -1, 999999]],
            [["a", "b", "c"], [1, "2", 3], None, "not a list", 123, {1: 2}],
        ),
        (
            "str_int_dict",
            [{"a": 1, "b": 2}, {}, {"long_key": 999999}],
            [{1: 2}, {"a": "b"}, None, "not a dict", 123, [1, 2, 3]],
        ),
        ("str_or_int", ["hello", 123, "", 0, -1], [None, [1, 2, 3], {"a": 1}, 1.23]),
        (
            "fixed_tuple",
            [("a", 1, True), ("", 0, False)],
            [(1, 2, 3), ("a", "b", "c"), None, "not a tuple", 123, [1, 2, 3]],
        ),
        (
            "str_set",
            [set(("a", "b", "c")), set(), set(("",))],
            [{1, 2, 3}, None, "not a set", 123, [1, 2, 3]],
        ),
        (
            "complex_nested",
            [[{"a": 1}, {"b": "value"}], [], None],
            ["not a list", 123, {"not": "a list"}],
        ),
    ],
)
def test_advanced_types(field, valid_values, invalid_values):
    """Test validation of advanced types."""
    for value in valid_values:
        model = AdvancedTypes(**{field: value})
        assert getattr(model, field)() == value
        assert model.validate().is_valid

    for value in invalid_values:
        with pytest.raises(ValidationError):
            AdvancedTypes(**{field: value})


# Tests for DateTime Models
def test_datetime_model():
    """Test validation of date and time types."""
    now = datetime.now()
    today = date.today()
    current_time = time(hour=12, minute=30)

    # Valid case
    model = DateTimeModel(timestamp=now, only_date=today, only_time=current_time)
    assert model.timestamp() == now
    assert model.only_date() == today
    assert model.only_time() == current_time
    assert model.validate().is_valid

    # Invalid cases
    with pytest.raises(ValidationError):
        DateTimeModel(
            timestamp="not a datetime", only_date=today, only_time=current_time
        )

    with pytest.raises(ValidationError):
        DateTimeModel(timestamp=now, only_date="not a date", only_time=current_time)

    with pytest.raises(ValidationError):
        DateTimeModel(timestamp=now, only_date=today, only_time="not a time")


# Tests for Custom Class Models
def test_custom_class_model():
    """Test validation of custom class types."""
    point = Point(x=1.0, y=2.0)
    points = [Point(x=1.0, y=2.0), Point(x=3.0, y=4.0)]

    # Valid case
    model = CustomClassModel(point=point, points=points)
    assert model.point() == point
    assert model.points() == points
    assert model.validate().is_valid

    # Invalid cases
    with pytest.raises(ValidationError):
        CustomClassModel(point="not a point", points=points)

    with pytest.raises(ValidationError):
        CustomClassModel(point=point, points=["not a point"])


# Property-based testing with hypothesis
try:
    from hypothesis import given, strategies as st

    @given(
        username=st.one_of(st.text(), st.integers(), st.none()),
        email=st.one_of(st.text(), st.integers(), st.none()),
        age=st.one_of(st.integers(), st.text(), st.none()),
        bio=st.one_of(st.text(), st.integers(), st.none(), st.lists(st.integers())),
    )
    def test_user_property_based(username, email, age, bio):
        """Property-based test for User model."""
        try:
            user = User(username=username, email=email, age=age, bio=bio)
            # If initialization succeeds, validation should pass
            assert user.validate().is_valid
            # And the values should be stored correctly
            assert user.username() == username
            assert user.email() == email
            assert user.age() == age
            assert user.bio() == bio
        except ValidationError:
            # If validation fails, at least one of the values should be of the wrong type
            assert not (
                isinstance(username, str)
                and isinstance(email, str)
                and isinstance(age, int)
                and (isinstance(bio, str) or bio is None)
            )
except ImportError:
    # Skip hypothesis tests if the library is not installed
    pass


# Tests for serialization and deserialization
@pytest.mark.parametrize(
    "model_class,valid_data",
    [
        (
            User,
            {
                "username": "john_doe",
                "email": "john@example.com",
                "age": 30,
                "bio": "Developer",
            },
        ),
        (
            Address,
            {
                "street": "123 Main St",
                "city": "New York",
                "country": "USA",
                "postal_code": "10001",
            },
        ),
        (
            AdvancedTypes,
            {
                "int_list": [1, 2, 3],
                "str_int_dict": {"a": 1, "b": 2},
                "str_or_int": "hello",
                "fixed_tuple": ("a", 1, True),
                "str_set": {"a", "b", "c"},
                "complex_nested": [{"a": 1}, {"b": 2}],
            },
        ),
    ],
)
def test_serialization_roundtrip(model_class, valid_data):
    """Test that a model can be serialized and deserialized correctly."""
    # Create original model
    original = model_class(**valid_data)

    # Test to_dict and from_dict
    data_dict = original.to_dict()
    print(data_dict)
    recreated_from_dict = model_class.from_dict(data_dict)
    print(recreated_from_dict)

    # Test to_json and from_json
    json_str = original.to_json()
    recreated_from_json = model_class.from_json(json_str)

    # Verify that the recreated models have the same data
    for field_name in valid_data:
        if hasattr(original, field_name) and callable(getattr(original, field_name)):
            original_value = getattr(original, field_name)()
            dict_value = getattr(recreated_from_dict, field_name)()
            json_value = getattr(recreated_from_json, field_name)()

            # Special handling for sets which become lists in JSON
            if isinstance(original_value, set):
                assert set(dict_value) == original_value
                assert set(json_value) == original_value
            # Special handling for tuples which become lists in JSON
            elif isinstance(original_value, tuple):
                assert tuple(dict_value) == original_value
                assert tuple(json_value) == original_value
            else:
                assert dict_value == original_value
                assert json_value == original_value


# Tests for error messages
@pytest.mark.parametrize(
    "invalid_data,expected_error_fields",
    [
        (
            {"username": 123, "email": "john@example.com", "age": 30, "bio": None},
            ["username"],
        ),
        ({"username": "john", "email": 123, "age": 30, "bio": None}, ["email"]),
        (
            {
                "username": "john",
                "email": "john@example.com",
                "age": "thirty",
                "bio": None,
            },
            ["age"],
        ),
        (
            {"username": 123, "email": 456, "age": "thirty", "bio": [1, 2, 3]},
            ["username", "email", "age", "bio"],
        ),
    ],
)
def test_validation_error_messages(invalid_data, expected_error_fields):
    """Test that validation errors contain the expected field names."""
    with pytest.raises(ValidationError) as excinfo:
        User.from_dict(invalid_data)

    error_message = str(excinfo.value)
    for field in expected_error_fields:
        assert field in error_message


# Tests for nested model validation with invalid data
def test_deeply_nested_model_validation():
    """Test validation of deeply nested models with invalid data."""
    # Create a valid user
    user = User(username="john", email="john@example.com", age=30)

    # Create a list with one valid address and one invalid address
    addresses = [
        Address(street="123 Main St", city="New York", country="USA"),
        {
            "street": "456 Elm St",
            "city": 123,
            "country": "USA",
        },  # city should be a string
    ]

    # This should fail because the second address is invalid
    with pytest.raises(ValidationError) as excinfo:
        UserProfile(user=user, addresses=addresses, preferences={"theme": "dark"})

    error_message = str(excinfo.value)
    assert "city" in error_message


# Tests for model initialization and validation
def test_model_initialization_valid():
    """Test that a model with valid data initializes successfully."""
    user = User(
        username="john_doe", email="john@example.com", age=30, bio="Software developer"
    )
    assert user.username() == "john_doe"
    assert user.email() == "john@example.com"
    assert user.age() == 30
    assert user.bio() == "Software developer"


def test_model_initialization_invalid():
    """Test that a model with invalid data raises ValidationError on initialization."""
    with pytest.raises(ValidationError) as excinfo:
        User(username=123, email="john@example.com", age="thirty", bio=None)

    error_message = str(excinfo.value)
    assert "username" in error_message
    assert "age" in error_message


def test_model_with_optional_fields():
    """Test that a model with optional fields can be initialized with None values."""
    user = User(username="john_doe", email="john@example.com", age=30, bio=None)
    assert user.bio() is None

    # Bio is optional, so it should pass validation
    assert user.validate().is_valid


def test_nested_model_initialization():
    """Test that a model with nested models initializes successfully."""
    user = User(username="john_doe", email="john@example.com", age=30)
    address1 = Address(
        street="123 Main St", city="New York", country="USA", postal_code="10001"
    )
    address2 = Address(
        street="456 Elm St", city="San Francisco", country="USA", postal_code=None
    )

    profile = UserProfile(
        user=user,
        addresses=[address1, address2],
        preferences={"theme": "dark", "notifications": True},
    )

    assert profile.user().username() == "john_doe"
    assert len(profile.addresses()) == 2
    assert profile.addresses()[0].city() == "New York"
    assert profile.preferences()["theme"] == "dark"


def test_nested_model_validation():
    """Test that a model with invalid nested models fails validation."""
    user = User(username="john_doe", email="john@example.com", age=30)

    # Invalid address (city is an int instead of str)
    invalid_address = {"street": "123 Main St", "city": 123, "country": "USA"}

    with pytest.raises(ValidationError) as excinfo:
        UserProfile(
            user=user, addresses=[invalid_address], preferences={"theme": "dark"}
        )

    error_message = str(excinfo.value)
    assert "city" in error_message


def test_custom_validation():
    """Test that custom validation logic works."""
    # Valid user
    user = CustomValidationUser(username="john_doe", email="john@example.com")
    assert user.username() == "john_doe"

    # Invalid username (too short)
    with pytest.raises(ValidationError) as excinfo:
        CustomValidationUser(username="jo", email="john@example.com")
    assert "Username must be at least 3 characters" in str(excinfo.value)

    # Invalid email (no @)
    with pytest.raises(ValidationError) as excinfo:
        CustomValidationUser(username="john_doe", email="johndoe.com")
    assert "Invalid email format" in str(excinfo.value)


# Tests for serialization and deserialization
def test_to_dict_and_from_dict():
    """Test that a model can be converted to a dict and back."""
    original = User(
        username="john_doe", email="john@example.com", age=30, bio="Developer"
    )

    # Convert to dict
    data = original.to_dict()
    assert data == {
        "username": "john_doe",
        "email": "john@example.com",
        "age": 30,
        "bio": "Developer",
    }

    # Create from dict
    recreated = User.from_dict(data)
    assert recreated.username() == original.username()
    assert recreated.email() == original.email()
    assert recreated.age() == original.age()
    assert recreated.bio() == original.bio()


def test_to_json_and_from_json():
    """Test that a model can be converted to JSON and back."""
    original = User(
        username="john_doe", email="john@example.com", age=30, bio="Developer"
    )

    # Convert to JSON
    json_str = original.to_json()

    # Create from JSON
    recreated = User.from_json(json_str)
    assert recreated.username() == original.username()
    assert recreated.email() == original.email()
    assert recreated.age() == original.age()
    assert recreated.bio() == original.bio()


def test_nested_model_serialization():
    """Test that a model with nested models can be serialized and deserialized."""
    user = User(username="john_doe", email="john@example.com", age=30)
    address = Address(street="123 Main St", city="New York", country="USA")

    profile = UserProfile(user=user, addresses=[address], preferences={"theme": "dark"})

    # Convert to dict
    data = profile.to_dict()

    # The nested user should be converted to a dict
    assert isinstance(data["user"], dict)
    assert data["user"]["username"] == "john_doe"

    # The addresses should be a list of dicts
    assert isinstance(data["addresses"], list)
    assert isinstance(data["addresses"][0], dict)
    assert data["addresses"][0]["city"] == "New York"


def test_invalid_data_from_dict():
    """Test that creating a model from an invalid dict raises ValidationError."""
    invalid_data = {
        "username": 123,  # Should be a string
        "email": "john@example.com",
        "age": "thirty",  # Should be an int
        "bio": None,
    }

    with pytest.raises(ValidationError) as excinfo:
        User.from_dict(invalid_data)

    error_message = str(excinfo.value)
    assert "username" in error_message
    assert "age" in error_message
