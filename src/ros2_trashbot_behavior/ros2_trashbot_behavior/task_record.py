import json
from pathlib import Path
import time


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
    config=None,
    error_code=None,
    final_state=None,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    started_at = machine.events[0].timestamp if machine.events else time.time()
    ended_at = machine.events[-1].timestamp if machine.events else started_at
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
        "duration": max(0.0, ended_at - started_at),
        "written_at": time.time(),
        "state_transitions": [
            {
                "timestamp": event.timestamp,
                "event": event.event.value,
                "from_state": event.from_state.value,
                "to_state": event.to_state.value,
                "message": event.message,
            }
            for event in machine.events
        ],
    }
    path = output_dir / f"{task_id}.json"
    temp_path = path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(path)
    return path
