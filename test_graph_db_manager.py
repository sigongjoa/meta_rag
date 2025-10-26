import pytest
from graph_db_manager import GraphDBManager

def test_add_problem():
    db_manager = GraphDBManager()
    db_manager.add_problem(problem_id=1, problem_text="This is a test problem.")
    node = "problem_1"
    assert db_manager.graph.has_node(node)
    assert db_manager.graph.nodes[node]["type"] == "problem"
    assert db_manager.graph.nodes[node]["id"] == 1

def test_add_concept():
    db_manager = GraphDBManager()
    db_manager.add_concept("calculus")
    assert db_manager.graph.has_node("calculus")
    assert db_manager.graph.nodes["calculus"]["type"] == "concept"

def test_link_problem_to_concepts():
    db_manager = GraphDBManager()
    db_manager.add_problem(problem_id=1, problem_text="A problem about derivatives.")
    concepts = ["calculus", "derivative"]
    db_manager.link_problem_to_concepts(problem_id=1, concepts=concepts)
    
    assert db_manager.graph.has_edge("problem_1", "calculus")
    assert db_manager.graph.has_edge("problem_1", "derivative")
    assert db_manager.graph.edges[("problem_1", "calculus")]["type"] == "contains_concept"

def test_get_graph_info():
    db_manager = GraphDBManager()
    db_manager.add_problem(problem_id=1, problem_text="A problem.")
    db_manager.link_problem_to_concepts(problem_id=1, concepts=["concept1", "concept2"])
    info = db_manager.get_graph_info()
    assert info["num_nodes"] == 3 # 1 problem + 2 concepts
    assert info["num_edges"] == 2

def test_linking_to_nonexistent_problem_raises_error():
    db_manager = GraphDBManager()
    with pytest.raises(ValueError):
        db_manager.link_problem_to_concepts(problem_id=99, concepts=["test"])
