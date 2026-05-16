import json
from pathlib import Path
import time


VALID_TASK_RECORD_SOURCES = {"software_proof", "hil_pass"}
ROUTE_PROGRESS_FIELDS = (
    "source",
    "route_contract_version",
    "route_file",
    "route_id",
    "route_file_basename",
    "checkpoint",
    "checkpoint_id",
    "current_index",
    "target",
    "current_target",
    "total",
    "total_checkpoints",
    "evidence_ref",
    "failure_code",
)
TERMINAL_COMPLETION_REHEARSAL_SUMMARY_SCHEMA = (
    "trashbot.route_task_terminal_completion_rehearsal_summary.v1"
)
TERMINAL_COMPLETION_REHEARSAL_GATE = (
    "software_proof_docker_route_task_terminal_completion_rehearsal_gate"
)
TERMINAL_COMPLETION_REHEARSAL_NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "real_route_collection",
    "wave_rover_motion",
    "real_serial_or_uart_feedback",
    "real_hil_pass",
    "real_dropoff_completion",
    "real_cancel_completion",
    "delivery_success",
    "objective_5_external_proof",
)


def _normalize_task_record_source(value):
    source = str(value or "").strip().lower().replace("-", "_")
    if source in VALID_TASK_RECORD_SOURCES:
        return source
    if source in {"task_orchestrator", "dry_run", "robot_sim", "simulated", "software", "software_proof"}:
        return "software_proof"
    if source == "hil":
        return "hil_pass"
    return "software_proof"


def _route_progress_from_nav_results(nav_results):
    for nav_result in reversed(nav_results or []):
        if not isinstance(nav_result, dict):
            continue
        evidence = nav_result.get("evidence")
        if not isinstance(evidence, dict):
            continue
        route_progress = evidence.get("route_progress")
        if isinstance(route_progress, dict) and route_progress:
            return dict(route_progress)

        # fixed-route status 历史上可能把进度字段放在 evidence 顶层。
        # 写入 task_record 时统一成 route_progress，避免 Task A 工具猜测旧形态。
        progress = {
            field: evidence[field]
            for field in ROUTE_PROGRESS_FIELDS
            if field in evidence
        }
        if progress:
            return progress
    return {}


def _route_progress_evidence_ref(route_progress):
    if not isinstance(route_progress, dict):
        return ""
    value = route_progress.get("evidence_ref")
    return str(value).strip() if value is not None else ""


def _terminal_completion_rehearsal_summary(
    *,
    task_id,
    final_status,
    final_state,
    error_code,
    error_message,
    failure_code,
    human_intervention_required,
    evidence_ref,
    route_progress,
    dropoff_result,
):
    # 终态复账摘要只服务 Docker/software proof 下的材料对齐。
    # 即便 dry-run 成功，也不能从 task_record 推导真实投放、取消完成或 delivery success。
    route_progress_present = isinstance(route_progress, dict) and bool(route_progress)
    dropoff = dropoff_result if isinstance(dropoff_result, dict) else {}
    dropoff_code = str(dropoff.get("result_code") or "").strip()
    dropoff_success = bool(dropoff.get("success")) if "success" in dropoff else False
    normalized_final_status = str(final_status or "").strip() or "unknown"
    normalized_final_state = str(final_state or "").strip() or "unknown"
    normalized_error_code = str(error_code or "").strip()
    normalized_failure_code = str(failure_code or normalized_error_code or "").strip()
    cancel_reason = ""
    if normalized_final_status == "canceled" or normalized_failure_code == "TASK_CANCEL":
        cancel_reason = str(error_message or "user canceled").strip()
    failure_reason = ""
    if normalized_final_status not in ("success", "canceled"):
        failure_reason = str(error_message or normalized_failure_code or "task terminal state is not successful").strip()
    recovery_reason = (
        "manual_recovery_required"
        if human_intervention_required
        else "no_real_recovery_evidence_in_software_proof"
    )
    return {
        "schema": TERMINAL_COMPLETION_REHEARSAL_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": TERMINAL_COMPLETION_REHEARSAL_GATE,
        "source_schema": "trashbot.task_record.v1",
        "task_id": str(task_id or ""),
        "terminal_verdict": {
            "status": (
                "route_task_terminal_completion_rehearsal"
                if normalized_final_status
                else "blocked_missing_route_task_terminal_completion_rehearsal"
            ),
            "verdict": "not_proven",
            "reason": "task record terminal state is metadata-only; delivery_success=false; primary_actions_enabled=false",
        },
        "final_status": normalized_final_status,
        "final_state": normalized_final_state,
        "error_code": normalized_error_code,
        "failure_code": normalized_failure_code,
        "dropoff_result": {
            "status": "not_proven",
            "result_code": dropoff_code,
            "reported_success": dropoff_success,
            "reason": str(dropoff.get("message") or "").strip(),
        },
        "cancel_reason": cancel_reason,
        "failure_reason": failure_reason,
        "recovery_reason": recovery_reason,
        "safe_evidence_ref": str(evidence_ref or "").strip(),
        "same_evidence_ref_required": True,
        "route_progress": {
            "present": route_progress_present,
            "evidence_ref": _route_progress_evidence_ref(route_progress),
        },
        "materials_status": {
            "status": "not_proven",
            "reason": "terminal completion rehearsal needs real field materials before any completion claim",
        },
        "operator_next_steps": [
            "Attach route status, task record, dropoff/cancel material, and completion signal with the same evidence_ref.",
            "Keep Robot/mobile summaries read-only until real field evidence is reviewed.",
        ],
        "phone_safe_summary": {
            "safe_copy": "Route/task terminal completion rehearsal is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_phone_copy": "Route/task terminal completion rehearsal is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        },
        "not_proven": list(TERMINAL_COMPLETION_REHEARSAL_NOT_PROVEN),
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def write_task_record(
    output_dir,
    task_id,
    machine,
    final_status,
    error_message,
    *,
    delivery_mode="",
    target=None,
    return_target="",
    nav_attempts=0,
    nav_results=None,
    dropoff_result=None,
    detection_snapshot_refs=None,
    elevator_assist=None,
    config=None,
    error_code=None,
    final_state=None,
    source="software_proof",
    result_path="",
    evidence_ref="",
    failure_code="",
    human_intervention_required=False,
    route_progress=None,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    started_at = machine.events[0].timestamp if machine.events else time.time()
    ended_at = machine.events[-1].timestamp if machine.events else started_at
    state_transitions = [
        {
            "timestamp": event.timestamp,
            "event": event.event.value,
            "from_state": event.from_state.value,
            "to_state": event.to_state.value,
            "message": event.message,
        }
        for event in machine.events
    ]
    nav_results = nav_results or []
    normalized_route_progress = (
        dict(route_progress)
        if isinstance(route_progress, dict) and route_progress
        else _route_progress_from_nav_results(nav_results)
    )
    route_progress_ref = _route_progress_evidence_ref(normalized_route_progress)
    payload_evidence_ref = str(evidence_ref or route_progress_ref or result_path).strip()
    if normalized_route_progress and "evidence_ref" not in normalized_route_progress and payload_evidence_ref:
        # task_record.route_progress 与顶层 evidence_ref 必须能指向同一轮软件证据。
        # 这里只补追踪字段，不改变 ROS action/topic/service 的运行时契约。
        normalized_route_progress["evidence_ref"] = payload_evidence_ref
    payload = {
        "task_id": task_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "delivery_mode": delivery_mode,
        "target": machine.target if target is None else target,
        "return_target": return_target,
        "nav_attempts": nav_attempts,
        "nav_results": nav_results,
        "dropoff_result": dropoff_result or {},
        "elevator_assist": elevator_assist or {
            "enabled": False,
            "mode": "",
            "state": "disabled",
            "phase": "disabled",
            "requires_human_help": False,
            "reason": "elevator assist disabled",
            "target_floor": "",
            "speaker_prompt": "",
            "evidence": {},
            "events": [],
        },
        "detection_snapshot_refs": detection_snapshot_refs or [],
        "config": config or {},
        "final_status": final_status,
        "error_code": (
            error_code
            if error_code is not None
            else (machine.events[-1].event.value if machine.events else "")
        ),
        "error_message": error_message,
        "final_state": final_state if final_state is not None else machine.state.value,
        "source": _normalize_task_record_source(source),
        "result_path": str(result_path),
        # evidence_ref 是 Task A artifact 与 replay 工具消费的稳定锚点。
        # route_progress 内已有锚点时优先保留，避免被 status 文件路径误当成实跑证据。
        "evidence_ref": payload_evidence_ref,
        "failure_code": failure_code,
        "human_intervention_required": bool(human_intervention_required),
        "route_progress": normalized_route_progress,
        "route_task_terminal_completion_rehearsal": _terminal_completion_rehearsal_summary(
            task_id=task_id,
            final_status=final_status,
            final_state=final_state if final_state is not None else machine.state.value,
            error_code=(
                error_code
                if error_code is not None
                else (machine.events[-1].event.value if machine.events else "")
            ),
            error_message=error_message,
            failure_code=failure_code,
            human_intervention_required=bool(human_intervention_required),
            evidence_ref=payload_evidence_ref,
            route_progress=normalized_route_progress,
            dropoff_result=dropoff_result,
        ),
        "duration": max(0.0, ended_at - started_at),
        "written_at": time.time(),
        "state_transitions": state_transitions,
        "state_transition_history": state_transitions,
    }
    path = output_dir / f"{task_id}.json"
    temp_path = path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(path)
    return path
