import operator
from typing import Any, ClassVar, Optional
from uuid import UUID
import warnings

from cachetools import TTLCache, cachedmethod
from fastapi import HTTPException

from langflow.custom.attributes import ATTR_FUNC_MAPPING
from langflow.custom.code_parser import CodeParser
from langflow.custom.eval import eval_custom_component_code
from langflow.utils import validate


class ComponentCodeNullError(HTTPException):
    pass


class ComponentFunctionEntrypointNameNullError(HTTPException):
    pass


class BaseComponent:
    ERROR_CODE_NULL: ClassVar[str] = "Python code must be provided."
    ERROR_FUNCTION_ENTRYPOINT_NAME_NULL: ClassVar[str] = "The name of the entrypoint function must be provided."

    _code: Optional[str] = None
    """The code of the component. Defaults to None."""
    _function_entrypoint_name: str = "build"
    field_config: dict = {}
    _user_id: Optional[str]
    global_flow_params: Optional[Any] = None
    _template_config: dict = {}

    def __init__(self, **data):
        self.cache = TTLCache(maxsize=1024, ttl=60)
        for key, value in data.items():
            if key == "user_id":
                setattr(self, "_user_id", value)
            elif key == "global_flow_params":
                setattr(self, "global_flow_params", value)
            else:
                setattr(self, key, value)


        # Validate the emoji at the icon field - no need to validate icon
        # if hasattr(self, "icon") and self.icon:
        #     self.icon = self.validate_icon(self.icon)

    def __setattr__(self, key, value):
        if key == "_user_id" and hasattr(self, "_user_id") and getattr(self, "_user_id") is not None:
            warnings.warn("user_id is immutable and cannot be changed.")
        super().__setattr__(key, value)

    @cachedmethod(cache=operator.attrgetter("cache"))
    def get_code_tree(self, code: str):
        parser = CodeParser(code)
        return parser.parse_code()

    def get_function(self):
        if not self._code:
            raise ComponentCodeNullError(
                status_code=400,
                detail={"error": self.ERROR_CODE_NULL, "traceback": ""},
            )

        if not self._function_entrypoint_name:
            raise ComponentFunctionEntrypointNameNullError(
                status_code=400,
                detail={
                    "error": self.ERROR_FUNCTION_ENTRYPOINT_NAME_NULL,
                    "traceback": "",
                },
            )

        return validate.create_function(self._code, self._function_entrypoint_name)

    @staticmethod
    def get_template_config(component):
        """
        Gets the template configuration for the custom component itself.
        """
        template_config = {}

        for attribute, func in ATTR_FUNC_MAPPING.items():
            if hasattr(component, attribute):
                value = getattr(component, attribute)
                if value is not None:
                    template_config[attribute] = func(value=value)

        for key in template_config.copy():
            if key not in ATTR_FUNC_MAPPING.keys():
                template_config.pop(key, None)

        return template_config

    def build_template_config(self) -> dict:
        """
        Builds the template configuration for the custom component.

        Returns:
            A dictionary representing the template configuration.
        """
        if not self._code:
            return {}

        cc_class = eval_custom_component_code(self._code)
        component_instance = cc_class(_code=self._code)
        template_config = self.get_template_config(component_instance)
        return template_config

    def build(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError
