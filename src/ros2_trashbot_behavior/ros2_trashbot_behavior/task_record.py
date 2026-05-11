import json
from pathlib import Path
import time


VALID_TASK_RECORD_SOURCES = {"software_proof", "hil_pass"}


def _normalize_task_record_source(value):
    source = str(value or "").strip().lower().replace("-", "_")
    if source in VALID_TASK_RECORD_SOURCES:
        return source
    if source in {"task_orchestrator", "dry_run", "robot_sim", "simulated", "software", "software_proof"}:
        return "software_proof"
    if source == "hil":
        return "hil_pass"
    return "software_proof"


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
    payload = {
        "task_id": task_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "delivery_mode": delivery_mode,
        "target": machine.target if target is None else target,
        "return_target": return_target,
        "nav_attempts": nav_attempts,
        "nav_results": nav_results or [],
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
        # evidence_ref is the durable anchor consumed by diagnostics/operator contracts.
        # Keep it explicit even when it equals result_path to avoid implicit inference.
        "evidence_ref": str(evidence_ref or result_path).strip(),
        "failure_code": failure_code,
        "human_intervention_required": bool(human_intervention_required),
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
