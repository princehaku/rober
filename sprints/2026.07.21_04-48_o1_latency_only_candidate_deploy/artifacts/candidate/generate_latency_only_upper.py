#!/usr/bin/env python3
"""从冻结的 85ba Upper 基线生成仅含键盘延迟优化的候选文件。"""

from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import json
from pathlib import Path


# 这些定义是本轮唯一允许从已验证组合实现移植到 85ba 基线的生产符号。
TOP_LEVEL_REPLACEMENTS = (
    "_ensure_ros_cmd_vel_context",
    "publish_ros_cmd_vel_inprocess_burst",
    "manual_motion_ros_cmd_vel_hold_refresh_transaction",
    "run_server",
    "create_app",
)
CLASS_METHOD_REPLACEMENTS = (("UpperRobotApi", "manual_control"),)
TOP_LEVEL_ADDITIONS = (
    "normalize_latency_trace",
    "upper_latency_timing",
    "prewarm_ros_cmd_vel_context",
)

# sensor-owned/canonical initialpose/lifecycle ownership 都属于 c8，候选中必须完全不存在。
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
    """hash 绑定生成器输入输出，避免部署时使用另一个未验证文件。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def node_index(text: str) -> tuple[ast.Module, dict[str, ast.AST]]:
    """建立顶层定义和类方法索引；AST 行号用于精确替换完整定义。"""
    tree = ast.parse(text)
    index: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            index[node.name] = node
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        index[f"{node.name}.{child.name}"] = child
    return tree, index


def node_text(lines: list[str], node: ast.AST) -> str:
    """保留已验证源码的中文注释和格式，而不是用 AST unparse 丢掉原因说明。"""
    start = int(getattr(node, "lineno")) - 1
    end = int(getattr(node, "end_lineno"))
    return "".join(lines[start:end])


def replace_ranges(base: str, source: str) -> str:
    """只替换白名单函数/方法；所有区间倒序应用，避免前序替换改变后续行号。"""
    _, base_index = node_index(base)
    _, source_index = node_index(source)
    base_lines = base.splitlines(keepends=True)
    source_lines = source.splitlines(keepends=True)
    replacements: list[tuple[int, int, str, str]] = []
    for name in TOP_LEVEL_REPLACEMENTS:
        old = base_index[name]
        new = source_index[name]
        replacements.append((old.lineno - 1, old.end_lineno, node_text(source_lines, new), name))
    for class_name, method_name in CLASS_METHOD_REPLACEMENTS:
        key = f"{class_name}.{method_name}"
        old = base_index[key]
        new = source_index[key]
        replacements.append((old.lineno - 1, old.end_lineno, node_text(source_lines, new), key))
    for start, end, replacement, _name in sorted(replacements, reverse=True):
        base_lines[start:end] = [replacement]
    return "".join(base_lines)


def add_latency_blocks(candidate: str, source: str) -> str:
    """新增 import、全局锁/trace 常量与 helper；锚点均来自冻结 85ba 文本。"""
    _, source_index = node_index(source)
    source_lines = source.splitlines(keepends=True)
    candidate = candidate.replace("import tempfile\n", "import tempfile\nimport threading\n", 1)
    global_anchor = "_ROS_CMD_VEL_CONTEXT: dict[str, Any] = {}\n"
    global_block = (
        global_anchor
        + "# rclpy node 不能被 watchdog thread 与 aiohttp request 同时 spin/publish；短临界区不包含 burst sleep。\n"
        + "_ROS_CMD_VEL_LOCK = threading.RLock()\n"
        + 'LATENCY_TRACE_SCHEMA = "trashbot.keyboard_wheel_latency_trace.v1"\n'
        + "# trace 只接受短关联键，避免把诊断 envelope 变成任意字符串回显面。\n"
        + 'LATENCY_TRACE_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")\n'
    )
    if candidate.count(global_anchor) != 1:
        raise RuntimeError("global_anchor_not_unique")
    candidate = candidate.replace(global_anchor, global_block, 1)
    helper_anchor = "def proof_flags() -> dict[str, Any]:\n"
    helper_text = "\n\n".join(
        node_text(source_lines, source_index[name]).rstrip() for name in TOP_LEVEL_ADDITIONS
    ) + "\n\n\n"
    if candidate.count(helper_anchor) != 1:
        raise RuntimeError("helper_anchor_not_unique")
    return candidate.replace(helper_anchor, helper_text + helper_anchor, 1)


def changed_symbols(base: str, candidate: str) -> list[str]:
    """列出 AST 真正变化的定义，审计时不能只相信生成器自己的白名单声明。"""
    _, before = node_index(base)
    _, after = node_index(candidate)
    changed: list[str] = []
    for name in sorted(set(before) | set(after)):
        # Class 聚合变化由其具体 method 解释，不重复放宽整个类。
        if name == "UpperRobotApi":
            continue
        old = before.get(name)
        new = after.get(name)
        old_dump = ast.dump(old, include_attributes=False) if old is not None else None
        new_dump = ast.dump(new, include_attributes=False) if new is not None else None
        if old_dump != new_dump:
            changed.append(name)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--patch", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    base_path = Path(args.base)
    source_path = Path(args.source)
    base = base_path.read_text(encoding="utf-8")
    source = source_path.read_text(encoding="utf-8")
    candidate = add_latency_blocks(replace_ranges(base, source), source)
    ast.parse(candidate)
    changed = changed_symbols(base, candidate)
    allowed = sorted((*TOP_LEVEL_REPLACEMENTS, *TOP_LEVEL_ADDITIONS, "UpperRobotApi.manual_control"))
    forbidden_hits = {token: candidate.count(token) for token in FORBIDDEN_SENTINELS if token in candidate}
    audit_pass = changed == allowed and not forbidden_hits

    candidate_path = Path(args.candidate)
    patch_path = Path(args.patch)
    manifest_path = Path(args.manifest)
    candidate_path.write_text(candidate, encoding="utf-8")
    patch_text = "".join(
        difflib.unified_diff(
            base.splitlines(keepends=True),
            candidate.splitlines(keepends=True),
            fromfile="a/onboard/scripts/upper_robot_api.py",
            tofile="b/onboard/scripts/upper_robot_api.py",
        )
    )
    patch_path.write_text(patch_text, encoding="utf-8")
    manifest = {
        "schema": "trashbot.o1.latency_only_upper_candidate.v1",
        "base_commit": "85ba7308785aa3c4033180a097e3d388358a97de",
        # manifest 会进入版本库，必须使用位置无关引用，不能泄漏生成机用户名或临时目录。
        "base_path": "85ba7308785aa3c4033180a097e3d388358a97de:onboard/scripts/upper_robot_api.py",
        "source_path": "onboard/scripts/upper_robot_api.py",
        "base_sha256": sha256_text(base),
        "source_sha256": sha256_text(source),
        "candidate_sha256": sha256_text(candidate),
        "patch_sha256": sha256_text(patch_text),
        "allowed_changed_symbols": allowed,
        "actual_changed_symbols": changed,
        "forbidden_sentinel_counts": {token: candidate.count(token) for token in FORBIDDEN_SENTINELS},
        "forbidden_hits": forbidden_hits,
        "ast_and_sentinel_audit_pass": audit_pass,
        "physical_latency_not_measured": True,
        "live_nonzero_request_count": 0,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if audit_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
