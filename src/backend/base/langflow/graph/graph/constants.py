from langflow.graph.vertex import types
from langflow.utils.lazy_load import LazyLoadDictBase


class VertexTypesDict(LazyLoadDictBase):
    def __init__(self):
        self._all_types_dict = None

    @property
    def VERTEX_TYPE_MAP(self):
        return self.all_types_dict

    def _build_dict(self):
        langchain_types_dict = self.get_type_dict()
        return {
            **langchain_types_dict,
        }

    def get_custom_component_vertex_type(self):
        return types.CustomComponentVertex

    def get_type_dict(self):
        return {
            **{t: types.CustomComponentVertex for t in custom_component_creator.to_list()},
        }


lazy_load_vertex_dict = VertexTypesDict()
