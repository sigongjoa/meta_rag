import re
from typing import Dict, Any, Optional

class ProblemParser:
    """
    Parses various problem formats to extract text, formulas, and metadata.
    Supports modular extension for different problem sources/types.
    """

    def __init__(self):
        # Regex patterns for common formula delimiters (LaTeX)
        self.formula_patterns = {
            "inline": r'\$(.+?)\$',
            "display": r'\$\$(.*?)\$\$',
            "latex_block": r'\\begin{equation}(.*?)\\end{equation}',
            "latex_align": r'\\begin{align}(.*?)\\end{align}',
        }
        # Example metadata pattern: "회사명_문제유형"
        self.metadata_pattern = r'^(?P<company>[^_]+)_(?P<problem_type>.+?):'

    def parse_problem(self, problem_string: str) -> Dict[str, Any]:
        """
        Parses a problem string into its components: text, formulas, and metadata.

        Args:
            problem_string: The raw input string of the problem.

        Returns:
            A dictionary containing 'text', 'formulas' (list of strings), and 'metadata' (dict).
        """
        extracted_formulas = []
        
        # 1. Extract Metadata
        metadata = self._extract_metadata(problem_string)
        if metadata:
            text_after_metadata_removal = re.sub(self.metadata_pattern, '', problem_string, count=1).strip()
        else:
            text_after_metadata_removal = problem_string

        problem_string_for_formulas = text_after_metadata_removal
        
        # 2. Collect all formula content and their full matched strings
        all_formula_matches_with_content: List[Tuple[str, str]] = [] # (full_match_str, content_str)

        # Process patterns in a specific order to avoid partial matches
        # (Longer/more specific patterns first for correct replacement order)
        pattern_definitions = [
            self.formula_patterns["latex_block"],
            self.formula_patterns["latex_align"],
            self.formula_patterns["display"],
            self.formula_patterns["inline"],
        ]
        
        # Sort patterns by length (descending) to ensure longest matches are replaced first
        pattern_definitions.sort(key=len, reverse=True)

        for pattern_regex in pattern_definitions:
            for match in re.finditer(pattern_regex, problem_string_for_formulas, re.DOTALL):
                full_match_str = match.group(0)
                formula_content = match.group(1).strip()
                if formula_content:
                    all_formula_matches_with_content.append((full_match_str, formula_content))

        # 3. Replace full matched formula strings with a unique placeholder
        #    and collect unique extracted formulas
        temp_text_for_cleaning = problem_string_for_formulas
        unique_extracted_formulas_set = set()
        
        # Sort by length of full_match_str (descending) to replace longer matches first
        all_formula_matches_with_content.sort(key=lambda x: len(x[0]), reverse=True)

        for i, (full_match_str, content_str) in enumerate(all_formula_matches_with_content):
            # Replace only if the full_match_str is still present in the text
            # This handles cases where a formula might have been part of a larger, already replaced formula
            if full_match_str in temp_text_for_cleaning:
                placeholder = f"__FORMULA_PLACEHOLDER_{i}__"
                temp_text_for_cleaning = temp_text_for_cleaning.replace(full_match_str, placeholder)
                unique_extracted_formulas_set.add(content_str)
        
        extracted_formulas = sorted(list(unique_extracted_formulas_set)) # Sort for consistent output

        # 4. Final text cleanup: replace placeholders with space, then clean up multiple spaces
        cleaned_text = re.sub(r'__FORMULA_PLACEHOLDER_\d+__', ' ', temp_text_for_cleaning)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        return {
            "text": cleaned_text,
            "formulas": extracted_formulas,
            "metadata": metadata
        }

    def _extract_metadata(self, problem_string: str) -> Optional[Dict[str, str]]:
        """
        Extracts metadata from the beginning of the problem string.
        """
        match = re.match(self.metadata_pattern, problem_string)
        if match:
            return match.groupdict()
        return None

    def add_custom_formula_pattern(self, name: str, pattern: str):
        """
        Adds or updates a custom regex pattern for formula extraction.
        """
        self.formula_patterns[name] = pattern

    def add_custom_metadata_pattern(self, pattern: str):
        """
        Sets a custom regex pattern for metadata extraction.
        """
        self.metadata_pattern = pattern
