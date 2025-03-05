from uhmactually.validator import ValidatedModel, validate
from uhmactually.core.validator_number import min


class TestModel(ValidatedModel):
    @validate
    @min(10)
    def value(self, value: int) -> int:
        return value


# Create a model with a valid value
model = TestModel(value=15)

# Print the model's attributes
print(f"Model attributes: {dir(model)}")
print(f"Model fields: {model._fields}")
print(f"Model cached values: {model._cached_values}")

# Test accessing the value as an attribute
print(f"model.value type: {type(model.value)}")
print(f"model.value: {model.value}")

# Try to call the value method
try:
    result = model.value()
    print(f"model.value(): {result}")
except Exception as e:
    print(f"Error calling model.value(): {e}")

# Try to set a new value
try:
    result = model.value(20)
    print(f"model.value(20): {result}")
    print(f"model.value after: {model.value}")
except Exception as e:
    print(f"Error calling model.value(20): {e}")
