import argparse
from datetime import datetime, timezone
import json
import pathlib
import uuid
import urllib.error
import urllib.request


ARCHIVE_EVENT_SCHEMA = "trashbot.archive.robot_event_envelope.v1"
ARCHIVE_EVENT_SOURCE = "software_proof"
ARCHIVE_EVENT_PROOF_STATUS = "not_proven"
ARCHIVE_EVENT_BOUNDARY = "software_proof_o6_board_event_publisher"
ARCHIVE_EVENT_TYPES = {
    "task_status",
    "elevator_state",
    "route_frame",
    "keyframe",
    "detection_result",
    "failure_reason",
}


def utc_timestamp():
    """云端按字符串排序时间线，因此统一使用 UTC ISO-8601 且保留 Z 后缀。"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_text(value):
    if value is None:
        return ""
    return str(value).strip()


def normalize_evidence_ref(value, *, robot_id="", task_id="", timestamp=""):
    """把本地路径、OSS 引用或已有 dict 收敛成 Task A 推荐的 evidence_ref 对象。"""
    if isinstance(value, dict):
        evidence_ref = dict(value)
    else:
        uri = _stable_text(value)
        evidence_ref = {
            "kind": "local_artifact_ref" if uri else "missing_ref",
            "uri": uri,
            "checksum": "",
        }
    # source/proof_status 必须固定，避免本地 mock 被上游误判为真实 OSS 证据。
    evidence_ref["source"] = ARCHIVE_EVENT_SOURCE
    evidence_ref["proof_status"] = ARCHIVE_EVENT_PROOF_STATUS
    if robot_id:
        evidence_ref.setdefault("robot_id", str(robot_id))
    if task_id:
        evidence_ref.setdefault("task_id", str(task_id))
    if timestamp:
        evidence_ref.setdefault("timestamp", str(timestamp))
    return evidence_ref


def build_archive_event(
    *,
    robot_id,
    task_id,
    event_type,
    evidence_ref,
    payload=None,
    timestamp=None,
    event_id=None,
):
    """创建机器人侧 O6 事件 envelope；字段保持 Task A archive event 兼容。"""
    event_timestamp = timestamp or utc_timestamp()
    normalized_type = _stable_text(event_type)
    if normalized_type not in ARCHIVE_EVENT_TYPES:
        raise ValueError(f"unsupported archive event_type: {normalized_type}")
    event_payload = payload if isinstance(payload, dict) else {}
    event_id = event_id or f"{task_id}-{normalized_type}-{uuid.uuid4().hex[:12]}"
    return {
        "schema": ARCHIVE_EVENT_SCHEMA,
        "event_id": event_id,
        "robot_id": _stable_text(robot_id),
        "task_id": _stable_text(task_id),
        "event_type": normalized_type,
        "timestamp": event_timestamp,
        "created_at": event_timestamp,
        "evidence_ref": normalize_evidence_ref(
            evidence_ref,
            robot_id=robot_id,
            task_id=task_id,
            timestamp=event_timestamp,
        ),
        "source": ARCHIVE_EVENT_SOURCE,
        "proof_status": ARCHIVE_EVENT_PROOF_STATUS,
        "evidence_boundary": ARCHIVE_EVENT_BOUNDARY,
        "payload": event_payload,
    }


def _event_payload_common(task_record):
    """抽取所有事件都需要的终态摘要，避免消费者只能解析 task_record 大对象。"""
    return {
        "final_status": _stable_text(task_record.get("final_status")),
        "final_state": _stable_text(task_record.get("final_state")),
        "error_code": _stable_text(task_record.get("error_code")),
        "failure_code": _stable_text(task_record.get("failure_code")),
        "source_record_schema": "trashbot.task_record.v1",
    }


def _route_progress_from_record(task_record):
    progress = task_record.get("route_progress")
    if isinstance(progress, dict) and progress:
        return dict(progress)
    # 旧记录可能只在 nav_results[-1].evidence.route_progress 里写进度。
    # 这里做只读兼容，不改变 task_record 的历史形态。
    for item in reversed(task_record.get("nav_results") or []):
        evidence = item.get("evidence") if isinstance(item, dict) else {}
        if not isinstance(evidence, dict):
            continue
        progress = evidence.get("route_progress")
        if isinstance(progress, dict) and progress:
            return dict(progress)
    return {}


def _keyframe_payloads(task_record, route_progress):
    payloads = []
    keyframe_dir = route_progress.get("keyframe_dir") if isinstance(route_progress, dict) else ""
    if keyframe_dir:
        payloads.append({"kind": "route_keyframe_dir", "keyframe_dir": keyframe_dir})
    for ref in task_record.get("keyframe_refs") or []:
        if ref:
            payloads.append({"kind": "keyframe_ref", "ref": str(ref)})
    return payloads


def task_record_to_archive_events(task_record, *, robot_id):
    """从 task_record 派生 O6 事件；只整理软件证据，不证明真实送达或硬件执行。"""
    if not isinstance(task_record, dict):
        raise TypeError("task_record must be a dict")
    task_id = _stable_text(task_record.get("task_id"))
    if not task_id:
        raise ValueError("task_record.task_id is required")
    evidence_ref = task_record.get("evidence_ref") or task_record.get("result_path") or ""
    common = _event_payload_common(task_record)
    events = [
        build_archive_event(
            robot_id=robot_id,
            task_id=task_id,
            event_type="task_status",
            evidence_ref=evidence_ref,
            payload={
                **common,
                "delivery_mode": _stable_text(task_record.get("delivery_mode")),
                "target": task_record.get("target"),
                "return_target": _stable_text(task_record.get("return_target")),
                "started_at": task_record.get("started_at"),
                "ended_at": task_record.get("ended_at"),
                "duration": task_record.get("duration"),
                "state_transition_count": len(task_record.get("state_transitions") or []),
            },
        )
    ]

    elevator = task_record.get("elevator_assist")
    if isinstance(elevator, dict) and (elevator.get("enabled") or elevator.get("events")):
        # 电梯事件必须保留 not_proven 边界，因为 dry-run 只证明流程路径。
        events.append(
            build_archive_event(
                robot_id=robot_id,
                task_id=task_id,
                event_type="elevator_state",
                evidence_ref=elevator.get("evidence_ref") or evidence_ref,
                payload={
                    **common,
                    "mode": _stable_text(elevator.get("mode")),
                    "state": _stable_text(elevator.get("state")),
                    "phase": _stable_text(elevator.get("phase")),
                    "target_floor": _stable_text(elevator.get("target_floor")),
                    "requires_human_help": bool(elevator.get("requires_human_help")),
                    "reason": _stable_text(elevator.get("reason") or elevator.get("failure_reason")),
                    "event_count": len(elevator.get("events") or []),
                },
            )
        )

    route_progress = _route_progress_from_record(task_record)
    if route_progress:
        events.append(
            build_archive_event(
                robot_id=robot_id,
                task_id=task_id,
                event_type="route_frame",
                evidence_ref=route_progress.get("evidence_ref") or evidence_ref,
                payload={
                    **common,
                    "route_progress": route_progress,
                    "nav_attempts": task_record.get("nav_attempts", 0),
                },
            )
        )

    for payload in _keyframe_payloads(task_record, route_progress):
        events.append(
            build_archive_event(
                robot_id=robot_id,
                task_id=task_id,
                event_type="keyframe",
                evidence_ref=payload.get("ref") or route_progress.get("evidence_ref") or evidence_ref,
                payload={**common, **payload},
            )
        )

    for index, ref in enumerate(task_record.get("detection_snapshot_refs") or []):
        if not ref:
            continue
        events.append(
            build_archive_event(
                robot_id=robot_id,
                task_id=task_id,
                event_type="detection_result",
                evidence_ref=ref,
                payload={**common, "snapshot_index": index, "snapshot_ref": str(ref)},
            )
        )

    final_status = _stable_text(task_record.get("final_status"))
    error_message = _stable_text(task_record.get("error_message"))
    failure_code = _stable_text(task_record.get("failure_code") or task_record.get("error_code"))
    if final_status not in ("", "success") or error_message or failure_code:
        events.append(
            build_archive_event(
                robot_id=robot_id,
                task_id=task_id,
                event_type="failure_reason",
                evidence_ref=evidence_ref,
                payload={
                    **common,
                    "reason": error_message or failure_code or "task did not report success",
                    "human_intervention_required": bool(task_record.get("human_intervention_required")),
                },
            )
        )
    return events


class ArchiveEventQueueClient:
    """本地 JSONL 队列加可选 HTTP POST；默认不访问公网，适合软件路径验证。"""

    def __init__(self, queue_path, *, archive_base_url="", bearer_token="", timeout_sec=2.0):
        self.queue_path = pathlib.Path(queue_path).expanduser()
        self.archive_base_url = _stable_text(archive_base_url).rstrip("/")
        self.bearer_token = _stable_text(bearer_token)
        self.timeout_sec = float(timeout_sec)

    def enqueue(self, event, *, reason="queued_without_archive_base_url", last_error=""):
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        # JSONL 便于后续 retry worker 逐行重放，也避免单个坏事件破坏整份 JSON。
        item = {
            "queued_at": utc_timestamp(),
            "delivery_status": "queued",
            "retry_stub": {
                "reason": reason,
                "last_error": last_error,
                "next_retry_policy": "manual_or_future_worker",
            },
            "event": event,
        }
        with self.queue_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
        return item

    def submit_event(self, event):
        if not self.archive_base_url:
            return self.enqueue(event)
        body = json.dumps(event).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        request = urllib.request.Request(
            f"{self.archive_base_url}/api/o6/archive/events",
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                payload = response.read().decode("utf-8") or "{}"
                return {
                    "delivery_status": "sent",
                    "http_status": response.status,
                    "response": json.loads(payload),
                }
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
            # 网络、授权或服务端不可用时只落本地队列，不能阻塞机器人任务终态写入。
            return self.enqueue(event, reason="archive_post_failed_retry_stub", last_error=str(exc))

    def submit_events(self, events):
        return [self.submit_event(event) for event in events]


def publish_task_record_archive_events(
    task_record_path,
    *,
    robot_id,
    queue_path,
    archive_base_url="",
    bearer_token="",
    timeout_sec=2.0,
):
    """读取 task_record 并发布/入队 O6 事件；返回本轮软件路径的发送摘要。"""
    path = pathlib.Path(task_record_path).expanduser()
    task_record = json.loads(path.read_text(encoding="utf-8"))
    events = task_record_to_archive_events(task_record, robot_id=robot_id)
    client = ArchiveEventQueueClient(
        queue_path,
        archive_base_url=archive_base_url,
        bearer_token=bearer_token,
        timeout_sec=timeout_sec,
    )
    deliveries = client.submit_events(events)
    return {
        "schema": "trashbot.archive.robot_event_publish_result.v1",
        "source": ARCHIVE_EVENT_SOURCE,
        "proof_status": ARCHIVE_EVENT_PROOF_STATUS,
        "evidence_boundary": ARCHIVE_EVENT_BOUNDARY,
        "task_record_path": str(path),
        "queue_path": str(client.queue_path),
        "event_count": len(events),
        "queued_count": sum(1 for item in deliveries if item.get("delivery_status") == "queued"),
        "sent_count": sum(1 for item in deliveries if item.get("delivery_status") == "sent"),
        "events": events,
        "deliveries": deliveries,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Publish O6 archive events from a trashbot task_record.")
    parser.add_argument("task_record_path")
    parser.add_argument("--robot-id", default="trashbot-dev")
    parser.add_argument("--queue-path", default="~/.ros/trashbot_o6_archive/events.jsonl")
    parser.add_argument("--archive-base-url", default="")
    parser.add_argument("--bearer-token", default="")
    args = parser.parse_args(argv)
    result = publish_task_record_archive_events(
        args.task_record_path,
        robot_id=args.robot_id,
        queue_path=args.queue_path,
        archive_base_url=args.archive_base_url,
        bearer_token=args.bearer_token,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["event_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
