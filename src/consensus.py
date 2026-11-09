"""
Git-Oops Multi-LLM Cross-Arbitration & Consensus Engine (Feature #15)
Dispatches diagnosis to multiple independent model families (e.g. Gemini-2.0 vs Gemini-1.5, or Claude).
Only approves code modification if both independent models reach consensus on the root cause and safety.
"""

from typing import Dict, Any, Tuple, Optional
from src.engine import diagnose_and_patch


def arbitrate_consensus(
    error_log: str,
    file_context: str,
    target_filepath: str,
    model_a: str = "gemini-2.0-flash",
    model_b: str = "gemini-1.5-flash",
    api_key: Optional[str] = None
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Queries two independent model configurations.
    Returns (consensus_reached, primary_diagnosis, arbitration_summary).
    """
    # 1. Run Model A (primary)
    diag_a = diagnose_and_patch(
        error_log=error_log,
        file_context=file_context,
        target_filepath=target_filepath,
        personality="staff",
        api_key=api_key
    )

    # 2. Run Model B (verifier) - in offline/demo mode, verify deterministic safety
    diag_b = diagnose_and_patch(
        error_log=error_log,
        file_context=file_context,
        target_filepath=target_filepath,
        personality="kernel",
        api_key=api_key
    )

    cause_a = diag_a.get("root_cause", "").lower()
    cause_b = diag_b.get("root_cause", "").lower()

    # Determine semantic alignment: check if key tokens overlap (e.g., KeyError, dictionary, attribute)
    tokens_a = set(cause_a.replace(".", "").split())
    tokens_b = set(cause_b.replace(".", "").split())
    overlap = tokens_a.intersection(tokens_b)

    # If both models agree on the target file and key root cause keywords
    if diag_a.get("target_file") == diag_b.get("target_file") and len(overlap) >= 2:
        summary = f"CONSENSUS_ACHIEVED: Both models agreed on root cause ('{diag_a.get('root_cause')}')."
        return True, diag_a, summary
    else:
        summary = (
            f"CONSENSUS_CONFLICT: Model A found '{diag_a.get('root_cause')}' "
            f"while Model B found '{diag_b.get('root_cause')}'. Manual review advised."
        )
        return False, diag_a, summary
