# UhmActually 🤓

*may as well just use java at this point*

## :book: Problem Statement

At my job, we needed a validation library capable of:
- Strict validation by schema
- Allow custom validation per field
- Maximize readability
- Able to dump objects and types easily

## 🔥 Quick Start

```python
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
    # this will work fine!
    def test_readme(self):
        user = User(age=18, nickname=None)
        assert user.age() == 18
        assert user.nickname() is None

    # you can't be called Shanyu, will throw a validation error
    def test_readme_fail(self):
        with pytest.raises(ValidationException):
            user = User(age=13, nickname="Shanyu")
            user.nickname()
```

## 🚀 Installation

```bash
pip install uhmactually
```
