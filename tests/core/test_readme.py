import pytest
from uhmactually.validator import ValidatedModel, validate, ValidationException
from uhmactually.core.validator_number import min
from uhmactually.core.validator_none import allow_none


class User(ValidatedModel):
    @validate
    @min(13)
    def age(self, value: int) -> int:
        return value

    @validate
    @allow_none  # null is cool here, but you shouldn't be called Shanyu. That's my name.
    def nickname(self, value: str) -> str:
        if value == "Shanyu":
            raise ValueError("You can't be called Shanyu")
        return value


class TestReadme:
    def test_readme(self):
        user = User(age=18, nickname=None)
        assert user.age() == 18
        assert user.nickname() is None

    def test_readme_fail(self):
        with pytest.raises(ValidationException):
            user = User(age=13, nickname="Shanyu")
            user.nickname()
