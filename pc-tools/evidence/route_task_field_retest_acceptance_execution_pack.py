#!/usr/bin/env python3
"""生成 route/task field retest acceptance execution pack artifact。

该 gate 只消费上一轮 route_task_field_retest_acceptance_review_decision 的
artifact、summary、wrapper/nested JSON，或 file/env 风格 source。输出用于现场
复跑准备的 owner checklist、rerun commands 和 safe evidence bundle。它不访问
真实材料目录、ROS graph、Nav2 runtime、serial/UART、硬件、真实电梯、外部云、
OSS/CDN、DB/queue、4G 或真实手机/browser，也不触发任何机器人动作。
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import route_task_field_retest_acceptance_review_decision as review


PACK_SCHEMA = "trashbot.route_task_field_retest_acceptance_execution_pack.v1"
PACK_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_acceptance_execution_pack_summary.v1"
SCHEMA_VERSION = 1
PACK_BOUNDARY = "software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate"

# execution pack 只承接上一轮 acceptance review decision，不能跳级消费 brief。
SOURCE_SCHEMAS = {review.DECISION_SCHEMA, review.DECISION_SUMMARY_SCHEMA}
SOURCE_BOUNDARY = review.DECISION_BOUNDARY

# 现场执行包必须继续沿用 acceptance 链路的八类 route/elevator 材料。
REQUIRED_ROUTE_ELEVATOR_MATERIALS = list(review.REQUIRED_EVIDENCE_PACKET)
NOT_PROVEN = list(review.NOT_PROVEN)

# rg 围栏和后续 Robot/mobile 消费都依赖这些 literal 明确边界。
BOUNDARY_NOTE = (
    "route_task_field_retest_acceptance_execution_pack; "
    "software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 不读取真实现场材料，只整理复跑执行包。
# 设计约束 02：review decision 未 ready 时仍生成 blocked pack，便于交接补救。
# 设计约束 03：file: 和 env: source 只解析 JSON 来源，不扩大证据能力边界。
# 设计约束 04：unsupported schema/boundary 必须 fail closed，避免跨契约消费。
# 设计约束 05：same evidence_ref 是复跑主键，不一致必须重跑上游 review。
# 设计约束 06：safe evidence bundle 只能包含白名单字段，不复制 raw artifact。
# 设计约束 07：owner checklist 是现场准备清单，不授权 Start/Dropoff/Cancel。
# 设计约束 08：rerun commands 是人工执行提示，不由本 gate 自动运行。
# 设计约束 09：summary 是 Robot/mobile 首选消费面，字段必须稳定。
# 设计约束 10：delivery_success 固定 false，不能被 source 覆盖。
# 设计约束 11：primary_actions_enabled 固定 false，不能被 source 覆盖。
# 设计约束 12：not_proven 固定保留 route/elevator、HIL、手机、外部云缺口。
# 设计约束 13：缺 evidence_ref 不进入 ready，因为真实材料无法同 ref 复账。
# 设计约束 14：弱类型 same_evidence_ref_required 视为上游不可信。
# 设计约束 15：success/control claim 直接阻断，避免软件证明误导现场。
# 设计约束 16：required materials 固定八类，新增材料要另开契约。
# 设计约束 17：handoff_owner 固定指向现场 owner，不推断真实负责人在线。
# 设计约束 18：dependency-free，便于 macOS PC 与 Docker 本地验证。
# 设计约束 19：exit code 保持 0，blocked artifact 也能进入 sprint 留档。
# 设计约束 20：本文件作为 Autonomy 范围交付，不修改 Robot 或 Full-stack 文件。


def _utc_now() -> str:
    # UTC 时间便于多机复制 artifact 后按时间线审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 复用上游 brief 的脱敏器，保持 route/elevator 链路 copy 规则一致。
    return review.brief.pack._safe_text(value)


def _safe_ref(value: Any) -> str:
    # evidence_ref 只保留安全短引用，路径类输入收敛为 file:<basename>。
    return review.brief.pack._safe_ref(value)


def _safe_value(value: Any) -> Any:
    # 最终 payload 递归脱敏，防止新增嵌套字段绕过局部 helper。
    return review.brief.pack._safe_value(value)


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # 上游字段可为字符串或 list；限制数量避免复制完整 raw artifact。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object 嵌套字段，字符串 wrapper 不能伪装可信 JSON。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 wrapper 字段位置不同，取首个非空值。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _resolve_source_path(source: str) -> tuple[str, str]:
    # file:/env: 只解决“从哪里读 JSON”，不把来源本身写入 safe bundle。
    text = str(source or "").strip()
    if text.startswith("file:"):
        return text.removeprefix("file:"), "file_source"
    if text.startswith("env:"):
        name = text.removeprefix("env:").strip()
        if not name:
            return "", "env_source_name_missing"
        value = os.environ.get(name, "").strip()
        if not value:
            return "", "env_source_missing"
        return value.removeprefix("file:"), "env_source"
    return text, "path_source"


def _load_json(source: str) -> tuple[dict[str, Any], str, str]:
    # 缺输入、坏 JSON 和非 object 都转成 blocked artifact，保持证据留痕。
    path, source_style = _resolve_source_path(source)
    if not path:
        return {}, "acceptance_review_decision_json_not_provided", source_style
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "acceptance_review_decision_json_missing", source_style
    except json.JSONDecodeError:
        return {}, "acceptance_review_decision_json_bad_json", source_style
    except (OSError, UnicodeDecodeError):
        return {}, "acceptance_review_decision_json_read_error", source_style
    if not isinstance(payload, dict):
        return {}, "acceptance_review_decision_json_not_object", source_style
    return payload, "", source_style


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 key，避免任意 JSON envelope 被当成 review decision。
    candidates = [payload]
    for key in (
        "route_task_field_retest_acceptance_review_decision",
        "route_task_field_retest_acceptance_review_decision_summary",
        "route_task_field_retest_acceptance_execution_pack_source",
        "acceptance_review_decision",
        "acceptance_review_decision_summary",
        "review_decision",
        "review_decision_summary",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_source_candidates(value))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先消费 schema 命中的对象；无命中时保留顶层用于 unsupported 说明。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _source_status(load_issue: str, source: dict[str, Any]) -> dict[str, str]:
    # schema 与 boundary 必须同时支持，防止拿错上游 JSON。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = _safe_text(source.get("schema", ""))
    boundary = _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))
    if schema in SOURCE_SCHEMAS and boundary == SOURCE_BOUNDARY:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_ref(source: dict[str, Any]) -> str:
    # evidence_ref 可位于 artifact、summary 或 safe_copy，统一收敛。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "route_task_field_retest_acceptance_review_decision_summary")
    return _safe_ref(
        _first_text(
            source.get("evidence_ref"),
            source.get("safe_evidence_ref"),
            summary.get("evidence_ref"),
            summary.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            default="",
        )
    )


def _source_review_decision(source: dict[str, Any]) -> str:
    # 只消费上游 review decision 状态，不推断真实路线或电梯结果。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "route_task_field_retest_acceptance_review_decision_summary")
    return _safe_text(
        _first_text(
            source.get("review_decision"),
            source.get("status"),
            summary.get("review_decision"),
            summary.get("status"),
            safe_copy.get("review_decision"),
            safe_copy.get("status"),
            default="missing",
        )
    )


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 弱类型字符串必须 fail closed；这里要求 JSON boolean true。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "route_task_field_retest_acceptance_review_decision_summary")
    return source.get(
        "same_evidence_ref_required",
        summary.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True)),
    )


def _material_status(source: dict[str, Any]) -> str:
    # material_status 只用于说明下一步补什么，不表达真实材料有效。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "route_task_field_retest_acceptance_review_decision_summary")
    return _safe_text(
        _first_text(
            source.get("material_status"),
            summary.get("material_status"),
            safe_copy.get("material_status"),
            default="missing",
        )
    )


def _missing_packet(source: dict[str, Any]) -> list[str]:
    # 只读取上游 summary 的缺项，不打开真实材料文件。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "route_task_field_retest_acceptance_review_decision_summary")
    raw_missing = (
        source.get("missing_evidence_packet")
        or source.get("missing_materials")
        or summary.get("missing_evidence_packet")
        or summary.get("missing_materials")
        or safe_copy.get("missing_evidence_packet")
    )
    missing: list[str] = []
    for item in _safe_list(raw_missing, limit=len(REQUIRED_ROUTE_ELEVATOR_MATERIALS)):
        if item in REQUIRED_ROUTE_ELEVATOR_MATERIALS and item not in missing:
            missing.append(item)
    return missing


def _owner_handoff_source(source: dict[str, Any]) -> dict[str, Any]:
    # summary 和 artifact 都可能有 owner_handoff；只复制脱敏后的白名单对象。
    summary = _dict(source, "route_task_field_retest_acceptance_review_decision_summary")
    handoff = source.get("owner_handoff") if isinstance(source.get("owner_handoff"), dict) else summary.get("owner_handoff")
    return _safe_value(handoff) if isinstance(handoff, dict) else {}


def _unsafe_source(source: dict[str, Any]) -> bool:
    # 上游已有 unsafe 扫描；这里再补 delivery/control 布尔硬门槛。
    if source.get("delivery_success") is True or source.get("primary_actions_enabled") is True:
        return True
    return review._unsafe_source(source)


def _pack_status(
    load_issue: str,
    source_status: dict[str, str],
    source_ref: str,
    requested_ref: str,
    same_ref_required: Any,
    unsafe: bool,
    source_decision: str,
) -> str:
    # fail-closed 顺序固定，危险输入和 ref 不一致优先于普通未 ready。
    if unsafe:
        return "rejected_unsafe_acceptance_review_decision_claim_not_proven"
    if load_issue or source_status["schema_status"] != "supported":
        return "unsupported_acceptance_review_decision_schema_not_proven"
    if not source_ref or (requested_ref and source_ref != requested_ref) or same_ref_required is not True:
        return "evidence_ref_mismatch_rerun_not_proven"
    if source_decision != "ready_for_controlled_field_retest_not_proven":
        return "blocked_acceptance_review_decision_not_ready"
    return "ready_for_field_retest_acceptance_execution_pack_not_proven"


def _owner_checklist(evidence_ref: str) -> list[str]:
    # checklist 是现场复跑准备顺序，不声明任何真实执行已发生。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"Confirm every route/elevator material will use evidence_ref={ref}.",
        "Prepare Nav2/fixed-route runtime log capture before moving the robot.",
        "Prepare route completion signal and task record export from the same retest.",
        "Prepare elevator door state and target floor confirmation notes before elevator entry.",
        "Prepare human assistance note template for any manual elevator help.",
        "Prepare dropoff or cancel completion note and delivery result placeholder.",
        "Keep delivery_success=false until Product reviews real field materials.",
        "Keep primary_actions_enabled=false in Robot diagnostics and mobile/web surfaces.",
    ]


def _rerun_commands(evidence_ref: str) -> list[str]:
    # commands 只描述 PC/Robot/mobile 复核链，不自动触发 ROS 或机器人控制。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        "python3 pc-tools/evidence/route_task_field_retest_acceptance_review_decision.py "
        "--acceptance-brief-json <acceptance_brief_summary.json> "
        f"--evidence-ref {ref} --output <acceptance_review_decision.json> "
        "--summary-output <acceptance_review_decision_summary.json>",
        "python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_pack.py "
        "--acceptance-review-decision-json <acceptance_review_decision_summary.json> "
        f"--evidence-ref {ref} --output <acceptance_execution_pack.json> "
        "--summary-output <acceptance_execution_pack_summary.json>",
        "PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest "
        "onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py",
        "python3 -m unittest mobile/web/test_mobile_web_entrypoint.py",
        "Keep field closeout blocked until real route/elevator materials are attached under the same evidence_ref.",
    ]


def _safe_evidence_bundle(
    status: str,
    evidence_ref: str,
    source_decision: str,
    material_status: str,
    missing_packet: list[str],
    next_required_evidence: list[str],
) -> dict[str, Any]:
    # bundle 是现场 owner 可转交的安全摘要，不含 raw JSON、路径、凭证或控制话术。
    return {
        "schema": f"{PACK_SUMMARY_SCHEMA}.safe_copy",
        "execution_pack_status": status,
        "status": status,
        "review_decision_source": source_decision,
        "evidence_boundary": PACK_BOUNDARY,
        "boundary": PACK_BOUNDARY,
        "evidence_ref": evidence_ref,
        "safe_evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "material_status": material_status,
        "missing_evidence_packet": list(missing_packet),
        "required_route_elevator_materials": list(REQUIRED_ROUTE_ELEVATOR_MATERIALS),
        "next_required_evidence": list(next_required_evidence),
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _next_required_evidence(status: str, missing_packet: list[str], evidence_ref: str) -> list[str]:
    # next evidence 只列材料类别和动作，不包含本机路径或 raw artifact。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "ready_for_field_retest_acceptance_execution_pack_not_proven":
        return [
            f"Run controlled field retest with evidence_ref={ref} unchanged.",
            "Attach every required route/elevator material before result intake.",
            "Record failure reason instead of success wording when any material is missing.",
        ]
    if status == "blocked_acceptance_review_decision_not_ready" and missing_packet:
        return [f"Backfill missing route/elevator material metadata first: {', '.join(missing_packet)}."]
    if status == "evidence_ref_mismatch_rerun_not_proven":
        return [f"Rerun acceptance brief, review decision, and execution pack with one safe evidence_ref={ref}."]
    if status == "rejected_unsafe_acceptance_review_decision_claim_not_proven":
        return ["Remove unsafe copy, success wording, raw paths, credentials, topics, serial/UART, or control claims."]
    return ["Regenerate a supported route_task_field_retest_acceptance_review_decision artifact or summary."]


def _handoff_owner(status: str, evidence_ref: str, source_handoff: dict[str, Any]) -> dict[str, Any]:
    # handoff_owner 说明谁准备材料，不授权任何主路径动作。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "owner": "Autonomy Algorithm Engineer",
        "field_owner": "Route/elevator field retest operator",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "source_owner_handoff": source_handoff,
        "handoff_note": (
            f"Use this pack to prepare the controlled route/elevator retest for evidence_ref={ref}."
            if status == "ready_for_field_retest_acceptance_execution_pack_not_proven"
            else f"Repair the acceptance review decision source before field retest for evidence_ref={ref}."
        ),
        "primary_actions_enabled": False,
    }


def _summary_payload(
    status: str,
    evidence_ref: str,
    source_decision: str,
    material_status: str,
    owner_checklist: list[str],
    rerun_commands: list[str],
    safe_bundle: dict[str, Any],
    handoff_owner: dict[str, Any],
    next_required_evidence: list[str],
) -> dict[str, Any]:
    # summary 是下游稳定消费面，字段与 artifact 保持同名核心契约。
    return {
        "schema": PACK_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": PACK_BOUNDARY,
        "boundary": PACK_BOUNDARY,
        "status": status,
        "execution_pack_status": status,
        "review_decision_source": source_decision,
        "evidence_ref": evidence_ref,
        "safe_evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "material_status": material_status,
        "owner_checklist": owner_checklist,
        "rerun_commands": rerun_commands,
        "safe_evidence_bundle": safe_bundle,
        "safe_copy": safe_bundle,
        "required_route_elevator_materials": list(REQUIRED_ROUTE_ELEVATOR_MATERIALS),
        "handoff_owner": handoff_owner,
        "next_required_evidence": next_required_evidence,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_acceptance_execution_pack(
    acceptance_review_decision_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    # 主构建函数保持 CLI/unittest 共用，便于离线验证同一逻辑。
    payload, load_issue, source_style = _load_json(acceptance_review_decision_json)
    source = _find_source(payload) if payload else {}
    source_status = _source_status(load_issue, source)
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source)
    resolved_ref = requested_ref or source_ref
    source_decision = _source_review_decision(source)
    same_ref_required = _same_ref_required(source)
    material_status = _material_status(source)
    missing_packet = _missing_packet(source)
    unsafe = _unsafe_source(source)
    status = _pack_status(
        load_issue,
        source_status,
        source_ref,
        requested_ref,
        same_ref_required,
        unsafe,
        source_decision,
    )
    owner_checklist = _owner_checklist(resolved_ref)
    rerun_commands = _rerun_commands(resolved_ref)
    next_required_evidence = _next_required_evidence(status, missing_packet, resolved_ref)
    safe_bundle = _safe_evidence_bundle(status, resolved_ref, source_decision, material_status, missing_packet, next_required_evidence)
    handoff_owner = _handoff_owner(status, resolved_ref, _owner_handoff_source(source))
    summary = _summary_payload(
        status,
        resolved_ref,
        source_decision,
        material_status,
        owner_checklist,
        rerun_commands,
        safe_bundle,
        handoff_owner,
        next_required_evidence,
    )
    artifact = {
        "schema": PACK_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": PACK_BOUNDARY,
        "boundary": PACK_BOUNDARY,
        "status": status,
        "execution_pack_status": status,
        "review_decision_source": source_decision,
        "source_acceptance_review_decision": {
            "source_style": source_style,
            "schema": _safe_text(source.get("schema", "")),
            "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
            "load_status": source_status["load_status"],
            "schema_status": source_status["schema_status"],
            "load_issue": source_status["load_issue"],
            "review_decision": source_decision,
            "unsafe_source": unsafe,
        },
        "evidence_ref": resolved_ref,
        "safe_evidence_ref": resolved_ref,
        "same_evidence_ref_required": True,
        "material_status": material_status,
        "owner_checklist": owner_checklist,
        "rerun_commands": rerun_commands,
        "safe_evidence_bundle": safe_bundle,
        "safe_copy": safe_bundle,
        "required_route_elevator_materials": list(REQUIRED_ROUTE_ELEVATOR_MATERIALS),
        "handoff_owner": handoff_owner,
        "next_required_evidence": next_required_evidence,
        "route_task_field_retest_acceptance_execution_pack_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_directory",
            "ros_graph",
            "nav2_runtime",
            "serial_uart",
            "hardware_transport",
            "real_elevator",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "phone_device_or_browser",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _unsafe_source(summary):
        # 最终防线：summary 不安全时同步降级 artifact 和白名单面。
        status = "rejected_unsafe_acceptance_review_decision_claim_not_proven"
        summary["status"] = status
        summary["execution_pack_status"] = status
        summary["safe_evidence_bundle"]["execution_pack_status"] = status
        summary["safe_copy"]["execution_pack_status"] = status
        artifact["status"] = status
        artifact["execution_pack_status"] = status
        artifact["safe_evidence_bundle"]["execution_pack_status"] = status
        artifact["safe_copy"]["execution_pack_status"] = status
        artifact["route_task_field_retest_acceptance_execution_pack_summary"] = summary
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时创建父目录；空路径表示只走 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 不接触运行时系统，只把 acceptance review decision 转成执行包。
    parser = argparse.ArgumentParser(description="Build route/task field retest acceptance execution pack artifact")
    parser.add_argument(
        "--acceptance-review-decision-json",
        required=True,
        help="acceptance review decision artifact, summary, wrapper, file:<path>, or env:<VAR>",
    )
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for the acceptance execution pack")
    parser.add_argument("--output", default="", help="optional acceptance execution pack artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional acceptance execution pack summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print acceptance execution pack artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_acceptance_execution_pack(
        args.acceptance_review_decision_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_acceptance_execution_pack: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"execution_pack_summary_file: {_safe_ref(args.summary_output)}")
        print(f"execution_pack_status: {artifact['execution_pack_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
