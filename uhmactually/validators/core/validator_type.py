from typing import (
    Any,
    Type,
    Union,
    get_origin,
    get_args,
    Optional,
    List,
    Dict,
    Tuple,
    Set,
    Callable,
)

from uhmactually.core import (
    Validator,
    ValidationError,
    ValidationResult,
    ValidatedModel,
)
from uhmactually.validators.registry import validator


@validator
class TypeValidator(Validator):
    """Validator that checks if a value is of the expected type."""

    def __init__(self, expected_type: Optional[Type] = None):
        self.expected_type = expected_type

    def validate(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Validate that a value is of the expected type.

        Args:
            value: The value to validate.
            field_name: The name of the field being validated.

        Returns:
            A ValidationResult object.
        """
        result = ValidationResult()

        # Skip validation if no expected_type is provided
        if self.expected_type is None:
            return result

        # Get the origin type (for generics like List, Dict, etc.)
        origin = get_origin(self.expected_type)

        # Handle Union types (e.g., Union[str, int])
        if origin is Union:
            union_types = get_args(self.expected_type)
            # Check if None is allowed
            none_allowed = type(None) in union_types

            # If value is None and None is allowed, skip validation
            if value is None and none_allowed:
                return result

            # Filter out None from union types for validation
            actual_types = [t for t in union_types if t is not type(None)]

            # Check if value matches any of the allowed types
            if not any(self.is_of_type(value, t) for t in actual_types):
                type_names = ", ".join(t.__name__ for t in actual_types)
                value_repr = self._get_value_repr(value)
                result.add_error(
                    ValidationError(
                        f"Expected one of types [{type_names}], got {type(value).__name__} with value: {value_repr}",
                        field_name,
                        value,
                    )
                )
        # Handle List types
        elif origin is list:
            if not self.is_of_type(value, list):
                value_repr = self._get_value_repr(value)
                result.add_error(
                    ValidationError(
                        f"Expected type list, got {type(value).__name__} with value: {value_repr}",
                        field_name,
                        value,
                    )
                )
            else:
                # Check the type of items in the list if specified
                item_types = get_args(self.expected_type)
                if item_types and item_types[0] is not Any:
                    item_type = item_types[0]
                    for i, item in enumerate(value):
                        # Skip None values if the item type allows it
                        if item is None:
                            if get_origin(item_type) is Union and type(
                                None
                            ) in get_args(item_type):
                                continue
                            else:
                                result.add_error(
                                    ValidationError(
                                        f"Item at index {i} cannot be None",
                                        field_name,
                                        item,
                                    )
                                )
                                continue

                        # Handle nested ValidatedModel classes
                        if issubclass(item_type, ValidatedModel):
                            mapped_item = None
                            if isinstance(item, item_type):
                                mapped_item = item
                            elif isinstance(item, dict):
                                mapped_item = item_type.from_dict(item)
                            elif isinstance(item, str):
                                mapped_item = item_type.from_json(item)
                            else:
                                raise ValueError(f"Unexpected item type: {type(item)}")

                            if mapped_item is None:
                                raise ValueError(
                                    f"Failed to map item to {item_type.__name__}"
                                )

                            remapped_item = mapped_item.validate(raise_exception=False)
                            if not remapped_item.is_valid:
                                for error in remapped_item.errors:
                                    result.add_error(error)

                        # For simple types, check directly
                        if not self.is_of_type(item, item_type):
                            item_repr = self._get_value_repr(item)
                            result.add_error(
                                ValidationError(
                                    f"Item at index {i} expected to be {item_type.__name__}, got {type(item).__name__} with value: {item_repr}",
                                    field_name,
                                    item,
                                )
                            )
        # Handle Dict types
        elif origin is dict:
            if not self.is_of_type(value, dict):
                value_repr = self._get_value_repr(value)
                result.add_error(
                    ValidationError(
                        f"Expected type dict, got {type(value).__name__} with value: {value_repr}",
                        field_name,
                        value,
                    )
                )
            else:
                # Check the key and value types if specified
                key_type, val_type = get_args(self.expected_type)
                if key_type is not Any:
                    for k in value.keys():
                        if not self.is_of_type(k, key_type):
                            key_repr = self._get_value_repr(k)
                            result.add_error(
                                ValidationError(
                                    f"Dict key expected to be {key_type.__name__}, got {type(k).__name__} with value: {key_repr}",
                                    field_name,
                                    k,
                                )
                            )

                if val_type is not Any:
                    for k, v in value.items():
                        # Skip None values if the value type allows it
                        if v is None:
                            if get_origin(val_type) is Union and type(None) in get_args(
                                val_type
                            ):
                                continue
                            else:
                                result.add_error(
                                    ValidationError(
                                        f"Dict value for key '{k}' cannot be None",
                                        field_name,
                                        v,
                                    )
                                )
                                continue

                        # For simple types, check directly
                        if not self.is_of_type(v, val_type):
                            val_repr = self._get_value_repr(v)
                            result.add_error(
                                ValidationError(
                                    f"Dict value for key '{k}' expected to be {val_type.__name__}, got {type(v).__name__} with value: {val_repr}",
                                    field_name,
                                    v,
                                )
                            )
        elif origin is tuple:
            if not self.is_of_type(value, tuple) and not self.is_of_type(value, list):
                value_repr = self._get_value_repr(value)
                result.add_error(
                    ValidationError(
                        f"Expected type tuple, got {type(value).__name__} with value: {value_repr}",
                        field_name,
                        value,
                    )
                )
            else:
                tuple_types = get_args(self.expected_type)
                if len(tuple_types) != len(value):
                    value_repr = self._get_value_repr(value)
                    result.add_error(
                        ValidationError(
                            f"Expected tuple of length {len(tuple_types)}, got tuple of length {len(value)} with value: {value_repr}",
                            field_name,
                            value,
                        )
                    )
                else:
                    for i, item in enumerate(value):
                        if not self.is_of_type(item, tuple_types[i]):
                            item_repr = self._get_value_repr(item)
                            result.add_error(
                                ValidationError(
                                    f"Tuple item at index {i} expected to be {tuple_types[i].__name__}, got {type(item).__name__} with value: {item_repr}",
                                    field_name,
                                    item,
                                )
                            )
        elif origin is set:
            if not self.is_of_type(value, set) and not self.is_of_type(value, list):
                value_repr = self._get_value_repr(value)
                result.add_error(
                    ValidationError(
                        f"Expected type set, got {type(value)} with value: {value_repr}",
                        field_name,
                        value,
                    )
                )
            else:
                item_type = get_args(self.expected_type)[0]
                if item_type is not Any:
                    for item in value:
                        if not self.is_of_type(item, item_type):
                            item_repr = self._get_value_repr(item)
                            result.add_error(
                                ValidationError(
                                    f"Set item expected to be {item_type.__name__}, got {type(item).__name__} with value: {item_repr}",
                                    field_name,
                                    item,
                                )
                            )
        # Handle regular types
        elif not self.is_of_type(value, self.expected_type):
            value_repr = self._get_value_repr(value)
            result.add_error(
                ValidationError(
                    f"Expected type {self.expected_type.__name__}, got {type(value).__name__} with value: {value_repr}",
                    field_name,
                    value,
                )
            )

        return result

    def default(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Default validation method that runs all the time.
        For TypeValidator, this does the same validation as the validate method.

        Args:
            value: The value to validate.
            field_name: The name of the field being validated.

        Returns:
            A ValidationResult object.
        """

        if func.__annotations__:
            self.expected_type = func.__annotations__["return"]
        else:
            self.expected_type = None
            print("No expected type found for function", func.__name__)

        # For TypeValidator, default validation is the same as regular validation
        return self.validate(func, value, field_name)

    def _get_value_repr(self, value: Any) -> str:
        """
        Get a safe string representation of a value for error messages.

        Args:
            value: The value to represent.

        Returns:
            A string representation of the value, truncated if too long.
        """
        try:
            # Convert value to string and truncate if too long
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:97] + "..."
            return value_str
        except Exception:
            # If string conversion fails, return a safe fallback
            return f"<{type(value).__name__} object (unconvertible to string)>"

    def is_of_type(self, object, expected_type: Type) -> bool:
        """
        Check if an object is of the expected type, handling generic types properly.

        Args:
            object: The object to check.
            expected_type: The expected type.

        Returns:
            True if the object is of the expected type, False otherwise.
        """
        # Get the origin type for generics
        origin = get_origin(expected_type)

        # Handle non-generic types directly
        if origin is None:
            if expected_type is Any:
                return True
            return isinstance(object, expected_type)

        # Handle Union types (including Optional which is Union[T, None])
        if origin is Union:
            args = get_args(expected_type)
            return any(self.is_of_type(object, arg) for arg in args)

        # For all container types, first check if the object is of the right container type
        if origin is list:
            return isinstance(object, list)
        elif origin is dict:
            return isinstance(object, dict)
        elif origin is tuple:
            return isinstance(object, tuple)
        elif origin is set:
            return isinstance(object, set)

        # For any other generic type, just check against the origin
        return isinstance(object, origin)


@validator
class InstanceValidator(Validator):
    """Validator that checks if a value is an instance of a specific class."""

    def __init__(self, cls: Optional[Type] = None):
        self.cls = cls

    def validate(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Validate that a value is an instance of the specified class.

        Args:
            value: The value to validate.
            field_name: The name of the field being validated.

        Returns:
            A ValidationResult object.
        """
        result = ValidationResult()

        # Skip validation if no class is provided
        if self.cls is None:
            return result

        if not isinstance(value, self.cls):
            # Get a safe string representation of the value
            try:
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:97] + "..."
            except Exception:
                value_str = f"<{type(value).__name__} object (unconvertible to string)>"

            result.add_error(
                ValidationError(
                    f"Expected instance of {self.cls.__name__}, got {type(value).__name__} with value: {value_str}",
                    field_name,
                    value,
                )
            )

        return result

    def default(self, func: Callable, value: Any, field_name: str) -> ValidationResult:
        """
        Default validation method that runs all the time.
        For InstanceValidator, this does nothing by default.

        Args:
            value: The value to validate.
            field_name: The name of the field being validated.

        Returns:
            A ValidationResult object.
        """

        # Default implementation does nothing
        return ValidationResult()


# Decorator factories
def is_type(expected_type: Type):
    """Decorator to validate that a value is of the expected type."""
    return TypeValidator.create_decorator(expected_type)


def is_instance_of(cls: Type):
    """Decorator to validate that a value is an instance of a specific class."""
    return InstanceValidator.create_decorator(cls)
