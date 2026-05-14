#!/usr/bin/env python3
"""生成 route/task rehearsal execution bundle manifest。

该工具只聚合 Docker/local 软件排练材料，不读取硬件、不触发 Nav2、不写入机器人状态。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import evidence_crosscheck


# manifest 边界单独命名，避免调用方把 artifact gate 和 bundle gate 混成真实上车证据。
# schema 名会被 diagnostics 与 sprint closeout 读取，所以保持稳定字符串而不是动态生成。
EXECUTION_BUNDLE_SCHEMA = "trashbot.route_task_rehearsal_execution_bundle"
# schema_version 从 1 起步，后续新增字段时可向后兼容消费旧 manifest。
EXECUTION_BUNDLE_VERSION = 1
# evidence_boundary 是本工具最重要的安全栏，必须比 status 字段更醒目。
EXECUTION_BUNDLE_BOUNDARY = "software_proof_docker_route_task_rehearsal_execution_bundle_gate"

# bundle 面向交接与支持场景，需要比底层 artifact 更明确地排除投放/取消完成语义。
# 这些枚举会进入 manifest，目的是让支持面看到 pass 时也不会误判真实送达完成。
EXECUTION_BUNDLE_NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "real_route_capture",
    "wave_rover_motion",
    "real_serial_or_uart_feedback",
    "real_hil_pass",
    "dropoff_completion",
    "cancel_completion",
    "delivery_success",
)


def _safe_text(value: Any) -> str:
    # 复用 crosscheck 的脱敏规则，保证 bundle manifest 与 artifact 的分享边界一致。
    # 这里不重新维护正则，避免两份工具对同一 secret 给出不同处理。
    return evidence_crosscheck._safe_text(value)


def _safe_value(value: Any) -> Any:
    # manifest 只记录可传递摘要；嵌套结构也必须走同一套脱敏逻辑。
    # 嵌套字段里也可能藏着路径或 token，因此不能只过滤顶层字符串。
    return evidence_crosscheck._safe_value(value)


def _load_json(path: Path, label: str) -> dict[str, Any]:
    # 这里显式要求 JSON object，避免把数组或字符串误包装成可交接 manifest。
    # Path 在调用侧已经 expanduser；这里保持只读，避免工具产生额外副作用。
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    # 上游 artifact/manifest 都按对象消费；非对象说明输入类型已经偏离契约。
    if not isinstance(payload, dict):
        raise ValueError(f"{label} payload is not a JSON object: {path}")
    return payload


def _status_from_artifact(artifact: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    # pass/fail 只来自软件对账；HIL 对齐仍是独立字段，不能扩大 bundle 含义。
    crosscheck_status = artifact.get("crosscheck_status")
    # 缺 crosscheck_status 时宁可 blocked，也不从其它字段猜测软件对账是否通过。
    if not isinstance(crosscheck_status, dict):
        return "blocked_missing_crosscheck_status", "missing", {}
    status = str(crosscheck_status.get("status", "")).strip() or "missing"
    # available_software_proof 是可交接状态，不是 delivery 或 HIL 完成状态。
    if status == "pass":
        return "available_software_proof", status, crosscheck_status
    return "blocked_crosscheck_mismatch", status, crosscheck_status


def _merge_not_proven(artifact: dict[str, Any]) -> list[str]:
    # 底层 artifact 已列出 HIL/运动边界；bundle 再补 route capture 与投放/取消完成边界。
    values: list[str] = []
    for item in artifact.get("not_proven", []):
        text = str(item).strip()
        # 保持原始顺序，方便人工对比 artifact 与 bundle 的边界是否一致。
        if text and text not in values:
            values.append(text)
    for item in EXECUTION_BUNDLE_NOT_PROVEN:
        # 只补缺项，避免同一风险重复出现影响支持人员快速阅读。
        if item not in values:
            values.append(item)
    return values


def _build_manifest(
    route_status: str,
    task_record: str,
    task_record_dir: str,
    hil_gate_output: str,
    artifact_path: Path,
    manifest_path: Path,
    crosscheck_exit_code: int,
) -> dict[str, Any]:
    artifact = _load_json(artifact_path, "route_task_rehearsal_artifact")
    # bundle status 直接从 artifact crosscheck 派生，避免第二套判定逻辑漂移。
    # 如果后续 crosscheck 增加字段，bundle 仍以 artifact 为单一事实来源。
    bundle_status, software_crosscheck_status, crosscheck_summary = _status_from_artifact(artifact)
    hil_summary = artifact.get("hil_alignment_status")
    diagnostics_summary = artifact.get("diagnostics_summary")
    # artifact 可能来自旧版本或手工材料；缺字段时以空摘要保守继续生成 manifest。
    if not isinstance(hil_summary, dict):
        # 缺 HIL 摘要不能推断 HIL 通过，只能保守地留空并依赖 not_proven。
        hil_summary = {}
    if not isinstance(diagnostics_summary, dict):
        # diagnostics_summary 只是辅助阅读字段，缺失时不应阻止 manifest 记录 mismatch。
        diagnostics_summary = {}

    # manifest 不复制 raw status/task payload，只保留脱敏引用和摘要，便于跨人交接。
    return {
        # 顶层字段给机器读，支持方可以先看 schema/status/boundary 三项。
        "schema": EXECUTION_BUNDLE_SCHEMA,
        "schema_version": EXECUTION_BUNDLE_VERSION,
        # 使用 UTC 时间，避免不同开发机时区影响材料排序。
        "generated_at": datetime.now(timezone.utc).isoformat(),
        # status 是软件交接状态，不作为机器人动作状态或任务终态使用。
        "status": bundle_status,
        # 顶层 evidence_boundary 让单独打开 manifest 的读者也能看到证据边界。
        "evidence_boundary": EXECUTION_BUNDLE_BOUNDARY,
        # evidence_ref 是串联 status/replay/task_record 的关键索引，必须保留在顶层。
        "evidence_ref": _safe_text(artifact.get("evidence_ref", "")),
        # diagnostics worker 只读消费这些顶层字段；放在顶层可避免被判成 unsupported manifest。
        "route_task_rehearsal_artifact_ref": _safe_text(str(artifact_path)),
        # 顶层 crosscheck_status 保持 artifact 原结构，便于 diagnostics 直接读取 status=pass/fail。
        "crosscheck_status": _safe_value(crosscheck_summary),
        # 顶层 HIL 摘要必须继续显示 not_proven，防止软件 pass 被误读为 HIL pass。
        "hil_alignment_status": _safe_value(hil_summary),
        # diagnostics_summary 是 phone/support safe 摘要，作为 manifest 顶层只读契约提供。
        "diagnostics_summary": _safe_value(diagnostics_summary),
        # inputs 只保存引用，不内联原始 payload，减少敏感路径和大对象扩散。
        "inputs": {
            "route_status_ref": _safe_text(route_status),
            "task_record_ref": _safe_text(task_record) if task_record else "",
            "task_record_dir_ref": _safe_text(task_record_dir) if task_record_dir else "",
            "hil_gate_output_ref": _safe_text(hil_gate_output) if hil_gate_output else "",
        },
        # outputs 让 diagnostics worker 能定位 manifest 与底层 artifact 的对应关系。
        "outputs": {
            "rehearsal_artifact_ref": _safe_text(str(artifact_path)),
            "manifest_ref": _safe_text(str(manifest_path)),
        },
        # artifact_status 保留 exit code，是为了区分软件 mismatch 与 HIL not_proven。
        "artifact_status": {
            "schema": _safe_text(artifact.get("schema", "")),
            "evidence_boundary": _safe_text(artifact.get("evidence_boundary", "")),
            "crosscheck_exit_code": crosscheck_exit_code,
            # software_crosscheck_status 方便 diagnostics 不展开 crosscheck_status 也能判断。
            "software_crosscheck_status": software_crosscheck_status,
            # 原始 crosscheck_status 保留软件 mismatch 明细，便于下一轮定位。
            "crosscheck_status": _safe_value(crosscheck_summary),
            # HIL alignment 放在相邻字段，明确它不是软件 pass 的一部分。
            "hil_alignment_status": _safe_value(hil_summary),
            "diagnostics_summary_status": _safe_text(diagnostics_summary.get("status", "")),
        },
        # summary 字段来自 artifact，便于单文件交接时不用再打开底层 artifact 才能判断。
        "route_status_summary": _safe_value(artifact.get("route_status_summary", {})),
        "task_record_summary": _safe_value(artifact.get("task_record_summary", {})),
        # not_proven 是产品边界字段，必须随 manifest 直接出现。
        "not_proven": _merge_not_proven(artifact),
        "next_step": _safe_text(
            diagnostics_summary.get(
                "next_step",
                "collect real Nav2/fixed-route and HIL evidence before claiming delivery success",
            )
        ),
        # 该字段是给 reviewer/PM 的显式防误读栏，不参与 pass/fail 计算。
        "bundle_pass_does_not_prove": list(EXECUTION_BUNDLE_NOT_PROVEN),
    }


def write_execution_bundle(
    route_status: str,
    task_record: str,
    task_record_dir: str,
    expected_evidence_ref: str,
    hil_gate_output: str,
    output_dir: str,
) -> tuple[Path, int]:
    output_root = Path(output_dir).expanduser()
    # output dir 可位于 /tmp，创建目录比要求调用方预建更适合围栏 drill。
    output_root.mkdir(parents=True, exist_ok=True)
    # 固定文件名能让 diagnostics 和 sprint 文档引用稳定，不需要猜最新文件。
    artifact_path = output_root / "route_task_rehearsal_artifact.json"
    manifest_path = output_root / "route_task_rehearsal_execution_bundle.json"

    # 先让已有 crosscheck 生成权威 artifact，bundle 只做二次聚合，不重新实现字段比对。
    # 这样字段比较规则仍由 evidence_crosscheck.py 统一维护。
    crosscheck_exit_code = evidence_crosscheck.run_crosscheck(
        str(Path(route_status).expanduser()),
        str(Path(task_record).expanduser()) if task_record else "",
        str(Path(task_record_dir).expanduser()) if task_record_dir else "",
        expected_evidence_ref,
        str(Path(hil_gate_output).expanduser()) if hil_gate_output else "",
        str(artifact_path),
    )

    # 即使 crosscheck 返回 fail，只要 artifact 已生成，也写 manifest 记录 blocked 原因。
    manifest = _build_manifest(
        route_status=str(Path(route_status).expanduser()),
        task_record=str(Path(task_record).expanduser()) if task_record else "",
        task_record_dir=str(Path(task_record_dir).expanduser()) if task_record_dir else "",
        hil_gate_output=str(Path(hil_gate_output).expanduser()) if hil_gate_output else "",
        artifact_path=artifact_path,
        manifest_path=manifest_path,
        crosscheck_exit_code=crosscheck_exit_code,
    )
    # sort_keys 让 diff 和人工复核稳定；ensure_ascii=False 保留中文边界说明可读性。
    # 结尾换行保持类 Unix 文本文件习惯，方便 git diff 与 shell 工具消费。
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"route/task rehearsal execution bundle: {_safe_text(str(manifest_path))}")
    # 返回 crosscheck exit code，调用方可在 CI/围栏中继续把 mismatch 视为失败。
    return manifest_path, crosscheck_exit_code


def main() -> int:
    # CLI 参数沿用 evidence_crosscheck 的输入模型，降低 operator 迁移成本。
    parser = argparse.ArgumentParser(
        description="Generate a software-proof route/task rehearsal execution bundle manifest"
    )
    # route_status 是唯一必填输入，因为 replay artifact path 可从 status.software_proof 派生。
    parser.add_argument("route_status", help="fixed_route status JSON file")
    # task_record 与 task_record_dir 二选一，保留手工文件和自动查找两种复盘模式。
    parser.add_argument("--task-record", default="", help="task_record JSON file")
    parser.add_argument(
        "--task-record-dir",
        default="",
        help="folder to auto-pick task_record by evidence_ref/result_path when --task-record is absent",
    )
    # evidence_ref override 用于受控样例，防止测试材料路径变化影响同 run 对账。
    parser.add_argument("--evidence-ref", default="", help="expected evidence_ref override for run-level alignment")
    parser.add_argument(
        "--hil-gate-output",
        default="",
        help="optional hil_evidence_packet_gate.py JSON output for alignment summary only",
    )
    # output-dir 必填，避免工具在当前目录静默生成证据文件造成仓库脏污。
    parser.add_argument("--output-dir", required=True, help="directory for artifact and execution bundle manifest")
    args = parser.parse_args()

    # main 只负责参数转发，核心逻辑放在函数里，方便后续小范围单测或 diagnostics 复用。
    _, exit_code = write_execution_bundle(
        route_status=args.route_status,
        task_record=args.task_record,
        task_record_dir=args.task_record_dir,
        expected_evidence_ref=args.evidence_ref,
        hil_gate_output=args.hil_gate_output,
        output_dir=args.output_dir,
    )
    return exit_code


if __name__ == "__main__":
    # SystemExit 保留 shell exit code，方便 sprint 验收命令直接判断 pass/fail。
    raise SystemExit(main())
