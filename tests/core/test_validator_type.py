import pytest
from uhmactually.validator import ValidatedModel, validate
from uhmactually.validator import ValidationException
from uhmactually.core.validator_type import typed


class TestTypeValidator:
    class TestModel(ValidatedModel):
        @validate
        @typed(int)  # explicit default
        def value(self, value) -> int:
            return value

        @validate  # implicit default
        def value_custom(self, value) -> int:
            if value == 15:
                raise ValueError("Value not be 15")
            return value

        @validate  # no type
        def value_no_type(self, value):
            return value

    def test_type_validator_success(self):
        model = self.TestModel(value=1, value_custom=1, value_no_type=1)
        assert model.value() == 1
        assert model.value_custom() == 1
        assert model.value_no_type() == 1

    def test_type_validator_failure(self):
        with pytest.raises(ValidationException):
            model = self.TestModel(value="1", value_custom=1, value_no_type="1")
            model.value()
            model.value_custom()
            model.value_no_type()

    def test_type_validator_failure_custom(self):
        with pytest.raises(ValidationException):
            model = self.TestModel(value=15, value_custom="15", value_no_type="15")
            model.value_custom()
            model.value_no_type()
