#!/usr/bin/env python3
"""把 O3 bounded route mock execution 摘要接入 O5 terminal-result 主链路。"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 该脚本只启动本地 in-process relay，不连接公网云、ROS2、Nav2 或底盘控制面。
# O5 本轮目标是证明 command enqueue -> terminal-result record -> result reconciliation 合同可串通。
# 输入必须来自 23:23 已接受的 O3 bounded route mock execution summary，避免把旧材料误接成新证据。
# 输出 summary 只保留 basename、短状态和 fixed false 字段，不回显 token、URL、绝对路径或控制入口 literal。
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
BEHAVIOR_SRC = WORKSPACE_ROOT / "onboard" / "src" / "ros2_trashbot_behavior"
if str(BEHAVIOR_SRC) not in sys.path:
    sys.path.insert(0, str(BEHAVIOR_SRC))

from ros2_trashbot_behavior.remote_cloud_relay import build_server  # noqa: E402


SUMMARY_SCHEMA = "trashbot.o5.bounded_route_terminal_result_bridge.v1"
SOURCE_SCHEMA = "trashbot.o3.bounded_route_mock_execution.v1"
SOURCE_PROOF_BOUNDARY = "software_proof_o3_o1_bounded_route_mock_execution_only"
PROOF_BOUNDARY = "software_proof_o5_bounded_route_terminal_result_bridge_only"
TERMINAL_RESULT_STATE = "terminal_result_recorded"
TASK_TERMINAL_STATE = "mock_route_execution_completed_not_live_route_execution"
RESULT_CODE = "mock_route_execution_completed_not_live_delivery"
COMMAND_TARGET = "bounded_route_terminal_result_bridge"
DEFAULT_ROBOT_ID = "trashbot-001"
DEFAULT_TOKEN = "o5-local-proof-token"

EXPECTED_PACKET_ID = "packet_o3_28_pose_same_task_replay_7d57826142b0c79c"
EXPECTED_TASK_ID = "task_o3_28_pose_fixed_route_consumer_20260713_0402"
EXPECTED_ROUTE_INTENT_ID = "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path"
EXPECTED_ROUTE_ROW_COUNT = 28
EXPECTED_SEGMENT_COUNT = 27

FIXED_FALSE_FIELDS = (
    "delivery_success",
    "route_execution_success",
    "safe_to_control",
    "hil_pass",
    "robot_control_executed",
    "connects_cloud_production",
    "uses_base_uart",
    "publishes_cmd_vel",
    "calls_base_manual",
)

SOURCE_FALSE_FIELDS = (
    "delivery_success",
    "route_execution_success",
    "safe_to_control",
    "hil_pass",
    "robot_control_executed",
    "uses_base_uart",
    "publishes_cmd_vel",
    "calls_base_manual",
)

NO_MOTION_GUARD_MARKERS = (
    "no /cmd_vel",
    "no /api/base/manual",
    "no NavigateToPose",
    "no WAVE ROVER UART",
)

RELAY_CAPABILITIES = (
    "cloud_phone_command_api",
    "cloud_command_terminal_result",
    "cloud_command_result_reconciliation",
)

REJECTED_CLAIMS = (
    "production cloud",
    "public https tls",
    "real 4g sim",
    "production worker cutover",
    "oss cdn live traffic",
    "true phone browser proof",
    "live route execution",
    "delivery success",
    "operator acceptance",
    "hil pass",
    "safe to control",
    "robot control execution",
)

FORBIDDEN_OUTPUT_MARKERS = (
    "Authorization",
    "Bearer",
    DEFAULT_TOKEN,
    "http://",
    "https://",
    "Traceback",
    "traceback",
    "/cmd_vel",
    "/api/base/manual",
    "NavigateToPose",
    "WAVE ROVER",
    "UART",
)


class BridgeInputError(ValueError):
    """输入 artifact 漂移时 fail closed，避免生成可被误读的 O5 结果材料。"""


class BridgeRuntimeError(RuntimeError):
    """本地 relay 主链路未按预期返回时 fail closed。"""


def utc_now_iso() -> str:
    """统一使用 UTC 秒级时间，便于 sprint artifact 可复核。"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json_object(path: Path) -> dict[str, Any]:
    """source summary 必须是单个 JSON object，不能接受 stdout、JSONL 或空文件。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BridgeInputError("source summary must be a JSON object")
    return data


def require_equal(data: dict[str, Any], key: str, expected: Any, label: str) -> None:
    """集中校验关键字段；错误只暴露字段名和值，不暴露本地路径。"""
    actual = data.get(key)
    if actual != expected:
        raise BridgeInputError(f"{label}.{key} expected {expected!r}, got {actual!r}")


def require_int(data: dict[str, Any], key: str, expected: int, label: str) -> None:
    """count 字段必须是精确 int，字符串或浮点都不能放大为证据。"""
    actual = data.get(key)
    if type(actual) is not int or actual != expected:
        raise BridgeInputError(f"{label}.{key} expected int {expected!r}, got {actual!r}")


def require_false(data: dict[str, Any], key: str, label: str) -> None:
    """安全字段必须是布尔 false；缺失、None 或字符串 false 都 fail closed。"""
    require_equal(data, key, False, label)


def validate_source_summary(source: dict[str, Any]) -> dict[str, Any]:
    """验证 O3 mock execution 摘要的身份、计数、状态和 no-motion 边界。"""
    require_equal(source, "schema", SOURCE_SCHEMA, "source")
    require_equal(source, "proof_boundary", SOURCE_PROOF_BOUNDARY, "source")
    require_equal(source, "mock_execution_status", TASK_TERMINAL_STATE, "source")
    require_equal(source, "mock_execution_completed", True, "source")
    require_equal(source, "packet_id", EXPECTED_PACKET_ID, "source")
    require_equal(source, "task_id", EXPECTED_TASK_ID, "source")
    require_equal(source, "route_intent_id", EXPECTED_ROUTE_INTENT_ID, "source")
    require_int(source, "route_csv_row_count", EXPECTED_ROUTE_ROW_COUNT, "source")
    require_int(source, "path_structured_pose_count", EXPECTED_ROUTE_ROW_COUNT, "source")
    require_int(source, "segment_count", EXPECTED_SEGMENT_COUNT, "source")
    require_int(source, "progress_jsonl_event_count", EXPECTED_SEGMENT_COUNT, "source")
    require_equal(source, "source_identity_verified", True, "source")
    require_equal(source, "source_counts_verified", True, "source")
    require_equal(source, "source_no_motion_guard_verified", True, "source")
    require_equal(source, "source_fixed_false_fields_verified", True, "source")

    fixed_false_fields = source.get("fixed_false_fields")
    if not isinstance(fixed_false_fields, dict):
        raise BridgeInputError("source.fixed_false_fields must be an object")
    for key in SOURCE_FALSE_FIELDS:
        require_false(source, key, "source")
        require_false(fixed_false_fields, key, "source.fixed_false_fields")

    # guard marker 只用于输入校验，不复制到输出 artifact，避免 CLI 输出带底层控制 literal。
    guard_text = " ".join(str(item) for item in source.get("no_motion_control_guard") or [])
    for marker in NO_MOTION_GUARD_MARKERS:
        if marker not in guard_text:
            raise BridgeInputError(f"source.no_motion_control_guard missing required marker: {marker!r}")

    return source


class RelayHttpClient:
    """最小 HTTP 客户端；只服务本地 in-process relay smoke，不做外部网络访问。"""

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
        """发送 JSON 请求并统一解析 relay 响应，HTTP error 也按 JSON body 返回。"""
        data = None
        headers = {"Accept": "application/json", "Authorization": f"Bearer {self.token}"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload, sort_keys=True).encode("utf-8")
        request = urllib.request.Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=3.0) as response:
                body = response.read().decode("utf-8") or "{}"
                return response.status, json.loads(body)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8") or "{}"
            return exc.code, json.loads(body)


@contextmanager
def local_relay(token: str):
    """启动本地 relay，并确保测试或 CLI 异常时也关闭 socket 线程。"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        old_archive_state = os.environ.get("TRASHBOT_O6_CLOUD_ARCHIVE_STATE")
        os.environ["TRASHBOT_O6_CLOUD_ARCHIVE_STATE"] = str(temp_root / "o6_archive_state.json")
        server = build_server("127.0.0.1", 0, temp_root / "relay_state.json", token)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield RelayHttpClient(f"http://127.0.0.1:{server.server_address[1]}", token)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)
            if old_archive_state is None:
                os.environ.pop("TRASHBOT_O6_CLOUD_ARCHIVE_STATE", None)
            else:
                os.environ["TRASHBOT_O6_CLOUD_ARCHIVE_STATE"] = old_archive_state


def command_id_for(source: dict[str, Any]) -> str:
    """command id 绑定 source task_id，便于重复运行时保持同一任务身份。"""
    return f"o5-bounded-route-terminal-result-bridge-{source['task_id']}"


def post_collect_command(client: RelayHttpClient, *, robot_id: str, command_id: str, source: dict[str, Any]) -> dict[str, Any]:
    """走 phone-facing collect 主路径；receipt 只证明入队，不证明执行或送达。"""
    status, receipt = client.request(
        "POST",
        "/api/commands/collect",
        {
            "robot_id": robot_id,
            "idempotency_key": command_id,
            "payload": {
                "target": COMMAND_TARGET,
                "task_id": source["task_id"],
                "packet_id": source["packet_id"],
                "route_intent_id": source["route_intent_id"],
            },
        },
    )
    if status not in (200, 201) or not receipt.get("ok"):
        raise BridgeRuntimeError(f"collect command enqueue failed with status {status}")
    if receipt.get("command_id") != command_id:
        raise BridgeRuntimeError("collect command receipt did not preserve command id")
    return receipt


def post_terminal_result(
    client: RelayHttpClient,
    *,
    robot_id: str,
    command_id: str,
    source: dict[str, Any],
    evidence_ref: str,
    generated_at_utc: str,
) -> dict[str, Any]:
    """走 robot-facing terminal-result 主路径，但 payload 明确是 mock not-live-delivery。"""
    status, recorded = client.request(
        "POST",
        f"/robots/{urllib.parse.quote(robot_id)}/commands/{urllib.parse.quote(command_id)}/terminal-result",
        {
            "schema": "trashbot.cloud_command_terminal_result.v1",
            "schema_version": 1,
            "robot_id": robot_id,
            "command_id": command_id,
            "terminal_result_type": "delivery_terminal",
            "task_terminal_state": TASK_TERMINAL_STATE,
            "result_code": RESULT_CODE,
            "error_code": "",
            "task_record_ref": source["task_id"],
            "evidence_ref": evidence_ref,
            "completed_at": generated_at_utc,
            "source": "o5_bounded_route_terminal_result_bridge",
            "delivery_success": False,
            "safe_to_control": False,
            "real_world_delivery_proven": False,
        },
    )
    if status not in (200, 201) or recorded.get("terminal_result_state") != TERMINAL_RESULT_STATE:
        raise BridgeRuntimeError(f"terminal result record failed with status {status}")
    return recorded


def get_reconciliation(client: RelayHttpClient, *, robot_id: str, command_id: str) -> dict[str, Any]:
    """走 phone-facing result readback；这里只读对账状态，不推进 ACK cursor。"""
    command_path = urllib.parse.quote(command_id)
    robot_query = urllib.parse.quote(robot_id)
    status, reconciliation = client.request("GET", f"/api/commands/{command_path}/result?robot_id={robot_query}")
    if status != 200 or reconciliation.get("result_state") != TERMINAL_RESULT_STATE:
        raise BridgeRuntimeError(f"result reconciliation failed with status {status}")
    return reconciliation


def assert_artifact_safe(summary: dict[str, Any]) -> None:
    """输出 artifact 不能包含 token、URL、绝对路径、traceback 或底层控制入口 literal。"""
    encoded = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    for marker in FORBIDDEN_OUTPUT_MARKERS:
        if marker in encoded:
            raise BridgeRuntimeError(f"summary contains forbidden marker: {marker}")
    if str(WORKSPACE_ROOT) in encoded:
        raise BridgeRuntimeError("summary contains workspace absolute path")


def build_summary(
    *,
    source: dict[str, Any],
    source_summary_ref: str,
    robot_id: str = DEFAULT_ROBOT_ID,
    generated_at_utc: str | None = None,
    token: str = DEFAULT_TOKEN,
) -> dict[str, Any]:
    """执行 O5 三段主链路，并将 relay 响应压缩成 artifact-safe summary。"""
    source = validate_source_summary(source)
    generated_at_utc = generated_at_utc or utc_now_iso()
    command_id = command_id_for(source)

    with local_relay(token) as client:
        receipt = post_collect_command(client, robot_id=robot_id, command_id=command_id, source=source)
        recorded = post_terminal_result(
            client,
            robot_id=robot_id,
            command_id=command_id,
            source=source,
            evidence_ref=source_summary_ref,
            generated_at_utc=generated_at_utc,
        )
        reconciliation = get_reconciliation(client, robot_id=robot_id, command_id=command_id)

    summary: dict[str, Any] = {
        "schema": SUMMARY_SCHEMA,
        "generated_at_utc": generated_at_utc,
        "owner_role": "robot-software-engineer",
        "proof_boundary": PROOF_BOUNDARY,
        "proof_boundary_class": "software_proof_local_mock_only",
        "source_schema": source["schema"],
        "source_proof_boundary": source["proof_boundary"],
        "source_summary_ref": source_summary_ref,
        "source_mock_execution_status": source["mock_execution_status"],
        "source_mock_execution_completed": bool(source["mock_execution_completed"]),
        "source_identity_verified": True,
        "source_counts_verified": True,
        "source_no_motion_guard_verified": True,
        "source_fixed_false_fields_verified": True,
        "task_id": source["task_id"],
        "packet_id": source["packet_id"],
        "route_intent_id": source["route_intent_id"],
        "route_csv_row_count": source["route_csv_row_count"],
        "path_structured_pose_count": source["path_structured_pose_count"],
        "segment_count": source["segment_count"],
        "progress_jsonl_event_count": source["progress_jsonl_event_count"],
        "mock_total_distance_m": source.get("mock_total_distance_m"),
        "mock_total_elapsed_s": source.get("mock_total_elapsed_s"),
        "robot_id": robot_id,
        "command_id": command_id,
        "relay_capabilities": list(RELAY_CAPABILITIES),
        "command_enqueue_state": "command_enqueued",
        "command_enqueue_http_status_class": "2xx",
        "command_receipt_capability": receipt.get("capability", ""),
        "command_receipt_ack_semantics": receipt.get("ack_semantics", ""),
        "terminal_result_state": recorded.get("terminal_result_state", ""),
        "terminal_result_type": recorded.get("terminal_result_type", ""),
        "task_terminal_state": recorded.get("task_terminal_state", ""),
        "result_code": recorded.get("result_code", ""),
        "task_record_ref": recorded.get("task_record_ref", ""),
        "evidence_ref": recorded.get("evidence_ref", ""),
        "reconciliation_schema": reconciliation.get("schema", ""),
        "reconciliation_capability": reconciliation.get("capability", ""),
        "reconciliation_state": reconciliation.get("result_state", ""),
        "reconciliation_command_state": reconciliation.get("command_state", ""),
        "reconciliation_ack_state": reconciliation.get("ack_state", ""),
        "next_required_evidence": reconciliation.get("next_required_evidence", ""),
        "fixed_false_fields": {key: False for key in FIXED_FALSE_FIELDS},
        "fixed_false_invariants": [f"{key}=false" for key in FIXED_FALSE_FIELDS],
        "rejected_claims": list(REJECTED_CLAIMS),
        "checks": [
            {
                "name": "source_bounded_route_mock_execution_identity",
                "status": "pass",
                "detail": "source schema, task, packet, route identity and counts matched the accepted mock execution summary",
            },
            {
                "name": "cloud_command_result_reconciliation",
                "status": "pass",
                "detail": "collect command, terminal result write and result readback all used existing relay HTTP routes",
            },
            {
                "name": "fixed_false_fields",
                "status": "pass",
                "detail": "all delivery, route, control, hardware and production claims remain false",
            },
        ],
        "rg_acceptance_anchors": [
            "bounded_route_terminal_result_bridge",
            PROOF_BOUNDARY,
            RESULT_CODE,
            TERMINAL_RESULT_STATE,
            "cloud_command_result_reconciliation",
        ],
    }
    for key in FIXED_FALSE_FIELDS:
        summary[key] = False
    summary["primary_actions_enabled"] = False
    summary["real_world_delivery_proven"] = False
    summary["production_cloud_ready"] = False
    assert_artifact_safe(summary)
    return summary


def write_summary(source_summary: Path, output: Path, *, generated_at_utc: str | None = None) -> dict[str, Any]:
    """读取 source、执行 bridge、写出 artifact；输出路径父目录按需创建。"""
    source = load_json_object(source_summary)
    summary = build_summary(
        source=source,
        source_summary_ref=source_summary.name,
        generated_at_utc=generated_at_utc,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _safe_error_text(exc: Exception) -> str:
    """CLI 失败只打印错误类别和短原因，避免 traceback 或本地路径进入日志。"""
    text = str(exc).replace(str(WORKSPACE_ROOT), "[workspace]")
    for marker in (DEFAULT_TOKEN, "Authorization", "Bearer"):
        text = text.replace(marker, "[redacted]")
    return f"{exc.__class__.__name__}: {text}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local O5 bounded route terminal-result bridge proof")
    parser.add_argument("--source-summary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        summary = write_summary(args.source_summary, args.output)
    except (BridgeInputError, BridgeRuntimeError, OSError, json.JSONDecodeError) as exc:
        print(_safe_error_text(exc), file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
