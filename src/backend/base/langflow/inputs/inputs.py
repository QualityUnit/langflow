import warnings
from typing import Any, AsyncIterator, Iterator, Optional, Union, get_args

from pydantic import Field, field_validator

from langflow.inputs.validators import CoalesceBool
from langflow.schema.data import Data
from langflow.schema.message import Message
from langflow.template.field.base import Input

from .input_mixin import (
    BaseInputMixin,
    DatabaseLoadMixin,
    DropDownMixin,
    FieldTypes,
    FileMixin,
    InputTraceMixin,
    ListableInputMixin,
    MetadataTraceMixin,
    MultilineMixin,
    RangeMixin,
    SerializableFieldTypes,
    TableMixin,
)


class TableInput(BaseInputMixin, MetadataTraceMixin, TableMixin, ListableInputMixin):
    field_type: SerializableFieldTypes = FieldTypes.TABLE
    is_list: bool = True

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Any, _info):
        # Check if value is a list of dicts
        if not isinstance(v, list):
            raise ValueError(f"TableInput value must be a list of dictionaries or Data. Value '{v}' is not a list.")

        for item in v:
            if not isinstance(item, (dict, Data)):
                raise ValueError(
                    f"TableInput value must be a list of dictionaries or Data. Item '{item}' is not a dictionary or Data."
                )
        return v


class HandleInput(BaseInputMixin, ListableInputMixin, MetadataTraceMixin):
    """
    Represents an Input that has a Handle to a specific type (e.g. BaseLanguageModel, BaseRetriever, etc.)

    This class inherits from the `BaseInputMixin` and `ListableInputMixin` classes.

    Attributes:
        input_types (list[str]): A list of input types.
        field_type (SerializableFieldTypes): The field type of the input.
    """

    input_types: list[str] = Field(default_factory=list)
    field_type: SerializableFieldTypes = FieldTypes.OTHER


class DataInput(HandleInput, InputTraceMixin, ListableInputMixin):
    """
    Represents an Input that has a Handle that receives a Data object.

    Attributes:
        input_types (list[str]): A list of input types supported by this data input.
    """

    input_types: list[str] = ["Data"]


class PromptInput(BaseInputMixin, ListableInputMixin, InputTraceMixin):
    field_type: SerializableFieldTypes = FieldTypes.PROMPT


# Applying mixins to a specific input type
class StrInput(BaseInputMixin, ListableInputMixin, DatabaseLoadMixin, MetadataTraceMixin):
    field_type: SerializableFieldTypes = FieldTypes.TEXT
    load_from_db: CoalesceBool = False
    """Defines if the field will allow the user to open a text editor. Default is False."""

    @staticmethod
    def _validate_value(v: Any, _info):
        """
        Validates the given value and returns the processed value.

        Args:
            v (Any): The value to be validated.
            _info: Additional information about the input.

        Returns:
            The processed value.

        Raises:
            ValueError: If the value is not of a valid type or if the input is missing a required key.
        """
        if not isinstance(v, str) and v is not None:
            # Keep the warning for now, but we should change it to an error
            if _info.data.get("input_types") and v.__class__.__name__ not in _info.data.get("input_types"):
                warnings.warn(
                    f"Invalid value type {type(v)} for input {_info.data.get('name')}. Expected types: {_info.data.get('input_types')}"
                )
            else:
                warnings.warn(f"Invalid value type {type(v)} for input {_info.data.get('name')}.")
        return v

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Any, _info):
        """
        Validates the given value and returns the processed value.

        Args:
            v (Any): The value to be validated.
            _info: Additional information about the input.

        Returns:
            The processed value.

        Raises:
            ValueError: If the value is not of a valid type or if the input is missing a required key.
        """
        is_list = _info.data["is_list"]
        value = None
        if is_list:
            value = [cls._validate_value(vv, _info) for vv in v]
        else:
            value = cls._validate_value(v, _info)
        return value


class MessageInput(StrInput, InputTraceMixin):
    input_types: list[str] = ["Message"]

    @staticmethod
    def _validate_value(v: Any, _info):
        # If v is a instance of Message, then its fine
        if isinstance(v, dict):
            return Message(**v)
        if isinstance(v, Message):
            return v
        if isinstance(v, str):
            return Message(text=v)
        elif isinstance(v, list) and all(isinstance(i, Message) or isinstance(i, str) for i in v):
            return v
        raise ValueError(f"Invalid value type {type(v)}")


class MessageTextInput(StrInput, MetadataTraceMixin, InputTraceMixin):
    """
    Represents a text input component for the Langflow system.

    This component is used to handle text inputs in the Langflow system. It provides methods for validating and processing text values.

    Attributes:
        input_types (list[str]): A list of input types that this component supports. In this case, it supports the "Message" input type.
    """

    input_types: list[str] = ["Message"]

    @staticmethod
    def _validate_value(v: Any, _info):
        """
        Validates the given value and returns the processed value.

        Args:
            v (Any): The value to be validated.
            _info: Additional information about the input.

        Returns:
            The processed value.

        Raises:
            ValueError: If the value is not of a valid type or if the input is missing a required key.
        """
        value: str | AsyncIterator | Iterator | None = None
        if isinstance(v, dict):
            v = Message(**v)
        if isinstance(v, str):
            value = v
        elif isinstance(v, Message):
            value = v.text
        elif isinstance(v, Data):
            if v.text_key in v.data:
                value = v.data[v.text_key]
            else:
                keys = ", ".join(v.data.keys())
                input_name = _info.data["name"]
                raise ValueError(
                    f"The input to '{input_name}' must contain the key '{v.text_key}'."
                    f"You can set `text_key` to one of the following keys: {keys} or set the value using another Component."
                )
        elif isinstance(v, (AsyncIterator, Iterator)):
            value = v
        elif isinstance(v, list) and all(isinstance(i, Message) or isinstance(i, str) for i in v):
            value = v
        else:
            raise ValueError(f"Invalid value type {type(v)}")
        return value


class MultilineInput(MessageTextInput, MultilineMixin, InputTraceMixin):
    """
    Represents a multiline input field.

    Attributes:
        field_type (SerializableFieldTypes): The type of the field. Defaults to FieldTypes.TEXT.
        multiline (CoalesceBool): Indicates whether the input field should support multiple lines. Defaults to True.
    """

    field_type: SerializableFieldTypes = FieldTypes.TEXT
    multiline: CoalesceBool = True


class MultilineSecretInput(MessageTextInput, MultilineMixin, InputTraceMixin):
    """
    Represents a multiline input field.

    Attributes:
        field_type (SerializableFieldTypes): The type of the field. Defaults to FieldTypes.TEXT.
        multiline (CoalesceBool): Indicates whether the input field should support multiple lines. Defaults to True.
    """

    field_type: SerializableFieldTypes = FieldTypes.PASSWORD
    multiline: CoalesceBool = True
    password: CoalesceBool = Field(default=True)


class SecretStrInput(BaseInputMixin, DatabaseLoadMixin):
    """
    Represents a field with password field type.

    This class inherits from `BaseInputMixin` and `DatabaseLoadMixin`.

    Attributes:
        field_type (SerializableFieldTypes): The field type of the input. Defaults to `FieldTypes.PASSWORD`.
        password (CoalesceBool): A boolean indicating whether the input is a password. Defaults to `True`.
        input_types (list[str]): A list of input types associated with this input. Defaults to an empty list.
    """

    field_type: SerializableFieldTypes = FieldTypes.PASSWORD
    password: CoalesceBool = Field(default=True)
    input_types: list[str] = ["Message"]
    load_from_db: CoalesceBool = True

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Any, _info):
        """
        Validates the given value and returns the processed value.

        Args:
            v (Any): The value to be validated.
            _info: Additional information about the input.

        Returns:
            The processed value.

        Raises:
            ValueError: If the value is not of a valid type or if the input is missing a required key.
        """
        value: str | AsyncIterator | Iterator | None = None
        if isinstance(v, str):
            value = v
        elif isinstance(v, Message):
            value = v.text
        elif isinstance(v, Data):
            if v.text_key in v.data:
                value = v.data[v.text_key]
            else:
                keys = ", ".join(v.data.keys())
                input_name = _info.data["name"]
                raise ValueError(
                    f"The input to '{input_name}' must contain the key '{v.text_key}'."
                    f"You can set `text_key` to one of the following keys: {keys} or set the value using another Component."
                )
        elif isinstance(v, (AsyncIterator, Iterator)):
            value = v
        else:
            raise ValueError(f"Invalid value type `{type(v)}` for input `{_info.data['name']}`")
        return value


class IntInput(BaseInputMixin, ListableInputMixin, RangeMixin, MetadataTraceMixin):
    """
    Represents an integer field.

    This class represents an integer input and provides functionality for handling integer values.
    It inherits from the `BaseInputMixin`, `ListableInputMixin`, and `RangeMixin` classes.

    Attributes:
        field_type (SerializableFieldTypes): The field type of the input. Defaults to FieldTypes.INTEGER.
    """

    field_type: SerializableFieldTypes = FieldTypes.INTEGER

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Any, _info):
        """
        Validates the given value and returns the processed value.

        Args:
            v (Any): The value to be validated.
            _info: Additional information about the input.

        Returns:
            The processed value.

        Raises:
            ValueError: If the value is not of a valid type or if the input is missing a required key.
        """

        if v and not isinstance(v, (int, float)):
            raise ValueError(f"Invalid value type {type(v)} for input {_info.data.get('name')}.")
        if isinstance(v, float):
            v = int(v)
        return v


class FloatInput(BaseInputMixin, ListableInputMixin, RangeMixin, MetadataTraceMixin):
    """
    Represents a float field.

    This class represents a float input and provides functionality for handling float values.
    It inherits from the `BaseInputMixin`, `ListableInputMixin`, and `RangeMixin` classes.

    Attributes:
        field_type (SerializableFieldTypes): The field type of the input. Defaults to FieldTypes.FLOAT.
    """

    field_type: SerializableFieldTypes = FieldTypes.FLOAT

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Any, _info):
        """
        Validates the given value and returns the processed value.

        Args:
            v (Any): The value to be validated.
            _info: Additional information about the input.

        Returns:
            The processed value.

        Raises:
            ValueError: If the value is not of a valid type or if the input is missing a required key.
        """
        if v and not isinstance(v, (int, float)):
            raise ValueError(f"Invalid value type {type(v)} for input {_info.data.get('name')}.")
        if isinstance(v, int):
            v = float(v)
        return v


class BoolInput(BaseInputMixin, ListableInputMixin, MetadataTraceMixin):
    """
    Represents a boolean field.

    This class represents a boolean input and provides functionality for handling boolean values.
    It inherits from the `BaseInputMixin` and `ListableInputMixin` classes.

    Attributes:
        field_type (SerializableFieldTypes): The field type of the input. Defaults to FieldTypes.BOOLEAN.
        value (CoalesceBool): The value of the boolean input.
    """

    field_type: SerializableFieldTypes = FieldTypes.BOOLEAN
    value: CoalesceBool = False


class NestedDictInput(BaseInputMixin, ListableInputMixin, MetadataTraceMixin, InputTraceMixin):
    """
    Represents a nested dictionary field.

    This class represents a nested dictionary input and provides functionality for handling dictionary values.
    It inherits from the `BaseInputMixin` and `ListableInputMixin` classes.

    Attributes:
        field_type (SerializableFieldTypes): The field type of the input. Defaults to FieldTypes.NESTED_DICT.
        value (Optional[dict]): The value of the input. Defaults to an empty dictionary.
    """

    field_type: SerializableFieldTypes = FieldTypes.NESTED_DICT
    show_secret: Optional[CoalesceBool] = True
    key_placeholder: Optional[str] = "Key"
    value_placeholder: Optional[str] = "Value"
    value: Optional[dict | Data] = {}


class DictInput(BaseInputMixin, ListableInputMixin, InputTraceMixin):
    """
    Represents a dictionary field.

    This class represents a dictionary input and provides functionality for handling dictionary values.
    It inherits from the `BaseInputMixin` and `ListableInputMixin` classes.

    Attributes:
        field_type (SerializableFieldTypes): The field type of the input. Defaults to FieldTypes.DICT.
        value (Optional[dict]): The value of the dictionary input. Defaults to an empty dictionary.
    """

    field_type: SerializableFieldTypes = FieldTypes.DICT
    value: Optional[dict] = {}


class DropdownInput(BaseInputMixin, DropDownMixin, MetadataTraceMixin):
    """
    Represents a dropdown input field.

    This class represents a dropdown input field and provides functionality for handling dropdown values.
    It inherits from the `BaseInputMixin` and `DropDownMixin` classes.

    Attributes:
        field_type (SerializableFieldTypes): The field type of the input. Defaults to FieldTypes.TEXT.
        options (Optional[Union[list[str], Callable]]): List of options for the field.
            Default is None.
    """

    field_type: SerializableFieldTypes = FieldTypes.TEXT
    options: list[str] = Field(default_factory=list)
    combobox: CoalesceBool = False


class MultiselectInput(BaseInputMixin, ListableInputMixin, DropDownMixin, MetadataTraceMixin):
    """
    Represents a multiselect input field.

    This class represents a multiselect input field and provides functionality for handling multiselect values.
    It inherits from the `BaseInputMixin`, `ListableInputMixin` and `DropDownMixin` classes.

    Attributes:
        field_type (SerializableFieldTypes): The field type of the input. Defaults to FieldTypes.TEXT.
        options (Optional[Union[list[str], Callable]]): List of options for the field. Only used when is_list=True.
            Default is None.
    """

    field_type: SerializableFieldTypes = FieldTypes.TEXT
    options: list[str] = Field(default_factory=list)
    is_list: bool = Field(default=True, serialization_alias="list")
    combobox: CoalesceBool = False

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Any, _info):
        # Check if value is a list of dicts
        if not isinstance(v, list):
            raise ValueError(f"MultiselectInput value must be a list. Value: '{v}'")
        for item in v:
            if not isinstance(item, str):
                raise ValueError(f"MultiselectInput value must be a list of strings. Item: '{item}' is not a string")
        return v


class FileInput(BaseInputMixin, ListableInputMixin, FileMixin, MetadataTraceMixin):
    """
    Represents a file field.

    This class represents a file input and provides functionality for handling file values.
    It inherits from the `BaseInputMixin`, `ListableInputMixin`, and `FileMixin` classes.

    Attributes:
        field_type (SerializableFieldTypes): The field type of the input. Defaults to FieldTypes.FILE.
    """

    field_type: SerializableFieldTypes = FieldTypes.FILE


DEFAULT_PROMPT_INTUT_TYPES = ["Message", "Text"]


class DefaultPromptField(Input):
    name: str
    display_name: Optional[str] = None
    field_type: str = "str"

    advanced: bool = False
    multiline: bool = True
    input_types: list[str] = DEFAULT_PROMPT_INTUT_TYPES
    value: Any = ""  # Set the value to empty string

class DynamicMultiSelect(BaseInputMixin):
    field_type: Optional[SerializableFieldTypes] = FieldTypes.DYNAMIC_MULTI_SELECT
    option_selection_limit: Optional[int] = None

class DynamicSingleSelect(BaseInputMixin):
    field_type: Optional[SerializableFieldTypes] = FieldTypes.DYNAMIC_SINGLE_SELECT

class MultiSelect(BaseInputMixin, DropDownMixin):
    field_type: Optional[SerializableFieldTypes] = FieldTypes.MULTI_SELECT
    options: list[str] = Field(default_factory=list)

class GoogleDrivePicker(BaseInputMixin):
    field_type: Optional[SerializableFieldTypes] = FieldTypes.GOOGLE_DRIVE_PICKER
    document_filter_type: Optional[str] = None


InputTypes = Union[
    Input,
    DefaultPromptField,
    BoolInput,
    DataInput,
    DictInput,
    DropdownInput,
    MultiselectInput,
    FileInput,
    FloatInput,
    HandleInput,
    IntInput,
    MultilineInput,
    MultilineSecretInput,
    NestedDictInput,
    PromptInput,
    SecretStrInput,
    StrInput,
    MessageTextInput,
    MessageInput,
    DynamicMultiSelect,
    DynamicSingleSelect,
    MultiSelect,
    GoogleDrivePicker,
    TableInput,
]

InputTypesMap: dict[str, type[InputTypes]] = {t.__name__: t for t in get_args(InputTypes)}


def instantiate_input(input_type: str, data: dict) -> InputTypes:
    input_type_class = InputTypesMap.get(input_type)
    if "type" in data:
        # Replate with field_type
        data["field_type"] = data.pop("type")
    if input_type_class:
        return input_type_class(**data)
    else:
        raise ValueError(f"Invalid input type: {input_type}")
