from typing import Any, Dict, List
from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, jsonschema as jsonschema_ref


class SchemaValidationError(Exception):
    fields: Dict[str, List[str]] = {}

    def __init__(self, *args: object, fields: Dict[str, List[str]]):
        self.fields = fields
        super(*args)


def validate_against_schema(payload: Any, validator: Draft202012Validator):
    fields: Dict[str, List[str]] = {}
    error: ValidationError
    for error in validator.iter_errors(payload):
        fields[error.json_path] = fields.get(error.json_path, [])
        fields[error.json_path].append(error.message)

    if fields:
        error_message = (
            "The provided payload is not compliant with the provided schema!"
        )
        raise SchemaValidationError(error_message, fields=fields)


def validate_json_schema(json_schema: Dict[str, Any]):
    """
    Validates a json_schema, against the JSON Meta Schema Draft 2020-12.
    Raises a SchemaValidationError if invalid.
    """
    json_schema_validator = Draft202012Validator(
        {
            "$ref": "https://json-schema.org/draft/2020-12/schema",
        }
    )
    try:
        validate_against_schema(json_schema, json_schema_validator)
    except SchemaValidationError as e:
        schema_name = json_schema.get("title", json_schema.get("$id"))
        error_message = (
            f"Schema {schema_name} is not compliant with JSON Schema Draft 2020-12!"
        )
        raise SchemaValidationError(error_message, fields=e.fields)


def validate_payload(payload: Any, json_schema: Dict[str, Any]):
    """
    Validates a payload, against the provided JSON Schema.
    Raises a SchemaValidationError if invalid.
    """
    schema_id = json_schema.get("$id", "temp-schema")
    registry = Registry().with_resources(
        [
            (
                f"urn:{schema_id}",
                jsonschema_ref.DRAFT202012.create_resource(json_schema),
            )
        ]
    )
    validator = Draft202012Validator(
        {
            "$ref": f"urn:{schema_id}",
        },
        registry=registry,
    )
    validate_against_schema(payload, validator)
