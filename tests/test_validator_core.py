import pytest
from typing import Optional

from uhmactually.core import (
    ValidationError,
    ValidatedModel,
    validate,
)
from uhmactually.validators import (
    optional_check,
)


# Test Models
class CoreValidatorModel(ValidatedModel):
    """A model with core validators."""

    @validate
    def required_field(self, value=None) -> str:
        if value is None:
            raise ValidationError(
                "None value is not allowed for field 'required_field'", None, value
            )
        return value

    @validate
    def nullable_field(self, value=None) -> str:
        # This field allows None values
        return value

    @validate
    def mandatory_field(self, value=None) -> str:
        if value is None:
            raise ValidationError(
                "Field 'mandatory_field' is required and cannot be None", None, value
            )
        return value

    @validate
    def optional_field(self, value=None) -> str:
        # This field is optional
        if value is None:
            optional_check(value)
        return value


class CombinedValidatorModel(ValidatedModel):
    """A model with combined core validators."""

    @validate
    def nullable_mandatory(self, value=None) -> Optional[str]:
        # This field is mandatory but can be None
        return value

    @validate
    def non_nullable_optional(self, value=None) -> str:
        # This field is optional but cannot be None
        if value is None:
            raise ValidationError("None value is not allowed", None, value)
        return value

    @validate
    def nullable_optional(self, value=None) -> Optional[str]:
        # This field is optional and can be None
        return value

    @validate
    def non_nullable_mandatory(self, value=None) -> str:
        # This field is mandatory and cannot be None
        if value is None:
            raise ValidationError("Field is required and cannot be None", None, value)
        return value


# Parametrized Tests for AllowNoneValidator
@pytest.mark.parametrize(
    "required_field,nullable_field,should_pass",
    [
        # Valid cases
        ("value", "value", True),
        ("value", None, True),
        # Invalid cases
        (None, "value", False),
        (None, None, False),
    ],
)
def test_allow_none_validator(required_field, nullable_field, should_pass):
    """Test AllowNoneValidator with various inputs."""
    if should_pass:
        model = CoreValidatorModel(
            required_field=required_field,
            nullable_field=nullable_field,
            mandatory_field="value",
            optional_field="value",
        )
        assert model.required_field() == required_field
        assert model.nullable_field() == nullable_field
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            CoreValidatorModel(
                required_field=required_field,
                nullable_field=nullable_field,
                mandatory_field="value",
                optional_field="value",
            )
        assert "None value is not allowed" in str(excinfo.value)


# Parametrized Tests for OptionalValidator
@pytest.mark.parametrize(
    "mandatory_field,optional_field,should_pass",
    [
        # Valid cases
        ("value", "value", True),
        ("value", None, True),
        # Invalid cases
        (None, "value", False),
        (None, None, False),
    ],
)
def test_optional_validator(mandatory_field, optional_field, should_pass):
    """Test OptionalValidator with various inputs."""
    if should_pass:
        model = CoreValidatorModel(
            required_field="value",
            nullable_field="value",
            mandatory_field=mandatory_field,
            optional_field=optional_field,
        )
        assert model.mandatory_field() == mandatory_field
        assert model.optional_field() == optional_field
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            CoreValidatorModel(
                required_field="value",
                nullable_field="value",
                mandatory_field=mandatory_field,
                optional_field=optional_field,
            )
        assert "is required and cannot be None" in str(excinfo.value)


# Parametrized Tests for Combined Validators
@pytest.mark.skip(reason="Not correct test")
@pytest.mark.parametrize(
    "nullable_mandatory,non_nullable_optional,nullable_optional,non_nullable_mandatory,should_pass,expected_error",
    [
        # All valid
        ("value", "value", "value", "value", True, None),
        # Valid combinations
        (None, "value", "value", "value", True, None),
        ("value", None, "value", "value", True, None),
        ("value", "value", None, "value", True, None),
        (None, None, None, "value", True, None),
        # Invalid combinations
        ("value", "value", "value", None, False, "non_nullable_mandatory"),
        (None, None, None, None, False, "non_nullable_mandatory"),
    ],
)
def test_combined_validators(
    nullable_mandatory,
    non_nullable_optional,
    nullable_optional,
    non_nullable_mandatory,
    should_pass,
    expected_error,
):
    """Test combined core validators with various inputs."""
    if should_pass:
        model = CombinedValidatorModel(
            nullable_mandatory=nullable_mandatory,
            non_nullable_optional=non_nullable_optional,
            nullable_optional=nullable_optional,
            non_nullable_mandatory=non_nullable_mandatory,
        )
        assert model.nullable_mandatory() == nullable_mandatory
        assert model.non_nullable_optional() == non_nullable_optional
        assert model.nullable_optional() == nullable_optional
        assert model.non_nullable_mandatory() == non_nullable_mandatory
        assert model.validate().is_valid
    else:
        with pytest.raises(ValidationError) as excinfo:
            CombinedValidatorModel(
                nullable_mandatory=nullable_mandatory,
                non_nullable_optional=non_nullable_optional,
                nullable_optional=nullable_optional,
                non_nullable_mandatory=non_nullable_mandatory,
            )
        if expected_error:
            assert expected_error in str(excinfo.value)


# Test error messages
def test_allow_none_error_message():
    """Test that AllowNoneValidator produces the expected error message."""
    with pytest.raises(ValidationError) as excinfo:
        CoreValidatorModel(
            required_field=None,
            nullable_field="value",
            mandatory_field="value",
            optional_field="value",
        )
    error_message = str(excinfo.value)
    assert "None value is not allowed for field 'required_field'" in error_message


def test_optional_error_message():
    """Test that OptionalValidator produces the expected error message."""
    with pytest.raises(ValidationError) as excinfo:
        CoreValidatorModel(
            required_field="value",
            nullable_field="value",
            mandatory_field=None,
            optional_field="value",
        )
    error_message = str(excinfo.value)
    assert "Field 'mandatory_field' is required and cannot be None" in error_message


# Test validation results
def test_validation_results():
    """Test that validation results contain the expected errors."""
    # Create a model with invalid values
    model = CoreValidatorModel(
        required_field="value",
        nullable_field="value",
        mandatory_field="value",
        optional_field="value",
    )

    # Manually set invalid values to bypass initialization validation
    model._data["required_field"] = None
    model._data["mandatory_field"] = None

    # Validate the model
    result = model.validate()

    # Check that validation failed
    assert not result.is_valid

    # Check that the expected errors are present
    errors = result.errors
    assert len(errors) == 2

    # Check error fields
    error_fields = [error.field for error in errors]
    assert "required_field" in error_fields
    assert "mandatory_field" in error_fields
