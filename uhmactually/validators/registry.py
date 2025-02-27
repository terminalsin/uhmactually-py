from functools import wraps
from typing import Union
import inspect

# Registry of all validators
VALIDATORS = {}


def validator(cls):
    """
    Decorator for validator classes.

    This decorator registers the validator class in the VALIDATORS registry
    and adds a create_decorator method to the class for creating field decorators.
    """
    # Register the validator in the registry
    VALIDATORS[cls.__name__] = cls

    # Add create_decorator method to the class
    def create_decorator(cls, *args, **kwargs):
        """
        Create a decorator for validating fields with this validator.

        Args:
            *args: Positional arguments to pass to the validator constructor.
            **kwargs: Keyword arguments to pass to the validator constructor.

        Returns:
            A decorator function that can be applied to model fields.
        """

        def decorator(func):
            # Store the validator class and arguments for later use
            func._validator_class = cls
            func._validator_args = args
            func._validator_kwargs = kwargs
            func._requires_validation = True

            # Check if this is an optional field
            if args and hasattr(args[0], "__origin__") and args[0].__origin__ is Union:
                if type(None) in args[0].__args__:
                    func._is_optional = True
                    func._allows_none = True

            @wraps(func)
            def wrapper(self, value=None):
                # If a value is provided, this is a validation call
                if value is not None:
                    # Call the original function which may contain custom validation
                    if (
                        func.__code__.co_code != b"d\x01S\x00"
                    ):  # Check if function body is not just 'pass'
                        # Check if the function accepts a value parameter
                        sig = inspect.signature(func)
                        param_count = len(sig.parameters)

                        # If the function only has 'self' parameter, don't pass value
                        if param_count == 1:
                            result = func(self)
                        else:
                            result = func(self, value)

                        # If the function returns a value, use that instead
                        if result is not None:
                            return result

                    return value

                # If no value is provided, this is a getter call
                # Return the value from the data dictionary if it exists
                if hasattr(self, "_data") and func.__name__ in self._data:
                    return self._data[func.__name__]

                # If the attribute doesn't exist, call the method
                return func(self)

            return wrapper

        return decorator

    # Add the create_decorator method to the class
    cls.create_decorator = classmethod(create_decorator)

    return cls
