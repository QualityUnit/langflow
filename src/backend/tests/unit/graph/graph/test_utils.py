import pytest

from langflow.graph.graph import utils


@pytest.fixture
def client():
    pass


@pytest.fixture
def graph():
    return {
        "A": {"successors": ["B"], "predecessors": []},
        "B": {"successors": ["D"], "predecessors": ["A", "C"]},
        "C": {"successors": ["B", "I"], "predecessors": ["N"]},
        "D": {"successors": ["E", "F"], "predecessors": ["B"]},
        "E": {"successors": ["G"], "predecessors": ["D"]},
        "F": {"successors": ["G", "H"], "predecessors": ["D"]},
        "G": {"successors": [], "predecessors": ["E", "F"]},
        "H": {"successors": [], "predecessors": ["F"]},
        "I": {"successors": ["M"], "predecessors": ["C", "J"]},
        "J": {"successors": ["I", "K"], "predecessors": ["N"]},
        "K": {"successors": ["Q", "P", "O"], "predecessors": ["J", "L"]},
        "L": {"successors": ["K"], "predecessors": []},
        "M": {"successors": [], "predecessors": ["I"]},
        "N": {"successors": ["C", "J"], "predecessors": []},
        "O": {"successors": ["R"], "predecessors": ["K"]},
        "P": {"successors": ["U"], "predecessors": ["K"]},
        "Q": {"successors": ["V"], "predecessors": ["K"]},
        "R": {"successors": ["S"], "predecessors": ["O"]},
        "S": {"successors": ["T"], "predecessors": ["R"]},
        "T": {"successors": [], "predecessors": ["S"]},
        "U": {"successors": ["W"], "predecessors": ["P"]},
        "V": {"successors": ["Y"], "predecessors": ["Q"]},
        "W": {"successors": ["X"], "predecessors": ["U"]},
        "X": {"successors": [], "predecessors": ["W"]},
        "Y": {"successors": ["Z"], "predecessors": ["V"]},
        "Z": {"successors": [], "predecessors": ["Y"]},
    }


def test_get_successors_a(graph):
    vertex_id = "A"

    result = utils.get_successors(graph, vertex_id)

    assert set(result) == {"A", "B", "D", "E", "F", "H", "G"}


def test_get_successors_z(graph):
    vertex_id = "Z"

    result = utils.get_successors(graph, vertex_id)

    assert set(result) == {"Z"}


def test_sort_up_to_vertex_n_is_start(graph):
    vertex_id = "N"

    result = utils.sort_up_to_vertex(graph, vertex_id, is_start=True)
    # Result shoud be all the vertices
    assert set(result) == set(graph.keys())


def test_sort_up_to_vertex_z(graph):
    vertex_id = "Z"

    result = utils.sort_up_to_vertex(graph, vertex_id)

    assert set(result) == {"L", "N", "J", "K", "Q", "V", "Y", "Z"}


def test_sort_up_to_vertex_x(graph):
    vertex_id = "X"

    result = utils.sort_up_to_vertex(graph, vertex_id)

    assert set(result) == {"L", "N", "J", "K", "P", "U", "W", "X"}


def test_sort_up_to_vertex_t(graph):
    vertex_id = "T"

    result = utils.sort_up_to_vertex(graph, vertex_id)

    assert set(result) == {"L", "N", "J", "K", "O", "R", "S", "T"}


def test_sort_up_to_vertex_m(graph):
    vertex_id = "M"

    result = utils.sort_up_to_vertex(graph, vertex_id)

    assert set(result) == {"N", "C", "J", "I", "M"}


def test_sort_up_to_vertex_h(graph):
    vertex_id = "H"

    result = utils.sort_up_to_vertex(graph, vertex_id)

    assert set(result) == {"N", "C", "A", "B", "D", "F", "H"}


def test_sort_up_to_vertex_g(graph):
    vertex_id = "G"

    result = utils.sort_up_to_vertex(graph, vertex_id)

    assert set(result) == {"N", "C", "A", "B", "D", "F", "E", "G"}


def test_sort_up_to_vertex_a(graph):
    vertex_id = "A"

    result = utils.sort_up_to_vertex(graph, vertex_id)

    assert set(result) == {"A"}


def test_sort_up_to_vertex_invalid_vertex(graph):
    vertex_id = "7"

    with pytest.raises(ValueError):
        utils.sort_up_to_vertex(graph, vertex_id)


def test_has_cycle():
    edges = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "B")]
    vertices = ["A", "B", "C", "D", "E"]
    assert utils.has_cycle(vertices, edges) is True


class TestFindCycleEdge:
    # Detects a cycle in a simple directed graph
    def test_detects_cycle_in_simple_graph(self):
        entry_point = "A"
        edges = [("A", "B"), ("B", "C"), ("C", "A")]
        result = utils.find_cycle_edge(entry_point, edges)
        assert result == ("C", "A")

    # Returns None when no cycle is present
    def test_returns_none_when_no_cycle(self):
        entry_point = "A"
        edges = [("A", "B"), ("B", "C")]
        result = utils.find_cycle_edge(entry_point, edges)
        assert result is None

    # Correctly identifies the first cycle encountered
    def test_identifies_first_cycle(self):
        entry_point = "A"
        edges = [("A", "B"), ("B", "C"), ("C", "A"), ("A", "D"), ("D", "E"), ("E", "A")]
        result = utils.find_cycle_edge(entry_point, edges)
        assert result == ("C", "A")

    # Handles graphs with multiple edges between the same nodes
    def test_multiple_edges_between_same_nodes(self):
        entry_point = "A"
        edges = [("A", "B"), ("A", "B"), ("B", "C"), ("C", "A")]
        result = utils.find_cycle_edge(entry_point, edges)
        assert result == ("C", "A")

    # Processes graphs with multiple disconnected components
    def test_disconnected_components(self):
        entry_point = "A"
        edges = [("A", "B"), ("B", "C"), ("D", "E"), ("E", "F"), ("F", "D")]
        result = utils.find_cycle_edge(entry_point, edges)
        assert result is None

    # Handles an empty list of edges
    def test_empty_edges_list(self):
        entry_point = "A"
        edges = []
        result = utils.find_cycle_edge(entry_point, edges)
        assert result is None

    # Manages a graph with a single node and no edges
    def test_single_node_no_edges(self):
        entry_point = "A"
        edges = []
        result = utils.find_cycle_edge(entry_point, edges)
        assert result is None

    # Detects cycles in graphs with self-loops
    def test_self_loop_cycle(self):
        entry_point = "A"
        edges = [("A", "A")]
        result = utils.find_cycle_edge(entry_point, edges)
        assert result == ("A", "A")

    # Handles graphs with multiple cycles
    def test_multiple_cycles(self):
        entry_point = "A"
        edges = [("A", "B"), ("B", "C"), ("C", "A"), ("B", "D"), ("D", "B")]
        result = utils.find_cycle_edge(entry_point, edges)
        assert result == ("C", "A")

    # Processes graphs with nodes having no outgoing edges
    def test_nodes_with_no_outgoing_edges(self):
        entry_point = "A"
        edges = [("A", "B"), ("B", "C")]
        result = utils.find_cycle_edge(entry_point, edges)
        assert result is None

    # Handles large graphs efficiently
    def test_large_graph_efficiency(self):
        entry_point = "0"
        edges = [(str(i), str(i + 1)) for i in range(1000)] + [("999", "0")]
        result = utils.find_cycle_edge(entry_point, edges)
        assert result == ("999", "0")

    # Manages graphs with duplicate edges
    def test_duplicate_edges(self):
        entry_point = "A"
        edges = [("A", "B"), ("B", "C"), ("C", "A"), ("C", "A")]
        result = utils.find_cycle_edge(entry_point, edges)
        assert result == ("C", "A")


class TestFindAllCycleEdges:
    # Detects cycles in a simple directed graph
    def test_detects_cycles_in_simple_graph(self):
        entry_point = "A"
        edges = [("A", "B"), ("B", "C"), ("C", "A")]
        result = utils.find_all_cycle_edges(entry_point, edges)
        assert result == [("C", "A")]

    # Identifies multiple cycles in a complex graph
    def test_identifies_multiple_cycles(self):
        entry_point = "A"
        edges = [("A", "B"), ("B", "C"), ("C", "A"), ("B", "D"), ("D", "B")]
        result = utils.find_all_cycle_edges(entry_point, edges)
        assert set(result) == {("C", "A"), ("D", "B")}

    # Returns an empty list when no cycles are present
    def test_no_cycles_present(self):
        entry_point = "A"
        edges = [("A", "B"), ("B", "C")]
        result = utils.find_all_cycle_edges(entry_point, edges)
        assert result == []

    # Handles graphs with a single node and no edges
    def test_single_node_no_edges(self):
        entry_point = "A"
        edges = []
        result = utils.find_all_cycle_edges(entry_point, edges)
        assert result == []

    # Processes graphs with disconnected components
    def test_disconnected_components(self):
        entry_point = "A"
        edges = [("A", "B"), ("C", "D")]
        result = utils.find_all_cycle_edges(entry_point, edges)
        assert result == []

    # Handles graphs with self-loops
    def test_self_loops(self):
        entry_point = "A"
        edges = [("A", "A")]
        result = utils.find_all_cycle_edges(entry_point, edges)
        assert result == [("A", "A")]

    # Manages graphs with multiple edges between the same nodes
    def test_multiple_edges_between_same_nodes(self):
        entry_point = "A"
        edges = [("A", "B"), ("A", "B"), ("B", "C"), ("C", "A")]
        result = utils.find_all_cycle_edges(entry_point, edges)
        assert result == [("C", "A")]

    # Processes graphs with nodes having no outgoing edges
    def test_nodes_with_no_outgoing_edges(self):
        entry_point = "A"
        edges = [("A", "B"), ("B", "C")]
        result = utils.find_all_cycle_edges(entry_point, edges)
        assert result == []

    # Handles large graphs efficiently
    def test_large_graphs_efficiency(self):
        entry_point = "A"
        edges = [(chr(65 + i), chr(65 + (i + 1) % 26)) for i in range(1000)]
        result = utils.find_all_cycle_edges(entry_point, edges)
        assert isinstance(result, list)

    # Manages graphs with nodes having no incoming edges
    def test_nodes_with_no_incoming_edges(self):
        entry_point = "A"
        edges = [("B", "C"), ("C", "D")]
        result = utils.find_all_cycle_edges(entry_point, edges)
        assert result == []

    # Handles graphs with mixed data types in edges
    def test_mixed_data_types_in_edges(self):
        entry_point = 1
        edges = [(1, 2), (2, 3), (3, 1)]
        result = utils.find_all_cycle_edges(entry_point, edges)
        assert result == [(3, 1)]

    # Processes graphs with duplicate edges
    def test_duplicate_edges(self):
        entry_point = "A"
        edges = [("A", "B"), ("A", "B"), ("B", "C"), ("C", "A"), ("C", "A")]
        result = utils.find_all_cycle_edges(entry_point, edges)
        assert set(result) == {("C", "A")}