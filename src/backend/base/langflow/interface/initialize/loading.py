import inspect
import json
from typing import Any, Dict, Type, Optional

from langflow.schema.artifact import get_artifact_type, post_process_raw
from langflow.schema import Data
import orjson
from loguru import logger

from langflow.interface.importing.utils import import_by_type

NODE_TYPE_TO_CLASS = {}


def get_class_from_node_type(node_type: str) -> Type:
    pass


async def instantiate_class(vertex: "Vertex", global_flow_params: Optional[Any]) -> Any:
    """Instantiate class from module type and key, and params"""
    node_type = vertex.vertex_type
    params = vertex.params
    params = convert_params_to_sets(params)
    params = convert_kwargs(params)

    logger.debug(f"Instantiating {node_type}")
    class_object = import_by_type(name=node_type)
    logger.debug(f"Instantiated {node_type}")

    # Instantiate the class based on the type
    # NOTE: there will be no validation for now since the types are loaded from config.yaml
    # return await instantiate_based_on_type(class_object, base_type, node_type, params, user_id=user_id)
    c = class_object(_vertex=vertex)
    c.global_flow_params = global_flow_params
    custom_component, build_results, artifacts = await build_component_and_get_results(
        component=c,
        params=params,
        vertex=vertex,
    )
    return custom_component, build_results, artifacts

async def build_component_and_get_results(
    component: "AppComponent",
    params: dict,
    vertex: "Vertex",
):
    params_copy = params.copy()

    if hasattr(component, "inputs") and len(component.inputs) > 0 and hasattr(component, "outputs") and len(component.outputs) > 0:
        # compiling in Input/Output mode. Trying to call build
        return await build_component_with_input_output(component, params_copy)
    else:
        # compiling with build method
        return await build_component(params_copy, component)

async def build_component(params: dict, component: "AppComponent"):
    # Determine if the build method is asynchronous
    is_async = inspect.iscoroutinefunction(component.build)

    # New feature: the component has a list of outputs and we have
    # to check the vertex.edges to see which is connected (coulb be multiple)
    # and then we'll get the output which has the name of the method we should call.
    # the methods don't require any params because they are already set in the custom_component
    # so we can just call them

    if is_async:
        # Await the build method directly if it's async
        build_result = await component.build(**params)
    else:
        # Call the build method directly if it's sync
        build_result = component.build(**params)
    custom_repr = component.custom_repr()
    if custom_repr is None and isinstance(build_result, (dict, Data, str)):
        custom_repr = build_result
    if not isinstance(custom_repr, str):
        custom_repr = str(custom_repr)
    raw = component.repr_value
    if hasattr(raw, "data") and raw is not None:
        raw = raw.data

    elif hasattr(raw, "model_dump") and raw is not None:
        raw = raw.model_dump()
    if raw is None and isinstance(build_result, (dict, Data, str)):
        raw = build_result.data if isinstance(build_result, Data) else build_result

    artifact_type = get_artifact_type(component.repr_value or raw, build_result)
    raw = post_process_raw(raw, artifact_type)
    artifact = {"repr": custom_repr, "raw": raw, "type": artifact_type}

    if component.vertex is not None:
        component._artifacts = {component.vertex.outputs[0].get("name"): artifact}
        component._results = {component.vertex.outputs[0].get("name"): build_result}
        return component, build_result, artifact

    raise ValueError("Custom component does not have a vertex")

async def build_component_with_input_output(component, params):
    # Now set the params as attributes of the custom_component
    component.set_attributes(params)

    # update component outputs if needed
    component.update_output_handles()

    build_results, artifacts = await component.build_results()

    return component, build_results, artifacts


def convert_params_to_sets(params):
    """Convert certain params to sets"""
    if "allowed_special" in params:
        params["allowed_special"] = set(params["allowed_special"])
    if "disallowed_special" in params:
        params["disallowed_special"] = set(params["disallowed_special"])
    return params


def convert_kwargs(params):
    # if *kwargs are passed as a string, convert to dict
    # first find any key that has kwargs or config in it
    kwargs_keys = [key for key in params.keys() if "kwargs" in key or "config" in key]
    for key in kwargs_keys:
        if isinstance(params[key], str):
            try:
                params[key] = orjson.loads(params[key])
            except json.JSONDecodeError:
                # if the string is not a valid json string, we will
                # remove the key from the params
                params.pop(key, None)
    return params
