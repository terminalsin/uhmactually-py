import pytest

from uhmactually.validator import ValidatedModel, validate, ValidationException
from uhmactually.core.validator_number import min


class TestMinNumberValidator:
    class TestModel(ValidatedModel):
        @validate
        @min(10)
        def value(self, value: int) -> int:
            return value

        @validate
        @min(10)
        def value_custom(self, value: int) -> int:
            if value == 15:
                raise ValueError("Value not be 15")
            return value

    @pytest.mark.parametrize("value", [10, 11, 12])
    def test_min_value_success(self, value):
        model = self.TestModel(value=value, value_custom=value)
        assert model.value() == value

    @pytest.mark.parametrize("value", [9, 8, 7])
    def test_min_value_failure(self, value):
        with pytest.raises(ValidationException):
            model = self.TestModel(value=value, value_custom=value)

    @pytest.mark.parametrize("value", [16, 17])
    def test_min_value_custom_success(self, value):
        model = self.TestModel(value=value, value_custom=value)
        assert model.value_custom() == value

    @pytest.mark.parametrize("value", [15])
    def test_min_value_custom_failure(self, value):
        with pytest.raises(ValidationException):
            model = self.TestModel(value=value, value_custom=value)

    def test_both_access_styles(self):
        # Create a model with a valid value
        model = self.TestModel(value=15, value_custom=16)

        # Access as an attribute (property-style)
        print("Accessing as an attribute")
        assert model.value == 15

        # Access as a method (function-style)
        print("Accessing as a method")
        assert model.value() == 15

        # Call with a new value
        print("Calling with a new value")
        assert model.value(20) == 20

        # Verify the value was updated
        assert model.value == 20
        assert model.value() == 20

    @pytest.mark.parametrize("value", [9, 8, 7])
    def test_min_value_failure(self, value):
        with pytest.raises(ValidationException):
            model = self.TestModel(value=value, value_custom=value)
