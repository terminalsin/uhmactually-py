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

    def __init__(self, message: str, field: str = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(f"{field}: {message}" if field else message)


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
        return "\n".join(str(error) for error in self.errors)


class Validator(ABC):
    """Abstract base class for all validators."""

    @abstractmethod
    def validate(self, value: Any, field_name: str) -> ValidationResult:
        """
        Validate a value and return a ValidationResult.
        This method should be overridden by subclasses.
        """
        # Default implementation does nothing
        return ValidationResult()

    @abstractmethod
    def default(self, value: Any, field_name: str) -> ValidationResult:
        """
        Default validation method that runs all the time.
        This method should be overridden by subclasses.

        Args:
            value: The value to validate.
            field_name: The name of the field being validated.

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


def validate(func=None, *, skip_validators=False):
    """
    Decorator to mark a field for validation.

    This decorator registers all known validators for the field and has them use their default
    function unless the field already has a specific validator decorator.

    Args:
        func: The function to decorate.
        skip_validators: If True, skip registered validators for this field.

    Returns:
        The decorated function.
    """

    def decorator(func: Callable):
        # Mark the function as requiring validation
        func._requires_validation = True
        func._skip_validators = skip_validators

        # Get the return type annotation if available
        if hasattr(func, "__annotations__") and "return" in func.__annotations__:
            func._return_type = func.__annotations__["return"]

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if len(args) == 1:
                print(f"wrapper called with {args}, {kwargs}")

                try:
                    return func(self, *args, **kwargs)
                except ValidationError as e:
                    raise e
                except Exception as e:
                    print(f"error: {e}")
                    raise e

            # If called without arguments, this is a getter call
            if hasattr(self, "_data") and func.__name__ in self._data:
                return self._data[func.__name__]

            # Call the original function if no value is stored
            return func(self)

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


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
        for name, value in kwargs.items():
            # Check if the field exists in the model
            if hasattr(self, name):
                attr = getattr(self, name)
                if callable(attr) and hasattr(attr, "_requires_validation"):
                    # Set the value directly in the data dictionary first to avoid validation during init
                    self._data[name] = value
                else:
                    # Set the value directly in the data dictionary
                    self._data[name] = value
            else:
                # Unknown field, store it anyway
                self._data[name] = value

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

        # Skip validation if configured to do so
        if hasattr(field_method, "_skip_validators") and field_method._skip_validators:
            return result

        # Import here to avoid circular imports
        from uhmactually.validators.registry import VALIDATORS

        # Check if the field has specific validators
        has_specific_validators = False

        # Run specific validators if present
        for validator_name, validator_cls in VALIDATORS.items():
            validator_attr = "_validator_class"

            if (
                hasattr(field_method, validator_attr)
                and field_method._validator_class == validator_cls
            ):
                has_specific_validators = True

                # Create validator instance with stored arguments
                args = getattr(field_method, "_validator_args", ())
                kwargs = getattr(field_method, "_validator_kwargs", {})
                validator_instance = validator_cls(*args, **kwargs)

                # Run the validate method
                validator_result = validator_instance.validate(
                    field_method, value, field_name
                )

                # Add any errors to the result
                for error in validator_result.errors:
                    result.add_error(error)

        # If no specific validators, run default validation for all registered validators
        if not has_specific_validators:
            # Also run default validation for all registered validators
            for validator_name, validator_cls in VALIDATORS.items():
                # Create validator instance with no arguments
                validator_instance = validator_cls()

                # Run the default method
                validator_result = validator_instance.default(
                    field_method, value, field_name
                )

                # Add any errors to the result
                for error in validator_result.errors:
                    result.add_error(error)

        # Validate nested models in lists
        if isinstance(value, list):
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
                                f"{field_name}[{i}]",
                                error.value,
                            )
                            result.add_error(prefixed_error)
                elif (
                    item_type
                    and hasattr(item_type, "__origin__")
                    and issubclass(item_type.__origin__, ValidatedModel)
                ):
                    # This is a list of ValidatedModel subclasses, but the item is not a ValidatedModel
                    result.add_error(
                        ValidationError(
                            f"Item at index {i} expected to be a ValidatedModel, got {type(item).__name__}",
                            field_name,
                            item,
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
                                f"{field_name}['{key}']",
                                error.value,
                            )
                            result.add_error(prefixed_error)
                elif (
                    value_type
                    and hasattr(value_type, "__origin__")
                    and issubclass(value_type.__origin__, ValidatedModel)
                ):
                    # This is a dict of ValidatedModel subclasses, but the value is not a ValidatedModel
                    result.add_error(
                        ValidationError(
                            f"Value for key '{key}' expected to be a ValidatedModel, got {type(item).__name__}",
                            field_name,
                            item,
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
                                f"{field_name}[{i}]",
                                error.value,
                            )
                            result.add_error(prefixed_error)
                elif (
                    item_type
                    and hasattr(item_type, "__origin__")
                    and issubclass(item_type.__origin__, ValidatedModel)
                ):
                    result.add_error(
                        ValidationError(
                            f"Tuple item at index {i} expected to be a ValidatedModel, got {type(item).__name__}",
                            field_name,
                            item,
                        )
                    )

        elif isinstance(value, ValidatedModel):
            nested_result = value.validate(raise_exception=False)
            if not nested_result.is_valid:
                for error in nested_result.errors:
                    # Prefix the error with the field name
                    result.add_error(error)

        # Call the field method with the value if it has a custom validation implementation
        parameters = inspect.signature(field_method).parameters
        if len(parameters) > 0:  # More than just 'self'
            try:
                # Call the method with the value to run any custom validation
                field_method(value)
            except ValidationError as e:
                result.add_error(e)

        return result

    def validate(self, raise_exception: bool = False) -> ValidationResult:
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
            if hasattr(self, field_name):
                field_method = getattr(self, field_name)
                if callable(field_method) and hasattr(
                    field_method, "_requires_validation"
                ):
                    field_result = self._validate_field(
                        field_name, self._data[field_name]
                    )

                    # Add any errors to the result
                    for error in field_result.errors:
                        result.add_error(error)

        # Raise exception if configured to do so
        if raise_exception and not result.is_valid:
            raise ValidationError(str(result))

        return result

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
    def from_json(cls, json_str: str):
        """Create a model instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
