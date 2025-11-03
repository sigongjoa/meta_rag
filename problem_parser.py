import re
from typing import Dict, Any, Optional
import networkx as nx

class ProblemParser:
    def __init__(self):
        self.formula_patterns = {
            "latex_block": r'\\begin{equation}(.*?)\\end{equation}',
            "latex_align": r'\\begin{align}(.*?)\\end{align}',
            "latex_gather": r'\\begin{gather}(.*?)\\end{gather}',
            "display": r'\$\$(.*?)\$\$',
            "inline": r'\$(.+?)\$',
        }
    def parse_problem(self, problem_string: str) -> Dict[str, Any]:
        metadata = None # Placeholder for actual metadata extraction
        text_after_metadata = problem_string # For now, assume no metadata prefix

        formulas = []

        def replace_and_collect(match):
            formula_content = ""
            for g in reversed(match.groups()):
                if g is not None:
                    formula_content = g.strip()
                    break
            if formula_content:
                formulas.append(formula_content)
            return ""

        combined_pattern = "|".join(
            f"({pattern})" for name, pattern in sorted(self.formula_patterns.items(), key=lambda item: len(item[1]), reverse=True)
        )

        text_with_formulas_removed = re.sub(combined_pattern, replace_and_collect, text_after_metadata, flags=re.DOTALL)
        
        # First, normalize all whitespace
        normalized_space_text = re.sub(r'\s+', ' ', text_with_formulas_removed).strip()
        
        # Then, remove spaces before punctuation
        cleaned_text = re.sub(r'\s+([.,?!])', r'\1', normalized_space_text)

        return {
            "text": cleaned_text,
            "formulas": sorted(list(set(formulas))),
            "metadata": metadata
        }

    def create_graph_representation(self, problem: Dict[str, Any]) -> nx.DiGraph:
        G = nx.DiGraph()
        problem_id = problem.get('id', 'problem')
        G.add_node(problem_id, type='problem')

        for concept in problem.get('concepts', []):
            G.add_node(concept, type='concept')
            G.add_edge(problem_id, concept, type='has_concept')

        for formula in problem.get('formulas', []):
            G.add_node(formula, type='formula')
            G.add_edge(problem_id, formula, type='has_formula')

        # Add edges between related concepts
        concepts = problem.get('concepts', [])
        if len(concepts) > 1:
            for i in range(len(concepts)):
                for j in range(i + 1, len(concepts)):
                    G.add_edge(concepts[i], concepts[j], type='related_concept')
                    G.add_edge(concepts[j], concepts[i], type='related_concept') # Make it symmetric for now

        return G