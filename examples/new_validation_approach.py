"""
Example demonstrating the new validation approach with helper functions.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Union

from uhmactually.core import ValidatedModel, validate, ValidationError
from uhmactually.validators import (
    # Helper functions for inline validation
    type_check,
    optional_check,
    min_length_check,
    max_length_check,
    min_value_check,
    max_value_check,
    pattern_check,
    one_of_check,
    is_enum_check,
)


# Example Enum
class UserRole(Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


# Example model using the new approach
class User(ValidatedModel):
    """
    User model with validation using helper functions.
    """

    @validate
    def username(self, value=None) -> str:
        """Username must be between 3 and 20 characters."""
        if value is not None:
            type_check(value, str)
            min_length_check(value, 3)
            max_length_check(value, 20)
            # Custom validation: username must not contain spaces
            if " " in value:
                raise ValidationError(
                    "Username must not contain spaces", "username", value
                )
        return value

    @validate
    def email(self, value=None) -> str:
        """Email must be a valid email address."""
        if value is not None:
            type_check(value, str)
            # Simple email validation using regex
            pattern_check(value, r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
        return value

    @validate
    def age(self, value=None) -> int:
        """Age must be between 18 and 120."""
        if value is not None:
            type_check(value, int)
            min_value_check(value, 18)
            max_value_check(value, 120)
        return value

    @validate
    def role(self, value=None) -> str:
        """Role must be a valid UserRole."""
        if value is not None:
            type_check(value, str)
            is_enum_check(value, UserRole)
        return value

    @validate
    def bio(self, value=None) -> Optional[str]:
        """Bio is optional but must be a string if provided."""
        if value is not None:
            type_check(value, str)
            max_length_check(value, 500)
        else:
            # This field is optional
            optional_check(value, is_optional=True)
        return value

    @validate
    def tags(self, value=None) -> List[str]:
        """Tags must be a list of strings."""
        if value is not None:
            type_check(value, list)
            # Check each tag
            for i, tag in enumerate(value):
                type_check(tag, str)
                min_length_check(tag, 1)
                max_length_check(tag, 20)
        return value

    @validate
    def preferences(self, value=None) -> Dict[str, Any]:
        """Preferences must be a dictionary."""
        if value is not None:
            type_check(value, dict)
            # Check theme if present
            if "theme" in value:
                one_of_check(value["theme"], ["light", "dark", "system"])
        return value


# Example model using the default validation approach
class SimpleUser(ValidatedModel):
    """
    User model with validation using default validation.
    """

    @validate
    def username(self) -> str:
        pass

    @validate
    def email(self) -> str:
        pass

    @validate
    def age(self) -> int:
        pass


# Example usage
def main():
    # Create a valid user
    try:
        user = User(
            username="john_doe",
            email="john@example.com",
            age=30,
            role=UserRole.ADMIN.value,
            bio="Software developer",
            tags=["python", "web", "api"],
            preferences={"theme": "dark", "notifications": True},
        )
        print(f"Valid user created: {user.to_dict()}")
    except ValidationError as e:
        print(f"Validation error: {e}")

    # Create an invalid user
    try:
        user = User(
            username="jo",  # Too short
            email="not-an-email",  # Invalid email
            age=15,  # Too young
            role="superuser",  # Invalid role
            bio="Bio is valid",
            tags=["python", 123],  # Invalid tag
            preferences={"theme": "blue"},  # Invalid theme
        )
        print(f"Invalid user created: {user.to_dict()}")
    except ValidationError as e:
        print(f"Validation error: {e}")

    # Create a valid simple user
    try:
        user = SimpleUser(
            username="john_doe",
            email="john@example.com",
            age=30,
        )
        print(f"Valid simple user created: {user.to_dict()}")
    except ValidationError as e:
        print(f"Validation error: {e}")

    # Create an invalid simple user
    try:
        user = SimpleUser(
            username=123,  # Not a string
            email="john@example.com",
            age="30",  # Not an int
        )
        print(f"Invalid simple user created: {user.to_dict()}")
    except ValidationError as e:
        print(f"Validation error: {e}")


if __name__ == "__main__":
    main()
