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
import inspect

from uhmactually.core import (
    Validator,
    ValidationError,
    ValidationResult,
    ValidatedModel,
)


# Helper functions for type validation
def is_type(value: Any, expected_type: Type) -> None:
    """
    Validate that a value is of the expected type.

    Args:
        value: The value to validate.
        expected_type: The expected type.

    Raises:
        ValidationError: If the value is not of the expected type.
    """
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"Expected type {expected_type.__name__}, got {type(value).__name__}",
            None,
            value,
        )


def is_instance_of(value: Any, cls: Type) -> None:
    """
    Validate that a value is an instance of the specified class.

    Args:
        value: The value to validate.
        cls: The expected class.

    Raises:
        ValidationError: If the value is not an instance of the specified class.
    """
    if not isinstance(value, cls):
        raise ValidationError(
            f"Expected instance of {cls.__name__}, got {type(value).__name__}",
            None,
            value,
        )


class TypeValidator(Validator):
    """Validator that checks if a value is of the expected type."""

    def __init__(self, expected_type: Optional[Type] = None):
        self.expected_type = expected_type

    def validate(
        self,
        func: Callable,
        value: Any,
        field_name: str,
        source_info: str = None,
        parent_object: Any = None,
    ) -> ValidationResult:
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
        if self.expected_type is None or value is None:
            return result

        # Get the origin type (for generics like List, Dict, etc.)
        origin = get_origin(self.expected_type)

        # Handle Any type (matches everything)
        if self.expected_type is Any:
            return result

        # Handle Union types (including Optional which is Union[T, None])
        if origin is Union:
            args = get_args(self.expected_type)
            # If None is one of the types, the value can be None
            if value is None and type(None) in args:
                return result

            # For non-None values, check if it matches any of the types
            if value is not None:
                # Remove None from the types to check
                types_to_check = [arg for arg in args if arg is not type(None)]
                for arg in types_to_check:
                    # Create a new validator for each type and check
                    type_validator = TypeValidator(arg)
                    type_result = type_validator.validate(
                        func, value, field_name, source_info, parent_object
                    )
                    if type_result.is_valid:
                        return result  # If any type matches, validation passes

                # If we get here, no type matched
                types_str = ", ".join(
                    [
                        arg.__name__ if hasattr(arg, "__name__") else str(arg)
                        for arg in types_to_check
                    ]
                )
                value_repr = self._get_value_repr(value)
                result.add_error(
                    ValidationError(
                        f"Expected one of types ({types_str}), got {type(value).__name__} with value: {value_repr}",
                        field_name,
                        value,
                        source_info,
                        parent_object,
                    )
                )
                return result

        # Handle List types
        elif origin is list:
            if not self.is_of_type(value, list):
                value_repr = self._get_value_repr(value)
                result.add_error(
                    ValidationError(
                        f"Expected type list, got {type(value).__name__} with value: {value_repr}",
                        field_name,
                        value,
                        source_info,
                        parent_object,
                    )
                )
            else:
                # Check the type of items in the list if specified
                item_types = get_args(self.expected_type)
                if item_types and item_types[0] is not Any:
                    item_type = item_types[0]
                    for i, item in enumerate(value):
                        if not self.is_of_type(item, item_type):
                            item_repr = self._get_value_repr(item)
                            result.add_error(
                                ValidationError(
                                    f"List item at index {i} expected to be {item_type.__name__}, got {type(item).__name__} with value: {item_repr}",
                                    field_name,
                                    item,
                                    source_info,
                                    parent_object,
                                )
                            )

                        # Handle nested ValidatedModel classes
                        if (
                            inspect.isclass(item_type)
                            and hasattr(item_type, "__mro__")
                            and any(
                                cls.__name__ == "ValidatedModel"
                                for cls in item_type.__mro__
                            )
                        ):
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

        # Handle Dict types
        elif origin is dict:
            if not self.is_of_type(value, dict):
                value_repr = self._get_value_repr(value)
                result.add_error(
                    ValidationError(
                        f"Expected type dict, got {type(value).__name__} with value: {value_repr}",
                        field_name,
                        value,
                        source_info,
                        parent_object,
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
                                    source_info,
                                    parent_object,
                                )
                            )
                if val_type is not Any:
                    for k, v in value.items():
                        if not self.is_of_type(v, val_type):
                            val_repr = self._get_value_repr(v)
                            result.add_error(
                                ValidationError(
                                    f"Dict value for key '{k}' expected to be {val_type.__name__}, got {type(v).__name__} with value: {val_repr}",
                                    field_name,
                                    v,
                                    source_info,
                                    parent_object,
                                )
                            )

        # Handle Tuple types
        elif origin is tuple:
            if not self.is_of_type(value, tuple):
                value_repr = self._get_value_repr(value)
                result.add_error(
                    ValidationError(
                        f"Expected type tuple, got {type(value).__name__} with value: {value_repr}",
                        field_name,
                        value,
                        source_info,
                        parent_object,
                    )
                )
            else:
                # Check the types of items in the tuple if specified
                item_types = get_args(self.expected_type)
                if item_types:
                    # Check if the tuple has the correct length
                    if len(value) != len(item_types):
                        result.add_error(
                            ValidationError(
                                f"Expected tuple of length {len(item_types)}, got length {len(value)}",
                                field_name,
                                value,
                                source_info,
                                parent_object,
                            )
                        )
                    else:
                        # Check each item against its expected type
                        for i, (item, item_type) in enumerate(zip(value, item_types)):
                            if item_type is not Any and not self.is_of_type(
                                item, item_type
                            ):
                                item_repr = self._get_value_repr(item)
                                result.add_error(
                                    ValidationError(
                                        f"Tuple item at index {i} expected to be {item_type.__name__}, got {type(item).__name__} with value: {item_repr}",
                                        field_name,
                                        item,
                                        source_info,
                                        parent_object,
                                    )
                                )

        # Handle Set types
        elif origin is set:
            if not self.is_of_type(value, set) and not self.is_of_type(value, list):
                value_repr = self._get_value_repr(value)
                result.add_error(
                    ValidationError(
                        f"Expected type set, got {type(value).__name__} with value: {value_repr}",
                        field_name,
                        value,
                        source_info,
                        parent_object,
                    )
                )
            else:
                # Check the type of items in the set if specified
                item_types = get_args(self.expected_type)
                if item_types and item_types[0] is not Any:
                    item_type = item_types[0]
                    for i, item in enumerate(value):
                        if not self.is_of_type(item, item_type):
                            item_repr = self._get_value_repr(item)
                            result.add_error(
                                ValidationError(
                                    f"Set item expected to be {item_type.__name__}, got {type(item).__name__} with value: {item_repr}",
                                    field_name,
                                    item,
                                    source_info,
                                    parent_object,
                                )
                            )

        # Handle all other types
        elif not self.is_of_type(value, self.expected_type):
            value_repr = self._get_value_repr(value)
            type_name = (
                self.expected_type.__name__
                if hasattr(self.expected_type, "__name__")
                else str(self.expected_type)
            )
            result.add_error(
                ValidationError(
                    f"Expected type {type_name}, got {type(value).__name__} with value: {value_repr}",
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
        For TypeValidator, this checks the type based on the function's return annotation.

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

        # Get the expected type from the function's return annotation
        if func.__annotations__ and "return" in func.__annotations__:
            self.expected_type = func.__annotations__["return"]
        else:
            # If no return type annotation, try to infer the type from the value
            self.expected_type = None
            print(
                f"No expected type found for function {func.__name__} in {field_name} from {source_info}"
            )

            # Even without a type annotation, we can still do basic type validation
            # based on the value's type
            if isinstance(value, (str, int, float, bool, list, dict, tuple, set)):
                # For basic types, validate that future values match this type
                expected_type = type(value)
                if not isinstance(value, expected_type):
                    result.add_error(
                        ValidationError(
                            f"Expected type {expected_type.__name__}, got {type(value).__name__}",
                            field_name,
                            value,
                            source_info,
                            parent_object,
                        )
                    )
                return result

        # For TypeValidator, default validation is the same as regular validation
        return self.validate(func, value, field_name, source_info, parent_object)

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


class InstanceValidator(Validator):
    """Validator that checks if a value is an instance of a specific class."""

    def __init__(self, cls: Optional[Type] = None):
        self.cls = cls

    def validate(
        self,
        func: Callable,
        value: Any,
        field_name: str,
        source_info: str = None,
        parent_object: Any = None,
    ) -> ValidationResult:
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
        For InstanceValidator, this does nothing by default.

        Args:
            value: The value to validate.
            field_name: The name of the field being validated.
            source_info: Additional information about the source of the value.
            parent_object: The object containing this field.

        Returns:
            A ValidationResult object.
        """

        # Default implementation does nothing
        return ValidationResult()


# Helper function wrappers for validators
def type_check(value, expected_type: Type, field_name: str = None):
    """
    Check if a value is of the expected type.

    Args:
        value: The value to check.
        expected_type: The expected type.
        field_name: The name of the field being validated. If None, will try to determine from call stack.

    Raises:
        ValidationError: If the value is not of the expected type.
    """
    # Try to determine field name from call stack if not provided
    if field_name is None:
        import inspect

        frame = inspect.currentframe().f_back
        if frame:
            # Get the function that called this function
            func_name = frame.f_code.co_name
            # If the function name is a property name in a ValidatedModel class, use it as field_name
            if func_name != "<module>":
                field_name = func_name

    validator = TypeValidator(expected_type)
    result = validator.validate(type_check, value, field_name or "value")
    if not result.is_valid:
        raise ValidationError(result.errors[0].message, field_name, value)


def instance_check(value, cls: Type, field_name: str = None):
    """
    Check if a value is an instance of the specified class.

    Args:
        value: The value to check.
        cls: The expected class.
        field_name: The name of the field being validated. If None, will try to determine from call stack.

    Raises:
        ValidationError: If the value is not an instance of the specified class.
    """
    # Try to determine field name from call stack if not provided
    if field_name is None:
        import inspect

        frame = inspect.currentframe().f_back
        if frame:
            # Get the function that called this function
            func_name = frame.f_code.co_name
            # If the function name is a property name in a ValidatedModel class, use it as field_name
            if func_name != "<module>":
                field_name = func_name

    validator = InstanceValidator(cls)
    result = validator.validate(instance_check, value, field_name or "value")
    if not result.is_valid:
        raise ValidationError(result.errors[0].message, field_name, value)
