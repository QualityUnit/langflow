# This module is used to import any langchain class by name.

import importlib
import sys
from typing import Any, Type
import copy
from langflow.settings import settings



def import_module(module_path: str) -> Any:
    """Import module from module path"""
    if "from" not in module_path:
        # Import the module using the module path
        return importlib.import_module(module_path)
    # Split the module path into its components
    _, module_path, _, object_name = module_path.split()

    # Import the module using the module path
    if module_path in sys.modules:
        module = importlib.reload(sys.modules[module_path])
    else:
        module = importlib.import_module(module_path)

    return getattr(module, object_name)


def import_by_type(name: str) -> Any:
    """Import class by type and name"""
    # fetching all components from settings
    components = settings.get_all_components()
    c = components[name].built_object
    # clone the object
    return copy.deepcopy(c)
