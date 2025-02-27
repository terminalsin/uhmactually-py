# UhmActually 🤓☝️

*Because sometimes you just need to validate your life choices... and your model attributes.*

## What's This All About?

Yo, ever been coding at 3 AM, chugging your fifth Red Bull, when suddenly your code blows up because someone passed in a string when you expected an integer? Yeah, we've all been there. That's why we made UhmActually - the validation library that's like having that annoying-but-right friend who's always correcting you.

```python
from uhmactually.core import ValidatedModel
from uhmactually.validators import min_value, max_value

class UserService(ValidatedModel):
    @min_value(21)  # ID must be at least 21
    @max_value(100)  # But not too high, we're not immortal yet
    def user_id(self) -> int:
        pass

# This works fine
user = UserService(user_id=25)
print(user.user_id())  # 25

# This blows up 💥
try:
    UserService(user_id=18)  # ValidationError: "Value 18 is less than the minimum value of 21"
except Exception as e:
    print(f"Validation failed: {e}")

# This also blows up 💥
try:
    UserService(user_id="twenty-five")  # ValidationError: "Expected a number for field 'user_id', got str"
except Exception as e:
    print(f"Validation failed: {e}")
```

## Installation

```bash
pip install uhmactually
```

Or if you're one of those poetry people:

```bash
poetry add uhmactually
```

## Why Should I Care? 🤷‍♂️

UhmActually is like spell-check for your model attributes. It's for when you're tired of writing:

```python
class MyModel:
    def __init__(self, value):
        if value is None:
            raise ValueError("Value cannot be None")
        if not isinstance(value, int):
            raise TypeError("Value must be an integer")
        if value < 0:
            raise ValueError("Value must be positive")
        if value > 100:
            raise ValueError("Value must be less than 100")
        self.value = value
        
    def get_value(self):
        return self.value
```

And instead want to write:

```python
from uhmactually.core import ValidatedModel
from uhmactually.validators import allow_none, is_type, min_value, max_value

class MyModel(ValidatedModel):
    @allow_none(False)
    @is_type(int)
    @min_value(0)
    @max_value(100)
    def value(self):
        pass
```

## Features That Slap 🔥

### Core Validators

```python
from uhmactually.core import ValidatedModel
from uhmactually.validators import allow_none, optional

class CoreValidators(ValidatedModel):
    # When None just won't cut it
    @allow_none(False)
    def must_have_value(self):
        pass

    # When it's cool to skip this one
    @optional(True)
    def can_skip_this(self):
        pass

# This works
model = CoreValidators(must_have_value="I exist!", can_skip_this=None)

# This fails
try:
    CoreValidators(must_have_value=None, can_skip_this="Optional but present")
except Exception as e:
    print(f"Validation failed: {e}")
```

### String Validators

```python
from uhmactually.core import ValidatedModel
from uhmactually.validators import contains, begins_with, pattern, min_length, max_length

class StringValidators(ValidatedModel):
    # For when you need that special something in your string
    @contains("pizza")
    def food_preference(self):
        pass

    # Make sure it starts right
    @begins_with("https://")
    def secure_url(self):
        pass

    # Regex for the win
    @pattern(r"^\d{3}-\d{2}-\d{4}$")
    def ssn(self):
        pass

    # Size matters
    @min_length(8)
    @max_length(64)
    def password(self):
        pass

# This works
model = StringValidators(
    food_preference="I love pizza with extra cheese",
    secure_url="https://example.com",
    ssn="123-45-6789",
    password="secureP@ssw0rd"
)

# This fails
try:
    StringValidators(
        food_preference="I hate vegetables",  # No pizza here!
        secure_url="http://example.com",      # Not https
        ssn="invalid-format",                 # Wrong format
        password="short"                      # Too short
    )
except Exception as e:
    print(f"Validation failed: {e}")
```

### Number Validators

```python
from uhmactually.core import ValidatedModel
from uhmactually.validators import min_value, max_value, in_range

class NumberValidators(ValidatedModel):
    # Keep it positive, bro
    @min_value(0)
    def square_root_input(self):
        pass

    # Don't go overboard
    @max_value(100)
    def percentage(self):
        pass

    # Stay in your lane
    @in_range(0, 1, min_inclusive=True, max_inclusive=True)
    def probability(self):
        pass

# This works
model = NumberValidators(square_root_input=16, percentage=75, probability=0.5)

# This fails
try:
    NumberValidators(square_root_input=-4, percentage=110, probability=1.5)
except Exception as e:
    print(f"Validation failed: {e}")
```

### Enum Validators

```python
from enum import Enum
from uhmactually.core import ValidatedModel
from uhmactually.validators import one_of, not_in, is_enum

class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

class EnumValidators(ValidatedModel):
    # Limited options only
    @one_of(["small", "medium", "large"])
    def coffee_size(self):
        pass

    # Some things are just forbidden
    @not_in(["password", "123456", "qwerty"])
    def user_password(self):
        pass

    # Enum validation
    @is_enum(Color)
    def favorite_color(self):
        pass

# This works
model = EnumValidators(
    coffee_size="medium",
    user_password="secure_p@ssw0rd!",
    favorite_color="blue"
)

# This fails
try:
    EnumValidators(
        coffee_size="extra-large",  # Not in allowed values
        user_password="password",   # In forbidden values
        favorite_color="purple"     # Not a valid enum value
    )
except Exception as e:
    print(f"Validation failed: {e}")
```

## Models That Validate Themselves

UhmActually is built around the `ValidatedModel` class that handles validation automatically:

```python
from uhmactually.core import ValidatedModel
from uhmactually.validators import min_length, pattern, min_value, max_value

class User(ValidatedModel):
    @min_length(3)
    def username(self) -> str:
        pass
        
    @pattern(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    def email(self) -> str:
        pass
        
    @min_value(13)
    @max_value(120)
    def age(self) -> int:
        pass

# This works
user = User(username="coolkid98", email="cool@example.com", age=21)

# This fails
try:
    User(username="me", email="not-an-email", age=9)
except Exception as e:
    print(f"Validation failed: {e}")
```

## When to Use This?

- When you're tired of writing the same validation code over and over
- When you want your validation logic separate from your business logic
- When you want to sound smart by saying "UhmActually 🤓☝️" before correcting someone's input
- When you need to validate model attributes with clear, declarative code

## When Not to Use This?

- When you need to validate regular function parameters (this library is for model attributes)
- When you enjoy writing validation code (weird flex, but okay)
- When you prefer runtime surprises (living on the edge, I see)
- When you're building something where incorrect inputs should cause nuclear meltdowns

## Contributing

Found a bug? Want to add a feature? Have a brilliant idea? Submit a PR! We're cool with that.

## License

MIT - Because sharing is caring, and we care about your validation needs.

---

Made with ❤️ and too much caffeine by students who were tired of debugging validation errors at 3 AM.

Remember: UhmActually 🤓☝️ - Because sometimes, being technically correct is the best kind of correct.
