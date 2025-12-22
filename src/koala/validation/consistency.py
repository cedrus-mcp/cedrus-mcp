"""Consistency validation checks."""

from koala.graph.argument_map import ArgumentMap
from koala.tools.tool_context import ToolContext


def check_consistency(arg_map: ArgumentMap, tc: ToolContext, fix: bool = False) -> None:
    """Check that the proposition graph is consistent, no equivalence class is self-contradictory."""

    equiv_classes = arg_map.list_equivalence_classes()
    for eq_class in equiv_classes:
        props = list(eq_class)
        for i in range(len(props)):
            for j in range(i + 1, len(props)):
                if arg_map.are_contradictory(props[i], props[j]):
                    if fix:
                        # automatically remove the equivalence causing the contradiction
                        arg_map.remove_negation(props[i], props[j])
                        tc.issue(
                            "info",
                            f"Removed negation between {props[i]} and {props[j]} to resolve self-contradiction.",
                        )
                        continue
                    else:
                        message = f"Equivalence class containing propositions {props} is self-contradictory due to {props[i]} and {props[j]}."
                        tc.issue("error", message)
                        tc.suggest(
                            "validate",
                            {
                                "fix": "true",
                            },
                            "Resolve self-contradictory logical relations and sanitize propositions by using auto-fix.",
                            "fix",
                        )
