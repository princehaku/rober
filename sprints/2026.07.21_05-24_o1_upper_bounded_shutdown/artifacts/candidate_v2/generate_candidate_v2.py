#!/usr/bin/env python3
"""在已验证 adadb0 latency-only Upper 上叠加 bounded shutdown，仍输出可从 85ba 直接应用的候选。"""

from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import json
from pathlib import Path


# 这些已有 latency symbols 仍是 85ba -> candidate v2 总白名单的一部分。
PREVIOUS_LATENCY_SYMBOLS = (
    "UpperRobotApi.manual_control",
    "_ensure_ros_cmd_vel_context",
    "create_app",
    "manual_motion_ros_cmd_vel_hold_refresh_transaction",
    "normalize_latency_trace",
    "prewarm_ros_cmd_vel_context",
    "publish_ros_cmd_vel_inprocess_burst",
    "run_server",
    "upper_latency_timing",
)

# v2 只替换与 teardown 串行、fail-closed 和 active-hold stop 直接相关的既有定义。
SHUTDOWN_REPLACEMENTS = (
    "_ensure_ros_cmd_vel_context",
    "prewarm_ros_cmd_vel_context",
    "publish_ros_cmd_vel_inprocess_burst",
    "build_stop_payload",
    "run_server",
    "UpperRobotApi.__init__",
    "UpperRobotApi._manual_hold_stop_sync",
    "UpperRobotApi._manual_hold_watchdog",
    "UpperRobotApi.manual_control",
)
SHUTDOWN_ADDITIONS = (
    "shutdown_ros_cmd_vel_context",
    "install_upper_shutdown_signal_handlers",
    "remove_upper_shutdown_signal_handlers",
    "bounded_manual_hold_stop_for_shutdown",
    "shutdown_upper_runtime",
)

# 这些字符串只属于 c8 Nav2/sensor-owned 合同，candidate v2 必须继续为零。
FORBIDDEN_SENTINELS = (
    "sensor_owned_scan",
    "initialpose_canonical_free_cell_opt_in",
    "reuse_existing_lidar_lifecycle",
    "DEFAULT_NAV2_MAP_FILE",
    "start_owned_process_created",
    "lidar_holder_owned",
    "scan_publisher_owned",
)


def sha256_text(text: str) -> str:
    """输入、候选和 patch 都以内容 hash 冻结，避免部署时换用未验证文件。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def definitions(text: str) -> dict[str, ast.AST]:
    """索引顶层定义与类方法，类聚合节点不作为放宽整个类的理由。"""
    tree = ast.parse(text)
    result: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            result[node.name] = node
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        result[f"{node.name}.{child.name}"] = child
    return result


def extract(lines: list[str], node: ast.AST) -> str:
    """用 AST 行界提取原始文本，以保留中文原因注释和手工格式。"""
    return "".join(lines[int(node.lineno) - 1 : int(node.end_lineno)])


def replace_shutdown_definitions(previous: str, source: str) -> str:
    """从当前组合实现只提取 shutdown 白名单，不带入任何 Nav2 definition。"""
    previous_index = definitions(previous)
    source_index = definitions(source)
    previous_lines = previous.splitlines(keepends=True)
    source_lines = source.splitlines(keepends=True)
    ranges: list[tuple[int, int, str]] = []
    for name in SHUTDOWN_REPLACEMENTS:
        old = previous_index[name]
        new = source_index[name]
        ranges.append((int(old.lineno) - 1, int(old.end_lineno), extract(source_lines, new)))
    for start, end, replacement in sorted(ranges, reverse=True):
        previous_lines[start:end] = [replacement]
    candidate = "".join(previous_lines)

    # 全局状态只扩展 shutdown/stop owner；不改变 latency trace 或 Nav2 常量。
    lock_anchor = "_ROS_CMD_VEL_LOCK = threading.RLock()\n"
    lock_block = (
        lock_anchor
        + "# shutdown state lock 与 ROS owner lock 分离，状态快照不能扩大 ROS 临界区。\n"
        + "# signal callback 不获取任何 owner 锁；它只负责唤醒 asyncio event。\n"
        + "# teardown worker 先退出 ROS 锁，再更新 terminal state，避免反向锁序。\n"
        + "# shutdown 状态不用 ROS 锁保护，避免 signal/teardown 为了记状态反而等待正在执行的 spin。\n"
        + "_ROS_CMD_VEL_SHUTDOWN_STATE_LOCK = threading.Lock()\n"
        + "# hold stop 可能来自 watchdog、release 或 runtime shutdown，三者只能串行发送零速。\n"
        + "# stop owner 锁不参与 keyboard publish，因此不会增加首帧 latency。\n"
        + "# watchdog、release 与 runtime shutdown 的零速收口不能并发抢 ROS/串口；该锁不在 keydown 热路径。\n"
        + "_MANUAL_HOLD_STOP_LOCK = threading.Lock()\n"
        + "# ROS teardown 的 join 使用短硬上限，超时 daemon worker 不阻止解释器退出。\n"
        + "ROS_CMD_VEL_SHUTDOWN_TIMEOUT_S = 0.8\n"
        + "# watchdog、hold stop 与 runner cleanup 都使用显式层级预算并分别记录结果。\n"
        + "UPPER_RUNNER_CLEANUP_TIMEOUT_S = 1.0\n"
    )
    if candidate.count(lock_anchor) != 1:
        raise RuntimeError("ros_lock_anchor_not_unique")
    candidate = candidate.replace(lock_anchor, lock_block, 1)

    # 新 helper 可放在 proof_flags 前；future annotations 允许 UpperRobotApi 类型稍后定义。
    addition_text = "\n\n".join(
        extract(source_lines, source_index[name]).rstrip() for name in SHUTDOWN_ADDITIONS
    ) + "\n\n\n"
    helper_anchor = "def proof_flags() -> dict[str, Any]:\n"
    if candidate.count(helper_anchor) != 1:
        raise RuntimeError("proof_flags_anchor_not_unique")
    return candidate.replace(helper_anchor, addition_text + helper_anchor, 1)


def changed_symbols(base: str, candidate: str) -> list[str]:
    """从真实 AST 反推变化集合，不能只相信生成器声明。"""
    before = definitions(base)
    after = definitions(candidate)
    changed: list[str] = []
    for name in sorted(set(before) | set(after)):
        if name == "UpperRobotApi":
            continue
        old = ast.dump(before[name], include_attributes=False) if name in before else None
        new = ast.dump(after[name], include_attributes=False) if name in after else None
        if old != new:
            changed.append(name)
    return changed


def unified_patch(before: str, after: str, *, before_label: str, after_label: str) -> str:
    """统一 patch path 固定到真实部署目标，支持 git apply dry-run/reverse。"""
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=before_label,
            tofile=after_label,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--previous", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--base-patch", required=True)
    parser.add_argument("--incremental-patch", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    base = Path(args.base).read_text(encoding="utf-8")
    previous = Path(args.previous).read_text(encoding="utf-8")
    source = Path(args.source).read_text(encoding="utf-8")
    candidate = replace_shutdown_definitions(previous, source)
    ast.parse(candidate)
    actual = changed_symbols(base, candidate)
    allowed = sorted(set(PREVIOUS_LATENCY_SYMBOLS) | set(SHUTDOWN_REPLACEMENTS) | set(SHUTDOWN_ADDITIONS))
    forbidden_counts = {token: candidate.count(token) for token in FORBIDDEN_SENTINELS}
    audit_pass = actual == allowed and all(count == 0 for count in forbidden_counts.values())

    base_patch = unified_patch(
        base,
        candidate,
        before_label="a/onboard/scripts/upper_robot_api.py",
        after_label="b/onboard/scripts/upper_robot_api.py",
    )
    incremental_patch = unified_patch(
        previous,
        candidate,
        # 增量 patch 仍绑定真实部署目标；只由输入 hash 区分它要求 adadb0 基线。
        before_label="a/onboard/scripts/upper_robot_api.py",
        after_label="b/onboard/scripts/upper_robot_api.py",
    )
    Path(args.candidate).write_text(candidate, encoding="utf-8")
    Path(args.base_patch).write_text(base_patch, encoding="utf-8")
    Path(args.incremental_patch).write_text(incremental_patch, encoding="utf-8")
    manifest = {
        "schema": "trashbot.o1.latency_only_upper_candidate_v2.v1",
        "base_commit": "85ba7308785aa3c4033180a097e3d388358a97de",
        "base_sha256": sha256_text(base),
        "previous_candidate_sha256": sha256_text(previous),
        "source_sha256": sha256_text(source),
        "candidate_v2_sha256": sha256_text(candidate),
        "base_patch_sha256": sha256_text(base_patch),
        "incremental_patch_sha256": sha256_text(incremental_patch),
        "allowed_changed_symbols": allowed,
        "actual_changed_symbols": actual,
        "forbidden_sentinel_counts": forbidden_counts,
        "ast_and_sentinel_audit_pass": audit_pass,
        "live_nonzero_request_count": 0,
        "physical_latency_not_measured": True,
    }
    Path(args.manifest).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if audit_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
