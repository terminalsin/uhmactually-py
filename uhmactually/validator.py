from typing import (
    TypeVar,
    Callable,
    Dict,
    List,
    Any,
    Optional,
    get_type_hints,
    Type,
    Union,
)
from abc import ABC, abstractmethod
import inspect
import functools

T = TypeVar("T")

# Registry to store validator classes
_validator_registry: Dict[str, Type["Validator"]] = {}


def validator(validator_class: Type["Validator"]) -> Type["Validator"]:
    """
    Decorator to register a Validator class.
    This allows the validator to be used throughout the system.
    """
    if not issubclass(validator_class, Validator):
        raise TypeError(
            f"@validator can only be applied to Validator subclasses, got {validator_class.__name__}"
        )

    # Register this validator class by its type
    _validator_registry[validator_class.registered_name()] = validator_class

    # Return the class unchanged
    return validator_class


def validate(field_func: Callable) -> Callable:
    """
    Decorator to mark a method as a field that needs validation.
    This applies to methods in ValidatedModel subclasses.
    """

    class ValidationMethodWrapper:
        def __init__(self, func):
            self.func = func
            self._is_validation_field = True
            self._validators = getattr(func, "_validators", [])
            functools.update_wrapper(self, func)

        def __get__(self, obj, objtype=None):
            if obj is None:
                return self

            @functools.wraps(self.func)
            def bound_method(*args, **kwargs):
                # No args means getter call
                if len(args) == 0:
                    # Return the cached value if available
                    field_name = self.func.__name__
                    if field_name in obj._cached_values:
                        return obj._cached_values[field_name]
                    # If no cached value and no args, run the function with None
                    return self.func(obj, None)
                # With args, validate and update the value
                result = self.func(obj, *args, **kwargs)
                # Update cached value
                field_name = self.func.__name__
                obj._cached_values[field_name] = result
                return result

            # Copy validator attributes to the bound method
            bound_method._validators = self._validators
            bound_method._is_validation_field = True

            return bound_method

        def __call__(self, *args, **kwargs):
            # This makes the wrapper callable directly
            return self.func(*args, **kwargs)

    return ValidationMethodWrapper(field_func)


class ValidationInput:
    """Container for data being validated along with its definition."""

    def __init__(
        self, value: Any, field_name: str, definition: Callable, model_instance=None
    ):
        self.value = value
        self.field_name = field_name
        self.definition = definition
        self.model_instance = model_instance

    def get_type(self) -> Optional[Type]:
        """Get the expected type from the field definition."""
        try:
            return get_type_hints(self.definition).get("return")
        except:
            return None


class ValidationResult:
    """Result of a validation operation."""

    def __init__(self, is_valid: bool, message: str = None, value: Any = None):
        self.is_valid = is_valid
        self.message = message
        self.value = value  # Can be used to transform the input


class Validator(ABC):
    """Abstract base class for all validators."""

    def __init__(self):
        self.validator_type = self.__class__.__name__.lower().replace("validator", "")

    @abstractmethod
    def validate(self, input: ValidationInput, **kwargs) -> ValidationResult:
        """
        Validate the input against this validator's rules.
        Returns a ValidationResult with success/failure and optional transformed value.
        """
        pass

    def default(self, input: ValidationInput) -> ValidationResult:
        """
        Default validation logic that runs even when this validator is not explicitly applied.
        This is useful for validators that should run implicitly based on type annotations
        or other function metadata.

        Most validators will return success() here (no-op), but specialized validators
        like TypeValidator or AllowNone will implement their own logic.

        Returns ValidationResult with success/failure and optional transformed value.
        """
        # By default, no validation is performed
        return self.success()

    @classmethod
    def registered_name(cls) -> str:
        """
        Get the name of the validator as it will be registered in the _validator_registry.
        """
        return cls.__name__.lower().replace("validator", "")

    def generate_decorator(self, **kwargs) -> Callable:
        """
        Generate a decorator for this validator that can be applied to model fields.
        """
        decorator_kwargs = kwargs
        validator_instance = self

        def decorator(func):
            # Create method wrapper class with descriptor protocol
            class MethodWrapper:
                def __init__(self, func):
                    self.func = func
                    self._validators = getattr(func, "_validators", [])
                    self._validators.append(
                        {
                            "validator": validator_instance,
                            "decorator_kwargs": decorator_kwargs,
                        }
                    )
                    self._is_validation_field = True
                    functools.update_wrapper(self, func)

                def __get__(self, obj, objtype=None):
                    if obj is None:
                        return self

                    @functools.wraps(self.func)
                    def bound_method(*args, **kwargs):
                        return self.func(obj, *args, **kwargs)

                    # Copy validator attributes to the bound method
                    bound_method._validators = self._validators
                    bound_method._is_validation_field = True

                    return bound_method

                def __call__(self, *args, **kwargs):
                    # This makes the wrapper callable directly
                    return self.func(*args, **kwargs)

            # Return an instance of the wrapper
            return MethodWrapper(func)

        return decorator

    def fail(self, message: str) -> ValidationResult:
        """Helper to create a failed validation result."""
        return ValidationResult(is_valid=False, message=message)

    def success(self, value: Any = None) -> ValidationResult:
        """Helper to create a successful validation result, optionally with a transformed value."""
        return ValidationResult(is_valid=True, value=value)


class ValidatedModel(ABC):
    """Base class for models with field validation."""

    def __init__(self, **kwargs):
        # Store all constructor arguments as attributes
        self._fields = {}  # Track fields that have been set
        self._cached_values = {}  # Store validated values
        self._wrapped_values = {}  # Store wrapped callable values

        for key, value in kwargs.items():
            self._fields[key] = value

        # Run validation after initialization
        self.validate()

    def __getattribute__(self, name):
        # Special attributes shouldn't trigger the wrapper logic
        if name.startswith("_") or name == "validate":
            return super().__getattribute__(name)

        # Check if we have a wrapped value already
        try:
            wrapped_values = super().__getattribute__("_wrapped_values")
            if name in wrapped_values:
                return wrapped_values[name]
        except (AttributeError, KeyError):
            pass

        # If no wrapped value, check for a cached value
        try:
            cached_values = super().__getattribute__("_cached_values")
            if name in cached_values:
                # Get the cached value
                value = cached_values[name]
                # Create a wrapper
                wrapper = CallableValue(value, self, name)
                # Store it for future use
                wrapped_values = super().__getattribute__("_wrapped_values")
                wrapped_values[name] = wrapper
                return wrapper
        except (AttributeError, KeyError):
            pass

        # If not a special attribute and not in cached values,
        # use the normal attribute lookup
        return super().__getattribute__(name)

    def validate(self):
        """
        Scans the model for fields marked with @validate and validates them.
        Raises ValidationException if validation fails.
        """
        # Find all methods marked with @validate
        validation_fields = {}
        for name, method in inspect.getmembers(self.__class__):
            if hasattr(method, "_is_validation_field") and method._is_validation_field:
                validation_fields[name] = method

        # Process each validation field
        for field_name, field_method in validation_fields.items():
            # Skip if field wasn't provided and there's no default
            if field_name not in self._fields and not hasattr(self, field_name):
                continue

            # Get the current value from stored fields
            field_value = self._fields.get(field_name)

            # Get parameter count to determine how to call the method
            sig = inspect.signature(field_method)
            param_count = len(sig.parameters)

            # Store the validated result for later use
            try:
                if param_count == 1:  # Just self
                    result = field_method(self)
                elif param_count == 2:  # self and input
                    result = field_method(self, field_value)
                else:
                    raise ValueError(
                        f"Invalid parameter count for {field_name}: expected 0 or 1, got {param_count - 1}"
                    )

                # Store the result for later retrieval
                if result is not None:
                    self._cached_values[field_name] = result
            except Exception as e:
                # If not a ValidationException, wrap it
                if not isinstance(e, ValidationException):
                    expected_type = get_type_hints(field_method).get("return", Any)
                    raise ValidationException(
                        message=str(e),
                        field_name=field_name,
                        received={"value": field_value},
                        expected={"type": str(expected_type)},
                    )
                raise

            # Run all explicitly attached validators
            explicit_validators = []
            if hasattr(field_method, "_validators") and field_method._validators:
                explicit_validators = field_method._validators

                for validator_config in explicit_validators:
                    validator_kwargs = validator_config["decorator_kwargs"]
                    validator_instance = validator_config["validator"]
                    self._run_validator(
                        validator_instance,
                        field_name,
                        field_method,
                        field_value,
                        **validator_kwargs,
                    )

            # Run default validation from all registered validators that are not explicitly attached
            for validator_type, validator_class in _validator_registry.items():
                # Check if this validator type is already used explicitly
                validator_already_used = any(
                    isinstance(v, dict)
                    and v["validator"].validator_type == validator_type
                    or hasattr(v, "validator_type")
                    and v.validator_type == validator_type
                    for v in explicit_validators
                )

                if validator_already_used:
                    continue

                # Create an instance if needed
                validator_instance = validator_class()

                # Create validation input for default validation
                validation_input = ValidationInput(
                    value=field_value,
                    field_name=field_name,
                    definition=field_method,
                    model_instance=self,
                )

                # Run the default validation (special validators like Type or AllowNone may do something here)
                try:
                    result = validator_instance.default(validation_input)
                    if not result.is_valid:
                        raise ValidationException(
                            message=result.message
                            or f"Default validation failed for {field_name}",
                            field_name=field_name,
                            received={"value": field_value},
                            expected={
                                "validator": validator_instance.validator_type,
                                "implicitRule": True,
                            },
                        )
                    elif result.value is not None:
                        # Update with transformed value
                        field_value = result.value
                        setattr(self, field_name, result.value)
                except Exception as e:
                    if not isinstance(e, ValidationException):
                        raise ValidationException(
                            message=str(e),
                            field_name=field_name,
                            received={"value": field_value},
                            expected={
                                "validator": validator_instance.validator_type,
                                "implicitRule": True,
                            },
                        )
                    raise

        # Run custom validation logic
        self._validate_custom()

    def _run_validator(
        self,
        validator_instance,
        field_name,
        field_method,
        field_value,
        **validator_kwargs,
    ):
        """Helper method to run a validator against a field."""
        # Prepare validation input
        validation_input = ValidationInput(
            value=field_value,
            field_name=field_name,
            definition=field_method,
            model_instance=self,
        )

        # Run validation
        try:
            result = validator_instance.validate(validation_input, **validator_kwargs)

            # Handle validation result
            if not result.is_valid:
                # No default, raise exception immediately
                raise ValidationException(
                    message=result.message or f"Validation failed for {field_name}",
                    field_name=field_name,
                    received={"value": field_value},
                    expected={"validator": validator_instance.validator_type},
                )
            elif result.value is not None:
                # Update with transformed value
                setattr(self, field_name, result.value)
        except Exception as e:
            # If not a ValidationException, wrap it
            if not isinstance(e, ValidationException):
                print(e)
                raise ValidationException(
                    message=str(e),
                    field_name=field_name,
                    received={"value": field_value},
                    expected={"validator": validator_instance.validator_type},
                )
            raise

    def _validate_custom(self):
        """Hook for custom validation logic in subclasses."""
        pass


class ValidationException(Exception):
    message: str
    field_name: str
    received: dict
    expected: dict

    def __init__(
        self,
        message: str,
        field_name: str,
        received: dict,
        expected: dict,
    ):
        self.message = message
        self.field_name = field_name
        self.received = received
        self.expected = expected
        super().__init__(self.format_error())

    def format_error(self) -> str:
        """Formats the validation error in a Rust-style with visual indicators."""
        error_lines = []

        # Header with error type and field
        error_lines.append(
            f"\033[1;31merror[E0001]\033[0m: validation failed for field '{self.field_name}'"
        )
        error_lines.append(f"  --> schema::{self.field_name}")
        error_lines.append(f"   |")

        # Add the error message
        error_lines.append(f"   | {self.message}")
        error_lines.append(f"   |")

        # Format the received value (flattened object)
        received_str = str(self.received)
        error_lines.append(f"   | received: {received_str}")

        # Use field_name directly as the problem key
        problem_key = self.field_name

        # Look for the problem key in the received object
        # Try to find exact match or nested path components
        highlight_pos = -1

        # First check for exact key match
        if f"'{problem_key}'" in received_str:
            highlight_pos = received_str.find(f"'{problem_key}'")
        # Otherwise check for potential nested fields (using parts of the field name)
        elif "." in problem_key:
            # For nested fields like 'user.age', try to find 'age'
            nested_key = problem_key.split(".")[-1]
            if f"'{nested_key}'" in received_str:
                highlight_pos = received_str.find(f"'{nested_key}'")

        # If we found the key in the received string, highlight it
        if highlight_pos >= 0:
            key_to_highlight = (
                problem_key
                if f"'{problem_key}'" in received_str
                else problem_key.split(".")[-1]
            )
            pad = " " * (len("   | received: ") + highlight_pos)
            error_lines.append(
                f"   |           {pad}{'^' * (len(str(key_to_highlight)) + 2)}"
            )

        # Show expected schema constraints
        schema_items = []
        for key, value in self.expected.items():
            schema_items.append(f"{key}: {value}")
        schema_str = "{" + ", ".join(schema_items) + "}"

        error_lines.append(f"   | expected schema: {schema_str}")
        error_lines.append(f"   |")

        # Add help suggestion if available
        if "suggestion" in self.expected:
            error_lines.append(
                f"   = \033[1;32mhelp\033[0m: {self.expected['suggestion']}"
            )
        else:
            # Generate a suggestion based on the field name
            error_lines.append(
                f"   = \033[1;32mhelp\033[0m: Check the '{problem_key}' value against the schema requirements"
            )

        return "\n".join(error_lines)

    def __str__(self) -> str:
        return self.format_error()


class CallableValue:
    """A wrapper for values that makes them callable."""

    def __init__(self, value, instance, field_name):
        self.value = value
        self.instance = instance
        self.field_name = field_name

    def __call__(self, *args, **kwargs):
        if not args and not kwargs:
            # Called with no arguments, just return the value
            return self.value

        # Called with arguments, try to update the value
        # Get the method from the class
        method = getattr(self.instance.__class__, self.field_name)
        if hasattr(method, "_is_validation_field") and method._is_validation_field:
            # Call the method with the new value
            result = method(self.instance, *args, **kwargs)
            # Update the cached value
            self.instance._cached_values[self.field_name] = result
            # Also update our value
            self.value = result
            return result

        # If it's not a validation field, just call the method
        return method(self.instance, *args, **kwargs)

    def __eq__(self, other):
        return self.value == other

    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return str(self.value)
