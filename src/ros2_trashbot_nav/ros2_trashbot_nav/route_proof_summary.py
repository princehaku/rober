"""Route proof summary helpers shared by dry-run status and offline proof."""

from typing import Any, Dict, Iterable, List

PASSED = "passed"
INVALID_ROUTE = "invalid_route"


def _to_non_negative_int(value: Any) -> int:
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return 0


def _normalized_missing(indexes: Iterable[Any], total_checkpoints: int) -> List[int]:
    normalized = set()
    for item in indexes:
        try:
            index = int(item)
        except (TypeError, ValueError):
            continue
        if 0 <= index < total_checkpoints:
            normalized.add(index)
    return sorted(normalized)


def build_route_proof_summary(
    *,
    total_checkpoints: Any,
    covered_checkpoints: Any,
    gate_status: Any,
    last_block_reason: Any = "",
    missing_checkpoints: Iterable[Any] = (),
) -> Dict[str, Any]:
    """Build normalized `route_proof_summary` with a single calculation rule."""
    total = _to_non_negative_int(total_checkpoints)
    covered = min(_to_non_negative_int(covered_checkpoints), total)
    coverage_rate = 0.0 if total <= 0 else round(float(covered) / float(total), 4)

    summary_gate_status = str(gate_status or "")
    summary_block_reason = str(last_block_reason or "")
    normalized_missing = _normalized_missing(missing_checkpoints, total)

    # Keep proof deterministic for fully-covered routes regardless of noisy hints.
    if total > 0 and covered >= total:
        normalized_missing = []
        summary_gate_status = PASSED
        summary_block_reason = ""
    elif not normalized_missing:
        normalized_missing = list(range(covered, total))

    return {
        "coverage_rate": coverage_rate,
        "covered_checkpoints": covered,
        "total_checkpoints": total,
        "missing_checkpoints": normalized_missing,
        "gate_status": summary_gate_status or INVALID_ROUTE,
        "last_block_reason": summary_block_reason,
    }


def summarize_checkpoints_from_visual_gate(checkpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Derive route proof summary from ordered checkpoint visual-gate results."""
    total = len(checkpoints)
    covered = 0
    block_reason = ""
    gate_status = PASSED if total > 0 else INVALID_ROUTE

    for checkpoint in checkpoints:
        status = str(checkpoint.get("status", ""))
        if status == PASSED and covered == int(checkpoint.get("index", covered)):
            covered += 1
            continue
        gate_status = status or INVALID_ROUTE
        block_reason = str(checkpoint.get("detail") or "")
        break

    return build_route_proof_summary(
        total_checkpoints=total,
        covered_checkpoints=covered,
        gate_status=gate_status,
        last_block_reason=block_reason,
    )
