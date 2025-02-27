from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Union,
    Callable,
    get_origin,
    get_args,
    get_type_hints,
)
import inspect
from functools import wraps
import json
from abc import ABC, abstractmethod


class ValidationError(Exception):
    """Exception raised for validation errors."""

    def __init__(
        self,
        message: str,
        field: str = None,
        value: Any = None,
        source_info: str = None,
        parent_object: Any = None,
    ):
        self.message = message
        self.field = field
        self.value = value
        self.source_info = source_info
        self.parent_object = parent_object

        # Format the error message to include the field as a stack trace indicator
        if field:
            error_message = f"{field}: {message}"

            # Add a stack trace-like indicator for the field
            value_repr = repr(value)
            # Truncate very long values
            if len(value_repr) > 100:
                value_repr = value_repr[:97] + "..."

            stack_trace = f"\n  at field '{field}' with value: {value_repr}"

            # Add source information if available
            if source_info:
                stack_trace += f"\n    defined in {source_info}"

            # Add parent object information if available
            if parent_object is not None:
                if hasattr(parent_object, "to_dict"):
                    parent_repr = parent_object.to_dict()
                else:
                    parent_repr = repr(parent_object)
                # Truncate very long parent object representations
                if len(parent_repr) > 200:
                    parent_repr = parent_repr[:197] + "..."
                stack_trace += f"\n    in object: {parent_repr}"

            super().__init__(error_message + stack_trace)
        else:
            # Even without a field, include it in the message if available
            if field:
                super().__init__(f"{field}: {message}")
            else:
                super().__init__(message)


class ValidationResult:
    """Class to hold validation results."""

    def __init__(self):
        self.errors: List[ValidationError] = []

    def add_error(self, error: ValidationError):
        self.errors.append(error)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def __str__(self) -> str:
        if self.is_valid:
            return "Validation passed"

        # Format errors in a stack trace-like manner
        error_messages = []
        for i, error in enumerate(self.errors):
            error_messages.append(f"Error {i + 1}: {str(error)}")

        return "\n" + "\n\n".join(error_messages)


class Validator(ABC):
    """Abstract base class for all validators."""

    @abstractmethod
    def validate(
        self,
        func: Callable,
        value: Any,
        field_name: str,
        source_info: str = None,
        parent_object: Any = None,
    ) -> ValidationResult:
        """
        Validate a value and return a ValidationResult.
        This method should be overridden by subclasses.

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

    @abstractmethod
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
        This method should be overridden by subclasses.

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


class ModelConfig:
    """Configuration class for ValidatedModel."""

    def __init__(
        self,
        validate_on_init: bool = True,
        validate_on_serialize: bool = True,
        allow_partial: bool = False,
        optional_fields: Optional[Set[str]] = None,
        strict_by_default: bool = True,
    ):
        self.validate_on_init = validate_on_init
        self.validate_on_serialize = validate_on_serialize
        self.allow_partial = allow_partial
        self.optional_fields = optional_fields or set()
        self.strict_by_default = strict_by_default


def validate(
    func: Optional[Callable] = None,
    *,
    is_optional: bool = False,
    skip_validators: Optional[List[str]] = None,
) -> Callable:
    """Decorator to validate a method."""
    from uhmactually.validators import type_check
    from uhmactually.validators import optional_check

    def decorator(func: Callable, is_optional: bool = False) -> Callable:
        """Decorator function."""
        # Store validation attributes in a dictionary to avoid issues with method objects
        validation_attrs = {
            "_requires_validation": True,
            "_skip_validators": skip_validators or [],
            "_validate_decorated": True,
        }

        # Preserve return type annotation if available
        if hasattr(func, "__annotations__") and "return" in func.__annotations__:
            validation_attrs["__annotations__"] = {
                "return": func.__annotations__["return"]
            }

        def is_optional_field(field):
            return get_origin(field) is Union and type(None) in get_args(field)

        @wraps(func)
        def wrapper(self, value=None):
            """Wrapper function."""
            # Check if this is a getter call (no arguments)
            data = None
            name = func.__name__
            if name in self._data:
                data = self._data[name]

            insect_return = inspect.signature(func).return_annotation

            if insect_return is not None:
                type_check(data, insect_return, func.__name__)

            print(
                f"checking optional data: {data} with return type {insect_return} and is_optional: {is_optional} with {get_origin(insect_return)} is {is_optional_field(insect_return)}"
            )
            if not is_optional and not is_optional_field(insect_return):
                print("not optional")
                optional_check(data)

            if func.__code__.co_argcount > 1:
                func(self, data)
            else:
                func(self)
            return data

        # Attach validation attributes to the wrapper function
        for attr_name, attr_value in validation_attrs.items():
            setattr(wrapper, attr_name, attr_value)

        return wrapper

    if func is None:
        return decorator
    return decorator(func, is_optional=is_optional)


class ValidatedModel:
    """Base class for models with validation."""

    # Default configuration
    _config = ModelConfig()

    def __init__(self, *args, **kwargs):
        """Initialize the model with the given data."""

        if len(args) > 0 and len(kwargs) > 0:
            raise ValueError(
                "Positional and keyword arguments are not allowed together, use either a dictionary or named arguments"
            )

        if len(args) > 0:
            if len(args) > 1:
                raise ValueError(
                    "Only one positional argument is allowed, use a dictionary or named arguments"
                )

            if not isinstance(args[0], dict):
                raise ValueError("Positional argument must be a dictionary")

            self = self.from_dict(args[0])
            return

        # Initialize data dictionary
        self._data = {}
        self._partial = False
        self._validate_on_set = False

        # Process all fields with validation
        print(f"kwargs: {kwargs}")
        for name, value in kwargs.items():
            # Check if the field exists in the model
            print(f"name: {name} with value: {value}")
            self._data[name] = value
            if hasattr(self, name):
                attr = getattr(self, name)
                if callable(attr) and hasattr(attr, "_requires_validation"):
                    # Set the value directly in the data dictionary first to avoid validation during init
                    print(f"Setting valid {name} to {value}")
                    # Call the validator method with the value to trigger validation
                    # This is needed for the new helper function approach
                    if hasattr(attr, "_validate_decorated"):
                        try:
                            attr(value)
                        except ValidationError as e:
                            # If validation fails, raise the error
                            raise e
                else:
                    # Set the value directly in the data dictionary
                    print(f"Setting {name} to {value}")
            else:
                # Unknown field, store it anyway
                print(f"Unknown field: {name} with value: {value}")

        # Enable validation on set after initialization
        self._validate_on_set = True

        # Validate the model if configured to do so
        if self._config.validate_on_init:
            self.validate(raise_exception=True)

    def _validate_field(self, field_name: str, value: Any) -> ValidationResult:
        """
        Validate a single field.

        Args:
            field_name: The name of the field to validate.
            value: The value to validate.

        Returns:
            A ValidationResult object.
        """
        result = ValidationResult()

        # Get the field method
        if not hasattr(self, field_name):
            return result

        field_method = getattr(self, field_name)
        if not callable(field_method) or not hasattr(
            field_method, "_requires_validation"
        ):
            return result

        # Get source information for the field method
        try:
            source_info = f"{self.__class__.__name__}.{field_name}"

            # Get the original undecorated method to find its source
            original_method = field_method
            while hasattr(original_method, "__wrapped__"):
                original_method = original_method.__wrapped__

            # Try to get the file and line number where the field method is defined
            source_file = inspect.getsourcefile(original_method)
            source_lines, start_line = inspect.getsourcelines(original_method)

            if source_file and start_line:
                # Get relative path if possible to make it more readable
                try:
                    import os

                    cwd = os.getcwd()
                    if source_file.startswith(cwd):
                        source_file = source_file[
                            len(cwd) + 1 :
                        ]  # +1 to remove the leading slash
                except:
                    pass  # Use the full path if we can't get the relative path

                source_info += f" ({source_file}:{start_line})"
        except (TypeError, OSError, AttributeError):
            source_info = f"{self.__class__.__name__}.{field_name}"

        # Skip validation if configured to do so
        if hasattr(field_method, "_skip_validators") and field_method._skip_validators:
            return result

        # Import here to avoid circular imports
        from uhmactually.validators.registry import VALIDATORS

        # Get a dictionary representation of the current object for context
        object_data = {}
        if hasattr(self, "_data"):
            object_data = self._data.copy()
            # Remove the current field to avoid circular references
            if field_name in object_data:
                object_data[field_name] = f"<current field: {type(value).__name__}>"

        # Track which validators have been executed
        executed_validators = set()

        # First, run specific validators that have been explicitly applied
        for validator_name, validator_cls in VALIDATORS.items():
            validator_attr = "_validator_class"

            if (
                hasattr(field_method, validator_attr)
                and field_method._validator_class == validator_cls
            ):
                # Specific validator is applied via decorator
                args = getattr(field_method, "_validator_args", ())
                kwargs = getattr(field_method, "_validator_kwargs", {})
                validator_instance = validator_cls(*args, **kwargs)

                # Run the validate method
                validator_result = validator_instance.validate(
                    field_method, value, field_name, source_info, object_data
                )

                # Add any errors to the result
                for error in validator_result.errors:
                    # Add source information to the error
                    updated_error = ValidationError(
                        error.message,
                        error.field,
                        error.value,
                        source_info,
                        object_data,
                    )
                    result.add_error(updated_error)

                # Mark this validator as executed
                executed_validators.add(validator_cls)

        # Call the field method with the value to run any custom validation
        # This will execute any helper functions in the method body
        try:
            # Check if the method accepts a value parameter
            sig = inspect.signature(field_method)
            param_count = len(sig.parameters)

            # Call the method with the value to run custom validation
            if param_count > 1:  # More than just 'self'
                field_method(value)
        except ValidationError as e:
            # Add source information to the error
            updated_error = ValidationError(
                e.message,
                e.field or field_name,
                e.value or value,
                source_info,
                object_data,
            )
            result.add_error(updated_error)

        # If we have errors from custom validation, skip default validation
        if result.errors:
            return result

        # Then, run default validation for validators that haven't been executed yet
        for validator_name, validator_cls in VALIDATORS.items():
            # Skip validators that have already been executed
            if validator_cls in executed_validators:
                continue

            # Create validator instance and run default validation
            validator_instance = validator_cls()
            validator_result = validator_instance.default(
                field_method, value, field_name, source_info, object_data
            )

            # Add any errors to the result
            for error in validator_result.errors:
                # Add source information to the error
                updated_error = ValidationError(
                    error.message, error.field, error.value, source_info, object_data
                )
                result.add_error(updated_error)

        # Validate nested models in lists
        if isinstance(value, list) or isinstance(value, set):
            # Check if we have type information for the list items
            item_type = None
            if hasattr(field_method, "_return_type"):
                return_type = field_method._return_type
                if get_origin(return_type) is list and get_args(return_type):
                    item_type = get_args(return_type)[0]

            # Validate each item in the list if it's a ValidatedModel
            for i, item in enumerate(value):
                if isinstance(item, ValidatedModel):
                    item_result = item.validate(raise_exception=False)
                    if not item_result.is_valid:
                        for error in item_result.errors:
                            # Prefix the error with the list index
                            prefixed_error = ValidationError(
                                f"Item at index {i}: {error.message}",
                                f"{field_name}[{i}].{error.field}"
                                if error.field
                                else f"{field_name}[{i}]",
                                error.value,
                                source_info,
                                object_data,
                            )
                            result.add_error(prefixed_error)
                elif (
                    item_type
                    and hasattr(item_type, "__origin__")
                    and hasattr(item_type.__origin__, "__mro__")
                    and any(
                        cls.__name__ == "ValidatedModel"
                        for cls in item_type.__origin__.__mro__
                    )
                ):
                    # This is a list of ValidatedModel subclasses, but the item is not a ValidatedModel
                    result.add_error(
                        ValidationError(
                            f"Item at index {i} expected to be a ValidatedModel, got {type(item).__name__}",
                            field_name,
                            item,
                            source_info,
                            object_data,
                        )
                    )

        # Validate nested models in dictionaries
        elif isinstance(value, dict):
            # Check if we have type information for the dict values
            value_type = None
            if hasattr(field_method, "_return_type"):
                return_type = field_method._return_type
                if get_origin(return_type) is dict and len(get_args(return_type)) >= 2:
                    value_type = get_args(return_type)[1]

            # Validate each value in the dict if it's a ValidatedModel
            for key, item in value.items():
                if isinstance(item, ValidatedModel):
                    item_result = item.validate(raise_exception=False)
                    if not item_result.is_valid:
                        for error in item_result.errors:
                            # Prefix the error with the dict key
                            prefixed_error = ValidationError(
                                f"Value for key '{key}': {error.message}",
                                f"{field_name}['{key}'].{error.field}"
                                if error.field
                                else f"{field_name}['{key}']",
                                error.value,
                                source_info,
                                object_data,
                            )
                            result.add_error(prefixed_error)
                elif (
                    value_type
                    and hasattr(value_type, "__origin__")
                    and hasattr(value_type.__origin__, "__mro__")
                    and any(
                        cls.__name__ == "ValidatedModel"
                        for cls in value_type.__origin__.__mro__
                    )
                ):
                    # This is a dict of ValidatedModel subclasses, but the value is not a ValidatedModel
                    result.add_error(
                        ValidationError(
                            f"Value for key '{key}' expected to be a ValidatedModel, got {type(item).__name__}",
                            field_name,
                            item,
                            source_info,
                            object_data,
                        )
                    )
        elif isinstance(value, tuple):
            # Validate each item in the tuple if it's a ValidatedModel
            for i, item in enumerate(value):
                item_type = None
                if hasattr(field_method, "_return_type"):
                    return_type = field_method._return_type
                    if (
                        get_origin(return_type) is tuple
                        and len(get_args(return_type)) >= i
                    ):
                        item_type = get_args(return_type)[i]

                if isinstance(item, ValidatedModel):
                    item_result = item.validate(raise_exception=False)
                    if not item_result.is_valid:
                        for error in item_result.errors:
                            # Prefix the error with the tuple index
                            prefixed_error = ValidationError(
                                f"Tuple item at index {i}: {error.message}",
                                f"{field_name}[{i}].{error.field}"
                                if error.field
                                else f"{field_name}[{i}]",
                                error.value,
                                source_info,
                                object_data,
                            )
                            result.add_error(prefixed_error)
                elif (
                    item_type
                    and hasattr(item_type, "__origin__")
                    and hasattr(item_type.__origin__, "__mro__")
                    and any(
                        cls.__name__ == "ValidatedModel"
                        for cls in item_type.__origin__.__mro__
                    )
                ):
                    result.add_error(
                        ValidationError(
                            f"Tuple item at index {i} expected to be a ValidatedModel, got {type(item).__name__}",
                            field_name,
                            item,
                            source_info,
                            object_data,
                        )
                    )

        return result

    def validate(self, raise_exception: bool = True) -> ValidationResult:
        """
        Validate the entire model.

        Args:
            raise_exception: If True, raise a ValidationError if validation fails.

        Returns:
            A ValidationResult object.
        """
        result = ValidationResult()

        # Validate each field
        for field_name in self._data:
            print(f"field_name internally: {field_name}")
            if hasattr(self, field_name):
                attr = getattr(self, field_name)
                if callable(attr) and hasattr(attr, "_requires_validation"):
                    if hasattr(attr, "_validate_decorated"):
                        try:
                            attr(self._data[field_name])
                        except ValidationError as e:
                            # If validation fails, raise the error
                            raise e
            else:
                # Unknown field, store it anyway
                print(
                    f"Unknown field: {field_name} with value: {self._data[field_name]}"
                )

        # Raise exception if configured to do so
        if raise_exception and not result.is_valid:
            raise ValidationError(str(result))

        return result

    def __eq__(self, other) -> bool:
        """Check if two models are equal."""
        return self.to_dict() == other.to_dict()

    @classmethod
    def partial(cls, **kwargs):
        """Create a partial model instance."""
        instance = cls(**kwargs)
        instance._partial = True
        return instance

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        result = {}

        # Include all fields with data
        for field_name in self._data:
            value = self._data[field_name]

            # Handle nested ValidatedModel instances
            if isinstance(value, ValidatedModel):
                result[field_name] = value.to_dict()
            # Handle lists of ValidatedModel instances
            elif isinstance(value, list):
                result[field_name] = [
                    item.to_dict() if isinstance(item, ValidatedModel) else item
                    for item in value
                ]
            # Handle dictionaries with ValidatedModel values
            elif isinstance(value, dict):
                result[field_name] = {
                    k: v.to_dict() if isinstance(v, ValidatedModel) else v
                    for k, v in value.items()
                }
            # Handle tuples with ValidatedModel values
            elif isinstance(value, tuple):
                result[field_name] = tuple(
                    v.to_dict() if isinstance(v, ValidatedModel) else v for v in value
                )
            # Handle sets with ValidatedModel values
            elif isinstance(value, set):
                result[field_name] = set(
                    v.to_dict() if isinstance(v, ValidatedModel) else v for v in value
                )
            else:
                result[field_name] = value

        return result

    def to_json(self) -> str:
        """Convert the model to a JSON string."""
        # Validate before serialization if configured
        if getattr(self.__class__._config, "validate_on_serialize", True):
            self.validate(raise_exception=True)

        return json.dumps(
            self.to_dict(),
            # handle sets and tuples
            default=lambda o: o.to_dict()
            if hasattr(o, "to_dict")
            else (tuple(o) if isinstance(o, (tuple, set)) else str(o)),
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create a model instance from a dictionary."""
        # Create the instance, which will validate the data
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "ValidatedModel":
        """
        Create a model from a JSON string.

        Args:
            json_str: The JSON string to parse.

        Returns:
            A new model instance.
        """
        data = json.loads(json_str)

        # Handle special types that JSON doesn't support natively
        for key, value in data.items():
            # Convert lists to tuples if the field expects a tuple
            if isinstance(value, list) and hasattr(cls, key):
                field_method = getattr(cls, key)
                if (
                    hasattr(field_method, "__annotations__")
                    and "return" in field_method.__annotations__
                ):
                    return_type = field_method.__annotations__["return"]
                    if get_origin(return_type) is tuple:
                        data[key] = tuple(value)

        return cls.from_dict(data)
