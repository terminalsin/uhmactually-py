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

_validator_registry: Dict[str, Dict[str, Any]] = {}


def validator(validator_class=None, *, accept_none=False):
    """
    Decorator to register a Validator class in the global registry.
    Can be used as @validator or @validator(accept_none=True)
    """

    def decorator(cls):
        if not issubclass(cls, Validator):
            raise TypeError(
                f"@validator can only be applied to Validator subclasses, got {cls.__name__}"
            )

        _validator_registry[cls.registered_name()] = {
            "validator": cls,
            "accept_none": accept_none,
        }
        return cls

    # Direct decoration: @validator
    if validator_class is not None:
        return decorator(validator_class)

    # Parameterized decoration: @validator(accept_none=True)
    return decorator


def validate(field_func: Callable) -> Callable:
    """Marks a method as a validated field in ValidatedModel subclasses."""

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
                field_name = self.func.__name__

                if not args:
                    if field_name in obj._cached_values:
                        return obj._cached_values[field_name]
                    return self.func(obj, None)

                result = self.func(obj, *args, **kwargs)
                obj._cached_values[field_name] = result
                return result

            bound_method._validators = self._validators
            bound_method._is_validation_field = True

            return bound_method

        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)

    return ValidationMethodWrapper(field_func)


class ValidationInput:
    """Container for data being validated with its metadata."""

    def __init__(
        self, value: Any, field_name: str, definition: Callable, model_instance=None
    ):
        self.value = value
        self.field_name = field_name
        self.definition = definition
        self.model_instance = model_instance

    def get_type(self) -> Optional[Type]:
        """Extracts type annotation from the field definition."""
        if not hasattr(self.definition, "__annotations__"):
            return None

        return self.definition.__annotations__.get("return")

    def create_context(self) -> dict:
        """Creates a context dictionary with all relevant validation information."""
        return {
            "value": self.value,
            "field_name": self.field_name,
            "model_instance": self.model_instance,
        }


class ValidationResult:
    """Result of a validation operation with status, message, and transformed value."""

    def __init__(
        self,
        is_valid: bool,
        message: str = None,
        value: Any = None,
        context: dict = None,
    ):
        self.is_valid = is_valid
        self.message = message
        self.value = value
        self.context = context or {}


class Validator(ABC):
    """Abstract base class for all validators."""

    def __init__(self):
        self.validator_type = self.__class__.__name__.lower().replace("validator", "")

    @abstractmethod
    def validate(self, input: ValidationInput, **kwargs) -> ValidationResult:
        """Validates input against rules, returning success/failure with optional transformation."""
        pass

    def default(self, input: ValidationInput) -> ValidationResult:
        """Default validation logic applied when not explicitly called."""
        return self.success()

    @classmethod
    def registered_name(cls) -> str:
        """Returns validator name for registry lookup."""
        return cls.__name__.lower().replace("validator", "")

    def generate_decorator(self, **kwargs) -> Callable:
        """Creates a decorator that applies this validator to model fields."""
        decorator_kwargs = kwargs
        validator_instance = self

        def decorator(func):
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

                    bound_method._validators = self._validators
                    bound_method._is_validation_field = True
                    return bound_method

                def __call__(self, *args, **kwargs):
                    return self.func(*args, **kwargs)

            return MethodWrapper(func)

        return decorator

    def fail(self, message: str, additional_context=None) -> ValidationResult:
        """Creates a failed validation result with given message."""
        context = {} if additional_context is None else additional_context
        return ValidationResult(is_valid=False, message=message, context=context)

    def success(self, value: Any = None, context=None) -> ValidationResult:
        """Creates a successful validation result with optional transformed value."""
        return ValidationResult(is_valid=True, value=value, context=context or {})


class ValidatedModel(ABC):
    """Base class for models with field validation."""

    def __init__(self, **kwargs):
        self._fields = {}
        self._cached_values = {}
        self._wrapped_values = {}

        for key, value in kwargs.items():
            self._fields[key] = value

        self.validate()

    def __getattribute__(self, name):
        if name.startswith("_") or name == "validate":
            return super().__getattribute__(name)

        try:
            wrapped_values = super().__getattribute__("_wrapped_values")
            if name in wrapped_values:
                return wrapped_values[name]
        except (AttributeError, KeyError):
            pass

        try:
            cached_values = super().__getattribute__("_cached_values")
            if name in cached_values:
                value = cached_values[name]
                wrapper = CallableValue(value, self, name)
                wrapped_values = super().__getattribute__("_wrapped_values")
                wrapped_values[name] = wrapper
                return wrapper
        except (AttributeError, KeyError):
            pass

        return super().__getattribute__(name)

    def validate(self):
        """Validates all fields in the model and raises ValidationException on failure."""
        validation_fields = self._get_validation_fields()

        for field_name, field_method in validation_fields.items():
            if field_name not in self._fields and not hasattr(self, field_name):
                continue

            field_value = self._fields.get(field_name)
            self._validate_field(field_name, field_method, field_value)

        self._validate_custom()

    def _get_validation_fields(self):
        """Finds all methods marked with @validate."""
        validation_fields = {}
        for name, method in inspect.getmembers(self.__class__):
            if hasattr(method, "_is_validation_field") and method._is_validation_field:
                validation_fields[name] = method
        return validation_fields

    def _validate_field(self, field_name, field_method, field_value):
        """Validates a single field using its method and attached validators."""
        sig = inspect.signature(field_method)
        param_count = len(sig.parameters)

        try:
            if param_count == 1:  # Just self
                result = field_method(self)
            elif param_count == 2:  # self and input
                result = field_method(self, field_value)
            else:
                raise ValueError(
                    f"Invalid parameter count for {field_name}: expected 0 or 1, got {param_count - 1}"
                )

            self._cached_values[field_name] = result
        except Exception as e:
            if not isinstance(e, ValidationException):
                expected_type = get_type_hints(field_method).get("return", Any)
                raise ValidationException(
                    message=str(e),
                    field_name=field_name,
                    received={"value": field_value},
                    expected={"type": str(expected_type)},
                )
            raise

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

        self._run_default_validators(
            field_name, field_method, field_value, explicit_validators
        )

    def _run_default_validators(
        self, field_name, field_method, field_value, explicit_validators
    ):
        """Runs default validators that aren't explicitly attached to the field."""
        for validator_type, validator_config in _validator_registry.items():
            validator_class = validator_config["validator"]
            accept_none = validator_config["accept_none"]

            validator_already_used = any(
                isinstance(v, dict)
                and v["validator"].validator_type == validator_type
                or hasattr(v, "validator_type")
                and v.validator_type == validator_type
                for v in explicit_validators
            )

            if validator_already_used:
                continue

            if field_value is None and not accept_none:
                continue

            validator_instance = validator_class()
            validation_input = ValidationInput(
                value=field_value,
                field_name=field_name,
                definition=field_method,
                model_instance=self,
            )

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

    def _run_validator(
        self,
        validator_instance,
        field_name,
        field_method,
        field_value,
        **validator_kwargs,
    ):
        """Runs a validator against a field."""
        validation_input = ValidationInput(
            value=field_value,
            field_name=field_name,
            definition=field_method,
            model_instance=self,
        )

        try:
            result = validator_instance.validate(validation_input, **validator_kwargs)

            if not result.is_valid:
                raise ValidationException(
                    message=result.message or f"Validation failed for {field_name}",
                    field_name=field_name,
                    received={"value": field_value},
                    expected={"validator": validator_instance.validator_type},
                )
            elif result.value is not None:
                setattr(self, field_name, result.value)
        except Exception as e:
            if not isinstance(e, ValidationException):
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
    """Exception raised when validation fails."""

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
        error_lines.append(
            f"\033[1;31merror[E0001]\033[0m: validation failed for field '{self.field_name}'"
        )
        error_lines.append(f"  --> schema::{self.field_name}")
        error_lines.append(f"   |")
        error_lines.append(f"   | {self.message}")
        error_lines.append(f"   |")

        received_str = str(self.received)
        error_lines.append(f"   | received: {received_str}")

        problem_key = self.field_name
        highlight_pos = self._find_highlight_position(received_str, problem_key)

        if highlight_pos >= 0:
            key_to_highlight = self._get_key_to_highlight(received_str, problem_key)
            pad = " " * (len("   | received: ") + highlight_pos)
            error_lines.append(
                f"   |           {pad}{'^' * (len(str(key_to_highlight)) + 2)}"
            )

        schema_items = []
        for key, value in self.expected.items():
            schema_items.append(f"{key}: {value}")
        schema_str = "{" + ", ".join(schema_items) + "}"

        error_lines.append(f"   | expected schema: {schema_str}")
        error_lines.append(f"   |")

        help_message = self._generate_help_message(problem_key)
        error_lines.append(f"   = \033[1;32mhelp\033[0m: {help_message}")

        return "\n".join(error_lines)

    def _find_highlight_position(self, received_str, problem_key):
        """Finds the position to highlight in the received string."""
        highlight_pos = -1

        if f"'{problem_key}'" in received_str:
            highlight_pos = received_str.find(f"'{problem_key}'")
        elif "." in problem_key:
            nested_key = problem_key.split(".")[-1]
            if f"'{nested_key}'" in received_str:
                highlight_pos = received_str.find(f"'{nested_key}'")

        return highlight_pos

    def _get_key_to_highlight(self, received_str, problem_key):
        """Determines which key to highlight in the error message."""
        if f"'{problem_key}'" in received_str:
            return problem_key
        elif "." in problem_key:
            return problem_key.split(".")[-1]
        return problem_key

    def _generate_help_message(self, problem_key):
        """Generates a helpful message for fixing the validation error."""
        if "suggestion" in self.expected:
            return self.expected["suggestion"]
        return f"Check the '{problem_key}' value against the schema requirements"

    def __str__(self) -> str:
        return self.format_error()


class CallableValue:
    """Value wrapper that enables getter/setter behavior while preserving comparison operations."""

    def __init__(self, value, instance, field_name):
        self.value = value
        self.instance = instance
        self.field_name = field_name

    def __call__(self, *args, **kwargs):
        if not args and not kwargs:
            return self.value

        method = getattr(self.instance.__class__, self.field_name)

        if hasattr(method, "_is_validation_field") and method._is_validation_field:
            result = method(self.instance, *args, **kwargs)
            self.instance._cached_values[self.field_name] = result
            self.value = result
            return result

        return method(self.instance, *args, **kwargs)

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return self.value != other

    def __lt__(self, other):
        return self.value < other

    def __le__(self, other):
        return self.value <= other

    def __gt__(self, other):
        return self.value > other

    def __ge__(self, other):
        return self.value >= other

    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return str(self.value)

    def __bool__(self):
        return bool(self.value)

    def __hash__(self):
        return hash(self.value)
