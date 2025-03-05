import pytest

from uhmactually.validator import ValidatedModel, validate, ValidationException
from uhmactually.core.validator_none import allow_none


class TestAllowNoneValidator:
    class TestModel(ValidatedModel):
        @validate
        @allow_none
        def value(self, value: int) -> int:
            return value

        @validate
        def cannot_none(self, value: int) -> int:
            return value

    def test_allow_none_success(self):
        model = self.TestModel(value=None, cannot_none=1)
        assert model.value() is None

    def test_allow_none_failure(self):
        with pytest.raises(ValidationException):
            model = self.TestModel(value=1, cannot_none=None)
