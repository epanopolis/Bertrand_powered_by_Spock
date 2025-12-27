"""
Hub to the endpoints

"""
# pylint: disable=relative-beyond-top-level
# pylint: disable=invalid-name

from .scanner import Shannon
from .turing_parser import Turing
from ..analytical_engine.babbage_eval import Knuth
from .dictionaries.tokens import token_dict
from .dictionaries.errors import Errors

# Project naming theme:
#  - Shannon: scanner helpers (information theory roots)
#  - VonNeumann: concrete lexer (machine model)
#  - Turing: parser (computability foundations)
#  - Hamilton: aux parser / reliability (Apollo-era software)
#  - Chomsky: entry point over grammars
#  - Grieg: token “orchestrator” (composer—because code should sing)
#  - Babbage: The evaluation "engine"

def chomsky(source):
    """
    Main function that ties together the scanner, parser, and evaluator.

    """
    try:
        # Step 1: Scan
        scanner = Shannon(token_dict)
        try:
            token_list = scanner.scan_source(source)
        except Errors as e:
            return {"success": False, "stage": "scanner", "error": \
                f"Scanner error: {e.error_report()}"}

        # Step 2: Parse
        try:
            parser = Turing(token_list)
            parsed_code = parser.parse()
        except Errors as e:
            return {"success": False, "stage": "parser", "error": \
            f"Parser error: {e.error_report()}"}

        # Step 3: Evaluate
        try:
            evaluator = Knuth(parsed_code)
            result = evaluator.engine()
        except Errors as e:
            return {"success": False, "stage": "evaluator", "error": \
                f"Evaluator error: {e.error_report()}"}

        return result

    except RuntimeError as e:
        # last-resort guard so failures always produce a dict
        return {"success": False, "stage": "unknown", "error": f"{e}"}
