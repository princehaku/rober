#!/usr/bin/env python3
"""本地复跑 O5 same-task archive smoke。

该脚本只使用 in-process relay、本地临时文件和 mock 材料，
验证 O5 reconciliation v2 -> manifest -> O6 archive -> O6 consumer 的软件链路。
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import struct
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "onboard" / "scripts"
BEHAVIOR_SRC = WORKSPACE_ROOT / "onboard" / "src" / "ros2_trashbot_behavior"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(BEHAVIOR_SRC) not in sys.path:
    sys.path.insert(0, str(BEHAVIOR_SRC))

import field_route_evidence_manifest as manifest  # noqa: E402
from ros2_trashbot_behavior.remote_cloud_relay import (  # noqa: E402
    CLOUD_DB_QUEUE_EXTERNAL_PROBE_EVIDENCE_BOUNDARY,
    CLOUD_DB_QUEUE_EXTERNAL_PROBE_SCHEMA,
    CLOUD_EXTERNAL_PROBE_EVIDENCE_BOUNDARY,
    CLOUD_EXTERNAL_PROBE_SCHEMA,
    build_server,
    cloud_db_queue_external_probe_bundle_summary,
    cloud_external_probe_bundle_summary,
    create_cloud_db_queue_external_probe_bundle_artifact,
    create_cloud_external_probe_bundle_artifact,
    O6_CLOUD_DB_QUEUE_EXTERNAL_PROBE_READBACK_SCHEMA,
    O6_CLOUD_EXTERNAL_PROBE_READBACK_SCHEMA,
    PROTOCOL_VERSION,
)


SMOKE_SCHEMA = "trashbot.o5.same_task_mission_archive_smoke.v1"
SMOKE_PROOF_BOUNDARY = "software_proof_o5_o6_live_endpoint_probe_readback_only"


class RelayHttpClient:
    """最小 HTTP 客户端，保持和 relay unittest 同源的请求习惯。"""

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=3.0) as response:
                body = response.read().decode("utf-8") or "{}"
                return response.status, json.loads(body)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8") or "{}"
            return exc.code, json.loads(body)


def write_text(path: Path, text: str) -> None:
    # smoke 材料全部在临时目录中自造，避免误读真实现场包。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _pack_cdr_u32(value: int) -> bytes:
    # route bag fixture 只需要最小可解析 CDR 结构，不引入额外依赖。
    return struct.pack("<I", int(value))


def _pack_cdr_float64(value: float) -> bytes:
    # TF/Odometry 位姿摘要走 float64，保持和解析器端一致。
    return struct.pack("<d", float(value))


def _pack_cdr_string(value: str) -> bytes:
    # CDR string 需要长度加结尾 NUL，否则解析器会把样本视为坏包。
    data = value.encode("utf-8")
    return _pack_cdr_u32(len(data) + 1) + data + b"\x00"


def _pack_cdr_bytes(payload: bytes, align: int) -> bytes:
    # 这里显式补齐对齐，是为了让本地 mock DB3 走到真实解析分支。
    pad = (align - (len(payload) % align)) % align
    return payload + (b"\x00" * pad)


def build_tf_message_cdr_payload(
    *,
    frame_pairs: list[tuple[str, str]],
    translations: list[tuple[float, float, float]],
) -> bytes:
    # TF 样本只写 frame id 和平移量，足够派生 nonzero pose progress。
    payload = bytearray()
    payload.extend(_pack_cdr_u32(1))
    payload.extend(_pack_cdr_u32(2))
    payload.extend(_pack_cdr_u32(3))
    payload.extend(_pack_cdr_string("tf_root"))
    payload.extend(_pack_cdr_u32(len(frame_pairs)))
    for index, (parent_frame_id, child_frame_id) in enumerate(frame_pairs):
        x_m, y_m, z_m = translations[index]
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
    # Odom 样本补一帧，确保 pose progress 既能读 TF 也能读 Odometry。
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


def write_route_bag_db3(path: Path, *, topics: list[tuple[int, str, str]], messages: list[tuple[int, int, int, bytes]]) -> None:
    # DB3 只建 manifest 解析所需的最小表结构，避免把 smoke 扩成 rosbag2 runtime。
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "CREATE TABLE topics(id INTEGER PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL, serialization_format TEXT NOT NULL, offered_qos_profiles TEXT NOT NULL)"
        )
        for topic_id, name, topic_type in topics:
            connection.execute(
                "INSERT INTO topics(id, name, type, serialization_format, offered_qos_profiles) VALUES (?, ?, ?, 'cdr', '')",
                (topic_id, name, topic_type),
            )
        connection.execute(
            "CREATE TABLE messages(id INTEGER PRIMARY KEY, topic_id INTEGER NOT NULL, timestamp INTEGER NOT NULL, data BLOB NOT NULL)"
        )
        for message_id, topic_id, timestamp, payload in messages:
            connection.execute(
                "INSERT INTO messages(id, topic_id, timestamp, data) VALUES (?, ?, ?, ?)",
                (message_id, topic_id, timestamp, sqlite3.Binary(bytes(payload))),
            )
        connection.commit()
    finally:
        connection.close()


def make_complete_fixture(root: Path) -> None:
    # route/map/keyframe/replay 都用固定 mock 材料，证明的是合同连通，不是真实路线执行。
    write_text(root / "map.yaml", "image: map.pgm\nresolution: 0.05\n")
    write_text(root / "map.pgm", "P5 1 1 255 0")
    write_text(root / "route.csv", "x,y,yaw\n0,0,0\n1,0,0\n")
    write_text(root / "manifest.json", '{"schema":"trashbot.vision_samples.v1","samples":[]}\n')
    write_text(root / "keyframes" / "0001.json", '{"x":0,"y":0}\n')
    write_text(root / "fixed_route_replay.jsonl", '{"event":"start"}\n{"event":"done"}\n')
    write_text(root / "route_bag" / "metadata.yaml", "rosbag2_bagfile_information:\n")


def make_motion_log_fixture(root: Path) -> None:
    # motion log 固定声明非零位移，仅作为软件证据输入，不触发任何真实控制。
    write_text(
        root / "pulse_and_stop2.log",
        "\n".join(
            [
                "2026-06-10T01:18:47+08:00",
                "pulse2_start",
                "publisher: beginning loop",
                "publishing #1: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=0.03, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.0))",
                "2026-06-10T01:19:04+08:00",
                "pulse2_done",
            ]
        )
        + "\n",
    )
    write_text(
        root / "waypoint_progress.log",
        "\n".join(
            [
                "waypoint_index=0,x=0.00,y=0.00",
                "waypoint_index=1,x=0.17,y=0.02",
            ]
        )
        + "\n",
    )


def write_nav2_goal_proof(path: Path, *, task_id: str) -> None:
    # Nav2 proof 固定为 mock succeeded，但安全字段全部 fail-closed。
    payload = {
        "schema": manifest.O11_NAV2_GOAL_PROOF_SCHEMA,
        "task_id": task_id,
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


@contextmanager
def patched_env(updates: dict[str, str]):
    # relay 用环境变量选 O6 state path；这里局部覆盖，避免污染调用方环境。
    previous = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            os.environ[key] = value
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def build_terminal_result_payload(*, robot_id: str, command_id: str) -> dict[str, Any]:
    # terminal result 只提供 manifest 允许消费的安全摘要字段。
    return {
        "schema": manifest.CLOUD_COMMAND_TERMINAL_RESULT_SCHEMA,
        "schema_version": 1,
        "robot_id": robot_id,
        "command_id": command_id,
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


def _assert_http(status: int, payload: dict[str, Any], expected_status: int, step: str) -> None:
    # smoke 失败时抛出简洁步骤名，便于 unittest 和 worker report 定位。
    if status != expected_status:
        raise RuntimeError(f"{step} failed with status {status}: {json.dumps(payload, ensure_ascii=False)}")


def _safe_basename(path_text: str | None) -> str:
    # 对外只回显 basename，避免把临时目录路径带入报告或文档。
    return Path(path_text).name if path_text else ""


def start_relay_server(state_path: Path, *, state_backend: str, token: str) -> tuple[Any, threading.Thread, RelayHttpClient]:
    # 每次启动都通过 build_server 注入 backend，SQLite shadow 要验证同一路径可被新进程语义读回。
    server = build_server("127.0.0.1", 0, state_path, token, state_backend=state_backend)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    client = RelayHttpClient(f"http://127.0.0.1:{server.server_address[1]}", token)
    return server, thread, client


def stop_relay_server(server: Any | None, thread: threading.Thread | None) -> None:
    # 显式关闭 socket，避免 SQLite restart path 因旧 server 未释放端口而误判。
    if server is None or thread is None:
        return
    server.shutdown()
    server.server_close()
    thread.join(timeout=1.0)


def build_archive_safe_manifest_payload(
    raw_manifest: dict[str, Any], *, robot_id: str, task_id: str
) -> dict[str, Any]:
    # O6 全局闸门会扫描所有键名；这里在不改 Algorithm 文件的前提下裁掉中间态块。
    payload = json.loads(json.dumps(raw_manifest))
    payload["robot_id"] = robot_id
    payload["task_id"] = task_id
    # same-task smoke 只需要 additive 摘要进入 archive/readback，不需要整段 field_motion 中间快照。
    payload.pop("field_motion_evidence_packet", None)
    same_task_gate = payload.get("same_task_mission_evidence_gate")
    if isinstance(same_task_gate, dict):
        refs = same_task_gate.get("terminal_refs")
        if isinstance(refs, dict):
            ref_list = [
                refs.get("command_id_ref"),
                refs.get("task_record_ref"),
                refs.get("evidence_ref"),
            ]
            same_task_gate["terminal_refs"] = [item for item in ref_list if isinstance(item, str) and item]
        delta = same_task_gate.get("mission_artifact_delta")
        if isinstance(delta, dict):
            same_task_gate["mission_artifact_delta"] = "cloud_terminal_route_execution_closure_pose_same_task"
        linked_flags = same_task_gate.get("linked_readiness_flags")
        if isinstance(linked_flags, dict):
            same_task_gate["linked_readiness_flags"] = {
                "delivery_result_evidence_ready": bool(linked_flags.get("delivery_result_evidence_ready")),
                "cloud_terminal_result_ready": bool(linked_flags.get("cloud_terminal_result_source_consumed")),
                "route_execution_result_delivery_readiness_ready": bool(
                    linked_flags.get("route_execution_result_delivery_readiness_ready")
                ),
                "route_delivery_closure_packet_ready": bool(linked_flags.get("route_delivery_closure_ready")),
                "route_bag_pose_progress_replay_ready": bool(
                    linked_flags.get("route_bag_pose_progress_ready")
                    or linked_flags.get("nonzero_pose_progress_observed")
                ),
                "same_task_id_match": bool(linked_flags.get("same_task_id_matched")),
            }
        same_task_gate["linked_delivery_result_evidence_ready"] = bool(
            same_task_gate["linked_readiness_flags"].get("delivery_result_evidence_ready")
        )
        same_task_gate["linked_cloud_terminal_result_ready"] = bool(
            same_task_gate["linked_readiness_flags"].get("cloud_terminal_result_ready")
        )
        same_task_gate["linked_route_execution_result_delivery_readiness_ready"] = bool(
            same_task_gate["linked_readiness_flags"].get("route_execution_result_delivery_readiness_ready")
        )
        same_task_gate["linked_route_delivery_closure_packet_ready"] = bool(
            same_task_gate["linked_readiness_flags"].get("route_delivery_closure_packet_ready")
        )
        same_task_gate["linked_route_bag_pose_progress_replay_ready"] = bool(
            same_task_gate["linked_readiness_flags"].get("route_bag_pose_progress_replay_ready")
        )
        same_task_gate["same_task_id_match"] = bool(same_task_gate["linked_readiness_flags"].get("same_task_id_match"))
        same_task_gate["same_task_id_consumed"] = bool(same_task_gate["linked_readiness_flags"].get("same_task_id_match"))
    return payload


def build_cloud_external_probe_readback(summary: dict[str, Any], *, task_id: str) -> dict[str, Any]:
    # 这里复用 relay 现有 summary 逻辑，只把 O6 读回真正需要的白名单字段落进 archive。
    is_ready = bool(summary.get("ok")) and bool(summary.get("endpoint_contract_ready"))
    return {
        "schema": O6_CLOUD_EXTERNAL_PROBE_READBACK_SCHEMA,
        "source_schema": CLOUD_EXTERNAL_PROBE_SCHEMA,
        "proof_scope": CLOUD_EXTERNAL_PROBE_EVIDENCE_BOUNDARY,
        "task_id": task_id,
        "status": "cloud_external_probe_ready_not_production_proof" if is_ready else "blocked_not_proven",
        "source": "o5_same_task_mission_archive_smoke" if is_ready else "",
        "endpoint_count": int(summary.get("endpoint_count") or 0) if is_ready else 0,
        "endpoints_covered": list(summary.get("endpoints_covered") or []) if is_ready else [],
        "endpoint_contract_ready": bool(summary.get("endpoint_contract_ready")) if is_ready else False,
        "base_url_scheme": "http" if is_ready else "",
        "blocked_reasons": [] if is_ready else ["cloud_external_probe_not_ready"],
        "next_required_evidence": [
            "real_public_https_probe",
            "production_cloud_trace",
        ],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "connects_cloud_production": False,
    }


def build_cloud_db_queue_external_probe_readback(summary: dict[str, Any], *, task_id: str) -> dict[str, Any]:
    # DB/queue probe 当前仍是 blocked-by-design，本轮只把枚举化诊断状态并入 same-task readback。
    is_ready = bool(summary.get("ok")) and int(summary.get("probe_count") or 0) > 0
    return {
        "schema": O6_CLOUD_DB_QUEUE_EXTERNAL_PROBE_READBACK_SCHEMA,
        "source_schema": CLOUD_DB_QUEUE_EXTERNAL_PROBE_SCHEMA,
        "proof_scope": CLOUD_DB_QUEUE_EXTERNAL_PROBE_EVIDENCE_BOUNDARY,
        "task_id": task_id,
        "status": "cloud_db_queue_external_probe_ready_not_production_proof" if is_ready else "blocked_not_proven",
        "source": "o5_same_task_mission_archive_smoke" if is_ready else "",
        "probe_count": int(summary.get("probe_count") or 0) if is_ready else 0,
        "probe_names": list(summary.get("probe_names") or []) if is_ready else [],
        "probe_statuses": {
            "db_connectivity_status": summary.get("db_connectivity_status"),
            "queue_connectivity_status": summary.get("queue_connectivity_status"),
            "migration_check_status": summary.get("migration_check_status"),
            "worker_check_status": summary.get("worker_check_status"),
            "multi_instance_consistency_status": summary.get("multi_instance_consistency_status"),
            "ordering_check_status": summary.get("ordering_check_status"),
            "transaction_isolation_status": summary.get("transaction_isolation_status"),
            "backup_recovery_status": summary.get("backup_recovery_status"),
        }
        if is_ready
        else {},
        "external_probe_complete": False,
        "blocked_reasons": [] if is_ready else ["cloud_db_queue_external_probe_not_ready"],
        "next_required_evidence": [
            "real_db_queue_probe",
            "production_db_queue_trace",
        ],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "connects_cloud_production": False,
    }


def run_smoke(
    *,
    task_id: str = "o5-reconciliation-same-task-smoke-001",
    robot_id: str = "trashbot-001",
    state_backend: str = "file",
) -> dict[str, Any]:
    # 整个 smoke 在单个临时目录中闭环，确保可复跑且不会触碰真实硬件/外网。
    normalized_backend = str(state_backend or "file").strip()
    if normalized_backend not in {"file", "sqlite"}:
        raise ValueError("state_backend must be one of: file, sqlite")
    with tempfile.TemporaryDirectory(prefix="o5-same-task-smoke-") as tmpdir:
        tmp_root = Path(tmpdir)
        artifact_root = tmp_root / "field_evidence"
        manifest_output = tmp_root / "field_evidence_manifest.json"
        nav2_proof = tmp_root / "nav2_goal_proof.json"
        reconciliation_json = tmp_root / "cloud_command_result_reconciliation.json"
        cloud_external_probe_artifact = tmp_root / "cloud_external_probe.json"
        cloud_db_queue_external_probe_artifact = tmp_root / "cloud_db_queue_external_probe.json"
        route_bag_db3 = artifact_root / "route_bag" / "route_bag_0.db3"
        route_bag_metadata = artifact_root / "route_bag" / "metadata.yaml"
        relay_state = tmp_root / ("relay_state.sqlite" if normalized_backend == "sqlite" else "relay_state.json")
        archive_state = tmp_root / "o6_archive_state.json"
        command_id = "o5-same-task-command-001"
        token = "phone-token"
        relay_restart_readback = False
        sqlite_state_store_reopened = False

        make_complete_fixture(artifact_root)
        write_nav2_goal_proof(nav2_proof, task_id=task_id)
        write_route_bag_db3(
            route_bag_db3,
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

        with patched_env({"TRASHBOT_O6_CLOUD_ARCHIVE_STATE": str(archive_state)}):
            server, thread, client = start_relay_server(relay_state, state_backend=normalized_backend, token=token)
            try:
                submit_status, submit_payload = client.request(
                    "POST",
                    "/api/commands/confirm-dropoff",
                    {
                        "robot_id": robot_id,
                        "command_id": command_id,
                        "idempotency_key": f"{command_id}-submit",
                        "payload": {
                            "task_id": task_id,
                            "reason": "local_mock_same_task_archive_smoke",
                        },
                    },
                )
                _assert_http(submit_status, submit_payload, 201, "submit_command")

                status_post_status, _ = client.request(
                    "POST",
                    f"/robots/{robot_id}/status",
                    {
                        "protocol_version": PROTOCOL_VERSION,
                        "state": "delivering",
                        "message": "local mock same-task smoke",
                        "updated_at": time.time(),
                    },
                )
                if status_post_status != 200:
                    raise RuntimeError("post_status failed")

                ack_status, ack_payload = client.request(
                    "POST",
                    f"/robots/{robot_id}/commands/{command_id}/ack",
                    {
                        "protocol_version": PROTOCOL_VERSION,
                        "state": "acked",
                        "message": "mock ack before terminal result",
                        "updated_at": time.time(),
                        "result": {"delivery_success": False},
                    },
                )
                _assert_http(ack_status, ack_payload, 200, "post_ack")

                terminal_status, terminal_payload = client.request(
                    "POST",
                    f"/robots/{robot_id}/commands/{command_id}/terminal-result",
                    build_terminal_result_payload(robot_id=robot_id, command_id=command_id),
                )
                _assert_http(terminal_status, terminal_payload, 201, "post_terminal_result")

                if normalized_backend == "sqlite":
                    # SQLite shadow 的核心验收点：terminal result 已落库后，relay 必须关闭再重启读回。
                    stop_relay_server(server, thread)
                    server = None
                    thread = None
                    server, thread, client = start_relay_server(
                        relay_state,
                        state_backend=normalized_backend,
                        token=token,
                    )
                    sqlite_state_store_reopened = True

                reconciliation_status, reconciliation_payload = client.request(
                    "GET",
                    f"/api/commands/{command_id}/result?robot_id={robot_id}",
                )
                _assert_http(reconciliation_status, reconciliation_payload, 200, "get_reconciliation")
                relay_restart_readback = normalized_backend == "sqlite"
                reconciliation_json.write_text(
                    json.dumps(reconciliation_payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                create_cloud_external_probe_bundle_artifact(
                    cloud_external_probe_artifact,
                    client.base_url,
                )
                cloud_external_probe_summary = cloud_external_probe_bundle_summary(cloud_external_probe_artifact)
                create_cloud_db_queue_external_probe_bundle_artifact(
                    cloud_db_queue_external_probe_artifact,
                    {
                        "TRASHBOT_REMOTE_CLOUD_DB_CONNECTIVITY_EXTERNAL_PROBE_STATUS": "not_externally_proven",
                        "TRASHBOT_REMOTE_CLOUD_QUEUE_CONNECTIVITY_EXTERNAL_PROBE_STATUS": "not_externally_proven",
                        "TRASHBOT_REMOTE_CLOUD_DB_MIGRATION_EXTERNAL_PROBE_STATUS": "not_externally_proven",
                        "TRASHBOT_REMOTE_CLOUD_QUEUE_WORKER_EXTERNAL_PROBE_STATUS": "not_externally_proven",
                        "TRASHBOT_REMOTE_CLOUD_MULTI_INSTANCE_EXTERNAL_PROBE_STATUS": "not_externally_proven",
                        "TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_EXTERNAL_PROBE_STATUS": "not_externally_proven",
                        "TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_EXTERNAL_PROBE_STATUS": "not_externally_proven",
                        "TRASHBOT_REMOTE_CLOUD_BACKUP_RECOVERY_EXTERNAL_PROBE_STATUS": "not_externally_proven",
                    },
                )
                cloud_db_queue_external_probe_summary = cloud_db_queue_external_probe_bundle_summary(
                    cloud_db_queue_external_probe_artifact
                )

                manifest_rc = manifest.main(
                    [
                        "--mode",
                        "local",
                        "--artifact-root",
                        str(artifact_root),
                        "--nav2-goal-proof-json",
                        str(nav2_proof),
                        "--cloud-terminal-result-json",
                        str(reconciliation_json),
                        "--route-bag-db3",
                        str(route_bag_db3),
                        "--route-bag-metadata-yaml",
                        str(route_bag_metadata),
                        "--route-bag-source-label",
                        "o5_same_task_archive_smoke",
                        "--output",
                        str(manifest_output),
                        "--run-id",
                        task_id,
                    ]
                )
                if manifest_rc != 0:
                    raise RuntimeError(f"manifest_main failed with rc={manifest_rc}")
                manifest_payload = json.loads(manifest_output.read_text(encoding="utf-8"))
                archive_manifest_payload = build_archive_safe_manifest_payload(
                    manifest_payload,
                    robot_id=robot_id,
                    task_id=task_id,
                )
                archive_manifest_payload["cloud_external_probe"] = build_cloud_external_probe_readback(
                    cloud_external_probe_summary,
                    task_id=task_id,
                )
                archive_manifest_payload["cloud_db_queue_external_probe"] = (
                    build_cloud_db_queue_external_probe_readback(
                        cloud_db_queue_external_probe_summary,
                        task_id=task_id,
                    )
                )

                archive_status_code, archive_payload = client.request(
                    "POST",
                    "/api/o6/archive/field-evidence",
                    archive_manifest_payload,
                )
                if archive_status_code not in (200, 201):
                    raise RuntimeError(
                        f"archive_field_evidence failed with status {archive_status_code}: "
                        f"{json.dumps(archive_payload, ensure_ascii=False)}"
                    )

                archive_detail_status, archive_detail_payload = client.request(
                    "GET",
                    f"/api/o6/archive/tasks/{task_id}",
                )
                _assert_http(archive_detail_status, archive_detail_payload, 200, "get_archive_detail")

                consumer_status, consumer_payload = client.request(
                    "GET",
                    f"/api/o6/consumer/tasks/{task_id}?include=same_task_mission_evidence_gate,cloud_external_probe,cloud_db_queue_external_probe",
                )
                _assert_http(consumer_status, consumer_payload, 200, "get_consumer_detail")
            finally:
                stop_relay_server(server, thread)

        manifest_gate = manifest_payload["same_task_mission_evidence_gate"]
        archive_gate = archive_detail_payload["task"]["field_evidence"]["same_task_mission_evidence_gate"]
        consumer_gate = consumer_payload["same_task_mission_evidence_gate"]
        archive_cloud_external_probe = archive_detail_payload["task"]["field_evidence"]["cloud_external_probe"]
        archive_cloud_db_queue_external_probe = archive_detail_payload["task"]["field_evidence"][
            "cloud_db_queue_external_probe"
        ]
        consumer_cloud_external_probe = consumer_payload["cloud_external_probe"]
        consumer_cloud_db_queue_external_probe = consumer_payload["cloud_db_queue_external_probe"]
        summary = {
            "schema": SMOKE_SCHEMA,
            "proof_boundary": SMOKE_PROOF_BOUNDARY,
            "status": "ready" if consumer_gate.get("status") == "same_task_mission_gate_ready_not_success_proof" else "blocked_not_proven",
            "robot_id": robot_id,
            "task_id": task_id,
            "command_id": command_id,
            "relay_state_backend": normalized_backend,
            "relay_restart_readback": relay_restart_readback,
            "sqlite_state_store_reopened": sqlite_state_store_reopened,
            "artifact_root_basename": artifact_root.name,
            "reconciliation": {
                "schema": reconciliation_payload.get("schema"),
                "command_state": reconciliation_payload.get("command_state"),
                "ack_state": reconciliation_payload.get("ack_state"),
                "result_state": reconciliation_payload.get("result_state"),
                "terminal_result_schema": ((reconciliation_payload.get("terminal_result") or {}).get("schema")),
                "terminal_result_type": reconciliation_payload.get("terminal_result_type"),
                "result_code": reconciliation_payload.get("result_code"),
                "task_record_ref": reconciliation_payload.get("task_record_ref"),
                "evidence_ref": reconciliation_payload.get("evidence_ref"),
            },
            "manifest": {
                "schema": manifest_payload.get("schema"),
                "status": manifest_payload.get("status"),
                "delivery_result_status": manifest_payload["delivery_result_evidence"].get("status"),
                "delivery_result_source_schema": manifest_payload["delivery_result_evidence"].get("source_schema"),
                "same_task_mission_gate_status": manifest_gate.get("status"),
                "same_task_terminal_refs": manifest_gate.get("terminal_refs"),
            },
            "archive": {
                "write_status": archive_payload.get("write_status", "created"),
                "same_task_mission_gate_status": archive_gate.get("status"),
                "field_evidence_source": archive_detail_payload["task"]["field_evidence"].get("source"),
                "cloud_external_probe_status": archive_cloud_external_probe.get("status"),
                "cloud_db_queue_external_probe_status": archive_cloud_db_queue_external_probe.get("status"),
            },
            "consumer": {
                "schema": consumer_payload.get("schema"),
                "same_task_mission_gate_status": consumer_gate.get("status"),
                "mission_artifact_delta": consumer_gate.get("mission_artifact_delta"),
                "terminal_refs": consumer_gate.get("terminal_refs"),
                "cloud_external_probe_status": consumer_cloud_external_probe.get("status"),
                "cloud_external_probe_endpoint_count": consumer_cloud_external_probe.get("endpoint_count"),
                "cloud_db_queue_external_probe_status": consumer_cloud_db_queue_external_probe.get("status"),
                "cloud_db_queue_external_probe_probe_count": consumer_cloud_db_queue_external_probe.get("probe_count"),
            },
            "generated_files": {
                "manifest_output": _safe_basename(str(manifest_output)),
                "reconciliation_json": _safe_basename(str(reconciliation_json)),
                "route_bag_db3": _safe_basename(str(route_bag_db3)),
                "cloud_external_probe_artifact": _safe_basename(str(cloud_external_probe_artifact)),
                "cloud_db_queue_external_probe_artifact": _safe_basename(
                    str(cloud_db_queue_external_probe_artifact)
                ),
            },
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
            "connects_cloud_production": False,
        }
        return summary


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local O5 same-task mission archive smoke.")
    parser.add_argument("--output", help="Optional JSON output path for the smoke summary.")
    parser.add_argument("--task-id", default="o5-reconciliation-same-task-smoke-001")
    parser.add_argument("--robot-id", default="trashbot-001")
    parser.add_argument(
        "--state-backend",
        default="file",
        choices=("file", "sqlite"),
        help="relay proof state backend; sqlite mode restarts relay before reconciliation readback",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    summary = run_smoke(task_id=args.task_id, robot_id=args.robot_id, state_backend=args.state_backend)
    encoded = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
