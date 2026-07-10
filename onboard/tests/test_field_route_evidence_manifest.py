import json
import sqlite3
import tempfile
import unittest
import struct
from pathlib import Path

import sys


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
REPO_ROOT = Path(__file__).resolve().parents[2]
LOCALIZATION_PATH_MATERIAL_ARTIFACT = (
    REPO_ROOT / "sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/38_pc_summary_after_map_fix.json"
)
sys.path.insert(0, str(SCRIPT_DIR))

import field_route_evidence_manifest as manifest  # noqa: E402


def write_text(path: Path, text: str) -> None:
    # fixture 文件统一从这里创建，保证每个 artifact 都是非空证据材料。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_route_bag_db3(
    path: Path,
    *,
    topics: list[tuple[int, str, str]] | None = None,
    messages: list[tuple[int, int, int] | tuple[int, int, int, bytes | str]] | None = None,
    include_topics_table: bool = True,
    include_messages_table: bool = True,
) -> None:
    # DB3 fixture 只建 rosbag2 必需元数据列；默认 payload 为空，但也允许按需注入安全样本。
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    try:
        if include_topics_table:
            connection.execute(
                "CREATE TABLE topics(id INTEGER PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL, serialization_format TEXT NOT NULL, offered_qos_profiles TEXT NOT NULL)"
            )
            for topic_id, name, topic_type in topics or []:
                connection.execute(
                    "INSERT INTO topics(id, name, type, serialization_format, offered_qos_profiles) VALUES (?, ?, ?, 'cdr', '')",
                    (topic_id, name, topic_type),
                )
        if include_messages_table:
            connection.execute("CREATE TABLE messages(id INTEGER PRIMARY KEY, topic_id INTEGER NOT NULL, timestamp INTEGER NOT NULL, data BLOB NOT NULL)")
            for message in messages or []:
                if len(message) == 3:
                    message_id, topic_id, timestamp = message
                    payload = b""
                else:
                    message_id, topic_id, timestamp, payload = message
                    if isinstance(payload, str):
                        payload = payload.encode("utf-8")
                connection.execute(
                    "INSERT INTO messages(id, topic_id, timestamp, data) VALUES (?, ?, ?, ?)",
                    (message_id, topic_id, timestamp, sqlite3.Binary(bytes(payload))),
                )
        connection.commit()
    finally:
        connection.close()


def _pack_cdr_u32(value: int) -> bytes:
    # CDR 小样本写入统一走小端 u32，保持和解析器端一致。
    return struct.pack("<I", int(value))


def _pack_cdr_u64(value: int) -> bytes:
    # 某些 ROS 消息 header 使用 64 位字段，补齐时需同构造器一致的对齐语义。
    return struct.pack("<Q", int(value))


def _pack_cdr_float32(value: float) -> bytes:
    # 语义摘要只验证数值提取边界，不关心浮点精度抖动。
    return struct.pack("<f", float(value))


def _pack_cdr_float64(value: float) -> bytes:
    # 位姿与 tf transform 使用 float64，因此这里显式按 64 位打包。
    return struct.pack("<d", float(value))


def _pack_cdr_string(value: str) -> bytes:
    # CDR string 先写长度（含末尾 NUL），再写 UTF-8 内容，长度 0 视为空字符串。
    data = value.encode("utf-8")
    return _pack_cdr_u32(len(data) + 1) + data + b"\x00"


def _pack_cdr_bytes(payload: bytes, align: int) -> bytes:
    # 对齐后再写入字节，方便在不引入正式 CDR 库的情况下生成可解析样本。
    if align <= 1:
        return payload
    pad = (align - (len(payload) % align)) % align
    return payload + (b"\x00" * pad)


def build_laserscan_cdr_payload(*, angle_min: float, angle_max: float, angle_increment: float, range_min: float, range_max: float, ranges: list[float]) -> bytes:
    # 仅构造本轮 test 需要的 LaserScan 最小语义字段，不输出 intensity 数据。
    payload = bytearray()
    payload.extend(_pack_cdr_u32(1))
    payload.extend(_pack_cdr_u32(2))
    payload.extend(_pack_cdr_u32(3))
    payload.extend(_pack_cdr_string("map"))
    payload.extend(_pack_cdr_float32(angle_min))
    payload.extend(_pack_cdr_float32(angle_max))
    payload.extend(_pack_cdr_float32(angle_increment))
    payload.extend(_pack_cdr_float32(0.0))
    payload.extend(_pack_cdr_float32(0.0))
    payload.extend(_pack_cdr_float32(range_min))
    payload.extend(_pack_cdr_float32(range_max))
    payload.extend(_pack_cdr_u32(len(ranges)))
    for item in ranges:
        payload.extend(_pack_cdr_float32(item))
    payload.extend(_pack_cdr_u32(0))
    return bytes(_pack_cdr_bytes(bytes(payload), 4))


def build_image_cdr_payload(*, width: int, height: int, encoding: str, step: int, data: bytes) -> bytes:
    # Image 样本只需要最少字段，图像内容长度可作为 data_size 被聚合验证。
    payload = bytearray()
    payload.extend(_pack_cdr_u32(1))
    payload.extend(_pack_cdr_u32(2))
    payload.extend(_pack_cdr_u32(3))
    payload.extend(_pack_cdr_string(""))
    payload.extend(_pack_cdr_u32(width))
    payload.extend(_pack_cdr_u32(height))
    payload.extend(_pack_cdr_string(encoding))
    payload.extend(struct.pack("<B", 0))
    payload.extend(_pack_cdr_u32(step))
    payload.extend(_pack_cdr_u32(len(data)))
    payload.extend(data)
    return bytes(_pack_cdr_bytes(bytes(payload), 4))


def build_tf_message_cdr_payload(
    *,
    frame_pairs: list[tuple[str, str]],
    translations: list[tuple[float, float, float]] | None = None,
) -> bytes:
    # TF 样本只写 frame ids 与 7 坐标/姿态占位字段，足够派生 transform_count 摘要。
    payload = bytearray()
    payload.extend(_pack_cdr_u32(1))
    payload.extend(_pack_cdr_u32(2))
    payload.extend(_pack_cdr_u32(3))
    payload.extend(_pack_cdr_string("tf_root"))
    payload.extend(_pack_cdr_u32(len(frame_pairs)))
    for index, (parent_frame_id, child_frame_id) in enumerate(frame_pairs):
        x_m, y_m, z_m = translations[index] if translations and index < len(translations) else (0.0, 0.0, 0.0)
        payload.extend(_pack_cdr_u32(0))
        payload.extend(_pack_cdr_u32(0))
        payload.extend(_pack_cdr_u32(0))
        payload.extend(_pack_cdr_string(parent_frame_id))
        payload.extend(_pack_cdr_string(child_frame_id))
        payload.extend(b"\x00" * ((8 - (len(payload) % 8)) % 8))
        payload.extend(_pack_cdr_bytes(_pack_cdr_float64(x_m), 8))
        payload.extend(_pack_cdr_float64(y_m))
        payload.extend(_pack_cdr_float64(z_m))
        payload.extend(_pack_cdr_float64(0.0))
        payload.extend(_pack_cdr_float64(0.0))
        payload.extend(_pack_cdr_float64(0.0))
        payload.extend(_pack_cdr_float64(0.0))
        payload.extend(_pack_cdr_float64(1.0))
    return bytes(_pack_cdr_bytes(bytes(payload), 8))


def build_odometry_cdr_payload(*, frame_id: str, child_frame_id: str, x: float, y: float, z: float = 0.0) -> bytes:
    # Odometry fixture 只写 frame pair 与平移值，便于验证 pose progress 只读摘要。
    payload = bytearray()
    payload.extend(_pack_cdr_u32(1))
    payload.extend(_pack_cdr_u32(2))
    payload.extend(_pack_cdr_u32(3))
    payload.extend(_pack_cdr_string(frame_id))
    payload.extend(_pack_cdr_string(child_frame_id))
    payload.extend(b"\x00" * ((8 - (len(payload) % 8)) % 8))
    payload.extend(_pack_cdr_float64(x))
    payload.extend(_pack_cdr_float64(y))
    payload.extend(_pack_cdr_float64(z))
    payload.extend(_pack_cdr_float64(0.0))
    payload.extend(_pack_cdr_float64(0.0))
    payload.extend(_pack_cdr_float64(0.0))
    payload.extend(_pack_cdr_float64(1.0))
    return bytes(_pack_cdr_bytes(bytes(payload), 8))


def _pad_cdr_alignment(payload: bytearray, alignment: int) -> None:
    # DiagnosticStatus 的 level 是 u8，后续 string 需要按 CDR 重新对齐到 4 字节。
    payload.extend(b"\x00" * ((alignment - (len(payload) % alignment)) % alignment))


def build_diagnostic_array_cdr_payload(*, statuses: list[dict[str, object]]) -> bytes:
    # DiagnosticArray fixture 覆盖 level/name/hardware_id/value 计数，不允许 message/value 原文出现在摘要。
    payload = bytearray()
    payload.extend(_pack_cdr_u32(1))
    payload.extend(_pack_cdr_u32(2))
    payload.extend(_pack_cdr_u32(3))
    payload.extend(_pack_cdr_string("diagnostic_frame"))
    _pad_cdr_alignment(payload, 4)
    payload.extend(_pack_cdr_u32(len(statuses)))
    for status in statuses:
        payload.extend(struct.pack("<B", int(status.get("level", 0))))
        _pad_cdr_alignment(payload, 4)
        payload.extend(_pack_cdr_string(str(status.get("name", ""))))
        _pad_cdr_alignment(payload, 4)
        payload.extend(_pack_cdr_string(str(status.get("message", ""))))
        _pad_cdr_alignment(payload, 4)
        payload.extend(_pack_cdr_string(str(status.get("hardware_id", ""))))
        _pad_cdr_alignment(payload, 4)
        values = status.get("values", [])
        payload.extend(_pack_cdr_u32(len(values) if isinstance(values, list) else 0))
        if isinstance(values, list):
            for item in values:
                key = str(item.get("key", "")) if isinstance(item, dict) else ""
                value = str(item.get("value", "")) if isinstance(item, dict) else ""
                _pad_cdr_alignment(payload, 4)
                payload.extend(_pack_cdr_string(key))
                _pad_cdr_alignment(payload, 4)
                payload.extend(_pack_cdr_string(value))
    return bytes(_pack_cdr_bytes(bytes(payload), 4))


def make_complete_fixture(root: Path) -> None:
    # 本地完整 fixture 只证明 artifact gate 逻辑，不伪装成真实现场路线成功。
    write_text(root / "map.yaml", "image: map.pgm\nresolution: 0.05\n")
    write_text(root / "map.pgm", "P5 1 1 255 0")
    write_text(root / "route.csv", "x,y,yaw\n0,0,0\n1,0,0\n")
    write_text(root / "manifest.json", '{"schema":"trashbot.vision_samples.v1","samples":[]}\n')
    write_text(root / "keyframes" / "0001.json", '{"x": 0, "y": 0}\n')
    write_text(root / "route_bag" / "metadata.yaml", "rosbag2_bagfile_information:\n")
    write_text(root / "fixed_route_replay.jsonl", '{"event":"start"}\n{"event":"done"}\n')


def make_real_bundle_fixture(root: Path, *, include_route_bag: bool = True) -> None:
    # 真实现场 bundle 走 map/route/keyframes 分层目录；测试必须覆盖这条 intake 路径。
    write_text(root / "map" / "trashbot_dynamic_odom_tf_map.yaml", "image: trashbot_dynamic_odom_tf_map.pgm\nresolution: 0.05\n")
    write_text(root / "map" / "trashbot_dynamic_odom_tf_map.pgm", "P5 1 1 255 0")
    write_text(root / "route" / "manifest.json", '{"schema":"trashbot.vision_samples.v1","samples":[{"sample_id":"route_keyframe_001"}]}\n')
    write_text(
        root / "route" / "route.csv",
        "\n".join(
            [
                "index,sec,nanosec,frame_id,x,y,z,qx,qy,qz,qw,frame",
                "0,1781025357,570312018,map,0.0,0.0,0.0,0.0,0.0,0.0,1.0,000.jpg",
                "1,1781025531,470292985,map,0.01050082056,0.0,0.0,0.0,0.0,0.0,1.0,001.jpg",
                "2,1781025531,820688003,map,0.0210126711,0.0,0.0,0.0,0.0,0.0,1.0,002.jpg",
            ]
        )
        + "\n",
    )
    write_text(root / "route" / "keyframes" / "000.json", '{"sample_ref":"vision_sample://keyframes/000.json"}\n')
    write_text(root / "route" / "keyframes" / "000.jpg", "jpg-000\n")
    write_text(root / "route" / "keyframes" / "001.json", '{"sample_ref":"vision_sample://keyframes/001.json"}\n')
    write_text(root / "route" / "keyframes" / "001.jpg", "jpg-001\n")
    write_text(root / "route" / "keyframes" / "002.json", '{"sample_ref":"vision_sample://keyframes/002.json"}\n')
    write_text(root / "route" / "keyframes" / "002.jpg", "jpg-002\n")
    write_text(
        root / "route" / "manifest.json",
        json.dumps(
            {
                "schema": "trashbot.vision_samples.v1",
                "samples": [
                    {
                        "sample_ref": "vision_sample://keyframes/000.json",
                        "context": {
                            "task_id": "",
                            "route_id": "dynamic_odom_tf_20260610",
                        },
                    }
                ],
            }
        )
        + "\n",
    )
    if include_route_bag:
        write_text(root / "route_bag" / "metadata.yaml", "rosbag2_bagfile_information:\n")


def write_preflight(path: Path, status: str, *, dry_run: bool = False, blocked_reason=None) -> None:
    # manifest 只读取 preflight 摘要字段，避免测试依赖完整 ROS2/SSH packet。
    payload = {
        "schema": "trashbot.board_field_evidence_preflight.v1",
        "status": status,
        "dry_run": dry_run,
        "blocked_reason": blocked_reason,
        "mode": "ssh",
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_existing_manifest(path: Path, **overrides) -> None:
    # 离线导入会读取现场包中已有 manifest；测试只放最小字段来验证安全 gate。
    payload = {
        "schema": manifest.SCHEMA,
        "gate_pass": True,
        "delivery_success": False,
        "safe_to_control": False,
        "primary_actions_enabled": False,
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload), encoding="utf-8")


def make_motion_log_fixture(root: Path, *, nonzero_cmd_vel: bool = True, nonzero_waypoint: bool = True) -> None:
    # remote_capture fixture 只证明现场日志可被摘要，不证明 Nav2 成功或 delivery 成功。
    cmd_vel = "0.03" if nonzero_cmd_vel else "0.0"
    waypoint_x = "0.17" if nonzero_waypoint else "0.00"
    write_text(
        root / "pulse_and_stop2.log",
        "\n".join(
            [
                "2026-06-10T01:18:47+08:00",
                "pulse2_start",
                "publisher: beginning loop",
                f"publishing #1: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x={cmd_vel}, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.0))",
                "2026-06-10T01:19:04+08:00",
                "pulse2_done",
            ]
        )
        + "\n",
    )
    write_text(
        root / "learn_launch.log",
        "\n".join(
            [
                "[INFO] [route_data_recorder]: Recording route data to /tmp/trashbot_dynamic_odom_tf_route",
                f"[INFO] [route_data_recorder]: Saved waypoint #17 at ({waypoint_x}, 0.00)",
                "[INFO] [slam_toolbox]: Message Filter dropping message: frame 'laser_frame'",
            ]
        )
        + "\n",
    )
    write_text(
        root / "odom_after_motion.txt",
        "\n".join(
            [
                "pose:",
                "  pose:",
                "    position:",
                "      x: 0.0",
                "      y: 0.0",
            ]
        )
        + "\n",
    )
    write_text(
        root / "tf_after_motion.txt",
        "\n".join(
            [
                "transform:",
                "  translation:",
                "    x: 0.0",
                "    y: 0.0",
            ]
        )
        + "\n",
    )


def write_nav2_goal_proof(path: Path, **overrides) -> None:
    # O11 proof fixture 只放允许摘要字段；真实日志路径/raw payload 必须由 fail-closed 测试覆盖。
    payload = {
        "schema": manifest.O11_NAV2_GOAL_PROOF_SCHEMA,
        "task_id": "proof_task_should_not_override_packet",
        "status": "goal_succeeded",
        "proof_status": "nav2_goal_succeeded_with_nonzero_base_feedback",
        "result_status": "succeeded",
        "result_status_code": 4,
        "goal_sent": True,
        "goal_accepted": True,
        "result_received": True,
        "nav2_goal_execution_proven": True,
        "base_motion_command_nonzero_proven": True,
        "base_command_mode": "ros",
        "requested_base_command_mode": "ros",
        "feedback_sample_count": 3,
        "robot_control_executed": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "goal_request": {"frame_id": "map", "x": 0.17, "y": 0.02, "yaw": 0.0},
        "base_feedback_summary": {
            "wheel_feedback_lr_nonzero_proven": True,
            "nonzero_sample_count": 2,
            "imu_attitude_delta_observed": True,
        },
        "base_command_summary": {
            "nonzero_command_observed": True,
            "nonzero_command_count": 4,
            "latest_nonzero_command_mode": "ros",
        },
    }
    payload.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_delivery_result_json(path: Path, **overrides) -> None:
    # delivery result fixture 只表达 mock/operator claim，不允许把真实成功、路径或凭证带进 additive。
    payload = {
        "schema": manifest.DELIVERY_RESULT_SOURCE_SCHEMA,
        "record_status": "operator_confirmed_dropoff",
        "delivery_result_claimed": True,
        "operator_confirmation_present": True,
        "dropoff_confirmation_type": "operator_ack",
        "completed_at_utc": "2026-07-09T08:00:00Z",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
    }
    payload.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_cloud_terminal_result_json(path: Path, **overrides) -> None:
    # O5 terminal result fixture 只表达云端软件终态，不允许把真实送达成功或敏感 ref 带进 manifest。
    payload = {
        "schema": manifest.CLOUD_COMMAND_TERMINAL_RESULT_SCHEMA,
        "schema_version": 1,
        "robot_id": "trashbot-001",
        "command_id": "safe_command_ref",
        "terminal_result_type": "dropoff_terminal",
        "terminal_result_state": "completed",
        "result_code": "dropoff_terminal_completed",
        "error_code": "",
        "task_record_ref": "safe_task_record_ref",
        "evidence_ref": "safe_evidence_ref",
        "completed_at": "2026-07-09T16:00:00+08:00",
        "source": "robot_remote_bridge",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "real_world_delivery_proven": False,
    }
    payload.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_cloud_terminal_reconciliation_json(path: Path, **overrides) -> None:
    # reconciliation fixture 只允许 recorded + nested direct terminal_result 进入摘要，其余状态都应 fail-closed。
    terminal_result_provided = "terminal_result" in overrides
    terminal_result = overrides.pop("terminal_result", None)
    if not terminal_result_provided:
        terminal_result = {
            "schema": manifest.CLOUD_COMMAND_TERMINAL_RESULT_SCHEMA,
            "schema_version": 1,
            "command_id": "safe_command_ref",
            "terminal_result_type": "dropoff_terminal",
            "task_terminal_state": "completed",
            "result_code": "dropoff_terminal_completed",
            "task_record_ref": "safe_task_record_ref",
            "evidence_ref": "safe_evidence_ref",
            "completed_at": "2026-07-09T16:00:00+08:00",
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
            "real_world_delivery_proven": False,
        }
    payload = {
        "schema": manifest.CLOUD_COMMAND_RESULT_RECONCILIATION_SCHEMA,
        "capability": "cloud_command_result_reconciliation",
        "evidence_boundary": "software_proof_docker_cloud_command_result_reconciliation_gate",
        "robot_id": "trashbot-001",
        "command_id": "safe_command_ref",
        "command_state": "terminal_result_recorded",
        "ack_state": "ack_recorded",
        "result_state": "terminal_result_recorded",
        "terminal_result": terminal_result,
        "terminal_result_type": "dropoff_terminal",
        "task_terminal_state": "completed",
        "result_code": "dropoff_terminal_completed",
        "task_record_ref": "safe_task_record_ref",
        "evidence_ref": "safe_evidence_ref",
        "delivery_success": False,
        "safe_to_control": False,
        "primary_actions_enabled": False,
        "real_world_delivery_proven": False,
    }
    payload.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_field_operator_confirmation_json(path: Path, **overrides) -> None:
    # operator confirmation fixture 只表达人工报告安全摘要，不输出操作者身份原文或备注正文。
    payload = {
        "schema": "trashbot.upper_robot_api.v1.operator_report_latest",
        "task_id": "field_operator_confirmation_ready",
        "operator_report_id": "operator-material-001",
        "operator_id": "operator-on-duty-a",
        "operator_report_present": True,
        "operator_report_status": "loaded",
        "operator_confirmation_present": True,
        "operator_confirmation_status": "confirmed",
        "operator_present": True,
        "physical_clearance_confirmed": True,
        "emergency_stop_ready": True,
        "observed_motion": True,
        "observed_stop": True,
        "reported_at": "2026-07-10T07:22:00Z",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "route_execution_success": False,
        "hil_pass": False,
        "connects_cloud_production": False,
    }
    payload.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_current_field_evidence_json(path: Path, **overrides) -> None:
    # current evidence fixture 贴近 2026-06-11 上位机 summary 形状，只保留安全摘要字段。
    payload = {
        "schema": "trashbot.pc_tools_workstation.robot_control_summary.v1",
        "console_status": "blocked",
        "observed_at_ms": 1781113175864,
        "read_endpoints": [
            {
                "id": "camera_health",
                "endpoint": "/api/camera/health",
                "http_status": 200,
                "request_status": "loaded",
                "schema": "trashbot.local_webrtc_camera_smoke.v1",
                "status": "ready",
                "evidence_ref": "camera-frame-visible",
                "key_values": {"safe_to_control": False},
                "blocked_reasons": [],
                "dangerous_true_fields": [],
            },
            {
                "id": "camera_devices",
                "endpoint": "/api/camera/devices",
                "http_status": 200,
                "request_status": "loaded",
                "schema": "trashbot.local_webrtc_camera_devices.v1",
                "status": "loaded",
                "evidence_ref": "camera-devices-loaded",
                "key_values": {},
                "blocked_reasons": [],
                "dangerous_true_fields": [],
            },
            {
                "id": "radar_status",
                "endpoint": "/api/radar/status",
                "http_status": 200,
                "request_status": "loaded",
                "schema": "trashbot.upper_robot_api.v1.radar_status",
                "status": "scan_once_hz_raw_packet_tf_observed",
                "evidence_ref": "radar-scan-observed",
                "key_values": {"safe_to_control": False, "delivery_success": False, "primary_actions_enabled": False},
                "blocked_reasons": [],
                "dangerous_true_fields": [],
            },
            {
                "id": "radar_scan_proof_latest",
                "endpoint": "/api/radar/scan-proof/latest",
                "http_status": 200,
                "request_status": "loaded",
                "schema": "trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result",
                "status": "loaded",
                "evidence_ref": "radar-scan-proof",
                "key_values": {"safe_to_control": False, "delivery_success": False, "primary_actions_enabled": False},
                "blocked_reasons": [],
                "dangerous_true_fields": [],
            },
            {
                "id": "radar_raw_packet_proof_latest",
                "endpoint": "/api/radar/raw-packet-proof/latest",
                "http_status": 200,
                "request_status": "loaded",
                "schema": "trashbot.upper_robot_api.v1.lidar_raw_packet_proof_latest_result",
                "status": "loaded",
                "evidence_ref": "radar-raw-packet-proof",
                "key_values": {"safe_to_control": False, "delivery_success": False, "primary_actions_enabled": False},
                "blocked_reasons": [],
                "dangerous_true_fields": [],
            },
            {
                "id": "map_proof_latest",
                "endpoint": "/api/map/proof/latest",
                "http_status": 200,
                "request_status": "loaded",
                "schema": "trashbot.upper_robot_api.v1.map_lifecycle_proof_latest",
                "status": "map_once_artifact_metadata_observed",
                "evidence_ref": "map-proof-loaded",
                "key_values": {"safe_to_control": False, "delivery_success": False, "primary_actions_enabled": False},
                "blocked_reasons": [],
                "dangerous_true_fields": [],
            },
            {
                "id": "nav2_status",
                "endpoint": "/api/nav2/status",
                "http_status": 200,
                "request_status": "loaded",
                "schema": "trashbot.upper_robot_api.v1.nav2_lifecycle_status",
                "status": "not_proven",
                "evidence_ref": "nav2-no-motion-path",
                "key_values": {"safe_to_control": False, "delivery_success": False, "primary_actions_enabled": False},
                "blocked_reasons": [],
                "dangerous_true_fields": [],
            },
            {
                "id": "nav2_proof_latest",
                "endpoint": "/api/nav2/proof/latest",
                "http_status": 200,
                "request_status": "loaded",
                "schema": "trashbot.upper_robot_api.v1.nav2_runtime_proof_latest",
                "status": "not_proven",
                "evidence_ref": "nav2-probe-loaded",
                "key_values": {
                    "safe_to_control": False,
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "path_generated": True,
                    "path_point_count": 31,
                },
                "blocked_reasons": [],
                "dangerous_true_fields": [],
            },
            {
                "id": "operator_report_latest",
                "endpoint": "/api/operator/report",
                "http_status": 200,
                "request_status": "loaded",
                "schema": "trashbot.upper_robot_api.v1.operator_report_latest_result",
                "status": "ready_for_execution",
                "evidence_ref": "manual-gate-material",
                "key_values": {"safe_to_control": False, "delivery_success": False, "primary_actions_enabled": False},
                "blocked_reasons": [],
                "dangerous_true_fields": [],
            },
            {
                "id": "base_status",
                "endpoint": "/api/base/status",
                "http_status": 200,
                "request_status": "loaded",
                "schema": "trashbot.upper_robot_api.v1.base_status",
                "status": "loaded",
                "evidence_ref": "base-status-loaded",
                "key_values": {"safe_to_control": False, "delivery_success": False, "primary_actions_enabled": False},
                "blocked_reasons": [],
                "dangerous_true_fields": [],
            },
            {
                "id": "base_feedback_samples_latest",
                "endpoint": "/api/base/feedback-samples/latest",
                "http_status": 200,
                "request_status": "loaded",
                "schema": "trashbot.upper_robot_api.v1.base_feedback_samples_latest_result",
                "status": "loaded",
                "evidence_ref": "base-feedback-loaded",
                "key_values": {"safe_to_control": False, "delivery_success": False, "primary_actions_enabled": False},
                "blocked_reasons": [],
                "dangerous_true_fields": [],
            },
        ],
        "o3_proof_summary": {
            "managed_runtime_started": True,
            "scan_once_observed": True,
            "map_once_observed": True,
            "amcl_pose_observed": True,
            "localization_tf_observed": None,
            "planner_server_active": True,
            "path_generation_requested": True,
            "path_generation_succeeded": True,
            "path_generated": True,
            "path_point_count": 31,
            "root_causes": [],
            "not_proven": ["Robot API proof fields not loaded", "delivery_success"],
        },
        "robot_api_connection": {
            "status": "blocked",
            "loaded_count": 8,
            "blocked_count": 5,
            "failed_count": 0,
            "schema_mismatch_count": 2,
            "dangerous_true_fields": [],
            "blocked_reasons": [],
            "last_refresh_ms": 1781113175864,
        },
        "readback_summary": {
            "camera": {
                "status": "ready",
                "devices_status": "loaded",
                "preview_status": "visible_frame_observed",
            },
            "lidar": {
                "status": "scan_once_hz_raw_packet_tf_observed",
                "latest_scan_proof_status": "loaded",
                "latest_raw_packet_proof_status": "loaded",
                "continuous_scan_status": "not_loaded",
                "lifecycle_running": "not_loaded",
                "lifecycle_state": "not_loaded",
                "continuous_window_observed": "not_loaded",
                "continuity_window_status": "not_loaded",
                "latest_scan_proof_fresh": "not_loaded",
            },
            "base": {
                "status": "loaded",
                "latest_feedback_status": "loaded",
                "feedback_ack_status": "not_loaded",
            },
        },
        "operator_hil_material_summary": {
            "status": "loaded",
            "source_endpoint_id": "operator_report_latest",
            "source_path": "operator_report_latest.structured_hil_claims",
            "report_status": "ready_for_execution",
            "evidence_ref": "current-field-evidence-20260611",
            "operator_present": True,
            "physical_clearance": True,
            "emergency_stop": True,
            "external_video": "true",
            "camera_visible": "true",
            "wheel_feedback": "false",
            "lidar_delta": "false",
            "route_map": "true",
            "delivery_claim": False,
            "site_state": "current_field_evidence_smoke",
        },
        "safe_command_boundary": {
            "manual_endpoint": "/api/base/manual",
            "stop_endpoint": "/api/base/stop",
            "cmd_vel_topic": "/cmd_vel",
            "nav2_goal": "Nav2 NavigateToPose locked",
            "map_start": "map start locked",
            "radar_start": "radar start locked",
            "keyboard_control": "keyboard control locked",
            "map_click_goal": "map click goal locked",
            "locked_reason": "requires safety lock, checklist, operator report materials, robot ACK, timeout/cancel/stop/recovery evidence before enablement",
            "manual_motion_entry_status": "controlled_jog_requires_hil_checklist_and_operator_report",
            "manual_motion_entry_label": "受控点动（需现场确认）",
            "allowed_directions": ["forward", "back", "left", "right", "stop"],
            "non_stop_requires_confirm_hil_checklist": True,
            "non_stop_requires_operator_report_preflight": True,
            "operator_report_preflight_endpoint": "/api/operator/report",
            "operator_report_preflight_required_fields": [
                "operator_present",
                "physical_clearance_confirmed",
                "emergency_stop_ready",
                "external_video_recorded",
                "external_video_ref",
                "visible_content_proven",
                "camera_artifacts_ref",
                "wheel_feedback_lr_nonzero_proven",
                "wheel_feedback_ref",
                "physical_motion_lidar_delta_proven",
                "scan_delta_ref",
            ],
            "speed_limit_mps": 0.12,
            "duration_limit_ms": 800,
            "hil_checklist": [
                {"id": "operator_ready", "label": "现场有人扶控并准备急停"},
                {"id": "clearance_confirmed", "label": "已确认小车周围无人和障碍"},
                {"id": "low_speed_only", "label": "本轮仅做低速短时点动"},
                {"id": "not_autonomy_mode", "label": "本轮不是自动导航任务"},
            ],
            "command_dispatch_enabled": False,
            "manual_control_enabled": False,
            "navigate_goal_enabled": False,
            "keyboard_control_enabled": False,
            "robot_control_executed": False,
        },
        "blocked_reasons": [],
        "not_proven": ["path_generated", "delivery_success"],
        "source": "software_proof",
        "proof_status": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "hil_pass": False,
        "connects_cloud_production": False,
    }
    payload.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_localization_path_material_json(path: Path, **overrides) -> None:
    # localization/path fixture 直接复用 O1 已收口的 38 号 summary，确保合同与当前历史材料一致。
    payload = json.loads(LOCALIZATION_PATH_MATERIAL_ARTIFACT.read_text(encoding="utf-8"))
    payload.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_clean_baseline_nav2_path_material_files(root: Path, **overrides) -> dict[str, Path]:
    # clean-baseline fixture 复用 2026-06-11 sprint 的 refresh/retry/latest/status/readback 形状，但只放安全白名单字段。
    refresh_payload = {
        "schema": manifest.CLEAN_BASELINE_NAV2_PATH_ALLOWED_SCHEMAS["refresh"],
        "task_id": "clean_baseline_nav2_path_material_ready",
        "status": "blocked_with_root_cause",
        "proof_status": None,
        "planner_server_active": False,
        "path_generation_requested": True,
        "path_generation_succeeded": False,
        "path_generated": False,
        "path_point_count": 0,
        "root_causes": ["tf_chain_missing_before_initialpose"],
        "blockers": [],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
    }
    retry_payload = {
        "schema": manifest.CLEAN_BASELINE_NAV2_PATH_ALLOWED_SCHEMAS["refresh"],
        "task_id": "clean_baseline_nav2_path_material_ready",
        "status": "refreshed",
        "proof_state": "nav2_no_motion_path_generation_runtime_observed",
        "managed_runtime_started": True,
        "managed_runtime_cleanup_ok": True,
        "initialpose_published": True,
        "amcl_pose_observed": True,
        "map_server_active": True,
        "amcl_active": True,
        "planner_server_active": True,
        "path_generation_succeeded": True,
        "path_generated": True,
        "path_point_count": 31,
        "root_causes": [],
        "blockers": [],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
    }
    latest_payload = {
        "schema": manifest.CLEAN_BASELINE_NAV2_PATH_ALLOWED_SCHEMAS["latest"],
        "task_id": "clean_baseline_nav2_path_material_ready",
        "status": "not_proven",
        "latest_proof_status": None,
        "latest_managed_runtime_started": None,
        "latest_managed_runtime_cleanup_ok": None,
        "latest_initialpose_published": None,
        "latest_amcl_pose_observed": None,
        "latest_map_server_active": None,
        "latest_amcl_active": None,
        "latest_planner_server_active": None,
        "latest_path_generation_succeeded": None,
        "latest_path_generated": None,
        "latest_path_point_count": None,
        "latest_root_causes": None,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
    }
    status_payload = {
        "schema": manifest.CLEAN_BASELINE_NAV2_PATH_ALLOWED_SCHEMAS["status"],
        "task_id": "clean_baseline_nav2_path_material_ready",
        "status": "not_proven",
        "proof_latest": {
            "latest_proof_status": "nav2_no_motion_path_generation_runtime_observed",
            "latest_managed_runtime_started": True,
            "latest_managed_runtime_cleanup_ok": True,
            "latest_initialpose_published": True,
            "latest_amcl_pose_observed": True,
            "latest_map_server_active": True,
            "latest_amcl_active": True,
            "latest_planner_server_active": True,
            "latest_path_generation_succeeded": True,
            "latest_path_generated": True,
            "latest_path_point_count": 31,
            "latest_root_causes": [],
        },
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
    }
    refresh_payload.update(overrides.get("refresh", {}))
    retry_payload.update(overrides.get("retry", {}))
    latest_payload.update(overrides.get("latest", {}))
    status_payload.update(overrides.get("status", {}))

    paths = {
        "refresh": root / "nav2_refresh_summary.json",
        "retry": root / "nav2_retry_summary.json",
        "latest": root / "nav2_latest_after_success.json",
        "status": root / "nav2_status_after_success.json",
        "txt": root / "nav2_success_readback_summary.txt",
        "between_cleanup": root / "between_retry_cleanup_readback.log",
        "post_cleanup": root / "post_success_cleanup_readback.log",
    }
    for key in ("refresh", "retry", "latest", "status"):
        payload = {
            "refresh": refresh_payload,
            "retry": retry_payload,
            "latest": latest_payload,
            "status": status_payload,
        }[key]
        write_text(paths[key], json.dumps(payload))
    write_text(
        paths["txt"],
        "\n".join(
            [
                "## retry response paths",
                "[\"latest_result\", \"proof\"]",
                "## latest success summary",
                json.dumps(latest_payload, ensure_ascii=False),
                "## status success summary",
                json.dumps(status_payload, ensure_ascii=False),
            ]
        )
        + "\n",
    )
    cleanup_text = "\n".join(
        [
            "remote_readback_phase=post_success_cleanup",
            "## target ps",
            "",
            "## ros2 node list",
            "",
            "## devices lsof/fuser",
            "-- /dev/ttyS5 lsof --",
            "-- /dev/ttyS5 fuser --",
            "-- /dev/ttyACM0 lsof --",
            "-- /dev/ttyACM0 fuser --",
            "",
            "## exact target ps after cleanup",
            "",
            "## ros2 node list after cleanup",
            "",
        ]
    )
    write_text(paths["between_cleanup"], cleanup_text + "\n")
    write_text(paths["post_cleanup"], cleanup_text + "\n")
    return paths


class FieldRouteEvidenceManifestTest(unittest.TestCase):
    def test_complete_local_fixture_passes_artifact_gate_but_not_delivery(self):
        # SSH blocker 不能第三次吞掉研发；完整 fixture 应能证明 manifest 软件路径。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            preflight = Path(tmpdir) / "preflight.json"
            make_complete_fixture(root)
            write_preflight(preflight, "blocked_ssh_unreachable", blocked_reason="blocked_ssh_unreachable")

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--preflight-json",
                    str(preflight),
                    "--output",
                    str(output),
                    "--run-id",
                    "unit_complete",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertEqual(packet["schema"], manifest.SCHEMA)
        self.assertTrue(packet["gate_pass"])
        self.assertTrue(packet["not_proven"])
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["delivery_success"])
        self.assertFalse(packet["primary_actions_enabled"])
        self.assertEqual(packet["blocked_reason"], "blocked_ssh_unreachable")
        self.assertTrue(packet["artifacts"]["keyframes"]["present"])
        self.assertGreater(packet["artifacts"]["rosbag"]["size_bytes"], 0)
        self.assertTrue(packet["artifacts"]["source_manifest"]["present"])
        self.assertEqual(packet["source_manifest"]["schema"], "trashbot.vision_samples.v1")
        self.assertEqual(packet["artifact_status"], "gated")
        self.assertEqual(packet["manifest_gate"]["status"], "gated")

    def test_input_alias_imports_offline_packet_directory(self):
        # tech-plan 验收命令使用 --input；它必须和 --artifact-root 进入同一条本地 intake 路径。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "packet"
            output = Path(tmpdir) / "manifest.json"
            make_complete_fixture(root)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--input",
                    str(root),
                    "--output",
                    str(output),
                    "--run-id",
                    "unit_input_alias",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertEqual(packet["artifact_root"], str(root))
        self.assertTrue(packet["gate_pass"])
        self.assertTrue(packet["not_proven"])
        self.assertEqual(packet["input_manifest"]["status"], "not_found")

    def test_missing_artifact_fails_closed_with_nonzero_rc(self):
        # 缺 route/replay 等必需材料时必须非零退出，方便 CI 或现场脚本 fail fast。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "missing"
            output = Path(tmpdir) / "manifest.json"
            preflight = Path(tmpdir) / "preflight.json"
            write_text(root / "map.yaml", "image: map.pgm\n")
            write_preflight(preflight, manifest.READY_PREFLIGHT_STATUS)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--preflight-json",
                    str(preflight),
                    "--output",
                    str(output),
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertFalse(packet["gate_pass"])
        self.assertEqual(packet["status"], "blocked_artifacts_missing")
        self.assertEqual(packet["blocked_reason"], "missing_required_artifact")
        self.assertFalse(packet["artifacts"]["route_csv"]["present"])

    def test_empty_keyframes_fail_closed(self):
        # keyframes 目录存在但没有图片/JSON 时仍是空证据，不能被目录名误导。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output = root / "manifest.json"
            preflight = root / "preflight.json"
            make_complete_fixture(root)
            for child in (root / "keyframes").iterdir():
                child.unlink()
            write_text(root / "keyframes" / "README.txt", "not a keyframe\n")
            write_preflight(preflight, manifest.READY_PREFLIGHT_STATUS)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--preflight-json",
                    str(preflight),
                    "--output",
                    str(output),
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertFalse(packet["gate_pass"])
        self.assertEqual(packet["status"], "blocked_artifacts_empty")
        self.assertEqual(packet["artifacts"]["keyframes"]["reason"], "no_keyframe_file")

    def test_schema_mismatch_field_evidence_manifest_fails_closed(self):
        # field evidence 旧输出带错 schema 时仍必须 fail closed，避免消费者误读旧契约。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "packet"
            output = Path(tmpdir) / "generated.json"
            make_complete_fixture(root)
            write_existing_manifest(root / "field_evidence_manifest.json", schema="trashbot.field_evidence_manifest.v0")

            rc = manifest.main(["--mode", "local", "--input", str(root), "--output", str(output)])
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertFalse(packet["gate_pass"])
        self.assertEqual(packet["status"], "blocked_existing_manifest_reuse")
        self.assertEqual(packet["blocked_reason"], "existing_manifest_schema_mismatch")
        self.assertEqual(packet["artifact_status"], "blocked")
        self.assertFalse(packet["delivery_success"])

    def test_route_source_manifest_schema_mismatch_is_upstream_evidence(self):
        # route/manifest.json 是路线采样 source manifest；vision_samples schema 不应阻断 field manifest 生成。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "bundle"
            output = Path(tmpdir) / "generated.json"
            derived = Path(tmpdir) / "derived_replay.jsonl"
            make_real_bundle_fixture(root, include_route_bag=True)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root / "route"),
                    "--map-yaml",
                    str(root / "map" / "trashbot_dynamic_odom_tf_map.yaml"),
                    "--map-pgm",
                    str(root / "map" / "trashbot_dynamic_odom_tf_map.pgm"),
                    "--derive-replay-jsonl",
                    str(derived),
                    "--output",
                    str(output),
                    "--run-id",
                    "unit_route_source_manifest",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertTrue(packet["gate_pass"])
        self.assertEqual(packet["status"], "field_evidence_manifest_ready_not_delivery_proof")
        self.assertEqual(packet["source_manifest"]["schema"], "trashbot.vision_samples.v1")
        self.assertEqual(packet["source_manifest"]["sample_count"], 1)
        self.assertEqual(packet["input_manifest"]["status"], "not_found")
        self.assertTrue(packet["artifacts"]["map_yaml"]["path"].endswith("trashbot_dynamic_odom_tf_map.yaml"))
        self.assertTrue(packet["artifacts"]["map_pgm"]["path"].endswith("trashbot_dynamic_odom_tf_map.pgm"))
        self.assertTrue(packet["artifacts"]["route_csv"]["path"].endswith("route.csv"))
        self.assertTrue(packet["artifacts"]["source_manifest"]["path"].endswith("manifest.json"))
        self.assertTrue(packet["artifacts"]["keyframes"]["path"].endswith("keyframes"))
        self.assertFalse(packet["artifacts"]["rosbag"]["required"])
        self.assertFalse(packet["artifacts"]["rosbag"]["present"])
        self.assertTrue(packet["artifacts"]["replay_jsonl"]["required"])
        self.assertTrue(packet["artifacts"]["replay_jsonl"]["present"])
        self.assertTrue(packet["route_root_seed_gate"]["enabled"])
        self.assertTrue(packet["not_proven"])
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["delivery_success"])
        self.assertFalse(packet["primary_actions_enabled"])

    def test_unsafe_existing_manifest_claim_fails_closed(self):
        # 离线 packet 不能自带 delivery/control 成功声明；真实控制与送达必须由后续现场验收证明。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "packet"
            output = Path(tmpdir) / "generated.json"
            make_complete_fixture(root)
            write_existing_manifest(root / "field_evidence_manifest.json", delivery_success=True, safe_to_control=True)

            rc = manifest.main(["--mode", "local", "--input", str(root), "--output", str(output)])
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertFalse(packet["gate_pass"])
        self.assertEqual(packet["blocked_reason"], "unsafe_existing_manifest_claim")
        self.assertEqual(packet["input_manifest"]["dangerous_true_fields"], ["delivery_success", "safe_to_control"])
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["primary_actions_enabled"])

    def test_dry_run_preflight_keeps_not_proven_even_with_complete_artifacts(self):
        # dry-run preflight 是模板证明；artifact 完整也不能解除 not_proven。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            preflight = Path(tmpdir) / "dry_preflight.json"
            make_complete_fixture(root)
            write_preflight(preflight, "dry_run_template_only_not_proven", dry_run=True)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--preflight-json",
                    str(preflight),
                    "--output",
                    str(output),
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertTrue(packet["gate_pass"])
        self.assertTrue(packet["not_proven"])
        self.assertFalse(packet["safe_to_control"])
        self.assertEqual(packet["blocked_reason"], "dry_run_template_only_not_proven")

    def test_ssh_command_is_read_only_and_uses_expected_port(self):
        # SSH 模式只运行远端 python 只读扫描，不包含 ros2 launch、cmd_vel 或导航命令。
        command = manifest.build_ssh_command("root@192.168.1.11", 37878, "/tmp/artifacts", 5)
        rendered = " ".join(command)

        self.assertEqual(command[0], "ssh")
        self.assertIn("-p", command)
        self.assertEqual(command[command.index("-p") + 1], "37878")
        self.assertEqual(command[-2], "root@192.168.1.11")
        self.assertIn("python3 -c", command[-1])
        self.assertIn("/tmp/artifacts", command[-1])
        self.assertNotIn("/cmd_vel", rendered)
        self.assertNotIn("ros2 launch", rendered)

    def test_real_bundle_layout_with_derived_replay_scans_generated_jsonl(self):
        # 真实 bundle 允许缺 replay 输入，但 derive 后应让 manifest 扫描到新文件。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "bundle"
            output = Path(tmpdir) / "manifest.json"
            derived = Path(tmpdir) / "derived_replay.jsonl"
            make_real_bundle_fixture(root, include_route_bag=True)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--input",
                    str(root),
                    "--derive-replay-jsonl",
                    str(derived),
                    "--output",
                    str(output),
                    "--run-id",
                    "unit_real_bundle_derive",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            replay_text = derived.read_text(encoding="utf-8")
            replay_lines = [json.loads(line) for line in replay_text.splitlines() if line.strip()]

        self.assertEqual(rc, 0)
        self.assertTrue(packet["gate_pass"])
        self.assertTrue(packet["artifacts"]["replay_jsonl"]["present"])
        self.assertEqual(packet["artifacts"]["replay_jsonl"]["path"], str(derived))
        self.assertTrue(packet["derived_replay"]["generated"])
        self.assertEqual(packet["derived_replay"]["frame_count"], 3)
        self.assertEqual(len(replay_lines), 3)
        self.assertEqual(replay_lines[0]["schema"], "trashbot.fixed_route_replay.v1")
        self.assertEqual(replay_lines[0]["event"], "route_frame")
        self.assertEqual(replay_lines[0]["timestamp_ms"], 1781025357570)
        self.assertEqual(replay_lines[1]["frame_index"], 1)
        self.assertEqual(replay_lines[1]["source_route_csv"], "field_route://route.csv")
        self.assertEqual(replay_lines[1]["evidence_ref"], "field_route://route/keyframes/001.jpg")
        self.assertFalse(replay_lines[1]["evidence_ref"].startswith("/"))
        self.assertNotIn("/cmd_vel", replay_text)
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["delivery_success"])
        self.assertFalse(packet["primary_actions_enabled"])

    def test_real_bundle_without_route_bag_stays_fail_closed_even_after_derive(self):
        # route_bag 缺失时必须 fail closed；derive replay 只能补 O7 回放材料，不能补 rosbag 证据。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "bundle"
            output = Path(tmpdir) / "manifest.json"
            derived = Path(tmpdir) / "derived_replay.jsonl"
            make_real_bundle_fixture(root, include_route_bag=False)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--input",
                    str(root),
                    "--derive-replay-jsonl",
                    str(derived),
                    "--output",
                    str(output),
                    "--run-id",
                    "unit_real_bundle_missing_bag",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertFalse(packet["gate_pass"])
        self.assertEqual(packet["status"], "blocked_artifacts_missing")
        self.assertEqual(packet["blocked_reason"], "missing_required_artifact")
        self.assertTrue(packet["derived_replay"]["generated"])
        self.assertEqual(packet["derived_replay"]["frame_count"], 3)
        self.assertFalse(packet["artifacts"]["rosbag"]["present"])
        self.assertTrue(packet["artifacts"]["rosbag"]["required"])
        self.assertTrue(packet["artifacts"]["replay_jsonl"]["present"])
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["delivery_success"])
        self.assertFalse(packet["primary_actions_enabled"])

    def test_real_bundle_without_replay_and_without_derive_stays_fail_closed(self):
        # 未启用 derive 且 bundle 内也没有 replay 文件时，replay_jsonl 必须继续作为必需材料阻断 gate。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "bundle"
            output = Path(tmpdir) / "manifest.json"
            make_real_bundle_fixture(root, include_route_bag=True)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--input",
                    str(root),
                    "--output",
                    str(output),
                    "--run-id",
                    "unit_real_bundle_missing_replay",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertFalse(packet["gate_pass"])
        self.assertEqual(packet["status"], "blocked_artifacts_missing")
        self.assertEqual(packet["blocked_reason"], "missing_required_artifact")
        self.assertTrue(packet["artifacts"]["rosbag"]["present"])
        self.assertTrue(packet["artifacts"]["rosbag"]["required"])
        self.assertFalse(packet["artifacts"]["replay_jsonl"]["present"])
        self.assertTrue(packet["artifacts"]["replay_jsonl"]["required"])
        self.assertFalse(packet["derived_replay"]["generated"])
        self.assertEqual(packet["derived_replay"]["blocked_reason"], "not_requested")

    def test_field_motion_packet_uses_live_motion_logs_when_route_bag_missing(self):
        # 现场 route-root seed 缺 route_bag 时，packet 仍可由 live motion log + route.csv 支撑 not-delivery proof。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "bundle"
            output = Path(tmpdir) / "manifest.json"
            derived = Path(tmpdir) / "derived_replay.jsonl"
            motion_logs = Path(tmpdir) / "remote_capture"
            make_real_bundle_fixture(root, include_route_bag=False)
            make_motion_log_fixture(motion_logs)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root / "route"),
                    "--map-yaml",
                    str(root / "map" / "trashbot_dynamic_odom_tf_map.yaml"),
                    "--map-pgm",
                    str(root / "map" / "trashbot_dynamic_odom_tf_map.pgm"),
                    "--motion-log-root",
                    str(motion_logs),
                    "--derive-replay-jsonl",
                    str(derived),
                    "--output",
                    str(output),
                    "--run-id",
                    "field_motion_evidence_packet_unit",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            motion_packet = packet["field_motion_evidence_packet"]

        self.assertEqual(rc, 0)
        self.assertEqual(motion_packet["schema"], manifest.FIELD_MOTION_PACKET_SCHEMA)
        self.assertEqual(motion_packet["proof_scope"], manifest.FIELD_MOTION_PACKET_PROOF_SCOPE)
        self.assertEqual(motion_packet["task_id"], "field_motion_evidence_packet_unit")
        self.assertEqual(motion_packet["task_id_source"], "run_id_fallback_due_missing_source_task_id")
        self.assertEqual(motion_packet["route_id"], "dynamic_odom_tf_20260610")
        self.assertTrue(motion_packet["route_summary"]["nonzero_displacement_observed"])
        self.assertEqual(motion_packet["route_summary"]["frame_count"], 3)
        self.assertTrue(motion_packet["motion_log_summary"]["live_motion_evidence_present"])
        self.assertTrue(motion_packet["motion_log_summary"]["live_nav2_log_present"])
        self.assertTrue(motion_packet["motion_log_summary"]["nonzero_cmd_vel_log_present"])
        self.assertFalse(motion_packet["motion_log_summary"]["direct_odom_capture_nonzero"])
        self.assertFalse(motion_packet["motion_log_summary"]["direct_tf_capture_nonzero"])
        self.assertTrue(motion_packet["route_bag_or_live_nav2_log"]["present"])
        self.assertEqual(motion_packet["route_bag_or_live_nav2_log"]["source"], "live_motion_log")
        self.assertEqual(motion_packet["derived_replay_summary"]["frame_count"], 3)
        self.assertIn("source_manifest_task_id_missing", motion_packet["blocked_reasons"])
        self.assertFalse(motion_packet["safe_to_control"])
        self.assertFalse(motion_packet["delivery_success"])
        self.assertFalse(motion_packet["primary_actions_enabled"])

    def test_nav2_goal_proof_ready_summary_is_additive_and_uses_packet_task_id(self):
        # O11 proof 的 task_id 不得覆盖 field packet lineage；控制执行字段也不能打开主动作。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--output",
                    str(output),
                    "--run-id",
                    "field_packet_task_id",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["nav2_goal_execution_evidence"]
            nested = packet["field_motion_evidence_packet"]["nav2_goal_execution_evidence"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA)
        self.assertEqual(evidence["proof_scope"], manifest.NAV2_GOAL_EXECUTION_EVIDENCE_PROOF_SCOPE)
        self.assertEqual(evidence["status"], "ready_not_delivery_proof")
        self.assertEqual(evidence["task_id"], "field_packet_task_id")
        self.assertEqual(evidence["task_id_source"], "run_id_fallback_due_missing_source_task_id")
        self.assertEqual(evidence["source_status"], "goal_succeeded")
        self.assertEqual(evidence["proof_status"], "nav2_goal_succeeded_with_nonzero_base_feedback")
        self.assertEqual(evidence["result_status"], "succeeded")
        self.assertEqual(evidence["result_status_code"], 4)
        self.assertTrue(evidence["goal_sent"])
        self.assertTrue(evidence["goal_accepted"])
        self.assertTrue(evidence["result_received"])
        self.assertTrue(evidence["nav2_goal_execution_proven"])
        self.assertTrue(evidence["base_motion_command_nonzero_proven"])
        self.assertEqual(evidence["base_command_mode"], "ros")
        self.assertEqual(evidence["requested_base_command_mode"], "ros")
        self.assertEqual(evidence["feedback_sample_count"], 3)
        self.assertEqual(evidence["goal_request"], {"frame_id": "map", "x": 0.17, "y": 0.02, "yaw": 0.0})
        self.assertTrue(evidence["base_feedback_summary"]["wheel_feedback_lr_nonzero_proven"])
        self.assertEqual(evidence["base_feedback_summary"]["nonzero_sample_count"], 2)
        self.assertTrue(evidence["base_feedback_summary"]["imu_attitude_delta_observed"])
        self.assertTrue(evidence["base_command_summary"]["nonzero_command_observed"])
        self.assertEqual(evidence["base_command_summary"]["nonzero_command_count"], 4)
        self.assertEqual(evidence["base_command_summary"]["latest_nonzero_command_mode"], "ros")
        self.assertIn("delivery_record_required_after_o11_execution_claim", evidence["next_required_evidence"])
        self.assertNotIn("proof_task_should_not_override_packet", json.dumps(evidence, ensure_ascii=False))
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(packet["field_motion_evidence_packet"]["robot_control_executed"])

    def test_nav2_goal_proof_schema_mismatch_fails_closed_without_breaking_artifact_gate(self):
        # proof schema 不匹配时只阻断 nav2_goal_execution_evidence，不把完整 artifact gate 改成失败。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof_schema_mismatch.json"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof, schema="trashbot.upper_robot_api.v0.nav2_goal_execution_proof")

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--output",
                    str(output),
                    "--run-id",
                    "schema_mismatch_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["nav2_goal_execution_evidence"]

        self.assertEqual(rc, 0)
        self.assertTrue(packet["gate_pass"])
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertEqual(evidence["source_schema"], "trashbot.upper_robot_api.v0.nav2_goal_execution_proof")
        self.assertIn("nav2_goal_proof_schema_mismatch", evidence["blocked_reasons"])
        self.assertFalse(evidence["nav2_goal_execution_proven"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_nav2_goal_proof_dangerous_true_and_unsafe_text_fail_closed_without_raw_echo(self):
        # 危险 true 与 path/raw/base64 文本只能产生安全 blocked 摘要，不能把原值写回 manifest。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof_unsafe.json"
            make_complete_fixture(root)
            write_nav2_goal_proof(
                proof,
                safe_to_control=True,
                debug_path="/root/secret/nav2_goal.json",
                raw_payload="base64:SECRET_PAYLOAD",
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--output",
                    str(output),
                    "--run-id",
                    "unsafe_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["nav2_goal_execution_evidence"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertIn("nav2_goal_proof_dangerous_true_claim", evidence["blocked_reasons"])
        self.assertIn("nav2_goal_proof_unsafe_field_or_text", evidence["blocked_reasons"])
        self.assertEqual(evidence["dangerous_true_fields"], ["safe_to_control"])
        self.assertGreaterEqual(evidence["unsafe_field_count"], 2)
        self.assertGreaterEqual(evidence["unsafe_text_field_count"], 2)
        self.assertNotIn("/root/secret", evidence_text)
        self.assertNotIn("SECRET_PAYLOAD", evidence_text)
        self.assertNotIn("raw_payload", evidence_text)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_delivery_result_ready_summary_is_additive_and_nested_under_field_motion_packet(self):
        # delivery result 只允许把白名单摘要挂到 manifest 顶层和 field packet，不覆盖 packet lineage。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            delivery_result = Path(tmpdir) / "delivery_result.json"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_delivery_result_json(delivery_result)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--delivery-result-json",
                    str(delivery_result),
                    "--output",
                    str(output),
                    "--run-id",
                    "field_packet_task_id",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["delivery_result_evidence"]
            nested = packet["field_motion_evidence_packet"]["delivery_result_evidence"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.DELIVERY_RESULT_EVIDENCE_SCHEMA)
        self.assertEqual(evidence["proof_scope"], manifest.DELIVERY_RESULT_EVIDENCE_PROOF_SCOPE)
        self.assertEqual(evidence["status"], "ready_not_delivery_proof")
        self.assertEqual(evidence["task_id"], "field_packet_task_id")
        self.assertEqual(evidence["task_id_source"], "run_id_fallback_due_missing_source_task_id")
        self.assertTrue(evidence["record_present"])
        self.assertTrue(evidence["record_read_ok"])
        self.assertEqual(evidence["record_status"], "operator_confirmed_dropoff")
        self.assertTrue(evidence["delivery_result_claimed"])
        self.assertTrue(evidence["operator_confirmation_present"])
        self.assertEqual(evidence["dropoff_confirmation_type"], "operator_ack")
        self.assertEqual(evidence["completed_at_utc"], "2026-07-09T08:00:00Z")
        self.assertTrue(evidence["linked_nav2_goal_execution_proven"])
        self.assertEqual(evidence["blocked_reasons"], [])
        self.assertIn("same_task_delivery_record_review", evidence["next_required_evidence"])
        self.assertNotIn("proof_task_should_not_override_packet", json.dumps(evidence, ensure_ascii=False))
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_delivery_result_missing_input_returns_blocked_summary_without_breaking_artifact_gate(self):
        # delivery result 缺失时只阻断 additive，不改变 artifact gate 的通过状态。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            make_complete_fixture(root)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--output",
                    str(output),
                    "--run-id",
                    "delivery_result_missing_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["delivery_result_evidence"]

        self.assertEqual(rc, 0)
        self.assertTrue(packet["gate_pass"])
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertFalse(evidence["record_present"])
        self.assertFalse(evidence["record_read_ok"])
        self.assertIn("delivery_result_json_missing", evidence["blocked_reasons"])
        self.assertIn("safe_delivery_result_json_for_selected_task", evidence["next_required_evidence"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_delivery_result_schema_mismatch_fails_closed_without_raw_echo(self):
        # schema mismatch 只能产出 blocked 摘要，方便 O6/O7 明确还缺正确合同。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            delivery_result = Path(tmpdir) / "delivery_result_schema_mismatch.json"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_delivery_result_json(delivery_result, schema="trashbot.delivery_result.v0")

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--delivery-result-json",
                    str(delivery_result),
                    "--output",
                    str(output),
                    "--run-id",
                    "delivery_result_schema_mismatch_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["delivery_result_evidence"]

        self.assertEqual(rc, 0)
        self.assertTrue(packet["gate_pass"])
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertEqual(evidence["source_schema"], "trashbot.delivery_result.v0")
        self.assertIn("delivery_result_schema_mismatch", evidence["blocked_reasons"])
        self.assertFalse(evidence["delivery_result_claimed"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_delivery_result_dangerous_true_and_unsafe_text_fail_closed_without_raw_echo(self):
        # delivery result 命中危险 true、路径和带凭证 URL 时必须只输出安全 blocked 摘要。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            delivery_result = Path(tmpdir) / "delivery_result_unsafe.json"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_delivery_result_json(
                delivery_result,
                robot_control_executed=True,
                attachment_path="/Users/m1/secret/delivery_result.json",
                callback_url="https://robot:supersecret@example.com/callback",
                raw_payload="base64:SECRET_DELIVERY_RESULT",
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--delivery-result-json",
                    str(delivery_result),
                    "--output",
                    str(output),
                    "--run-id",
                    "delivery_result_unsafe_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["delivery_result_evidence"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertIn("delivery_result_dangerous_true_claim", evidence["blocked_reasons"])
        self.assertIn("delivery_result_unsafe_field_or_text", evidence["blocked_reasons"])
        self.assertEqual(evidence["dangerous_true_fields"], ["robot_control_executed"])
        self.assertGreaterEqual(evidence["unsafe_field_count"], 2)
        self.assertGreaterEqual(evidence["unsafe_text_field_count"], 3)
        self.assertNotIn("/Users/m1/secret", evidence_text)
        self.assertNotIn("supersecret", evidence_text)
        self.assertNotIn("SECRET_DELIVERY_RESULT", evidence_text)
        self.assertNotIn("callback_url", evidence_text)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_cloud_terminal_result_ready_summary_is_delivery_result_evidence_source(self):
        # O5 终态结果只能作为 delivery_result_evidence 安全来源，不能覆盖 manifest 的 task_id。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            terminal_result = Path(tmpdir) / "cloud_terminal_result.json"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_cloud_terminal_result_json(terminal_result)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--cloud-terminal-result-json",
                    str(terminal_result),
                    "--output",
                    str(output),
                    "--run-id",
                    "cloud_terminal_delivery_bridge_task",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["delivery_result_evidence"]
            nested = packet["field_motion_evidence_packet"]["delivery_result_evidence"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.DELIVERY_RESULT_EVIDENCE_SCHEMA)
        self.assertEqual(evidence["source"], "cloud_command_terminal_result")
        self.assertEqual(evidence["source_schema"], manifest.CLOUD_COMMAND_TERMINAL_RESULT_SCHEMA)
        self.assertEqual(evidence["status"], "ready_not_delivery_proof")
        self.assertEqual(evidence["task_id"], "cloud_terminal_delivery_bridge_task")
        self.assertEqual(evidence["record_status"], "completed")
        self.assertTrue(evidence["delivery_result_claimed"])
        self.assertTrue(evidence["operator_confirmation_present"])
        self.assertEqual(evidence["dropoff_confirmation_type"], "cloud_dropoff_terminal")
        self.assertEqual(evidence["completed_at_utc"], "2026-07-09T08:00:00Z")
        self.assertEqual(evidence["command_id_ref"], "safe_command_ref")
        self.assertEqual(evidence["task_record_ref"], "safe_task_record_ref")
        self.assertEqual(evidence["evidence_ref"], "safe_evidence_ref")
        self.assertEqual(evidence["blocked_reasons"], [])
        self.assertNotIn("trashbot-001", json.dumps(evidence, ensure_ascii=False))
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_cloud_terminal_result_schema_mismatch_fails_closed(self):
        # schema 不匹配时只保留安全来源摘要，不能把 O5 终态误接为 delivery_result_evidence ready。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            terminal_result = Path(tmpdir) / "cloud_terminal_schema_mismatch.json"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_cloud_terminal_result_json(terminal_result, schema="trashbot.cloud_command_terminal_result.v0")

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--cloud-terminal-result-json",
                    str(terminal_result),
                    "--output",
                    str(output),
                    "--run-id",
                    "cloud_terminal_schema_mismatch_task",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["delivery_result_evidence"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["source"], "cloud_command_terminal_result")
        self.assertEqual(evidence["source_schema"], "trashbot.cloud_command_terminal_result.v0")
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertIn("cloud_terminal_result_schema_mismatch", evidence["blocked_reasons"])
        self.assertFalse(evidence["delivery_result_claimed"])
        self.assertFalse(evidence["delivery_success"])

    def test_cloud_terminal_result_dangerous_true_and_unsafe_refs_fail_closed_without_raw_echo(self):
        # terminal ref 出现路径、URL、token/raw/base64 时只输出计数和字段名，不能回显敏感值。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            terminal_result = Path(tmpdir) / "cloud_terminal_unsafe.json"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_cloud_terminal_result_json(
                terminal_result,
                delivery_success=True,
                task_record_ref="/Users/m1/secret/task_record.json",
                evidence_ref="https://example.com/private/evidence.json",
                raw_payload="base64:SECRET_CLOUD_TERMINAL_RESULT",
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--cloud-terminal-result-json",
                    str(terminal_result),
                    "--output",
                    str(output),
                    "--run-id",
                    "cloud_terminal_unsafe_task",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["delivery_result_evidence"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["source"], "cloud_command_terminal_result")
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertIn("cloud_terminal_result_dangerous_true_claim", evidence["blocked_reasons"])
        self.assertIn("cloud_terminal_result_unsafe_field_or_text", evidence["blocked_reasons"])
        self.assertIn("delivery_success", evidence["dangerous_true_fields"])
        self.assertGreaterEqual(evidence["unsafe_field_count"], 1)
        self.assertGreaterEqual(evidence["unsafe_text_field_count"], 3)
        self.assertNotIn("/Users/m1/secret", evidence_text)
        self.assertNotIn("https://example.com/private", evidence_text)
        self.assertNotIn("SECRET_CLOUD_TERMINAL_RESULT", evidence_text)
        self.assertNotIn("raw_payload", evidence_text)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_cloud_terminal_reconciliation_recorded_wrapper_is_normalized_to_delivery_result_evidence(self):
        # reconciliation v2 只在 recorded + nested direct terminal_result 合法时转成同一 delivery_result_evidence 合同。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            reconciliation = Path(tmpdir) / "cloud_terminal_reconciliation.json"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_cloud_terminal_reconciliation_json(reconciliation)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--cloud-terminal-result-json",
                    str(reconciliation),
                    "--output",
                    str(output),
                    "--run-id",
                    "cloud_terminal_reconciliation_task",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["delivery_result_evidence"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["source"], "cloud_command_terminal_result")
        self.assertEqual(evidence["source_schema"], manifest.CLOUD_COMMAND_TERMINAL_RESULT_SCHEMA)
        self.assertEqual(evidence["status"], "ready_not_delivery_proof")
        self.assertEqual(evidence["task_id"], "cloud_terminal_reconciliation_task")
        self.assertEqual(evidence["record_status"], "completed")
        self.assertTrue(evidence["delivery_result_claimed"])
        self.assertTrue(evidence["operator_confirmation_present"])
        self.assertEqual(evidence["dropoff_confirmation_type"], "cloud_dropoff_terminal")
        self.assertEqual(evidence["completed_at_utc"], "2026-07-09T08:00:00Z")
        self.assertEqual(evidence["command_id_ref"], "safe_command_ref")
        self.assertEqual(evidence["task_record_ref"], "safe_task_record_ref")
        self.assertEqual(evidence["evidence_ref"], "safe_evidence_ref")
        self.assertEqual(evidence["blocked_reasons"], [])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_cloud_terminal_reconciliation_non_recorded_state_fails_closed(self):
        # pending/missing/store_unavailable 不能借 wrapper 顶层字段伪装成已完成 delivery result。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            reconciliation = Path(tmpdir) / "cloud_terminal_reconciliation_pending.json"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_cloud_terminal_reconciliation_json(
                reconciliation,
                command_state="terminal_result_pending",
                result_state="terminal_result_pending",
                terminal_result=None,
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--cloud-terminal-result-json",
                    str(reconciliation),
                    "--output",
                    str(output),
                    "--run-id",
                    "cloud_terminal_reconciliation_pending_task",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["delivery_result_evidence"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertIn("cloud_terminal_result_reconciliation_result_state_not_recorded", evidence["blocked_reasons"])
        self.assertIn("cloud_terminal_result_reconciliation_terminal_result_missing", evidence["blocked_reasons"])
        self.assertIn("recorded_reconciliation_terminal_result", evidence["next_required_evidence"])
        self.assertIn("nested_cloud_terminal_result", evidence["next_required_evidence"])
        self.assertFalse(evidence["delivery_result_claimed"])
        self.assertFalse(evidence["delivery_success"])

    def test_cloud_terminal_reconciliation_task_alignment_and_unsafe_refs_fail_closed_without_raw_echo(self):
        # wrapper task 对不齐或 nested ref 不安全时，只输出 blocked 摘要，不能回显 token/path/raw/base64。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            reconciliation = Path(tmpdir) / "cloud_terminal_reconciliation_unsafe.json"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_cloud_terminal_reconciliation_json(
                reconciliation,
                task_id="other-task",
                terminal_result={
                    "schema": manifest.CLOUD_COMMAND_TERMINAL_RESULT_SCHEMA,
                    "command_id": "safe_command_ref",
                    "terminal_result_type": "dropoff_terminal",
                    "task_terminal_state": "completed",
                    "result_code": "dropoff_terminal_completed",
                    "task_record_ref": "/Users/m1/secret/task_record.json",
                    "evidence_ref": "base64:SECRET_RECON_EVIDENCE",
                    "completed_at": "2026-07-09T16:00:00+08:00",
                    "safe_to_control": False,
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "robot_control_executed": False,
                    "real_world_delivery_proven": False,
                },
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--cloud-terminal-result-json",
                    str(reconciliation),
                    "--output",
                    str(output),
                    "--run-id",
                    "cloud_terminal_reconciliation_alignment_task",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["delivery_result_evidence"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertIn("cloud_terminal_result_reconciliation_task_id_mismatch", evidence["blocked_reasons"])
        self.assertNotIn("/Users/m1/secret", evidence_text)
        self.assertNotIn("SECRET_RECON_EVIDENCE", evidence_text)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_route_execution_result_delivery_readiness_ready_summary_is_additive_and_nested_under_field_motion_packet(self):
        # 结果链 readiness 需要同一 task_id 下同时具备 nav2、pose progress、delivery result 和 operator confirmation 摘要。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            delivery_result = Path(tmpdir) / "delivery_result.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_delivery_result_json(delivery_result)
            write_route_bag_db3(
                db3,
                topics=[
                    (1, "/tf", "tf2_msgs/msg/TFMessage"),
                    (2, "/odom", "nav_msgs/msg/Odometry"),
                ],
                messages=[
                    (1, 1, 1781020583610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.0, 0.0, 0.0)],
                    )),
                    (2, 1, 1781020584610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.3, 0.4, 0.0)],
                    )),
                    (3, 2, 1781020585610099932, build_odometry_cdr_payload(
                        frame_id="map",
                        child_frame_id="base_link",
                        x=0.3,
                        y=0.4,
                    )),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--delivery-result-json",
                    str(delivery_result),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--route-bag-source-label",
                    "unit-route-execution-result-delivery-readiness",
                    "--output",
                    str(output),
                    "--run-id",
                    "route_execution_result_delivery_readiness_task",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_execution_result_delivery_readiness"]
            nested = packet["field_motion_evidence_packet"]["route_execution_result_delivery_readiness"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA)
        self.assertEqual(evidence["proof_scope"], manifest.ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_PROOF_SCOPE)
        self.assertEqual(evidence["status"], "route_execution_result_delivery_readiness_ready_not_delivery_proof")
        self.assertEqual(evidence["task_id"], "route_execution_result_delivery_readiness_task")
        self.assertEqual(evidence["task_id_source"], "run_id_fallback_due_missing_source_task_id")
        self.assertEqual(evidence["route_execution_result_status"], "ready_not_delivery_proof")
        self.assertEqual(evidence["route_execution_source"], "nav2_goal_execution_evidence+route_bag_pose_progress_replay")
        self.assertTrue(evidence["route_execution_result_ready"])
        self.assertFalse(evidence["route_execution_success"])
        self.assertEqual(evidence["delivery_result_readiness_status"], "ready_not_delivery_proof")
        self.assertTrue(evidence["delivery_result_readiness_ready"])
        self.assertEqual(evidence["operator_confirmation_readiness_status"], "ready_not_delivery_proof")
        self.assertTrue(evidence["operator_confirmation_readiness_ready"])
        self.assertTrue(evidence["linked_nav2_goal_execution_proven"])
        self.assertTrue(evidence["linked_delivery_result_claimed"])
        self.assertTrue(evidence["linked_operator_confirmation_present"])
        self.assertEqual(evidence["blocked_reasons"], [])
        self.assertIn("real_route_execution_result_delivery_acceptance", evidence["next_required_evidence"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_route_execution_result_delivery_readiness_missing_inputs_returns_blocked_summary(self):
        # 缺少 nav2 proof、pose progress 和 delivery result 时，结果链摘要必须整体 blocked。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            make_complete_fixture(root)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_execution_result_delivery_readiness_missing",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_execution_result_delivery_readiness"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertEqual(evidence["route_execution_result_status"], "blocked_not_proven")
        self.assertFalse(evidence["route_execution_result_ready"])
        self.assertFalse(evidence["delivery_result_readiness_ready"])
        self.assertFalse(evidence["operator_confirmation_readiness_ready"])
        self.assertIn("linked_nav2_goal_execution_evidence_not_ready", evidence["blocked_reasons"])
        self.assertIn("linked_route_bag_pose_progress_replay_not_ready", evidence["blocked_reasons"])
        self.assertIn("linked_delivery_result_evidence_not_ready", evidence["blocked_reasons"])
        self.assertIn("linked_nav2_goal_execution_evidence", evidence["next_required_evidence"])
        self.assertIn("linked_route_bag_pose_progress_replay", evidence["next_required_evidence"])
        self.assertIn("same_task_delivery_result_record", evidence["next_required_evidence"])
        self.assertIn("same_task_operator_confirmation", evidence["next_required_evidence"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_route_execution_result_delivery_readiness_conflicting_delivery_claim_stays_blocked(self):
        # operator confirmation 先到、delivery claim 缺失时不能被解释成结果链 ready。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            delivery_result = Path(tmpdir) / "delivery_result_conflict.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_delivery_result_json(
                delivery_result,
                record_status="pending_review",
                delivery_result_claimed=False,
                operator_confirmation_present=True,
                dropoff_confirmation_type="operator_ack",
            )
            write_route_bag_db3(
                db3,
                topics=[(1, "/tf", "tf2_msgs/msg/TFMessage")],
                messages=[
                    (1, 1, 1781020583610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.0, 0.0, 0.0)],
                    )),
                    (2, 1, 1781020584610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.3, 0.4, 0.0)],
                    )),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--delivery-result-json",
                    str(delivery_result),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_execution_result_delivery_conflict",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_execution_result_delivery_readiness"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertTrue(evidence["route_execution_result_ready"])
        self.assertFalse(evidence["delivery_result_readiness_ready"])
        self.assertFalse(evidence["operator_confirmation_readiness_ready"])
        self.assertTrue(evidence["linked_nav2_goal_execution_proven"])
        self.assertFalse(evidence["linked_delivery_result_claimed"])
        self.assertTrue(evidence["linked_operator_confirmation_present"])
        self.assertIn("linked_delivery_result_evidence_not_ready", evidence["blocked_reasons"])
        self.assertIn("delivery_result_readiness_not_ready", evidence["blocked_reasons"])
        self.assertIn("operator_confirmation_readiness_not_ready", evidence["blocked_reasons"])
        self.assertIn("operator_confirmation_present_without_delivery_result_claim", evidence["blocked_reasons"])

    def test_route_delivery_closure_packet_ready_summary_is_additive_and_nested_under_field_motion_packet(self):
        # closure packet 只表示同一 task_id 的软件证据闭合，不表示真实送达成功。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            delivery_result = Path(tmpdir) / "delivery_result.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_delivery_result_json(delivery_result)
            write_route_bag_db3(
                db3,
                topics=[
                    (1, "/tf", "tf2_msgs/msg/TFMessage"),
                    (2, "/odom", "nav_msgs/msg/Odometry"),
                ],
                messages=[
                    (1, 1, 1781020583610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.0, 0.0, 0.0)],
                    )),
                    (2, 1, 1781020584610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.3, 0.4, 0.0)],
                    )),
                    (3, 2, 1781020585610099932, build_odometry_cdr_payload(
                        frame_id="map",
                        child_frame_id="base_link",
                        x=0.3,
                        y=0.4,
                    )),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--delivery-result-json",
                    str(delivery_result),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--route-bag-source-label",
                    "unit-route-delivery-closure",
                    "--output",
                    str(output),
                    "--run-id",
                    "route_delivery_closure_task",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_delivery_closure_packet"]
            nested = packet["field_motion_evidence_packet"]["route_delivery_closure_packet"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA)
        self.assertEqual(evidence["proof_scope"], manifest.ROUTE_DELIVERY_CLOSURE_PACKET_PROOF_SCOPE)
        self.assertEqual(evidence["status"], "route_delivery_closure_ready_not_success_proof")
        self.assertEqual(evidence["task_id"], "route_delivery_closure_task")
        self.assertEqual(evidence["task_id_source"], "run_id_fallback_due_missing_source_task_id")
        self.assertTrue(evidence["closure_ready"])
        self.assertEqual(evidence["linked_nav2_goal_status"], "ready_not_delivery_proof")
        self.assertEqual(evidence["linked_delivery_result_status"], "ready_not_delivery_proof")
        self.assertEqual(
            evidence["linked_route_execution_result_status"],
            "route_execution_result_delivery_readiness_ready_not_delivery_proof",
        )
        self.assertEqual(evidence["linked_pose_progress_status"], "ready_not_live_nav2_proof")
        self.assertEqual(evidence["linked_route_execution_source"], "nav2_goal_execution_evidence+route_bag_pose_progress_replay")
        self.assertTrue(evidence["linked_nav2_goal_execution_proven"])
        self.assertTrue(evidence["linked_delivery_result_claimed"])
        self.assertTrue(evidence["linked_operator_confirmation_present"])
        self.assertTrue(evidence["linked_nonzero_pose_progress_observed"])
        self.assertTrue(evidence["linked_route_execution_result_ready"])
        self.assertTrue(evidence["linked_delivery_result_readiness_ready"])
        self.assertTrue(evidence["linked_operator_confirmation_readiness_ready"])
        self.assertEqual(evidence["blocked_reasons"], [])
        self.assertEqual(evidence["next_required_evidence"], ["real_route_delivery_success_proof"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["route_execution_success"])

    def test_route_delivery_closure_packet_task_mismatch_or_unsafe_text_stays_blocked(self):
        # closure packet 命中 task mismatch 或 unsafe text 时必须 blocked，且不能回显敏感文本。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            delivery_result = Path(tmpdir) / "delivery_result.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_delivery_result_json(delivery_result)
            write_route_bag_db3(
                db3,
                topics=[(1, "/tf", "tf2_msgs/msg/TFMessage")],
                messages=[
                    (1, 1, 1781020583610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.0, 0.0, 0.0)],
                    )),
                    (2, 1, 1781020584610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.3, 0.4, 0.0)],
                    )),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--delivery-result-json",
                    str(delivery_result),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_delivery_closure_task_mismatch",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            packet["route_execution_result_delivery_readiness"]["task_id"] = "other-task"
            packet["route_execution_result_delivery_readiness"]["route_execution_source"] = "/root/secret/nav2.log"
            evidence = manifest.build_route_delivery_closure_packet(packet)
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertFalse(evidence["closure_ready"])
        self.assertIn("route_execution_result_delivery_readiness_task_id_mismatch", evidence["blocked_reasons"])
        self.assertIn("route_execution_result_delivery_readiness_unsafe_text", evidence["blocked_reasons"])
        self.assertIn("linked_route_execution_result_delivery_readiness", evidence["next_required_evidence"])
        self.assertIn("same_task_route_delivery_closure_inputs", evidence["next_required_evidence"])
        self.assertNotIn("/root/secret", evidence_text)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["route_execution_success"])

    def test_same_task_mission_evidence_gate_ready_consumes_cloud_terminal_and_route_links(self):
        # same-task gate 必须消费 O5 terminal result 来源和路线 linked additive，而不是读取 raw cloud/route payload。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            terminal_result = Path(tmpdir) / "cloud_terminal_result.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_cloud_terminal_result_json(terminal_result)
            write_route_bag_db3(
                db3,
                topics=[
                    (1, "/tf", "tf2_msgs/msg/TFMessage"),
                    (2, "/odom", "nav_msgs/msg/Odometry"),
                ],
                messages=[
                    (1, 1, 1781020583610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.0, 0.0, 0.0)],
                    )),
                    (2, 1, 1781020584610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.3, 0.4, 0.0)],
                    )),
                    (3, 2, 1781020585610099932, build_odometry_cdr_payload(
                        frame_id="map",
                        child_frame_id="base_link",
                        x=0.3,
                        y=0.4,
                    )),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--cloud-terminal-result-json",
                    str(terminal_result),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--route-bag-source-label",
                    "unit-same-task-mission-gate",
                    "--output",
                    str(output),
                    "--run-id",
                    "same_task_mission_gate_task",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["same_task_mission_evidence_gate"]
            nested = packet["field_motion_evidence_packet"]["same_task_mission_evidence_gate"]
            delivery_evidence = packet["delivery_result_evidence"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA)
        self.assertEqual(evidence["proof_scope"], manifest.SAME_TASK_MISSION_EVIDENCE_GATE_PROOF_SCOPE)
        self.assertEqual(evidence["status"], "same_task_mission_gate_ready_not_success_proof")
        self.assertEqual(evidence["task_id"], "same_task_mission_gate_task")
        self.assertTrue(evidence["same_task_mission_gate_ready"])
        self.assertEqual(delivery_evidence["source_schema"], manifest.CLOUD_COMMAND_TERMINAL_RESULT_SCHEMA)
        self.assertEqual(evidence["terminal_refs"]["command_id_ref"], "safe_command_ref")
        self.assertEqual(evidence["terminal_refs"]["task_record_ref"], "safe_task_record_ref")
        self.assertEqual(evidence["terminal_refs"]["evidence_ref"], "safe_evidence_ref")
        self.assertTrue(evidence["linked_readiness_flags"]["same_task_id_matched"])
        self.assertTrue(evidence["linked_readiness_flags"]["cloud_terminal_result_source_consumed"])
        self.assertTrue(evidence["linked_readiness_flags"]["route_execution_result_delivery_readiness_ready"])
        self.assertTrue(evidence["linked_readiness_flags"]["route_delivery_closure_ready"])
        self.assertTrue(evidence["linked_readiness_flags"]["nonzero_pose_progress_observed"])
        self.assertTrue(evidence["same_task_id_consumed"])
        self.assertFalse(evidence["live_or_field_command_executed"])
        self.assertEqual(evidence["support_only_reason"], "local_or_mock_same_task_artifacts_only")
        self.assertFalse(evidence["okr_credit_allowed"])
        self.assertTrue(evidence["mission_artifact_delta"]["same_task_id_consumed"])
        self.assertTrue(evidence["mission_artifact_delta"]["same_task_field_material_consumed"])
        self.assertTrue(evidence["mission_artifact_delta"]["same_task_terminal_result_linked_to_route_execution"])
        self.assertFalse(evidence["mission_artifact_delta"]["live_or_field_command_executed"])
        self.assertEqual(evidence["mission_artifact_delta"]["support_only_reason"], "local_or_mock_same_task_artifacts_only")
        self.assertFalse(evidence["mission_artifact_delta"]["okr_credit_allowed"])
        self.assertFalse(evidence["mission_artifact_delta"]["delivery_success_delta"])
        self.assertFalse(evidence["mission_artifact_delta"]["production_cloud_evidence_delta"])
        self.assertEqual(evidence["blocked_reasons"], [])
        self.assertIn("real_same_task_mission_success_proof", evidence["next_required_evidence"])
        self.assertIn("production_cloud_or_live_route_execution_acceptance", evidence["next_required_evidence"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["route_execution_success"])

    def test_same_task_mission_evidence_gate_blocks_task_source_and_unsafe_drift_without_secret_echo(self):
        # gate 复核所有 linked summary 的 task/source/unsafe 状态，避免 closure ready 被包装成 mission success。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            terminal_result = Path(tmpdir) / "cloud_terminal_result.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_cloud_terminal_result_json(terminal_result)
            write_route_bag_db3(
                db3,
                topics=[(1, "/tf", "tf2_msgs/msg/TFMessage")],
                messages=[
                    (1, 1, 1781020583610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.0, 0.0, 0.0)],
                    )),
                    (2, 1, 1781020584610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.3, 0.4, 0.0)],
                    )),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--cloud-terminal-result-json",
                    str(terminal_result),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--output",
                    str(output),
                    "--run-id",
                    "same_task_mission_gate_blocked",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            packet["delivery_result_evidence"]["source_schema"] = manifest.DELIVERY_RESULT_SOURCE_SCHEMA
            packet["route_delivery_closure_packet"]["task_id"] = "other-task"
            packet["route_execution_result_delivery_readiness"]["route_execution_source"] = "/Users/m1/token/secret_nav2.log"
            packet["route_bag_pose_progress_replay"]["unsafe_field_count"] = 1
            evidence = manifest.build_same_task_mission_evidence_gate(packet)
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertFalse(evidence["same_task_mission_gate_ready"])
        self.assertFalse(evidence["linked_readiness_flags"]["same_task_id_matched"])
        self.assertFalse(evidence["linked_readiness_flags"]["cloud_terminal_result_source_consumed"])
        self.assertIn("delivery_result_evidence_source_schema_mismatch", evidence["blocked_reasons"])
        self.assertIn("route_delivery_closure_packet_task_id_mismatch", evidence["blocked_reasons"])
        self.assertIn("route_execution_result_delivery_readiness_unsafe_text", evidence["blocked_reasons"])
        self.assertIn("route_bag_pose_progress_replay_unsafe_summary", evidence["blocked_reasons"])
        self.assertFalse(evidence["same_task_id_consumed"])
        self.assertFalse(evidence["live_or_field_command_executed"])
        self.assertEqual(evidence["support_only_reason"], "same_task_id_mismatch_or_missing")
        self.assertFalse(evidence["okr_credit_allowed"])
        self.assertIn("same_task_cloud_terminal_result_source", evidence["next_required_evidence"])
        self.assertIn("same_task_terminal_route_delivery_task_id_alignment", evidence["next_required_evidence"])
        self.assertNotIn("/Users/m1", evidence_text)
        self.assertNotIn("secret_nav2", evidence_text)
        self.assertFalse(evidence["mission_artifact_delta"]["same_task_terminal_result_linked_to_route_execution"])
        self.assertEqual(evidence["mission_artifact_delta"]["support_only_reason"], "same_task_id_mismatch_or_missing")
        self.assertFalse(evidence["mission_artifact_delta"]["okr_credit_allowed"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["route_execution_success"])

    def test_current_field_evidence_material_packet_ready_consumes_camera_radar_map_nav2_and_manual_gate_summary(self):
        # current field evidence packet 只证明安全材料摘要被消费，不证明 route execution、delivery 或 control。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            current_summary = Path(tmpdir) / "current_field_evidence.json"
            make_complete_fixture(root)
            write_current_field_evidence_json(current_summary)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--current-field-evidence-json",
                    str(current_summary),
                    "--output",
                    str(output),
                    "--run-id",
                    "current_field_evidence_ready",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["current_field_evidence_material"]
            nested = packet["field_motion_evidence_packet"]["current_field_evidence_material"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.CURRENT_FIELD_EVIDENCE_MATERIAL_SCHEMA)
        self.assertEqual(evidence["proof_scope"], manifest.CURRENT_FIELD_EVIDENCE_MATERIAL_PROOF_SCOPE)
        self.assertEqual(evidence["evidence_boundary"], manifest.CURRENT_FIELD_EVIDENCE_MATERIAL_PROOF_SCOPE)
        self.assertEqual(evidence["status"], "current_field_evidence_ready_not_route_execution_proof")
        self.assertTrue(evidence["current_field_evidence_ready_not_route_execution_proof"])
        self.assertTrue(evidence["live_or_field_material_consumed"])
        self.assertEqual(
            evidence["present_materials"],
            [
                "camera_frame_observed",
                "radar_scan_observed",
                "map_material_observed",
                "nav2_no_motion_path_generated",
                "manual_gate_blocked_expected",
            ],
        )
        self.assertEqual(evidence["missing_materials"], [])
        self.assertTrue(evidence["camera_frame_observed"])
        self.assertTrue(evidence["radar_scan_observed"])
        self.assertTrue(evidence["map_material_observed"])
        self.assertTrue(evidence["nav2_no_motion_path_generated"])
        self.assertTrue(evidence["manual_gate_blocked_expected"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["hil_pass"])
        self.assertFalse(evidence["connects_cloud_production"])
        self.assertFalse(evidence["route_execution_success"])
        self.assertEqual(evidence["blocked_reasons"], [])
        self.assertEqual(evidence["next_required_evidence"], ["real_current_field_evidence_route_execution_acceptance"])
        self.assertEqual(evidence["material_summaries"]["camera"]["camera_frame_observed"], True)
        self.assertEqual(evidence["material_summaries"]["radar"]["radar_scan_observed"], True)
        self.assertEqual(evidence["material_summaries"]["map"]["map_material_observed"], True)
        self.assertEqual(evidence["material_summaries"]["nav2_no_motion_path"]["nav2_no_motion_path_generated"], True)
        self.assertEqual(evidence["material_summaries"]["manual_gate"]["manual_gate_blocked_expected"], True)
        self.assertNotIn("/Users/m1", evidence_text)
        self.assertNotIn("traceback", evidence_text.lower())
        self.assertNotIn("token", evidence_text.lower())

    def test_current_field_evidence_material_packet_fail_closed_on_dangerous_true_and_unsafe_text(self):
        # hostile summary 里一旦把控制类 boolean 置真或把安全摘要字段污染成绝对路径，packet 必须 blocked。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            current_summary = Path(tmpdir) / "current_field_evidence.json"
            make_complete_fixture(root)
            write_current_field_evidence_json(current_summary)
            payload = json.loads(current_summary.read_text(encoding="utf-8"))
            payload["safe_command_boundary"]["locked_reason"] = "/Users/m1/secret/camera_status.txt"
            payload["safe_command_boundary"]["command_dispatch_enabled"] = True
            payload["operator_hil_material_summary"]["delivery_claim"] = True
            current_summary.write_text(json.dumps(payload), encoding="utf-8")

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--current-field-evidence-json",
                    str(current_summary),
                    "--output",
                    str(output),
                    "--run-id",
                    "current_field_evidence_hostile",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["current_field_evidence_material"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertFalse(evidence["current_field_evidence_ready_not_route_execution_proof"])
        self.assertFalse(evidence["manual_gate_blocked_expected"])
        self.assertIn("current_field_evidence_dangerous_true_claim", evidence["blocked_reasons"])
        self.assertIn("current_field_evidence_unsafe_text", evidence["blocked_reasons"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["hil_pass"])
        self.assertFalse(evidence["connects_cloud_production"])
        self.assertNotIn("/Users/m1/secret/camera_status.txt", evidence_text)
        self.assertNotIn("traceback", evidence_text.lower())

    def test_localization_path_material_readback_ready_consumes_default_artifact_38(self):
        # 本轮 localization/path additive 必须直接兼容 O1 的 38 号 same-run readback，并保持 path=false 边界。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            make_complete_fixture(root)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--localization-path-material-json",
                    str(LOCALIZATION_PATH_MATERIAL_ARTIFACT),
                    "--output",
                    str(output),
                    "--run-id",
                    "localization_path_material_readback_ready",
                ]
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            evidence = payload["localization_path_material_readback"]
            nested = payload["field_motion_evidence_packet"]["localization_path_material_readback"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA)
        self.assertEqual(evidence["proof_scope"], manifest.LOCALIZATION_PATH_MATERIAL_READBACK_PROOF_SCOPE)
        self.assertEqual(evidence["evidence_boundary"], manifest.LOCALIZATION_PATH_MATERIAL_READBACK_PROOF_SCOPE)
        self.assertEqual(evidence["status"], manifest.LOCALIZATION_PATH_MATERIAL_READBACK_READY_STATUS)
        self.assertTrue(evidence["same_run_localization_material_present"])
        self.assertTrue(evidence["same_run_localization_material_consumed"])
        self.assertTrue(evidence["same_run_map_once_observed"])
        self.assertTrue(evidence["same_run_amcl_pose_observed"])
        self.assertTrue(evidence["same_run_localization_tf_map_to_odom"])
        self.assertTrue(evidence["same_run_localization_tf_map_to_base_link"])
        self.assertTrue(evidence["same_run_planner_server_active"])
        self.assertTrue(evidence["same_run_path_generation_requested"])
        self.assertFalse(evidence["same_run_path_generation_succeeded"])
        self.assertFalse(evidence["same_run_path_generated"])
        self.assertEqual(evidence["same_run_path_point_count"], 0)
        self.assertFalse(evidence["same_run_path_proven"])
        self.assertFalse(evidence["cross_run_clean_baseline_path_comparator_present"])
        self.assertFalse(evidence["same_run_override_allowed"])
        self.assertEqual(evidence["blocked_reasons"], [])
        self.assertEqual(
            evidence["next_required_evidence"],
            ["current_same_run_path_generation_success_or_live_route_execution_proof"],
        )
        self.assertEqual(evidence["source_schema"], "trashbot.pc_tools_workstation.robot_control_summary.v1")
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["hil_pass"])
        self.assertFalse(evidence["nav2_route_execution_success"])
        self.assertFalse(evidence["route_execution_success"])
        self.assertNotIn("/root/", evidence_text)
        self.assertNotIn("http://", evidence_text)
        self.assertNotIn("token", evidence_text.lower())

    def test_localization_path_material_readback_fail_closed_on_task_mismatch_and_cross_run_confusion(self):
        # task drift、危险 true、allowlisted 字段污染和 cross-run comparator 混入都只能 section-local blocked。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            localization_summary = Path(tmpdir) / "localization_path_material.json"
            make_complete_fixture(root)
            write_localization_path_material_json(
                localization_summary,
                task_id="other_task",
                cross_run_clean_baseline_path_comparator_present=True,
                cross_run_clean_baseline_path_summary={
                    "path_point_count": 31,
                    "same_run_override_allowed": True,
                },
            )
            payload = json.loads(localization_summary.read_text(encoding="utf-8"))
            for endpoint in payload["read_endpoints"]:
                if endpoint.get("id") == "status":
                    endpoint["status"] = "/Users/m1/token/localization_status.txt"
                if endpoint.get("id") == "nav2_proof_latest":
                    endpoint["key_values"]["safe_to_control"] = "true"
            localization_summary.write_text(json.dumps(payload), encoding="utf-8")

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--localization-path-material-json",
                    str(localization_summary),
                    "--output",
                    str(output),
                    "--run-id",
                    "localization_path_material_readback_blocked",
                ]
            )
            result = json.loads(output.read_text(encoding="utf-8"))
            evidence = result["localization_path_material_readback"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertIn("localization_path_material_task_mismatch", evidence["blocked_reasons"])
        self.assertIn("localization_path_cross_run_comparator_confusion", evidence["blocked_reasons"])
        self.assertIn("localization_path_dangerous_true_claim", evidence["blocked_reasons"])
        self.assertIn("localization_path_unsafe_text", evidence["blocked_reasons"])
        self.assertIn("nav2_proof_latest.safe_to_control", evidence["dangerous_true_fields"])
        self.assertFalse(evidence["same_run_path_proven"])
        self.assertFalse(evidence["cross_run_clean_baseline_path_comparator_present"])
        self.assertFalse(evidence["same_run_override_allowed"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["hil_pass"])
        self.assertFalse(evidence["nav2_route_execution_success"])
        self.assertFalse(evidence["route_execution_success"])
        self.assertNotIn("/Users/m1", evidence_text)
        self.assertNotIn("localization_status.txt", evidence_text)
        self.assertNotIn("\"path_point_count\": 31", evidence_text)

    def test_field_operator_confirmation_material_ready_consumes_operator_report_without_delivery_proof(self):
        # operator confirmation material 只能作为准现场人工确认摘要，不能打开控制或宣称送达成功。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            operator_report = Path(tmpdir) / "operator_report.json"
            make_complete_fixture(root)
            write_field_operator_confirmation_json(operator_report)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--field-operator-confirmation-json",
                    str(operator_report),
                    "--output",
                    str(output),
                    "--run-id",
                    "field_operator_confirmation_ready",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["field_operator_confirmation_material"]
            nested = packet["field_motion_evidence_packet"]["field_operator_confirmation_material"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA)
        self.assertEqual(evidence["proof_scope"], manifest.FIELD_OPERATOR_CONFIRMATION_MATERIAL_PROOF_SCOPE)
        self.assertEqual(evidence["evidence_boundary"], manifest.FIELD_OPERATOR_CONFIRMATION_MATERIAL_PROOF_SCOPE)
        self.assertEqual(evidence["status"], manifest.FIELD_OPERATOR_CONFIRMATION_READY_STATUS)
        self.assertTrue(evidence["same_task_id_consumed"])
        self.assertTrue(evidence["linked_route_material_present"])
        self.assertFalse(evidence["linked_delivery_material_present"])
        self.assertTrue(evidence["operator_material_consumed"])
        self.assertEqual(evidence["operator_report_status"], "loaded")
        self.assertEqual(evidence["operator_confirmation_status"], "confirmed")
        self.assertTrue(evidence["operator_present"])
        self.assertTrue(evidence["physical_clearance_confirmed"])
        self.assertTrue(evidence["emergency_stop_ready"])
        self.assertTrue(evidence["observed_motion"])
        self.assertTrue(evidence["observed_stop"])
        self.assertEqual(evidence["reported_at"], "2026-07-10T07:22:00Z")
        self.assertEqual(evidence["blocked_reasons"], [])
        self.assertIn("same_task_delivery_result_material", evidence["next_required_evidence"])
        self.assertTrue(evidence["material_summaries"]["operator_report"]["operator_identity_present"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["route_execution_success"])
        self.assertFalse(evidence["hil_pass"])
        self.assertFalse(evidence["connects_cloud_production"])
        self.assertNotIn("operator-on-duty-a", evidence_text)
        self.assertNotIn("operator-material-001", evidence_text)
        self.assertNotIn("/Users/m1", evidence_text)
        self.assertNotIn("token", evidence_text.lower())

    def test_field_operator_confirmation_material_fail_closed_on_unsafe_task_mismatch_and_missing_identity(self):
        # task drift、危险 true 和 raw/body/path/token 类污染必须 section-local blocked，且不能回显原文。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            operator_report = Path(tmpdir) / "operator_report.json"
            make_complete_fixture(root)
            write_field_operator_confirmation_json(
                operator_report,
                task_id="other_task",
                operator_id=None,
                operator_report_id=None,
                safe_to_control=True,
                raw_body="/Users/m1/secret/operator-token-response-body.txt",
                operator_confirmation={"status": "confirmed", "observed_motion": True, "observed_stop": True},
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--field-operator-confirmation-json",
                    str(operator_report),
                    "--output",
                    str(output),
                    "--run-id",
                    "field_operator_confirmation_ready",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["field_operator_confirmation_material"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertFalse(evidence["same_task_id_consumed"])
        self.assertFalse(evidence["operator_material_consumed"])
        self.assertFalse(evidence["operator_identity_present"])
        self.assertIn("field_operator_confirmation_task_mismatch", evidence["blocked_reasons"])
        self.assertIn("field_operator_confirmation_operator_identity_missing", evidence["blocked_reasons"])
        self.assertIn("field_operator_confirmation_dangerous_true_claim", evidence["blocked_reasons"])
        self.assertIn("field_operator_confirmation_unsafe_field", evidence["blocked_reasons"])
        self.assertIn("field_operator_confirmation_unsafe_text", evidence["blocked_reasons"])
        self.assertIn("safe_to_control", evidence["dangerous_true_fields"])
        self.assertGreaterEqual(evidence["unsafe_field_count"], 1)
        self.assertGreaterEqual(evidence["unsafe_text_field_count"], 1)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["route_execution_success"])
        self.assertFalse(evidence["hil_pass"])
        self.assertFalse(evidence["connects_cloud_production"])
        self.assertNotIn("operator-token", evidence_text)
        self.assertNotIn("response-body", evidence_text)
        self.assertNotIn("/Users/m1", evidence_text)
        self.assertNotIn("raw_body", evidence_text)

    def test_clean_baseline_nav2_path_material_packet_ready_consumes_txt_and_same_dir_summaries(self):
        # clean-baseline additive 应该能从 readback txt 入口归并同目录 refresh/retry/latest/status/cleanup 材料。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            nav2_artifacts = Path(tmpdir) / "clean_baseline_nav2"
            output = Path(tmpdir) / "manifest.json"
            make_complete_fixture(root)
            paths = write_clean_baseline_nav2_path_material_files(nav2_artifacts)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--clean-baseline-nav2-path-json",
                    str(paths["txt"]),
                    "--output",
                    str(output),
                    "--run-id",
                    "clean_baseline_nav2_path_material_ready",
                ]
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            evidence = payload["clean_baseline_nav2_path_material"]
            nested = payload["field_motion_evidence_packet"]["clean_baseline_nav2_path_material"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.CLEAN_BASELINE_NAV2_PATH_MATERIAL_SCHEMA)
        self.assertEqual(evidence["proof_scope"], manifest.CLEAN_BASELINE_NAV2_PATH_MATERIAL_PROOF_SCOPE)
        self.assertEqual(evidence["evidence_boundary"], manifest.CLEAN_BASELINE_NAV2_PATH_MATERIAL_PROOF_SCOPE)
        self.assertEqual(evidence["status"], "clean_baseline_nav2_path_material_ready_not_route_execution_proof")
        self.assertTrue(evidence["clean_baseline_nav2_path_material_ready_not_route_execution_proof"])
        self.assertEqual(evidence["first_attempt_status"], "blocked_with_root_cause")
        self.assertEqual(evidence["retry_status"], "nav2_no_motion_path_generation_runtime_observed")
        self.assertTrue(evidence["retry_success"])
        self.assertTrue(evidence["path_generation_succeeded"])
        self.assertTrue(evidence["path_generated"])
        self.assertEqual(evidence["path_point_count"], 31)
        self.assertTrue(evidence["planner_server_active"])
        self.assertTrue(evidence["managed_runtime_started"])
        self.assertTrue(evidence["initialpose_published"])
        self.assertTrue(evidence["amcl_pose_observed"])
        self.assertTrue(evidence["map_server_active"])
        self.assertTrue(evidence["amcl_active"])
        self.assertTrue(evidence["cleanup_readback_clean"])
        self.assertEqual(evidence["first_failure"]["root_causes"], ["tf_chain_missing_before_initialpose"])
        self.assertEqual(evidence["retry_success_summary"]["path_point_count"], 31)
        self.assertEqual(evidence["blocked_reasons"], [])
        self.assertEqual(evidence["next_required_evidence"], ["real_live_nav2_route_execution_after_clean_baseline_path_material"])
        self.assertTrue(any(item["material"] == "clean_baseline_nav2_path_artifacts" for item in evidence["material_sample_refs"]))
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["hil_pass"])
        self.assertFalse(evidence["connects_cloud_production"])
        self.assertFalse(evidence["route_execution_success"])
        self.assertNotIn("/Users/m1", evidence_text)
        self.assertNotIn("traceback", evidence_text.lower())
        self.assertNotIn("token", evidence_text.lower())

    def test_clean_baseline_nav2_path_material_packet_fail_closed_on_dangerous_true_and_task_mismatch(self):
        # 任一 sibling summary 若出现危险 true、task drift 或敏感文本，clean-baseline additive 只能 blocked。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            nav2_artifacts = Path(tmpdir) / "clean_baseline_nav2"
            output = Path(tmpdir) / "manifest.json"
            make_complete_fixture(root)
            paths = write_clean_baseline_nav2_path_material_files(
                nav2_artifacts,
                retry={
                    "task_id": "other_task",
                    "safe_to_control": True,
                    "root_causes": ["/Users/m1/token/traceback.txt"],
                },
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--clean-baseline-nav2-path-json",
                    str(paths["refresh"]),
                    "--output",
                    str(output),
                    "--run-id",
                    "clean_baseline_nav2_path_material_ready",
                ]
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            evidence = payload["clean_baseline_nav2_path_material"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertFalse(evidence["clean_baseline_nav2_path_material_ready_not_route_execution_proof"])
        self.assertIn("clean_baseline_nav2_path_material_task_mismatch", evidence["blocked_reasons"])
        self.assertIn("clean_baseline_nav2_path_material_dangerous_true_claim", evidence["blocked_reasons"])
        self.assertIn("clean_baseline_nav2_path_material_unsafe_text", evidence["blocked_reasons"])
        self.assertIn("retry.safe_to_control", evidence["dangerous_true_fields"])
        self.assertGreaterEqual(evidence["unsafe_text_field_count"], 1)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["hil_pass"])
        self.assertFalse(evidence["connects_cloud_production"])
        self.assertFalse(evidence["route_execution_success"])
        self.assertNotIn("/Users/m1", evidence_text)
        self.assertNotIn("traceback.txt", evidence_text)
        self.assertNotIn("token", evidence_text.lower())

    def test_same_task_field_material_packet_ready_even_when_map_yaml_missing(self):
        # map.yaml 缺口要被记录，但不能阻止 route/keyframe/route bag/replay 这些准现场材料被消费。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            make_complete_fixture(root)
            (root / "map.yaml").unlink()

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--output",
                    str(output),
                    "--run-id",
                    "same_task_field_material_ready_without_map_yaml",
                ]
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            evidence = payload["same_task_field_material_packet"]
            nested = payload["field_motion_evidence_packet"]["same_task_field_material_packet"]

        self.assertEqual(rc, 2)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA)
        self.assertEqual(evidence["proof_scope"], manifest.SAME_TASK_FIELD_MATERIAL_PACKET_PROOF_SCOPE)
        self.assertEqual(evidence["status"], "ready_not_delivery_proof")
        self.assertTrue(evidence["same_task_id_consumed"])
        self.assertTrue(evidence["live_or_field_material_consumed"])
        self.assertIn("map_yaml", evidence["missing_materials"])
        self.assertIn("route_csv", evidence["present_materials"])
        self.assertIn("keyframes", evidence["present_materials"])
        self.assertIn("route_bag_or_rosbag", evidence["present_materials"])
        self.assertIn("replay_jsonl", evidence["present_materials"])
        self.assertFalse(evidence["map_yaml_present"])
        self.assertTrue(evidence["route_csv_present"])
        self.assertTrue(evidence["keyframes_present"])
        self.assertTrue(evidence["route_bag_or_rosbag_present"])
        self.assertTrue(evidence["replay_jsonl_present"])
        self.assertEqual(evidence["material_summaries"]["route_csv"]["basename"], "route.csv")
        self.assertEqual(evidence["material_summaries"]["replay_jsonl"]["basename"], "fixed_route_replay.jsonl")
        self.assertEqual(evidence["material_summaries"]["keyframes"]["count"], 1)
        self.assertEqual(evidence["material_summaries"]["replay_jsonl"]["count"], 2)
        self.assertIn("same_task_field_material_map_yaml_missing_optional", evidence["blocked_reasons"])
        self.assertIn("attach_map_yaml_for_navigation_context", evidence["next_required_evidence"])
        self.assertIn("same_task_delivery_record_or_operator_confirmation", evidence["next_required_evidence"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["route_execution_success"])

    def test_same_task_field_material_packet_fail_closed_on_unsafe_source_manifest_without_secret_echo(self):
        # source manifest 若混入危险 true、路径或 secret，packet 只能 blocked，且不能回显原文。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            make_complete_fixture(root)
            write_text(
                root / "manifest.json",
                json.dumps(
                    {
                        "schema": "trashbot.vision_samples.v1",
                        "safe_to_control": True,
                        "samples": [
                            {
                                "sample_ref": "vision_sample://keyframes/0001.json",
                                "context": {
                                    "task_id": "same_task_field_material_unsafe",
                                    "trace_path": "/Users/m1/token/secret_material.json",
                                    "raw_payload": "base64:SECRET_FIELD_PACKET",
                                },
                            }
                        ],
                    }
                )
                + "\n",
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--output",
                    str(output),
                    "--run-id",
                    "same_task_field_material_unsafe",
                ]
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            evidence = payload["same_task_field_material_packet"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertTrue(evidence["same_task_id_consumed"])
        self.assertTrue(evidence["live_or_field_material_consumed"])
        self.assertIn("same_task_field_material_dangerous_true_claim", evidence["blocked_reasons"])
        self.assertIn("same_task_field_material_unsafe_field", evidence["blocked_reasons"])
        self.assertIn("same_task_field_material_unsafe_text", evidence["blocked_reasons"])
        self.assertIn("safe_to_control", evidence["dangerous_true_fields"])
        self.assertGreaterEqual(evidence["unsafe_field_count"], 2)
        self.assertGreaterEqual(evidence["unsafe_text_field_count"], 2)
        self.assertNotIn("/Users/m1", evidence_text)
        self.assertNotIn("SECRET_FIELD_PACKET", evidence_text)
        self.assertNotIn("secret_material", evidence_text)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["route_execution_success"])

    def test_same_task_route_execution_material_packet_ready_consumes_same_task_route_materials(self):
        # 新 packet 汇总 field materials、Nav2、delivery、pose progress 和 replay，只证明材料消费不证明送达成功。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            terminal_result = Path(tmpdir) / "cloud_terminal_result.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_cloud_terminal_result_json(terminal_result)
            write_route_bag_db3(
                db3,
                topics=[
                    (1, "/tf", "tf2_msgs/msg/TFMessage"),
                    (2, "/odom", "nav_msgs/msg/Odometry"),
                ],
                messages=[
                    (1, 1, 1781020583610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.0, 0.0, 0.0)],
                    )),
                    (2, 1, 1781020584610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.3, 0.4, 0.0)],
                    )),
                    (3, 2, 1781020585610099932, build_odometry_cdr_payload(
                        frame_id="map",
                        child_frame_id="base_link",
                        x=0.3,
                        y=0.4,
                    )),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--cloud-terminal-result-json",
                    str(terminal_result),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--route-bag-source-label",
                    "unit-same-task-route-execution-material",
                    "--output",
                    str(output),
                    "--run-id",
                    "same_task_route_execution_material_ready",
                ]
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            evidence = payload["same_task_route_execution_material_packet"]
            nested = payload["field_motion_evidence_packet"]["same_task_route_execution_material_packet"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA)
        self.assertEqual(evidence["proof_scope"], manifest.SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_PROOF_SCOPE)
        self.assertEqual(evidence["evidence_boundary"], manifest.SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_PROOF_SCOPE)
        self.assertEqual(evidence["status"], "route_execution_material_ready_not_delivery_proof")
        self.assertTrue(evidence["same_task_id_consumed"])
        self.assertEqual(evidence["same_task_field_material_packet_status"], "ready_not_delivery_proof")
        self.assertTrue(evidence["route_execution_material_consumed"])
        self.assertFalse(evidence["live_or_field_command_evidence_present"])
        self.assertTrue(evidence["delivery_or_operator_material_consumed"])
        self.assertFalse(evidence["route_execution_credit_candidate"])
        self.assertEqual(evidence["credit_support_only_reason"], "local_or_mock_same_task_artifacts_only")
        self.assertIn("same_task_live_motion_log_or_field_nav2_command_evidence", evidence["credit_required_evidence"])
        self.assertEqual(evidence["route_execution_result_status"], "route_execution_result_delivery_readiness_ready_not_delivery_proof")
        self.assertEqual(evidence["route_delivery_closure_status"], "route_delivery_closure_ready_not_success_proof")
        self.assertEqual(evidence["nav2_goal_execution_status"], "ready_not_delivery_proof")
        self.assertEqual(evidence["delivery_result_status"], "ready_not_delivery_proof")
        self.assertEqual(evidence["pose_progress_replay_status"], "ready_not_live_nav2_proof")
        self.assertEqual(evidence["route_replay_jsonl_status"], "present_not_delivery_proof")
        self.assertTrue(evidence["route_execution_material_flags"]["route_execution_result_delivery_readiness_consumed"])
        self.assertTrue(evidence["route_execution_material_flags"]["route_bag_pose_progress_replay_consumed"])
        self.assertTrue(evidence["route_execution_material_flags"]["route_replay_jsonl_consumed"])
        self.assertEqual(evidence["material_summaries"]["route_csv"]["basename"], "route.csv")
        self.assertEqual(evidence["material_summaries"]["replay_jsonl"]["count"], 2)
        self.assertTrue(any(item["material"] == "replay_jsonl" for item in evidence["material_sample_refs"]))
        self.assertIn("real_live_nav2_route_execution_result", evidence["next_required_evidence"])
        self.assertNotIn(str(root), evidence_text)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["hil_pass"])
        self.assertFalse(evidence["route_execution_success"])

    def test_same_task_route_execution_material_packet_sets_credit_candidate_with_live_and_delivery_material(self):
        # credit candidate 需要 same-task route execution ready，再叠加 live/field command 与 delivery/operator 材料。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            motion_logs = Path(tmpdir) / "remote_capture"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            terminal_result = Path(tmpdir) / "cloud_terminal_result.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            make_motion_log_fixture(motion_logs, nonzero_cmd_vel=True, nonzero_waypoint=True)
            write_nav2_goal_proof(proof)
            write_cloud_terminal_result_json(terminal_result)
            write_route_bag_db3(
                db3,
                topics=[(1, "/tf", "tf2_msgs/msg/TFMessage")],
                messages=[
                    (1, 1, 1781020583610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.0, 0.0, 0.0)],
                    )),
                    (2, 1, 1781020584610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.3, 0.4, 0.0)],
                    )),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--motion-log-root",
                    str(motion_logs),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--cloud-terminal-result-json",
                    str(terminal_result),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--route-bag-source-label",
                    "field-live-route-execution-material",
                    "--output",
                    str(output),
                    "--run-id",
                    "same_task_route_execution_credit_candidate",
                ]
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            evidence = payload["same_task_route_execution_material_packet"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "route_execution_material_ready_not_delivery_proof")
        self.assertTrue(evidence["route_execution_material_consumed"])
        self.assertTrue(evidence["live_or_field_command_evidence_present"])
        self.assertTrue(evidence["delivery_or_operator_material_consumed"])
        self.assertTrue(evidence["route_execution_credit_candidate"])
        self.assertIsNone(evidence["credit_support_only_reason"])
        self.assertNotIn("same_task_live_motion_log_or_field_nav2_command_evidence", evidence["credit_required_evidence"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_same_task_route_execution_material_packet_marks_delivery_material_missing_for_credit(self):
        # 即使 route execution 材料 ready，缺 delivery claim/operator confirmation 也只能停在 support-only。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            motion_logs = Path(tmpdir) / "remote_capture"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            terminal_result = Path(tmpdir) / "cloud_terminal_result.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            make_motion_log_fixture(motion_logs, nonzero_cmd_vel=True, nonzero_waypoint=True)
            write_nav2_goal_proof(proof)
            write_cloud_terminal_result_json(terminal_result)
            write_route_bag_db3(
                db3,
                topics=[(1, "/tf", "tf2_msgs/msg/TFMessage")],
                messages=[
                    (1, 1, 1781020583610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.0, 0.0, 0.0)],
                    )),
                    (2, 1, 1781020584610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.3, 0.4, 0.0)],
                    )),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--motion-log-root",
                    str(motion_logs),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--cloud-terminal-result-json",
                    str(terminal_result),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--output",
                    str(output),
                    "--run-id",
                    "same_task_route_execution_credit_delivery_missing",
                ]
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            packet = payload["field_motion_evidence_packet"]
            packet["delivery_result_evidence"]["delivery_result_claimed"] = False
            packet["delivery_result_evidence"]["operator_confirmation_present"] = False
            evidence = manifest.build_same_task_route_execution_material_packet(packet)

        self.assertEqual(rc, 0)
        self.assertTrue(evidence["route_execution_material_consumed"])
        self.assertTrue(evidence["live_or_field_command_evidence_present"])
        self.assertFalse(evidence["delivery_or_operator_material_consumed"])
        self.assertFalse(evidence["route_execution_credit_candidate"])
        self.assertEqual(evidence["credit_support_only_reason"], "delivery_or_operator_material_missing")
        self.assertIn("same_task_delivery_result_or_operator_confirmation", evidence["credit_required_evidence"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["safe_to_control"])

    def test_same_task_route_execution_material_packet_blocks_without_route_execution_material(self):
        # 只有 route.csv/keyframes/route_bag 目录不够，至少还要 replay 或 linked route execution 摘要。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            make_complete_fixture(root)
            (root / "fixed_route_replay.jsonl").unlink()

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--output",
                    str(output),
                    "--run-id",
                    "same_task_route_execution_material_missing",
                ]
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            evidence = payload["same_task_route_execution_material_packet"]

        self.assertEqual(rc, 2)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertTrue(evidence["same_task_id_consumed"])
        self.assertFalse(evidence["route_execution_material_consumed"])
        self.assertEqual(evidence["route_replay_jsonl_status"], "missing")
        self.assertIn("same_task_route_execution_material_missing", evidence["blocked_reasons"])
        self.assertIn("same_task_route_replay_jsonl", evidence["next_required_evidence"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_same_task_route_execution_material_packet_fail_closed_on_unsafe_linked_summaries(self):
        # task drift、危险 true 和敏感文本只能阻断新 packet，不能把路径、token、base64/raw 泄漏出去。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            terminal_result = Path(tmpdir) / "cloud_terminal_result.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_nav2_goal_proof(proof)
            write_cloud_terminal_result_json(terminal_result)
            write_route_bag_db3(
                db3,
                topics=[(1, "/tf", "tf2_msgs/msg/TFMessage")],
                messages=[
                    (1, 1, 1781020583610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.0, 0.0, 0.0)],
                    )),
                    (2, 1, 1781020584610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.3, 0.4, 0.0)],
                    )),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--cloud-terminal-result-json",
                    str(terminal_result),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--output",
                    str(output),
                    "--run-id",
                    "same_task_route_execution_material_unsafe",
                ]
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            packet = payload["field_motion_evidence_packet"]
            packet["same_task_field_material_packet"]["task_id"] = "other-task"
            packet["route_execution_result_delivery_readiness"]["safe_to_control"] = True
            packet["route_delivery_closure_packet"]["linked_route_execution_source"] = "/Users/m1/token/secret_nav2.log"
            packet["route_bag_payload_replay"]["payload_sha256_prefix_samples"] = ["base64:SECRET_ROUTE_PAYLOAD"]
            evidence = manifest.build_same_task_route_execution_material_packet(packet)
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertFalse(evidence["same_task_id_consumed"])
        self.assertFalse(evidence["route_execution_material_consumed"])
        self.assertFalse(evidence["route_execution_credit_candidate"])
        self.assertEqual(evidence["credit_support_only_reason"], "same_task_id_mismatch_or_missing")
        self.assertIn("same_task_live_motion_log_or_field_nav2_command_evidence", evidence["credit_required_evidence"])
        self.assertIn("same_task_field_material_packet_not_ready_or_task_mismatch", evidence["blocked_reasons"])
        self.assertIn("same_task_route_execution_material_dangerous_true_claim", evidence["blocked_reasons"])
        self.assertIn("same_task_route_execution_material_unsafe_text", evidence["blocked_reasons"])
        self.assertIn("route_execution_result_delivery_readiness.safe_to_control", evidence["dangerous_true_fields"])
        self.assertGreaterEqual(evidence["unsafe_text_field_count"], 2)
        self.assertNotIn("/Users/m1", evidence_text)
        self.assertNotIn("secret_nav2", evidence_text)
        self.assertNotIn("SECRET_ROUTE_PAYLOAD", evidence_text)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["hil_pass"])
        self.assertFalse(evidence["route_execution_success"])

    def test_same_task_mission_evidence_gate_allows_okr_credit_only_with_live_motion_delta(self):
        # same-task gate 即使 ready，也只有明确消费 live/field motion 材料时才允许计主 OKR credit。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            motion_logs = Path(tmpdir) / "remote_capture"
            output = Path(tmpdir) / "manifest.json"
            proof = Path(tmpdir) / "o11_proof.json"
            terminal_result = Path(tmpdir) / "cloud_terminal_result.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            make_motion_log_fixture(motion_logs, nonzero_cmd_vel=True, nonzero_waypoint=True)
            write_nav2_goal_proof(proof)
            write_cloud_terminal_result_json(terminal_result)
            write_route_bag_db3(
                db3,
                topics=[
                    (1, "/tf", "tf2_msgs/msg/TFMessage"),
                    (2, "/odom", "nav_msgs/msg/Odometry"),
                ],
                messages=[
                    (1, 1, 1781020583610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.0, 0.0, 0.0)],
                    )),
                    (2, 1, 1781020584610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.3, 0.4, 0.0)],
                    )),
                    (3, 2, 1781020585610099932, build_odometry_cdr_payload(
                        frame_id="map",
                        child_frame_id="base_link",
                        x=0.3,
                        y=0.4,
                    )),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--motion-log-root",
                    str(motion_logs),
                    "--nav2-goal-proof-json",
                    str(proof),
                    "--cloud-terminal-result-json",
                    str(terminal_result),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--route-bag-source-label",
                    "field-route-bag-capture",
                    "--output",
                    str(output),
                    "--run-id",
                    "same_task_mission_credit_live_delta",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["same_task_mission_evidence_gate"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "same_task_mission_gate_ready_not_success_proof")
        self.assertTrue(evidence["same_task_mission_gate_ready"])
        self.assertTrue(evidence["same_task_id_consumed"])
        self.assertTrue(evidence["live_or_field_command_executed"])
        self.assertIsNone(evidence["support_only_reason"])
        self.assertTrue(evidence["okr_credit_allowed"])
        self.assertTrue(evidence["mission_artifact_delta"]["same_task_field_material_consumed"])
        self.assertTrue(evidence["mission_artifact_delta"]["live_or_field_command_executed"])
        self.assertIsNone(evidence["mission_artifact_delta"]["support_only_reason"])
        self.assertTrue(evidence["mission_artifact_delta"]["okr_credit_allowed"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_same_task_mission_evidence_gate_support_only_reason_classifies_probe_checklist_readback_and_local(self):
        # support-only reason 必须把 probe/checklist/readback/local 分类清楚，避免后续又把 wrapper 记成 mission 进度。
        base_packet = {
            "task_id": "same-task-credit-classify",
            "motion_log_summary": {
                "live_motion_evidence_present": False,
                "live_nav2_log_present": False,
                "path": None,
            },
            "route_bag_or_live_nav2_log": {
                "source": "route_bag",
                "status": "route_bag_present_not_delivery_proof",
            },
            "route_bag_evidence": {
                "source_label": "unit-route-bag",
                "status": "ready_not_route_execution_proof",
            },
            "delivery_result_evidence": {
                "schema": manifest.DELIVERY_RESULT_EVIDENCE_SCHEMA,
                "proof_scope": manifest.DELIVERY_RESULT_EVIDENCE_PROOF_SCOPE,
                "status": "ready_not_delivery_proof",
                "task_id": "same-task-credit-classify",
                "source": "cloud_command_terminal_result",
                "source_schema": manifest.CLOUD_COMMAND_TERMINAL_RESULT_SCHEMA,
                "command_id_ref": "safe_command_ref",
                "task_record_ref": "safe_task_record_ref",
                "evidence_ref": "safe_evidence_ref",
                "completed_at_utc": "2026-07-09T08:00:00Z",
                "delivery_result_claimed": True,
                "operator_confirmation_present": True,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "robot_control_executed": False,
            },
            "route_execution_result_delivery_readiness": {
                "schema": manifest.ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA,
                "proof_scope": manifest.ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_PROOF_SCOPE,
                "status": "route_execution_result_delivery_readiness_ready_not_delivery_proof",
                "task_id": "same-task-credit-classify",
                "route_execution_source": "nav2_goal_execution_evidence+route_bag_pose_progress_replay",
                "route_execution_result_ready": True,
                "delivery_result_readiness_ready": True,
                "operator_confirmation_readiness_ready": True,
            },
            "route_delivery_closure_packet": {
                "schema": manifest.ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA,
                "proof_scope": manifest.ROUTE_DELIVERY_CLOSURE_PACKET_PROOF_SCOPE,
                "status": "route_delivery_closure_ready_not_success_proof",
                "task_id": "same-task-credit-classify",
                "linked_route_execution_source": "nav2_goal_execution_evidence+route_bag_pose_progress_replay",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "robot_control_executed": False,
                "route_execution_success": False,
            },
            "route_bag_pose_progress_replay": {
                "schema": manifest.ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA,
                "proof_scope": manifest.ROUTE_BAG_POSE_PROGRESS_REPLAY_PROOF_SCOPE,
                "status": "ready_not_live_nav2_proof",
                "task_id": "same-task-credit-classify",
                "nonzero_pose_progress_observed": True,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "robot_control_executed": False,
                "route_execution_success": False,
            },
        }
        cases = [
            ("local", "unit-local-route-bag", "local_or_mock_same_task_artifacts_only"),
            ("probe", "same-task-probe-summary", "probe_only_same_task_artifacts"),
            ("checklist", "same-task-checklist-summary", "checklist_only_same_task_artifacts"),
            ("readback", "same-task-readback-summary", "readback_only_same_task_artifacts"),
        ]

        for label, source_label, expected_reason in cases:
            with self.subTest(label=label):
                packet = json.loads(json.dumps(base_packet))
                packet["route_bag_evidence"]["source_label"] = source_label
                evidence = manifest.build_same_task_mission_evidence_gate(packet)
                self.assertEqual(evidence["status"], "same_task_mission_gate_ready_not_success_proof")
                self.assertTrue(evidence["same_task_mission_gate_ready"])
                self.assertFalse(evidence["live_or_field_command_executed"])
                self.assertEqual(evidence["support_only_reason"], expected_reason)
                self.assertFalse(evidence["okr_credit_allowed"])
                self.assertEqual(evidence["mission_artifact_delta"]["support_only_reason"], expected_reason)
                self.assertFalse(evidence["mission_artifact_delta"]["okr_credit_allowed"])

    def test_route_bag_db3_ready_summary_is_additive_and_nested_under_field_motion_packet(self):
        # route_bag_evidence 只读取 DB3 metadata 表，不读取 messages.data，也不输出绝对路径。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_route_bag_db3(
                db3,
                topics=[
                    (1, "/tf_static", "tf2_msgs/msg/TFMessage"),
                    (2, "/scan", "sensor_msgs/msg/LaserScan"),
                    (3, "/camera/image_raw", "sensor_msgs/msg/Image"),
                ],
                messages=[
                    (1, 2, 1781020583610099932),
                    (2, 2, 1781020584610099932),
                    (3, 3, 1781020588575096861),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--route-bag-source-label",
                    "unit-route-bag",
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_packet_task",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_evidence"]
            nested = packet["field_motion_evidence_packet"]["route_bag_evidence"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.ROUTE_BAG_EVIDENCE_SCHEMA)
        self.assertEqual(evidence["proof_scope"], manifest.ROUTE_BAG_EVIDENCE_PROOF_SCOPE)
        self.assertEqual(evidence["status"], "ready_not_route_execution_proof")
        self.assertEqual(evidence["source_label"], "unit-route-bag")
        self.assertEqual(evidence["task_id"], "route_bag_packet_task")
        self.assertTrue(evidence["metadata_present"])
        self.assertTrue(evidence["metadata_read_ok"])
        self.assertEqual(evidence["metadata_basename"], "metadata.yaml")
        self.assertTrue(evidence["db3_present"])
        self.assertTrue(evidence["db3_read_ok"])
        self.assertTrue(evidence["sqlite_schema_ok"])
        self.assertEqual(evidence["db3_basename"], "route_bag_0.db3")
        self.assertEqual(evidence["topic_count"], 3)
        self.assertEqual(evidence["message_count"], 3)
        self.assertEqual(evidence["timestamp_first_ns"], 1781020583610099932)
        self.assertEqual(evidence["timestamp_last_ns"], 1781020588575096861)
        self.assertEqual(evidence["sample_topic_names"], ["/tf_static", "/scan", "/camera/image_raw"])
        self.assertEqual(evidence["blocked_reasons"], [])
        self.assertEqual(len(evidence["db3_sha256_prefix"]), 16)
        self.assertNotIn(str(root), evidence_text)
        self.assertNotIn(str(db3), evidence_text)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["live_nav2_run_proven"])
        self.assertFalse(evidence["route_execution_success"])

    def test_route_bag_missing_input_returns_blocked_summary_without_breaking_artifact_gate(self):
        # 未传 DB3 时也要输出同形 blocked 摘要，方便 O6/O7 明确下一步需要 route bag。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            make_complete_fixture(root)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_missing_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_evidence"]

        self.assertEqual(rc, 0)
        self.assertTrue(packet["gate_pass"])
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertFalse(evidence["db3_present"])
        self.assertFalse(evidence["db3_read_ok"])
        self.assertFalse(evidence["metadata_present"])
        self.assertIn("route_bag_db3_missing", evidence["blocked_reasons"])
        self.assertIn("safe_route_bag_db3_with_topics_and_messages", evidence["next_required_evidence"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])

    def test_route_bag_invalid_db3_fails_closed_without_raw_echo(self):
        # 无效 SQLite 文件不能被大小/hash 伪装成可消费 route_bag evidence。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            make_complete_fixture(root)
            write_text(db3, "not a sqlite db\n")

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_invalid_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_evidence"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertTrue(evidence["db3_present"])
        self.assertFalse(evidence["db3_read_ok"])
        self.assertIn("route_bag_db3_unreadable", evidence["blocked_reasons"])
        self.assertEqual(evidence["sample_topic_names"], [])
        self.assertFalse(evidence["delivery_success"])

    def test_route_bag_schema_mismatch_fails_closed_without_breaking_artifact_gate(self):
        # SQLite 可读但缺 topics/messages schema 时，只阻断 route_bag_evidence additive。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            make_complete_fixture(root)
            write_route_bag_db3(db3, topics=[(1, "/scan", "sensor_msgs/msg/LaserScan")], include_messages_table=False)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_schema_mismatch_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_evidence"]

        self.assertEqual(rc, 0)
        self.assertTrue(packet["gate_pass"])
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertTrue(evidence["db3_read_ok"])
        self.assertFalse(evidence["sqlite_schema_ok"])
        self.assertIn("route_bag_sqlite_schema_mismatch", evidence["blocked_reasons"])
        self.assertFalse(evidence["route_execution_success"])

    def test_route_bag_empty_topics_and_messages_fail_closed(self):
        # 空 topics 或 messages 不能被解释成现场 route_bag 可用，只能作为缺口展示。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            make_complete_fixture(root)
            write_route_bag_db3(db3)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_empty_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_evidence"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertTrue(evidence["sqlite_schema_ok"])
        self.assertEqual(evidence["topic_count"], 0)
        self.assertEqual(evidence["message_count"], 0)
        self.assertIn("route_bag_topics_empty", evidence["blocked_reasons"])
        self.assertIn("route_bag_messages_empty", evidence["blocked_reasons"])
        self.assertFalse(evidence["delivery_success"])

    def test_route_bag_unsafe_metadata_and_source_label_fail_closed_without_secret_echo(self):
        # metadata/source label 里的危险 true、凭证 URL 和 raw/base64 只能生成计数，不能回显原文。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_route_bag_db3(
                db3,
                topics=[(1, "/scan", "sensor_msgs/msg/LaserScan")],
                messages=[(1, 1, 1781020583610099932)],
            )
            write_text(
                metadata,
                "safe_to_control: true\ncallback: https://robot:supersecret@example.com/cb\nraw_payload: base64:SECRET_ROUTE_BAG\n",
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--route-bag-source-label",
                    "https://robot:supersecret@example.com/route_bag",
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_unsafe_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_evidence"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertIsNone(evidence["source_label"])
        self.assertIn("route_bag_metadata_dangerous_true_claim", evidence["blocked_reasons"])
        self.assertIn("route_bag_metadata_unsafe_text", evidence["blocked_reasons"])
        self.assertIn("route_bag_source_label_unsafe_text", evidence["blocked_reasons"])
        self.assertEqual(evidence["dangerous_true_fields"], ["safe_to_control"])
        self.assertGreaterEqual(evidence["unsafe_text_field_count"], 2)
        self.assertNotIn("supersecret", evidence_text)
        self.assertNotIn("SECRET_ROUTE_BAG", evidence_text)
        self.assertNotIn("raw_payload", evidence_text)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_route_bag_payload_replay_ready_summary_is_additive_and_nested_under_field_motion_packet(self):
        # payload replay 只把 BLOB 摘要、安全前缀和时间窗挂到 packet，不暴露 raw payload 或绝对路径。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_route_bag_db3(
                db3,
                topics=[
                    (1, "/tf_static", "tf2_msgs/msg/TFMessage"),
                    (2, "/scan", "sensor_msgs/msg/LaserScan"),
                    (3, "/camera/image_raw", "sensor_msgs/msg/Image"),
                ],
                messages=[
                    (1, 2, 1781020583610099932, b"scan-frame-1"),
                    (2, 2, 1781020584610099932, b"scan-frame-2"),
                    (3, 3, 1781020588575096861, b"camera-frame-1"),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--route-bag-source-label",
                    "unit-route-bag-payload",
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_payload_packet_task",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_payload_replay"]
            nested = packet["field_motion_evidence_packet"]["route_bag_payload_replay"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA)
        self.assertEqual(evidence["proof_scope"], manifest.ROUTE_BAG_PAYLOAD_REPLAY_PROOF_SCOPE)
        self.assertEqual(evidence["status"], "ready_not_route_execution_proof")
        self.assertEqual(evidence["source_label"], "unit-route-bag-payload")
        self.assertEqual(evidence["task_id"], "route_bag_payload_packet_task")
        self.assertTrue(evidence["metadata_present"])
        self.assertTrue(evidence["metadata_read_ok"])
        self.assertEqual(evidence["metadata_basename"], "metadata.yaml")
        self.assertTrue(evidence["db3_present"])
        self.assertTrue(evidence["db3_read_ok"])
        self.assertTrue(evidence["sqlite_schema_ok"])
        self.assertEqual(evidence["db3_basename"], "route_bag_0.db3")
        self.assertEqual(evidence["topic_count"], 3)
        self.assertEqual(evidence["message_count"], 3)
        self.assertEqual(evidence["timestamp_first_ns"], 1781020583610099932)
        self.assertEqual(evidence["timestamp_last_ns"], 1781020588575096861)
        self.assertEqual(evidence["sample_topic_names"], ["/tf_static", "/scan", "/camera/image_raw"])
        self.assertEqual(evidence["payload_sample_count"], 3)
        self.assertEqual(evidence["payload_size_min_bytes"], len(b"scan-frame-1"))
        self.assertEqual(evidence["payload_size_max_bytes"], len(b"camera-frame-1"))
        self.assertGreater(evidence["payload_size_avg_bytes"], 0)
        self.assertEqual(len(evidence["payload_sha256_prefix_samples"]), 3)
        self.assertTrue(all(isinstance(item, str) for item in evidence["payload_sha256_prefix_samples"]))
        self.assertEqual(len(evidence["payload_sha256_prefix_samples"][0]), 12)
        self.assertNotIn(str(root), evidence_text)
        self.assertNotIn(str(db3), evidence_text)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["live_nav2_run_proven"])
        self.assertFalse(evidence["route_execution_success"])

    def test_route_bag_payload_replay_missing_input_returns_blocked_summary_without_breaking_artifact_gate(self):
        # 未传 DB3 时，payload replay 只能输出同形 blocked 摘要，不改变 artifact gate 结果。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            make_complete_fixture(root)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_payload_missing_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_payload_replay"]

        self.assertEqual(rc, 0)
        self.assertTrue(packet["gate_pass"])
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertFalse(evidence["db3_present"])
        self.assertFalse(evidence["db3_read_ok"])
        self.assertFalse(evidence["metadata_present"])
        self.assertIn("route_bag_payload_db3_missing", evidence["blocked_reasons"])
        self.assertIn("safe_route_bag_payload_replay_db3_with_nonempty_payloads", evidence["next_required_evidence"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])

    def test_route_bag_payload_replay_invalid_db3_fails_closed_without_raw_echo(self):
        # 无效 SQLite 文件不能被文件大小或 hash 前缀伪装成可消费 payload replay。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            make_complete_fixture(root)
            write_text(db3, "not a sqlite db\n")

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_payload_invalid_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_payload_replay"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertTrue(evidence["db3_present"])
        self.assertFalse(evidence["db3_read_ok"])
        self.assertIn("route_bag_payload_db3_unreadable", evidence["blocked_reasons"])
        self.assertEqual(evidence["payload_sample_count"], 0)
        self.assertFalse(evidence["delivery_success"])

    def test_route_bag_payload_replay_payload_empty_and_empty_tables_fail_closed(self):
        # 空表和空 payload 都必须 fail closed，不能被 topic 目录或 DB3 文件大小伪装成 ready。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            make_complete_fixture(root)
            write_route_bag_db3(db3)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_payload_empty_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_payload_replay"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertTrue(evidence["sqlite_schema_ok"])
        self.assertEqual(evidence["topic_count"], 0)
        self.assertEqual(evidence["message_count"], 0)
        self.assertEqual(evidence["payload_sample_count"], 0)
        self.assertEqual(evidence["payload_size_min_bytes"], 0)
        self.assertIn("route_bag_payload_topics_empty", evidence["blocked_reasons"])
        self.assertIn("route_bag_payload_messages_empty", evidence["blocked_reasons"])
        self.assertIn("route_bag_payload_empty", evidence["blocked_reasons"])
        self.assertFalse(evidence["delivery_success"])

    def test_route_bag_payload_replay_unsafe_metadata_and_source_label_fail_closed_without_secret_echo(self):
        # payload replay 的安全扫描必须同时约束 metadata、source label 和 payload 文本，不把秘密回显到结果里。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_route_bag_db3(
                db3,
                topics=[(1, "/scan", "sensor_msgs/msg/LaserScan")],
                messages=[(1, 1, 1781020583610099932, b"scan-payload")],
            )
            write_text(
                metadata,
                "safe_to_control: true\ncallback: https://robot:supersecret@example.com/cb\nraw_payload: base64:SECRET_ROUTE_BAG\n",
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--route-bag-source-label",
                    "https://robot:supersecret@example.com/route_bag",
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_payload_unsafe_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_payload_replay"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertIsNone(evidence["source_label"])
        self.assertIn("route_bag_metadata_dangerous_true_claim", evidence["blocked_reasons"])
        self.assertIn("route_bag_metadata_unsafe_text", evidence["blocked_reasons"])
        self.assertIn("route_bag_payload_source_label_unsafe_text", evidence["blocked_reasons"])
        self.assertEqual(evidence["dangerous_true_fields"], ["safe_to_control"])
        self.assertGreaterEqual(evidence["unsafe_text_field_count"], 2)
        self.assertNotIn("supersecret", evidence_text)
        self.assertNotIn("SECRET_ROUTE_BAG", evidence_text)
        self.assertNotIn("raw_payload", evidence_text)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_route_bag_payload_replay_prefix_samples_are_string_array(self):
        # 合同要求短 hash 前缀样本必须是 string[]，而不是结构化对象。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_route_bag_db3(
                db3,
                topics=[(1, "/scan", "sensor_msgs/msg/LaserScan")],
                messages=[
                    (1, 1, 1781020583610099932, b"payload-a"),
                    (2, 1, 1781020584610099932, b"payload-b"),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--route-bag-source-label",
                    "unit-route-bag-payload",
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_payload_prefix_array",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_payload_replay"]

        self.assertEqual(rc, 0)
        self.assertTrue(all(isinstance(item, str) for item in evidence["payload_sha256_prefix_samples"]))
        self.assertTrue(all(len(item) == 12 for item in evidence["payload_sha256_prefix_samples"]))

    def test_route_bag_pose_progress_replay_ready_summary_is_additive_and_nested_under_field_motion_packet(self):
        # pose progress replay 只读派生平移与 frame pair，不回显 raw payload，也不打开控制成功声明。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_route_bag_db3(
                db3,
                topics=[
                    (1, "/tf", "tf2_msgs/msg/TFMessage"),
                    (2, "/odom", "nav_msgs/msg/Odometry"),
                ],
                messages=[
                    (1, 1, 1781020583610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.0, 0.0, 0.0)],
                    )),
                    (2, 1, 1781020584610099932, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "base_link")],
                        translations=[(0.3, 0.4, 0.0)],
                    )),
                    (3, 2, 1781020585610099932, build_odometry_cdr_payload(
                        frame_id="map",
                        child_frame_id="base_link",
                        x=0.3,
                        y=0.4,
                    )),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--route-bag-source-label",
                    "unit-route-bag-pose-progress",
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_pose_progress_packet_task",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_pose_progress_replay"]
            nested = packet["field_motion_evidence_packet"]["route_bag_pose_progress_replay"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA)
        self.assertEqual(evidence["proof_scope"], manifest.ROUTE_BAG_POSE_PROGRESS_REPLAY_PROOF_SCOPE)
        self.assertEqual(evidence["status"], "ready_not_live_nav2_proof")
        self.assertEqual(evidence["source_label"], "unit-route-bag-pose-progress")
        self.assertEqual(evidence["task_id"], "route_bag_pose_progress_packet_task")
        self.assertTrue(evidence["db3_present"])
        self.assertTrue(evidence["db3_read_ok"])
        self.assertTrue(evidence["sqlite_schema_ok"])
        self.assertEqual(evidence["db3_basename"], "route_bag_0.db3")
        self.assertEqual(evidence["topic_count"], 2)
        self.assertEqual(evidence["message_count"], 3)
        self.assertEqual(evidence["pose_sample_count"], 3)
        self.assertEqual(evidence["pose_decode_ok_count"], 3)
        self.assertEqual(evidence["pose_decode_failed_count"], 0)
        self.assertEqual(evidence["pose_topic_types"], ["nav_msgs/msg/Odometry", "tf2_msgs/msg/TFMessage"])
        self.assertEqual(evidence["pose_frame_pairs"], [["map", "base_link"]])
        self.assertEqual(evidence["pose_time_span_ns"], 2000000000)
        self.assertTrue(evidence["nonzero_pose_progress_observed"])
        self.assertEqual(evidence["start_pose"]["frame_id"], "map")
        self.assertEqual(evidence["end_pose"]["child_frame_id"], "base_link")
        self.assertAlmostEqual(evidence["displacement_m"], 0.5, places=6)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["live_nav2_run_proven"])
        self.assertFalse(evidence["route_execution_success"])
        self.assertIn("safe_route_bag_db3_with_pose_progress_messages", evidence["next_required_evidence"])
        self.assertNotIn("/cmd_vel", evidence_text)

    def test_route_bag_pose_progress_replay_missing_input_returns_blocked_summary_without_breaking_artifact_gate(self):
        # 缺 route_bag_db3 时只能得到 blocked 摘要，不能被解释成位姿进度已经证明。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            make_complete_fixture(root)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_pose_progress_missing_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_pose_progress_replay"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertIn("route_bag_pose_progress_db3_missing", evidence["blocked_reasons"])
        self.assertIn("safe_route_bag_db3_with_pose_progress_messages", evidence["next_required_evidence"])
        self.assertFalse(evidence["nonzero_pose_progress_observed"])

    def test_route_bag_pose_progress_replay_decode_failed_for_corrupt_payload(self):
        # corrupt payload 不能被当成位姿进度成功，必须进入 blocked_not_proven。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_route_bag_db3(
                db3,
                topics=[(1, "/tf", "tf2_msgs/msg/TFMessage")],
                messages=[(1, 1, 1781020583610099932, b"corrupt-pose-progress")],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_pose_progress_decode_failed_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_pose_progress_replay"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertIn("route_bag_pose_progress_decode_failed", evidence["blocked_reasons"])
        self.assertEqual(evidence["pose_decode_failed_count"], 1)
        self.assertFalse(evidence["nonzero_pose_progress_observed"])

    def test_route_bag_pose_progress_replay_unsafe_topic_name_fail_closed_without_secret_echo(self):
        # unsafe topic 名必须 fail closed，不能借 pose progress contract 回显控制话题。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_route_bag_db3(
                db3,
                topics=[(1, "/cmd_vel", "tf2_msgs/msg/TFMessage")],
                messages=[(1, 1, 1781020583610099932, build_tf_message_cdr_payload(frame_pairs=[("map", "base_link")]))],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_pose_progress_unsafe_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_pose_progress_replay"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertIn("route_bag_pose_progress_unsafe_topic_name", evidence["blocked_reasons"])
        self.assertNotIn("/cmd_vel", evidence_text)
        self.assertFalse(evidence["nonzero_pose_progress_observed"])

    def test_route_bag_semantic_replay_ready_summary_is_additive_and_nested_under_field_motion_packet(self):
        # route bag semantic replay 在 manifest 顶层与 packet 中并行输出，可用于 O6/O7 只读语义检查。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_route_bag_db3(
                db3,
                topics=[
                    (1, "/scan", "sensor_msgs/msg/LaserScan"),
                    (2, "/camera/image_raw", "sensor_msgs/msg/Image"),
                    (3, "/tf_static", "tf2_msgs/msg/TFMessage"),
                    (4, "/odom", "nav_msgs/msg/Odometry"),
                    (5, "/diagnostics", "diagnostic_msgs/msg/DiagnosticArray"),
                ],
                messages=[
                    (1, 1, 1781020583610099932, build_laserscan_cdr_payload(
                        angle_min=-1.5708,
                        angle_max=1.5708,
                        angle_increment=0.0087,
                        range_min=0.05,
                        range_max=12.0,
                        ranges=[0.5, 0.6, float("nan"), 2.1],
                    )),
                    (2, 2, 1781020584610099932, build_image_cdr_payload(
                        width=640,
                        height=360,
                        encoding="rgb8",
                        step=1920,
                        data=b"image-bytes-a",
                    )),
                    (3, 3, 1781020588575096861, build_tf_message_cdr_payload(
                        frame_pairs=[("map", "camera_link"), ("base_link", "laser_frame")],
                    )),
                    (4, 4, 1781020589575096861, build_odometry_cdr_payload(
                        frame_id="odom",
                        child_frame_id="base_link",
                        x=1.25,
                        y=0.5,
                    )),
                    (5, 5, 1781020590575096861, build_diagnostic_array_cdr_payload(
                        statuses=[
                            {
                                "level": 0,
                                "name": "Base OK",
                                "message": "voltage nominal raw value token should not echo",
                                "hardware_id": "base_board",
                                "values": [{"key": "voltage_raw", "value": "token-secret"}],
                            },
                            {
                                "level": 2,
                                "name": "Lidar Warn",
                                "message": "Traceback /Users/m1/token",
                                "hardware_id": "lidar_front",
                                "values": [
                                    {"key": "temp", "value": "42C"},
                                    {"key": "url", "value": "https://robot:secret@example.com"},
                                ],
                            },
                        ],
                    )),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--route-bag-source-label",
                    "unit-route-bag-semantic",
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_semantic_packet_task",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_semantic_replay"]
            nested = packet["field_motion_evidence_packet"]["route_bag_semantic_replay"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA)
        self.assertEqual(evidence["proof_scope"], manifest.ROUTE_BAG_SEMANTIC_REPLAY_PROOF_SCOPE)
        self.assertEqual(evidence["status"], "ready_not_route_execution_proof")
        self.assertEqual(evidence["source_label"], "unit-route-bag-semantic")
        self.assertEqual(evidence["task_id"], "route_bag_semantic_packet_task")
        self.assertTrue(evidence["db3_present"])
        self.assertTrue(evidence["db3_read_ok"])
        self.assertTrue(evidence["sqlite_schema_ok"])
        self.assertEqual(evidence["db3_basename"], "route_bag_0.db3")
        self.assertEqual(evidence["topic_count"], 5)
        self.assertEqual(evidence["message_count"], 5)
        self.assertEqual(evidence["timestamp_first_ns"], 1781020583610099932)
        self.assertEqual(evidence["timestamp_last_ns"], 1781020590575096861)
        self.assertEqual(evidence["sample_topic_names"], ["/scan", "/camera/image_raw", "/tf_static", "/odom", "/diagnostics"])
        self.assertEqual(evidence["semantic_sample_count"], 5)
        self.assertEqual(evidence["semantic_decode_ok_count"], 5)
        self.assertEqual(evidence["semantic_decode_failed_count"], 0)
        self.assertEqual(
            evidence["semantic_topic_types"],
            [
                "diagnostic_msgs/msg/DiagnosticArray",
                "nav_msgs/msg/Odometry",
                "sensor_msgs/msg/Image",
                "sensor_msgs/msg/LaserScan",
                "tf2_msgs/msg/TFMessage",
            ],
        )
        self.assertEqual(evidence["laser_scan_summary"]["sample_count"], 1)
        self.assertGreater(evidence["laser_scan_summary"]["range_sample_count"], 0)
        self.assertEqual(evidence["image_summary"]["image_sample_count"], 1)
        self.assertEqual(evidence["image_summary"]["encodings"], ["rgb8"])
        self.assertEqual(evidence["image_summary"]["width_min"], 640)
        self.assertEqual(evidence["image_summary"]["height_min"], 360)
        self.assertEqual(evidence["tf_summary"]["tf_sample_count"], 1)
        self.assertEqual(evidence["tf_summary"]["transform_count_total"], 2)
        self.assertIn(["map", "camera_link"], evidence["tf_summary"]["frame_pairs"])
        self.assertEqual(evidence["odometry_summary"]["sample_count"], 1)
        self.assertEqual(evidence["odometry_summary"]["nonzero_translation_sample_count"], 0)
        self.assertEqual(evidence["odometry_summary"]["frame_pairs"], [["odom", "base_link"]])
        self.assertEqual(evidence["odometry_summary"]["start_translation"], {"x_m": 0.0, "y_m": 0.0, "z_m": 0.0})
        self.assertEqual(evidence["odometry_summary"]["end_translation"], {"x_m": 0.0, "y_m": 0.0, "z_m": 0.0})
        self.assertEqual(evidence["odometry_summary"]["translation_norm_min"], 0.0)
        self.assertEqual(evidence["odometry_summary"]["translation_norm_max"], 0.0)
        self.assertEqual(evidence["diagnostic_array_summary"]["sample_count"], 1)
        self.assertEqual(evidence["diagnostic_array_summary"]["status_count"], 2)
        self.assertEqual(evidence["diagnostic_array_summary"]["highest_level"], 2)
        self.assertEqual(evidence["diagnostic_array_summary"]["level_distribution"], {"0": 1, "2": 1})
        self.assertEqual(evidence["diagnostic_array_summary"]["status_name_samples"], ["Base OK", "Lidar Warn"])
        self.assertEqual(evidence["diagnostic_array_summary"]["hardware_id_samples"], ["base_board", "lidar_front"])
        self.assertEqual(evidence["diagnostic_array_summary"]["key_value_pair_count"], 3)
        self.assertEqual(evidence["blocked_reasons"], [])
        self.assertNotIn(str(root), evidence_text)
        self.assertNotIn(str(db3), evidence_text)
        self.assertNotIn("token-secret", evidence_text)
        self.assertNotIn("voltage_raw", evidence_text)
        self.assertNotIn("Traceback", evidence_text)
        self.assertNotIn("robot:secret", evidence_text)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["live_nav2_run_proven"])
        self.assertFalse(evidence["route_execution_success"])

    def test_route_bag_semantic_replay_missing_input_returns_blocked_summary_without_breaking_artifact_gate(self):
        # 路由 bag 不传时仍保留同形 blocked 摘要，不阻断 manifest gate。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            make_complete_fixture(root)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_semantic_missing_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_semantic_replay"]

        self.assertEqual(rc, 0)
        self.assertTrue(packet["gate_pass"])
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertFalse(evidence["db3_present"])
        self.assertFalse(evidence["db3_read_ok"])
        self.assertIn("route_bag_semantic_db3_missing", evidence["blocked_reasons"])
        self.assertIn("safe_route_bag_db3_with_safe_whitelist_semantic_messages", evidence["next_required_evidence"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])

    def test_route_bag_semantic_replay_invalid_db3_fails_closed_without_raw_echo(self):
        # 无效 sqlite 只输出 blocked 摘要，不回显 payload/path/secret 文本。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            make_complete_fixture(root)
            write_text(db3, "not a sqlite db\n")

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_semantic_invalid_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_semantic_replay"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertTrue(evidence["db3_present"])
        self.assertFalse(evidence["db3_read_ok"])
        self.assertIn("route_bag_semantic_db3_unreadable", evidence["blocked_reasons"])
        self.assertNotIn(str(db3), evidence_text)
        self.assertNotIn("not a sqlite db", evidence_text)
        self.assertFalse(evidence["delivery_success"])

    def test_route_bag_semantic_replay_decode_failed_for_corrupt_payload(self):
        # payload 解码失败时 fail-closed，不应抛异常，也不能伪造 ready 状态。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            make_complete_fixture(root)
            write_route_bag_db3(
                db3,
                topics=[(1, "/scan", "sensor_msgs/msg/LaserScan")],
                messages=[(1, 1, 1781020583610099932, b"\x00\x01\x02")],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_semantic_decode_failed_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_semantic_replay"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertEqual(evidence["semantic_sample_count"], 1)
        self.assertEqual(evidence["semantic_decode_ok_count"], 0)
        self.assertEqual(evidence["semantic_decode_failed_count"], 1)
        self.assertIn("route_bag_semantic_decode_failed", evidence["blocked_reasons"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])

    def test_route_bag_semantic_replay_unsafe_metadata_and_source_label_fail_closed_without_secret_echo(self):
        # metadata 与 source label 命中安全边界时返回 blocked 摘要，不透传 secret。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_route_bag_db3(
                db3,
                topics=[(1, "/scan", "sensor_msgs/msg/LaserScan")],
                messages=[
                    (1, 1, 1781020583610099932, build_laserscan_cdr_payload(
                        angle_min=-1.0,
                        angle_max=1.0,
                        angle_increment=0.02,
                        range_min=0.05,
                        range_max=10.0,
                        ranges=[0.9],
                    )),
                ],
            )
            write_text(
                metadata,
                "safe_to_control: true\ncallback: https://robot:supersecret@example.com/cb\nraw_payload: base64:SECRET_ROUTE_BAG\n",
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--route-bag-source-label",
                    "https://robot:supersecret@example.com/route_bag",
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_semantic_unsafe_packet",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_semantic_replay"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertIsNone(evidence["source_label"])
        self.assertIn("route_bag_metadata_dangerous_true_claim", evidence["blocked_reasons"])
        self.assertIn("route_bag_metadata_unsafe_text", evidence["blocked_reasons"])
        self.assertIn("route_bag_semantic_source_label_unsafe_text", evidence["blocked_reasons"])
        self.assertEqual(evidence["dangerous_true_fields"], ["safe_to_control"])
        self.assertGreaterEqual(evidence["unsafe_text_field_count"], 2)
        self.assertNotIn("supersecret", evidence_text)
        self.assertNotIn("SECRET_ROUTE_BAG", evidence_text)
        self.assertNotIn(str(root), evidence_text)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["robot_control_executed"])

    def test_route_bag_full_semantic_decode_matrix_ready_counts_decoded_unsupported_and_failed(self):
        # full matrix 必须按 topic/type 输出真实覆盖，不允许只新增 wrapper 或隐藏 unsupported/failed。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_route_bag_db3(
                db3,
                topics=[
                    (1, "/scan", "sensor_msgs/msg/LaserScan"),
                    (2, "/diagnostics", "diagnostic_msgs/msg/DiagnosticArray"),
                    (3, "/camera/image_raw", "sensor_msgs/msg/Image"),
                    (4, "/odom", "nav_msgs/msg/Odometry"),
                    (5, "/diagnostics_custom", "custom_msgs/msg/Diagnostics"),
                ],
                messages=[
                    (1, 1, 1781020583610099932, build_laserscan_cdr_payload(
                        angle_min=-1.0,
                        angle_max=1.0,
                        angle_increment=0.02,
                        range_min=0.05,
                        range_max=10.0,
                        ranges=[0.9, 1.2],
                    )),
                    (2, 2, 1781020584610099932, build_diagnostic_array_cdr_payload(
                        statuses=[
                            {
                                "level": 1,
                                "name": "Battery Warn",
                                "message": "raw diagnostic traceback /Users/m1/token should stay private",
                                "hardware_id": "power_board",
                                "values": [{"key": "secret_key", "value": "SECRET_DIAGNOSTIC_VALUE"}],
                            }
                        ],
                    )),
                    (3, 3, 1781020585610099932, b"\x00\x01\x02"),
                    (4, 4, 1781020586610099932, build_odometry_cdr_payload(
                        frame_id="odom",
                        child_frame_id="base_link",
                        x=0.75,
                        y=0.25,
                    )),
                    (5, 5, 1781020587610099932, b"unsupported-custom-payload"),
                ],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--route-bag-source-label",
                    "unit-route-bag-full-semantic-matrix",
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_full_semantic_matrix_task",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_full_semantic_decode_matrix"]
            nested = packet["field_motion_evidence_packet"]["route_bag_full_semantic_decode_matrix"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence, nested)
        self.assertEqual(evidence["schema"], manifest.ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA)
        self.assertEqual(evidence["proof_scope"], manifest.ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_PROOF_SCOPE)
        self.assertEqual(evidence["status"], "ready_not_route_execution_proof")
        self.assertEqual(evidence["source_label"], "unit-route-bag-full-semantic-matrix")
        self.assertTrue(evidence["db3_read_ok"])
        self.assertTrue(evidence["sqlite_schema_ok"])
        self.assertEqual(evidence["topic_count"], 5)
        self.assertEqual(evidence["message_count"], 5)
        self.assertEqual(evidence["topic_type_count"], 5)
        self.assertEqual(evidence["decoded_topic_type_count"], 3)
        self.assertEqual(evidence["unsupported_topic_type_count"], 1)
        self.assertEqual(evidence["failed_topic_type_count"], 1)
        self.assertEqual(evidence["decoded_message_sample_count"], 3)
        self.assertEqual(evidence["unsupported_message_sample_count"], 1)
        self.assertEqual(evidence["decode_failed_message_sample_count"], 1)
        self.assertEqual(evidence["coverage_ratio"], 0.6)
        self.assertIn("route_bag_full_semantic_decode_matrix_unsupported_topic_type", evidence["blocked_reasons"])
        self.assertIn("route_bag_full_semantic_decode_matrix_decode_failed", evidence["blocked_reasons"])
        matrix_by_topic = {
            (item["topic_name"], item["topic_type"]): item
            for item in evidence["topic_type_matrix"]
        }
        allowed_item_keys = {
            "topic_name",
            "topic_type",
            "message_count",
            "sampled_message_count",
            "decoded_message_sample_count",
            "decode_failed_message_sample_count",
            "unsupported_message_sample_count",
            "status",
            "blocked_reason",
            "decoder_name",
            "sample_sha256_prefixes",
        }
        for item in evidence["topic_type_matrix"]:
            self.assertEqual(set(item.keys()), allowed_item_keys)
            for digest_prefix in item["sample_sha256_prefixes"]:
                self.assertRegex(digest_prefix, r"^[0-9a-f]{12}$")
        self.assertEqual(matrix_by_topic[("/scan", "sensor_msgs/msg/LaserScan")]["status"], "decoded")
        self.assertEqual(matrix_by_topic[("/scan", "sensor_msgs/msg/LaserScan")]["decoder_name"], "decode_laserscan_payload")
        self.assertEqual(matrix_by_topic[("/odom", "nav_msgs/msg/Odometry")]["status"], "decoded")
        self.assertEqual(matrix_by_topic[("/odom", "nav_msgs/msg/Odometry")]["decoder_name"], "decode_odometry_payload")
        self.assertEqual(matrix_by_topic[("/diagnostics", "diagnostic_msgs/msg/DiagnosticArray")]["status"], "decoded")
        self.assertEqual(
            matrix_by_topic[("/diagnostics", "diagnostic_msgs/msg/DiagnosticArray")]["decoder_name"],
            "decode_diagnostic_array_payload",
        )
        self.assertEqual(matrix_by_topic[("/diagnostics_custom", "custom_msgs/msg/Diagnostics")]["status"], "unsupported")
        self.assertIsNone(matrix_by_topic[("/diagnostics_custom", "custom_msgs/msg/Diagnostics")]["decoder_name"])
        self.assertEqual(matrix_by_topic[("/camera/image_raw", "sensor_msgs/msg/Image")]["status"], "failed")
        self.assertNotIn(str(root), evidence_text)
        self.assertNotIn(str(db3), evidence_text)
        self.assertNotIn("unsupported-custom-payload", evidence_text)
        self.assertNotIn("SECRET_DIAGNOSTIC_VALUE", evidence_text)
        self.assertNotIn("secret_key", evidence_text)
        self.assertNotIn("traceback", evidence_text)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])
        self.assertFalse(evidence["robot_control_executed"])
        self.assertFalse(evidence["live_nav2_run_proven"])
        self.assertFalse(evidence["route_execution_success"])

    def test_route_bag_full_semantic_decode_matrix_missing_input_returns_blocked_summary(self):
        # 缺 DB3 时只阻断 additive，不影响 artifact gate，也不能伪造 matrix coverage。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            make_complete_fixture(root)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_full_semantic_matrix_missing",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_full_semantic_decode_matrix"]

        self.assertEqual(rc, 0)
        self.assertTrue(packet["gate_pass"])
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertFalse(evidence["db3_present"])
        self.assertFalse(evidence["db3_read_ok"])
        self.assertEqual(evidence["topic_type_count"], 0)
        self.assertEqual(evidence["coverage_ratio"], 0.0)
        self.assertIn("route_bag_full_semantic_decode_matrix_db3_missing", evidence["blocked_reasons"])
        self.assertIn("safe_route_bag_db3_with_decodable_semantic_topic_types", evidence["next_required_evidence"])
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["primary_actions_enabled"])

    def test_route_bag_full_semantic_decode_matrix_unsupported_only_stays_blocked(self):
        # 只有 unknown safe type 时可以展示 unsupported matrix，但没有 decoded type 不能 ready。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            make_complete_fixture(root)
            write_route_bag_db3(
                db3,
                topics=[(1, "/diagnostics", "custom_msgs/msg/Diagnostics")],
                messages=[(1, 1, 1781020583610099932, b"unsupported-only")],
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_full_semantic_matrix_unsupported",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_full_semantic_decode_matrix"]

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertEqual(evidence["topic_type_count"], 1)
        self.assertEqual(evidence["decoded_topic_type_count"], 0)
        self.assertEqual(evidence["unsupported_topic_type_count"], 1)
        self.assertEqual(evidence["failed_topic_type_count"], 0)
        self.assertEqual(evidence["unsupported_message_sample_count"], 1)
        self.assertEqual(evidence["coverage_ratio"], 0.0)
        self.assertEqual(evidence["topic_type_matrix"][0]["status"], "unsupported")
        self.assertIn("route_bag_full_semantic_decode_matrix_decoded_topic_type_missing", evidence["blocked_reasons"])
        self.assertIn("route_bag_full_semantic_decode_matrix_unsupported_topic_type", evidence["blocked_reasons"])

    def test_route_bag_full_semantic_decode_matrix_unsafe_topic_type_and_text_fail_closed(self):
        # unsafe topic/type/source/metadata 必须 fail-closed，且不能把 /cmd_vel、路径或 secret 写入 matrix。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            db3 = root / "route_bag" / "route_bag_0.db3"
            metadata = root / "route_bag" / "metadata.yaml"
            make_complete_fixture(root)
            write_route_bag_db3(
                db3,
                topics=[
                    (1, "/cmd_vel", "geometry_msgs/msg/Twist"),
                    (2, "/scan", "/Users/m1/secret/RawType"),
                ],
                messages=[
                    (1, 1, 1781020583610099932, b"control-payload"),
                    (2, 2, 1781020584610099932, b"type-path-payload"),
                ],
            )
            write_text(
                metadata,
                "safe_to_control: true\ncallback: https://robot:supersecret@example.com/cb\nraw_payload: base64:SECRET_ROUTE_BAG\n",
            )

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--route-bag-db3",
                    str(db3),
                    "--route-bag-metadata-yaml",
                    str(metadata),
                    "--route-bag-source-label",
                    "https://robot:supersecret@example.com/route_bag",
                    "--output",
                    str(output),
                    "--run-id",
                    "route_bag_full_semantic_matrix_unsafe",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            evidence = packet["route_bag_full_semantic_decode_matrix"]
            evidence_text = json.dumps(evidence, ensure_ascii=False)

        self.assertEqual(rc, 0)
        self.assertEqual(evidence["status"], "blocked_not_proven")
        self.assertIsNone(evidence["source_label"])
        self.assertEqual(evidence["topic_type_count"], 0)
        self.assertIn("route_bag_metadata_dangerous_true_claim", evidence["blocked_reasons"])
        self.assertIn("route_bag_metadata_unsafe_text", evidence["blocked_reasons"])
        self.assertIn("route_bag_full_semantic_decode_matrix_source_label_unsafe_text", evidence["blocked_reasons"])
        self.assertIn("route_bag_full_semantic_decode_matrix_unsafe_topic_name", evidence["blocked_reasons"])
        self.assertIn("route_bag_full_semantic_decode_matrix_unsafe_topic_type", evidence["blocked_reasons"])
        self.assertEqual(evidence["dangerous_true_fields"], ["safe_to_control"])
        self.assertGreaterEqual(evidence["unsafe_field_count"], 2)
        self.assertGreaterEqual(evidence["unsafe_text_field_count"], 2)
        self.assertNotIn("/cmd_vel", evidence_text)
        self.assertNotIn("/Users/m1", evidence_text)
        self.assertNotIn("supersecret", evidence_text)
        self.assertNotIn("SECRET_ROUTE_BAG", evidence_text)
        self.assertNotIn("control-payload", evidence_text)
        self.assertFalse(evidence["safe_to_control"])
        self.assertFalse(evidence["delivery_success"])
        self.assertFalse(evidence["robot_control_executed"])


if __name__ == "__main__":
    unittest.main()
