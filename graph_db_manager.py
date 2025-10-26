import networkx as nx
from typing import List

class GraphDBManager:
    """
    Manages the knowledge graph using NetworkX.
    """
    def __init__(self):
        """
        Initializes the GraphDBManager with an empty directed graph.
        """
        self.graph = nx.DiGraph()

    def add_problem(self, problem_id: int, problem_text: str):
        """
        Adds a problem node to the graph.
        """
        self.graph.add_node(
            f"problem_{problem_id}",
            type="problem",
            id=problem_id,
            text=problem_text
        )

    def add_concept(self, concept: str):
        """
        Adds a concept node to the graph if it doesn't already exist.
        """
        if not self.graph.has_node(concept):
            self.graph.add_node(concept, type="concept")

    def link_problem_to_concepts(self, problem_id: int, concepts: List[str]):
        """
        Creates edges from a problem node to a list of concept nodes.
        """
        problem_node = f"problem_{problem_id}"
        if not self.graph.has_node(problem_node):
            raise ValueError(f"Problem node {problem_node} does not exist.")
            
        for concept in concepts:
            self.add_concept(concept)
            self.graph.add_edge(problem_node, concept, type="contains_concept")

    def get_graph_info(self):
        """
        Returns basic information about the graph.
        """
        return {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
        }
