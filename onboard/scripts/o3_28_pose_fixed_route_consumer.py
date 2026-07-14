#!/usr/bin/env python3
"""消费 03:00 fresh 28-pose path artifact，生成 strict no-motion fixed-route 材料。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 这个脚本只做离线 artifact 消费，不能接入任何 ROS runtime。
# 这样设计是为了把“路线材料可消费”和“机器人可以执行路线”严格分开。
# 本轮 primary source 只能是 03:00 fresh structured path summary。
# 旧 21:57 stdout-tail 材料仍可做 comparator，但不能再作为 primary。
# route_intent_id 和 task_id 在脚本里固定，便于 O6/O7 或后续 replay 复核同源性。
# 28 不是长期路线点数常量，而是本轮 source artifact 的验收条件。
# 如果下一轮 live path 变成其他点数，应新增 consumer 或显式放宽合同。
# safety false 字段由 summary 顶层和 proof 双重校验，避免 wrapper 漂移。
# 输出 JSONL 只写 structured_pose event，方便用一行一个 pose 做机器断言。
# 输出 CSV 展开 position/orientation，方便 shell、spreadsheet 和 artifact review 读取。
# 脚本不提供任何控制相关 CLI 参数，避免误把 consumer 工具扩展成执行工具。
# 任何未来执行 gate 都必须新增独立脚本和独立验收，不复用本 consumer 入口。
# 这能让当前 sprint 的证据边界在代码层和 artifact 层保持一致。
SCHEMA = "trashbot.fixed_route_28_pose_consumer.v1"
REPLAY_SCHEMA = "trashbot.fixed_route_28_pose_replay.v1"
ROUTE_CSV_SCHEMA = "trashbot.fixed_route_28_pose_route_csv.v1"
EXPECTED_POSE_COUNT = 28
ROUTE_INTENT_ID = "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path"
TASK_ID = "task_o3_28_pose_fixed_route_consumer_20260713_0402"
SUMMARY_NAME = "fixed_route_28_pose_consumer_summary.json"
REPLAY_NAME = "fixed_route_28_pose_replay.jsonl"
ROUTE_CSV_NAME = "fixed_route_28_pose_route.csv"
HISTORIC_COMPARATOR_REF = (
    "sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/"
    "artifacts/algorithm/fixed_route_consumer_dry_run_summary.json"
)


class ConsumerInputError(ValueError):
    """输入 artifact 不满足 fresh 28-pose 消费条件时 fail closed。"""


def utc_now_iso() -> str:
    """用 UTC 时间标记产物，避免不同开发机时区影响 artifact 可读性。"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    """只接受 JSON object，避免把 stdout tail 或 JSONL 错当 summary。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConsumerInputError(f"source summary must be a JSON object: {path}")
    return data


def sha256_file(path: Path) -> str:
    """记录 source hash，后续复核能确认 consumer 没换过 primary artifact。"""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_equal(data: dict[str, Any], key: str, expected: Any, label: str) -> None:
    """集中做等值断言，让失败原因直接指向漂移字段。"""
    actual = data.get(key)
    if actual != expected:
        raise ConsumerInputError(f"{label}.{key} expected {expected!r}, got {actual!r}")


def require_false(data: dict[str, Any], key: str, label: str) -> None:
    """安全字段只能显式为 false，缺失或 None 都不能被当成安全。"""
    require_equal(data, key, False, label)


def require_true(data: dict[str, Any], key: str, label: str) -> None:
    """关键 fresh/path 字段必须显式为 true，避免误吃 partial wrapper。"""
    require_equal(data, key, True, label)


def require_number(value: Any, label: str) -> float:
    """pose 坐标和四元数必须是数值，后续 CSV/JSONL 才能被结构断言复核。"""
    if not isinstance(value, (int, float)):
        raise ConsumerInputError(f"{label} must be numeric, got {value!r}")
    return float(value)


def normalize_pose(raw_pose: dict[str, Any], order: int) -> dict[str, Any]:
    """把 source pose 收敛成固定 schema，避免 consumer 依赖上游字段顺序。"""
    if not isinstance(raw_pose, dict):
        raise ConsumerInputError(f"pose[{order}] must be an object")

    # source_index 必须和列表顺序一致；这能阻止排序漂移或人工补点。
    source_index = raw_pose.get("source_index")
    if source_index != order:
        raise ConsumerInputError(f"pose[{order}].source_index expected {order}, got {source_index!r}")

    # frame_id 是 fixed-route material 的坐标系锚点，缺失时不能假定为 map。
    frame_id = raw_pose.get("frame_id")
    if not isinstance(frame_id, str) or not frame_id:
        raise ConsumerInputError(f"pose[{order}].frame_id must be a non-empty string")

    # stamp 保留原始 planner path 时间戳，用于后续对比是否来自同一 capture。
    stamp = raw_pose.get("stamp")
    if not isinstance(stamp, dict):
        raise ConsumerInputError(f"pose[{order}].stamp must be an object")
    stamp_sec = stamp.get("sec")
    stamp_nanosec = stamp.get("nanosec")
    if not isinstance(stamp_sec, int) or not isinstance(stamp_nanosec, int):
        raise ConsumerInputError(f"pose[{order}].stamp sec/nanosec must be integers")

    return {
        # order 是 consumer 自己的稳定行号，source_index 是上游 path 的原始索引。
        "order": order,
        "source_index": source_index,
        "frame_id": frame_id,
        "stamp": {"sec": stamp_sec, "nanosec": stamp_nanosec},
        "position": {
            # position 三轴都显式保留，避免 CSV 读者把缺省 z 当成真实测量。
            "x": require_number(raw_pose.get("x"), f"pose[{order}].x"),
            "y": require_number(raw_pose.get("y"), f"pose[{order}].y"),
            "z": require_number(raw_pose.get("z"), f"pose[{order}].z"),
        },
        "orientation": {
            # orientation 用四元数原样传递，不在 consumer 中重新计算 yaw。
            "qx": require_number(raw_pose.get("qx"), f"pose[{order}].qx"),
            "qy": require_number(raw_pose.get("qy"), f"pose[{order}].qy"),
            "qz": require_number(raw_pose.get("qz"), f"pose[{order}].qz"),
            "qw": require_number(raw_pose.get("qw"), f"pose[{order}].qw"),
        },
    }


def validate_source_summary(source: dict[str, Any]) -> list[dict[str, Any]]:
    """校验 fresh 28-pose 条件；任一条件漂移都不生成消费材料。"""
    proof = source.get("proof")
    if not isinstance(proof, dict):
        raise ConsumerInputError("source.proof must be present")

    # 顶层 summary 和 proof 都必须证明 path generated，防止只读到包装层成功。
    require_true(source, "path_generated", "source")
    require_true(proof, "path_generated", "source.proof")
    # 28-pose 是本轮验收目标；旧 21-pose expectation 不能在这里硬编码回去。
    require_equal(source, "path_structured_pose_count", EXPECTED_POSE_COUNT, "source")
    require_equal(proof, "path_structured_pose_count", EXPECTED_POSE_COUNT, "source.proof")
    # fresh_live_artifact_used 是替代 01:00 partial stdout-tail 的关键证据。
    require_true(proof, "fresh_live_artifact_used", "source.proof")
    # 旧 21:57 artifact 只能作为 comparator；一旦被标成 live proof 就 fail closed。
    require_false(proof, "historic_21_57_artifact_reused_as_live_proof", "source.proof")

    # 本 consumer 只读 planner-only artifact；如果上游 safety 字段漂移为 true，必须停住。
    for key in (
        "route_execution_success",
        "delivery_success",
        "hil_pass",
        "safe_to_control",
        "publishes_cmd_vel",
        "calls_base_manual",
        "uses_base_uart",
        "robot_control_executed",
    ):
        require_false(source, key, "source")
        require_false(proof, key, "source.proof")

    raw_poses = proof.get("path_structured_poses")
    if not isinstance(raw_poses, list):
        raise ConsumerInputError("source.proof.path_structured_poses must be a list")
    if len(raw_poses) != EXPECTED_POSE_COUNT:
        raise ConsumerInputError(
            f"source.proof.path_structured_poses expected {EXPECTED_POSE_COUNT}, got {len(raw_poses)}"
        )

    # 逐个 pose 正规化，保证后续 JSONL 和 CSV 来自同一份字段检查。
    return [normalize_pose(pose, order) for order, pose in enumerate(raw_poses)]


def replay_event_for_pose(pose: dict[str, Any], primary_source_artifact: str) -> dict[str, Any]:
    """JSONL 每行只承载一个 structured pose，方便按 event 过滤和计数。"""
    return {
        # schema 放在每行，单独抽取某个 pose 时仍能知道解析合同。
        "schema": REPLAY_SCHEMA,
        "event": "structured_pose",
        "route_intent_id": ROUTE_INTENT_ID,
        "task_id": TASK_ID,
        # order/source_index 双写，既能检查 consumer 顺序，也能追溯上游 path 顺序。
        "order": pose["order"],
        "source_index": pose["source_index"],
        "frame_id": pose["frame_id"],
        "stamp": pose["stamp"],
        # position/orientation 保持对象结构，便于 JSON reader 直接按语义读取。
        "position": pose["position"],
        "orientation": pose["orientation"],
        "primary_source_artifact": primary_source_artifact,
        # 每行都保留 no-motion 标记，避免 JSONL 被脱离 summary 使用时边界丢失。
        "strict_no_motion": True,
        "route_execution_success": False,
    }


def csv_row_for_pose(pose: dict[str, Any], primary_source_artifact: str) -> dict[str, Any]:
    """CSV 展开 position/orientation，保证 shell 里的 csv.DictReader 能直接断言字段。"""
    return {
        # CSV 也写 schema，避免后续 route.csv 与真实采集 route.csv 混淆。
        "schema": ROUTE_CSV_SCHEMA,
        "route_intent_id": ROUTE_INTENT_ID,
        "task_id": TASK_ID,
        # order/source_index 均为列字段，方便简单断言首尾 0/27。
        "order": pose["order"],
        "source_index": pose["source_index"],
        "frame_id": pose["frame_id"],
        "stamp_sec": pose["stamp"]["sec"],
        "stamp_nanosec": pose["stamp"]["nanosec"],
        # 坐标拆成扁平列，是为了兼容 spreadsheet 和 csv.DictReader。
        "x": pose["position"]["x"],
        "y": pose["position"]["y"],
        "z": pose["position"]["z"],
        # 四元数原样展开，不在 artifact consumer 层做 yaw 近似。
        "qx": pose["orientation"]["qx"],
        "qy": pose["orientation"]["qy"],
        "qz": pose["orientation"]["qz"],
        "qw": pose["orientation"]["qw"],
        "primary_source_artifact": primary_source_artifact,
        # CSV 脱离 summary 传播时也必须显示 strict no-motion 边界。
        "strict_no_motion": True,
    }


def build_checks() -> list[dict[str, str]]:
    """checks 只记录本轮真实验证过的 artifact 条件，不替代 route execution。"""
    return [
        {
            # 这条 check 对应“替代 01:00 primary partial material”的产品目标。
            "name": "fresh_source_selected",
            "status": "pass",
            "detail": "primary source is the 03:00 fresh same-run structured path summary",
        },
        {
            # comparator 只帮助审计历史链路，不参与本轮 route rows 生成。
            "name": "historic_21_57_not_primary",
            "status": "pass",
            "detail": "old 21:57 partial stdout-tail material is retained only as comparator",
        },
        {
            # 这里写 consumed without fabricating points，防止 21->28 或 28->21 被误读。
            "name": "structured_pose_count",
            "status": "pass",
            "detail": "28 complete structured poses were consumed without fabricating points",
        },
        {
            # safety invariant 是本脚本的验收条件，不是运行时安全认证。
            "name": "strict_no_motion_invariants",
            "status": "pass",
            "detail": "route/control/delivery/HIL/safe-to-control fields remain false",
        },
    ]


def build_summary(
    source: dict[str, Any],
    poses: list[dict[str, Any]],
    source_summary_path: Path,
    output_dir: Path,
    generated_at_utc: str,
) -> dict[str, Any]:
    """汇总 consumer 结果，同时把不允许声明的能力固定写成 false。"""
    proof = source["proof"]
    primary_source_artifact = source_summary_path.as_posix()
    output_prefix = output_dir.as_posix()
    # 首尾 pose 进入 summary，人工 review 不必打开整份 JSONL 就能识别路线范围。
    first_pose = poses[0]
    last_pose = poses[-1]

    return {
        # schema 和 identity 是后续 O6/O7/readback 消费的最小稳定入口。
        "schema": SCHEMA,
        "generated_at_utc": generated_at_utc,
        "route_intent_id": ROUTE_INTENT_ID,
        "task_id": TASK_ID,
        # primary source 和 hash 用于证明本轮确实消费 03:00 summary。
        "primary_source_artifact": primary_source_artifact,
        "primary_source_sha256": sha256_file(source_summary_path),
        # 旧材料保留为 comparator，可追溯但不能驱动本轮路线行。
        "historic_21_57_artifact_primary_source": False,
        "historic_21_57_comparator_ref": HISTORIC_COMPARATOR_REF,
        # 这个布尔值是 Product acceptance 的核心机器可读信号。
        "fresh_28_pose_structured_material_consumed": True,
        "path_generated": True,
        "path_point_count": int(source["path_point_count"]),
        "path_structured_pose_count": len(poses),
        "validation_status": "pass_fresh_28_pose_structured_material",
        "dry_run_status": "accepted_strict_no_motion_28_pose_consumer_material",
        # artifact_boundary 明确本轮只推进 consumer material，不推进执行信用。
        "artifact_boundary": "software_proof_o3_o1_strict_no_motion_fresh_28_pose_fixed_route_consumer_only",
        "source_evidence": {
            # source_evidence 只摘取上游 proof 关键事实，不复制整份大 artifact。
            "status": proof.get("status"),
            "evidence_type": proof.get("evidence_type"),
            "path_generation_attempted": proof.get("path_generation_attempted"),
            "path_generation_requested": proof.get("path_generation_requested"),
            "path_generation_boundary": proof.get("path_generation_boundary"),
            "path_generation_service_name": proof.get("path_generation_service_name"),
            # fresh/historic 字段在 summary 中再次保留，便于 grep 级验收。
            "fresh_live_artifact_used": proof.get("fresh_live_artifact_used"),
            "historic_21_57_artifact_reused_as_live_proof": proof.get(
                "historic_21_57_artifact_reused_as_live_proof"
            ),
            "blocked_reason": proof.get("blocked_reason"),
            "proof_boundary": proof.get("proof_boundary"),
            # path_goal_request 解释为什么当前 live path 是 y=0.25 的 28 点。
            "path_goal_request": proof.get("path_goal_request"),
        },
        "material_shape": {
            # 行数和首尾索引是最容易被自动验收复核的结构指标。
            "replay_event_count": len(poses),
            "csv_material_row_count": len(poses),
            "first_pose": first_pose,
            "last_pose": last_pose,
            "source_index_min": first_pose["source_index"],
            "source_index_max": last_pose["source_index"],
            # frame_ids 让 review 立刻看到是否出现跨 frame 混入。
            "frame_ids": sorted({pose["frame_id"] for pose in poses}),
        },
        "route_material_refs": {
            # refs 统一写相对仓库路径，方便 sprint artifact 搬运和 rg。
            "summary_json_ref": f"{output_prefix}/{SUMMARY_NAME}",
            "route_replay_jsonl_ref": f"{output_prefix}/{REPLAY_NAME}",
            "route_csv_ref": f"{output_prefix}/{ROUTE_CSV_NAME}",
        },
        "checks": build_checks(),
        # 从这里开始是 no-motion 安全围栏；任何 true 都会误导后续执行 gate。
        "strict_no_motion": True,
        "strict_no_motion_boundary": (
            "artifact-only fixed-route consumer material; no NavigateToPose, controller/BT, "
            "/cmd_vel, /api/base/manual, WAVE ROVER UART, route execution, delivery, HIL, "
            "or safe-to-control claim was produced"
        ),
        # 这些字段故意顶层展开，方便最简单的 JSON assert 和 rg 检查。
        "safe_to_control": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
        "robot_control_executed": False,
        "route_execution_success": False,
        "delivery_success": False,
        "hil_pass": False,
        "rejected_claims": [
            # rejected_claims 是给人工复核看的边界说明，不是动态能力判定。
            "route_execution_success",
            "NavigateToPose",
            "controller_bt_execution",
            "publishes_cmd_vel",
            "calls_base_manual",
            "uses_base_uart",
            "delivery_success",
            "hil_pass",
            "safe_to_control",
            "production_external_evidence",
            "historic_21_57_partial_stdout_tail_as_primary_source",
        ],
        "next_evidence_required": [
            # 下一步必须新增执行证据，不能继续把 consumer material 当执行成功。
            "later explicit Nav2 or fixed-route route execution record before route_execution_success can change",
            "delivery/operator acceptance evidence before delivery_success can change",
            "current live HIL evidence before hil_pass or safe_to_control can change",
            "production cloud/readback evidence before O5/O6/O7 production credit can change",
        ],
        "rg_acceptance_anchors": [
            # anchors 专门服务 sprint 验收命令，保持和 tech-plan 中的 grep 一致。
            "28",
            "path_structured_pose_count=28",
            "fixed-route",
            f"route_intent_id={ROUTE_INTENT_ID}",
            f"task_id={TASK_ID}",
            "route_execution_success=false",
            "delivery_success=false",
            "hil_pass=false",
            "safe_to_control=false",
            "historic_21_57_artifact_primary_source=false",
        ],
    }


def write_outputs(source_summary_path: Path, output_dir: Path, generated_at_utc: str | None = None) -> dict[str, Any]:
    """主写入入口；测试和 CLI 共用，防止命令路径与单测逻辑分叉。"""
    # 先读取和校验 source，再创建输出目录；失败时不留下半成品。
    source = load_json(source_summary_path)
    poses = validate_source_summary(source)
    output_dir.mkdir(parents=True, exist_ok=True)

    # timestamp 可被单测注入，真实 CLI 默认使用当前 UTC。
    timestamp = generated_at_utc or utc_now_iso()
    summary = build_summary(source, poses, source_summary_path, output_dir, timestamp)
    primary_source_artifact = source_summary_path.as_posix()

    # JSONL 一行一个 pose，后续可以流式读取，不依赖整文件加载。
    replay_path = output_dir / REPLAY_NAME
    with replay_path.open("w", encoding="utf-8") as handle:
        for pose in poses:
            handle.write(json.dumps(replay_event_for_pose(pose, primary_source_artifact), ensure_ascii=False))
            handle.write("\n")

    # CSV 写 header，是为了让 csv.DictReader 的结构断言稳定。
    csv_path = output_dir / ROUTE_CSV_NAME
    fieldnames = list(csv_row_for_pose(poses[0], primary_source_artifact).keys())
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for pose in poses:
            writer.writerow(csv_row_for_pose(pose, primary_source_artifact))

    # summary 最后写；这样 refs 指向的 JSONL/CSV 已经真实存在。
    summary_path = output_dir / SUMMARY_NAME
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    """CLI 只暴露 source 与 output，避免误加会触发运动的参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-summary", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    """命令行入口返回非零即代表 consumer fail-closed。"""
    args = parse_args()
    summary = write_outputs(args.source_summary, args.output_dir)
    print(json.dumps({"status": "ok", "summary": summary["route_material_refs"]["summary_json_ref"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
