# arvis/reflexive/introspection/counterfactual_introspector.py

from typing import Dict, Any
class CounterfactualIntrospector:
    """
    Explains ARVIS counterfactual reasoning.
    """

    def describe(self)-> Dict[str, Any]:

        return {
            "name": "counterfactual_reasoning",
            "description": (
                "ARVIS evaluates alternative decisions by simulating "
                "their impact on predicted risk and uncertainty."
            ),
            "actions_evaluated": [
                "normal",
                "confirmation",
                "exploration",
                "abstain",
            ],
            "principle": "select action minimizing predicted risk + action cost",
        }