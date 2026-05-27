import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


ARCHIVE_SCHEMA = "trashbot.archive.v1"
ANNOTATION_SCHEMA = "trashbot.annotation.v1"
INFERENCE_SCHEMA = "trashbot.inference.v1"
# 这组常量是安全边界，不从 CLI 覆盖，防止本地样本被误升格为真实证据。
SOURCE = "software_proof"
PROOF_STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_o6_o7_algorithm_evidence_feed"


def utc_timestamp():
    """O6/O7 时间线按字符串排序；统一 UTC Z 后缀便于离线 diff。"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _evidence_ref(uri, *, robot_id, task_id, kind="mock_object_ref"):
    """生成 O6 evidence_ref；这里故意使用 mock URI，避免被误认为真实 OSS。"""
    # O6 数据库存 object reference，不存图片或大日志正文；mock URI 只证明字段形状。
    return {
        "kind": kind,
        "uri": str(uri),
        "checksum": "",
        "source": SOURCE,
        "proof_status": PROOF_STATUS,
        "robot_id": robot_id,
        "task_id": task_id,
    }


def _route_frame(index, timestamp_ms, x_m, y_m, yaw_rad, speed_mps, state, evidence_uri):
    """O7 route replay 只需要白名单字段；帧 payload 不携带图片正文。"""
    # pose/velocity 按 O7 adapter 现有白名单组织，方便 route replay inspector 直接摘要。
    return {
        "frame_index": index,
        "timestamp_ms": timestamp_ms,
        "pose": {"x_m": x_m, "y_m": y_m, "yaw_rad": yaw_rad},
        "velocity": {"linear_mps": speed_mps},
        "state": state,
        "map_frame": "map",
        "evidence_ref": evidence_uri,
    }


def _archive_event(robot_id, task_id, event_id, event_type, created_at, evidence_uri, payload):
    """创建 Task A 兼容 event；所有算法样本都保持 software_proof/not_proven。"""
    # timestamp 与 created_at 保持一致，兼容 Task B robot-side event envelope。
    return {
        "robot_id": robot_id,
        "task_id": task_id,
        "event_id": event_id,
        "event_type": event_type,
        "created_at": created_at,
        "timestamp": created_at,
        "source": SOURCE,
        "proof_status": PROOF_STATUS,
        "evidence_ref": _evidence_ref(evidence_uri, robot_id=robot_id, task_id=task_id),
        "payload": dict(payload),
    }


def build_offline_algorithm_archive(robot_id="trashbot-dev", task_id="offline-algorithm-evidence-001"):
    """构造可被 O6 存档、O7 回放/标注消费的最小离线算法证据包。"""
    created_at = "2026-05-27T00:00:00Z"
    date = created_at[:10]
    route_id = "mock_route_elevator_floor_demo"
    # mock:// 避免触发 O7 adapter 对本机绝对路径、串口和凭证的安全扫描。
    base_ref = f"mock://o6-o7-algorithm-feed/{robot_id}/{task_id}"

    # 三帧轨迹覆盖起步、电梯门口等待、驶出电梯三个状态，便于 O7 回放检查。
    frames = [
        _route_frame(0, 0, 0.0, 0.0, 0.0, 0.00, "route_start", f"{base_ref}/route-frame-000.json"),
        _route_frame(1, 1200, 0.8, 0.1, 0.04, 0.18, "approach_elevator", f"{base_ref}/route-frame-001.json"),
        _route_frame(2, 2400, 1.2, 0.2, 0.06, 0.10, "exit_elevator_zone", f"{base_ref}/route-frame-002.json"),
    ]
    events = [
        # route_frame 事件的 payload 会被 Task C/O7 adapter 转成 trajectory_frames。
        _archive_event(robot_id, task_id, "offline-route-frame-000", "route_frame", "2026-05-27T00:00:00Z", f"{base_ref}/route-frame-000.json", frames[0]),
        _archive_event(robot_id, task_id, "offline-route-frame-001", "route_frame", "2026-05-27T00:00:01Z", f"{base_ref}/route-frame-001.json", frames[1]),
        _archive_event(
            robot_id,
            task_id,
            "offline-keyframe-001",
            "keyframe",
            "2026-05-27T00:00:02Z",
            f"{base_ref}/keyframe-elevator-door-open.jpg",
            {
                "keyframe_id": "keyframe-elevator-door-open",
                "media_ref": f"{base_ref}/keyframe-elevator-door-open.jpg",
                "route_frame_index": 1,
                "mock_capture": True,
            },
        ),
        # elevator_state payload 不写 state/evidence_ref，避免被 O7 误归入 trajectory sample。
        _archive_event(
            robot_id,
            task_id,
            "offline-elevator-state-001",
            "elevator_state",
            "2026-05-27T00:00:03Z",
            f"{base_ref}/elevator-door-floor-state.json",
            {
                "elevator_phase": "waiting_for_door",
                "door_state": "open_candidate",
                "floor_label": "F3_candidate",
                "confidence": 0.72,
                "human_help_required": True,
                "mock_capture": True,
            },
        ),
        # detection_result 提供障碍物标注种子，不声明真实检测准确率。
        _archive_event(
            robot_id,
            task_id,
            "offline-detection-result-001",
            "detection_result",
            "2026-05-27T00:00:04Z",
            f"{base_ref}/obstacle-label-sample.json",
            {
                "detection_id": "mock-obstacle-001",
                "label_type": "obstacle_type",
                "label_value": "temporary_box_candidate",
                "bbox_xywh_norm": [0.42, 0.58, 0.16, 0.20],
                "confidence": 0.61,
                "mock_capture": True,
            },
        ),
        _archive_event(robot_id, task_id, "offline-route-frame-002", "route_frame", "2026-05-27T00:00:05Z", f"{base_ref}/route-frame-002.json", frames[2]),
        # ASR/TTS stub 只给 PC 端检查语音字段槽位；不连接真实麦克风、云端语音或喇叭。
        _archive_event(
            robot_id,
            task_id,
            "offline-asr-partial-001",
            "asr_transcript",
            "2026-05-27T00:00:06Z",
            f"{base_ref}/asr-partial-001.json",
            {
                "event_type": "partial",
                "timestamp_ms": 6000,
                "transcript": "请等待电梯",
                "confidence": 0.54,
                "evidence_ref": f"{base_ref}/asr-partial-001.json",
                "mock_capture": True,
            },
        ),
        _archive_event(
            robot_id,
            task_id,
            "offline-asr-final-001",
            "asr_transcript",
            "2026-05-27T00:00:07Z",
            f"{base_ref}/asr-final-001.json",
            {
                "event_type": "final",
                "timestamp_ms": 7000,
                "transcript": "请帮我按三楼",
                "confidence": 0.82,
                "evidence_ref": f"{base_ref}/asr-final-001.json",
                "mock_capture": True,
            },
        ),
        _archive_event(
            robot_id,
            task_id,
            "offline-tts-draft-001",
            "tts_draft",
            "2026-05-27T00:00:08Z",
            f"{base_ref}/tts-draft-001.json",
            {
                "text": "请帮我按三楼，我会等待人工确认。",
                "voice_profile": "mock-operator-default",
                "language": "zh-CN",
                "evidence_ref": f"{base_ref}/tts-draft-001.json",
                "mock_capture": True,
            },
        ),
        # safe command stub 只覆盖 envelope 字段；PC 端必须继续显示不发送、不执行、不接 ACK。
        _archive_event(
            robot_id,
            task_id,
            "offline-command-manual-001",
            "safe_command_stub",
            "2026-05-27T00:00:09Z",
            f"{base_ref}/command-manual-001.json",
            {
                "command_id": "mock-manual-turn-001",
                "command_type": "manual_turn",
                "status": "draft_fixture_only",
                "requested_direction": "left",
                "envelope_ref": f"{base_ref}/manual-turn-envelope.json",
                "idempotency_key_ref": f"{base_ref}/idempotency-manual-001.json",
                "evidence_ref": f"{base_ref}/command-manual-001.json",
                "mock_capture": True,
            },
        ),
        _archive_event(
            robot_id,
            task_id,
            "offline-command-nav-001",
            "safe_command_stub",
            "2026-05-27T00:00:10Z",
            f"{base_ref}/command-nav-001.json",
            {
                "command_id": "mock-navigate-goal-001",
                "command_type": "navigate_goal",
                "status": "draft_fixture_only",
                "goal_source": "fixture_map_goal_slot",
                "map_frame": "map",
                "x_m": 1.2,
                "y_m": 0.2,
                "yaw_rad": 0.06,
                "envelope_ref": f"{base_ref}/navigate-goal-envelope.json",
                "idempotency_key_ref": f"{base_ref}/idempotency-nav-001.json",
                "evidence_ref": f"{base_ref}/command-nav-001.json",
                "mock_capture": True,
            },
        ),
    ]

    # 标注样本覆盖电梯门、楼层和障碍物三类，供 O7 labeling queue 形成 review sample。
    annotations = [
        _annotation_record(robot_id, task_id, "offline-annotation-door-001", "keyframe-elevator-door-open", "route-frame-001", f"{base_ref}/keyframe-elevator-door-open.jpg", "elevator_door_state", "open_candidate", f"{base_ref}/annotation-door-001.json"),
        _annotation_record(robot_id, task_id, "offline-annotation-floor-001", "floor-panel-candidate", "route-frame-001", f"{base_ref}/floor-panel-candidate.jpg", "floor_label", "F3_candidate", f"{base_ref}/annotation-floor-001.json"),
        _annotation_record(robot_id, task_id, "offline-annotation-obstacle-001", "mock-obstacle-001", "route-frame-002", f"{base_ref}/obstacle-label-sample.jpg", "obstacle_type", "temporary_box_candidate", f"{base_ref}/annotation-obstacle-001.json"),
    ]

    # 规则 stub 只输出候选值和解释，不能被标记为真实模型或鲁棒性提升。
    inferences = [
        _inference_record(robot_id, task_id, "offline-inference-door-001", "elevator_door_state", "offline_rule_stub/elevator_door_v0", "open_candidate", 0.72, "mock bright vertical gap heuristic", f"{base_ref}/inference-door-001.json"),
        _inference_record(robot_id, task_id, "offline-inference-floor-001", "floor_label", "offline_rule_stub/floor_text_v0", "F3_candidate", 0.64, "mock OCR token vote", f"{base_ref}/inference-floor-001.json"),
    ]

    return {
        # 顶层 false 字段让 O7 fail-closed UI 可以直接展示安全边界。
        "schema": ARCHIVE_SCHEMA,
        "source": SOURCE,
        "proof_status": PROOF_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "production_ready": False,
        "production_db_connected": False,
        "real_cloud_archive_connected": False,
        "real_realtime_api_connected": False,
        "mock_feed": True,
        "offline_only": True,
        "not_proven": [
            "real_route",
            "real_elevator",
            "real_floor_recognition",
            "real_model_runtime",
            "real_asr_tts_runtime",
            "real_safe_command_api",
            "real_robot_ack",
            "real_oss_upload",
            "real_o7_replay",
        ],
        "tasks": [
            {
                # task 只提供 O7 selector 与 replay 所需字段，不包含 action success 语义。
                "robot_id": robot_id,
                "task_id": task_id,
                "created_at": created_at,
                "date": date,
                "status": "offline_mock_bundle",
                "route_id": route_id,
                "map_frame": "map",
                "source": SOURCE,
                "proof_status": PROOF_STATUS,
                "evidence_ref": _evidence_ref(f"{base_ref}/task.json", robot_id=robot_id, task_id=task_id),
                "started_at_ms": 0,
                "updated_at_ms": 5000,
                "keyframe_refs": [f"{base_ref}/keyframe-elevator-door-open.jpg"],
                "allowed_label_types": ["elevator_door_state", "floor_label", "obstacle_type"],
            }
        ],
        "events": events,
        "annotations": annotations,
        "inferences": inferences,
    }


def _annotation_record(robot_id, task_id, annotation_id, item_id, frame_id, media_ref, label_type, label_value, evidence_uri):
    """标注记录只用于 O7 本地 review，不代表人工真值或训练集已可导出。"""
    # annotation_status 使用 draft_mock，避免被下游解释为人工审核完成。
    return {
        "schema": ANNOTATION_SCHEMA,
        "annotation_id": annotation_id,
        "robot_id": robot_id,
        "task_id": task_id,
        "item_id": item_id,
        "frame_id": frame_id,
        "media_ref": media_ref,
        "label_type": label_type,
        "label_value": label_value,
        "annotation_status": "draft_mock",
        "evidence_ref": _evidence_ref(evidence_uri, robot_id=robot_id, task_id=task_id),
    }


def _inference_record(robot_id, task_id, inference_id, inference_type, model_ref, value, confidence, reason, evidence_uri):
    """推理记录是轻量规则 stub，输出候选值但固定 not_proven。"""
    # model_ref 固定 offline_rule_stub 前缀，说明这是规则样例，不是云端模型 runtime。
    return {
        "schema": INFERENCE_SCHEMA,
        "inference_id": inference_id,
        "robot_id": robot_id,
        "task_id": task_id,
        "inference_type": inference_type,
        "inference_status": PROOF_STATUS,
        "model_ref": model_ref,
        "result": {"value": value, "confidence": confidence, "reason": reason},
        "evidence_ref": _evidence_ref(evidence_uri, robot_id=robot_id, task_id=task_id),
    }


def write_offline_algorithm_archive(output_path, *, robot_id="trashbot-dev", task_id="offline-algorithm-evidence-001"):
    """把 generator 输出写成格式化 JSON，便于 reviewer 和 O7 本地入口复验。"""
    archive = build_offline_algorithm_archive(robot_id=robot_id, task_id=task_id)
    path = Path(output_path).expanduser()
    # CLI 允许写临时目录，便于在 Docker/local 中生成 O7 可读取的 archive fixture。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return archive


def main(argv=None):
    # CLI 只暴露 robot/task/output 三个参数，证据边界由代码固定，避免误配置。
    parser = argparse.ArgumentParser(description="Generate offline O6/O7 algorithm evidence feed")
    parser.add_argument("--output", required=True, help="Output trashbot.archive.v1 JSON file")
    parser.add_argument("--robot-id", default="trashbot-dev")
    parser.add_argument("--task-id", default="offline-algorithm-evidence-001")
    args = parser.parse_args(argv)
    archive = write_offline_algorithm_archive(args.output, robot_id=args.robot_id, task_id=args.task_id)
    print(json.dumps({
        "schema": ARCHIVE_SCHEMA,
        "task_id": archive["tasks"][0]["task_id"],
        "event_count": len(archive["events"]),
        "annotation_count": len(archive["annotations"]),
        "inference_count": len(archive["inferences"]),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "mock_feed": True,
        "offline_only": True,
        "proof_status": PROOF_STATUS,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
