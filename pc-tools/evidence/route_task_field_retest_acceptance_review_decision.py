#!/usr/bin/env python3
"""生成 route/task field retest acceptance review decision artifact。

该 gate 只读取上一轮 route_task_field_retest_acceptance_brief 的 artifact、
summary 或 wrapper/nested JSON，把现场验收入口简报转成 PC / Robot / mobile
可消费的 metadata-only review decision。它不读取真实材料目录，不访问 ROS graph、
Nav2 runtime、serial/UART、硬件、真实电梯、外部云、OSS/CDN、DB/queue、4G
或真实手机/browser，也不触发任何机器人动作。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import route_task_field_retest_acceptance_brief as brief


# review decision 是 acceptance brief 之后的新契约，不能复用 brief schema。
DECISION_SCHEMA = "trashbot.route_task_field_retest_acceptance_review_decision.v1"
DECISION_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_acceptance_review_decision_summary.v1"
SCHEMA_VERSION = 1
DECISION_BOUNDARY = "software_proof_docker_route_task_field_retest_acceptance_review_decision_gate"

# 只接受 acceptance brief，避免 dispatch、callback 或 result 材料被跳级解释。
SOURCE_SCHEMAS = {brief.BRIEF_SCHEMA, brief.BRIEF_SUMMARY_SCHEMA}
SOURCE_BOUNDARY = brief.BRIEF_BOUNDARY

# 八类材料沿用 acceptance brief 的 packet 清单；本 gate 只看摘要状态。
REQUIRED_EVIDENCE_PACKET = brief.REQUIRED_EVIDENCE_PACKET

# not_proven 固定覆盖路线、电梯、投放、HIL、手机和外部云缺口。
NOT_PROVEN = brief.NOT_PROVEN

# rg 围栏和人工复盘都依赖这些 literal 识别边界。
BOUNDARY_NOTE = (
    "route_task_field_retest_acceptance_review_decision; "
    "software_proof_docker_route_task_field_retest_acceptance_review_decision_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 只消费 acceptance brief，不读取真实材料目录。
# 设计约束 02：review_decision 只表达现场验收前的下一步，不证明现场结果。
# 设计约束 03：ready 分支仍保持 not_proven，不能改变 Robot/mobile action。
# 设计约束 04：unsupported schema/boundary 必须 fail closed，禁止跨契约消费。
# 设计约束 05：same evidence_ref 是证据链主键，不一致必须复跑 brief/review。
# 设计约束 06：unsafe copy 和 success/control claim 优先阻断，避免文案扩权。
# 设计约束 07：material backfill 只要求补摘要材料，不要求本 gate 打开文件。
# 设计约束 08：owner handoff 是只读交接摘要，不授权 Start/Dropoff/Cancel。
# 设计约束 09：summary 是 Robot/mobile 首选消费面，只输出白名单字段。
# 设计约束 10：wrapper/nested JSON 只递归固定 key，避免任意 payload 被采信。
# 设计约束 11：缺 evidence_ref 不进入 ready，因为后续材料无法复账。
# 设计约束 12：weak same_evidence_ref_required 必须复跑，不能降级为人工通过。
# 设计约束 13：source brief blocked 时保持 blocked，不升级为受控现场复跑。
# 设计约束 14：required_evidence_packet 固定八类，新增材料必须另开契约评审。
# 设计约束 15：rerun_commands 是 PC operator 提示，不触发 ROS 或机器人动作。
# 设计约束 16：输出递归脱敏，blocked artifact 也不能泄漏 raw source。
# 设计约束 17：dependency-free，便于 macOS PC 和 Docker 本地验证。
# 设计约束 18：exit code 保持 0，让 blocked decision 也能作为证据落盘。
# 设计约束 19：Robot diagnostics 和 mobile panel 只能消费 summary/safe_copy。
# 设计约束 20：本 gate 不推进 Objective 5 external proof。
# 设计约束 21：本 gate 不替代真实 route/elevator field review。
# 设计约束 22：本 gate 不访问 fixed-route runtime、task record 或 delivery result。
# 设计约束 23：ready 只代表进入受控现场复跑前的材料审查口径已统一。
# 设计约束 24：needs backfill 只要求补齐缺失 packet metadata。
# 设计约束 25：needs owner handoff 只要求补交接字段，不授权现场动作。
# 设计约束 26：unsupported 和 bad JSON 统一引导重生 supported brief。
# 设计约束 27：safe_copy schema 带 `.safe_copy` 后缀，方便下游识别白名单面。
# 设计约束 28：boundary 与 evidence_boundary 同值，兼容旧消费者。
# 设计约束 29：safe_evidence_ref 与 evidence_ref 同值，兼容 Robot/mobile 命名。
# 设计约束 30：status 与 review_decision 同值，便于 rg 和 diagnostics 检索。
# 设计约束 31：material_status 不从真实文件推导，只从 source packet status 推导。
# 设计约束 32：next_required_evidence 只列材料类别，不包含本机路径。
# 设计约束 33：source_acceptance_brief 只保留 schema/boundary/status/ref 摘要。
# 设计约束 34：source unsafe/success 布尔保留定位，不回显命中文案。
# 设计约束 35：delivery_success 固定 false，不能被 source 覆盖。
# 设计约束 36：primary_actions_enabled 固定 false，不能被 source 覆盖。
# 设计约束 37：本文件作为 Autonomy 范围交付，不修改 Robot 或 Full-stack 文件。


def _utc_now() -> str:
    # UTC 时间便于 Docker-only artifact 跨机器按时间线审计。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON 和非 object 都转成 blocked artifact，保持证据留痕。
    if not path:
        return {}, "acceptance_brief_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "acceptance_brief_json_missing"
    except json.JSONDecodeError:
        return {}, "acceptance_brief_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "acceptance_brief_json_read_error"
    if not isinstance(payload, dict):
        return {}, "acceptance_brief_json_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object 嵌套字段，字符串 wrapper 不能伪装可信 JSON。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 wrapper 的字段位置不同，取首个非空值。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # 下游只需要短清单；限长能避免复制完整上游 artifact。
    if isinstance(value, list):
        return [brief.pack._safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [brief.pack._safe_text(value)]


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 key，避免把任意 raw payload 当成 acceptance brief。
    candidates = [payload]
    for key in (
        "route_task_field_retest_acceptance_review_decision",
        "route_task_field_retest_acceptance_review_decision_summary",
        "route_task_field_retest_acceptance_brief",
        "route_task_field_retest_acceptance_brief_summary",
        "acceptance_brief",
        "acceptance_brief_summary",
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
    # 优先消费 schema 命中的嵌套对象；没有命中时保留顶层解释 unsupported。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _source_status(load_issue: str, source: dict[str, Any]) -> dict[str, str]:
    # schema 与 boundary 必须同时支持，防止跨 gate JSON 混入 review。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = brief.pack._safe_text(source.get("schema", ""))
    boundary = brief.pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))
    if schema in SOURCE_SCHEMAS and boundary == SOURCE_BOUNDARY:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_evidence_ref(source: dict[str, Any]) -> str:
    # same evidence_ref 是 acceptance brief 与 review decision 串联主键。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "acceptance_brief_summary")
    return brief.pack._safe_ref(
        _first_text(
            source.get("evidence_ref"),
            source.get("safe_evidence_ref"),
            summary.get("evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 弱类型字符串必须 fail closed；这里要求 JSON boolean true。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "acceptance_brief_summary")
    return source.get(
        "same_evidence_ref_required",
        summary.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True)),
    )


def _source_acceptance_status(source: dict[str, Any]) -> str:
    # 只消费上游 brief 状态，不推断真实路线或电梯结果。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "acceptance_brief_summary")
    return brief.pack._safe_text(
        _first_text(
            source.get("acceptance_status"),
            source.get("status"),
            summary.get("acceptance_status"),
            summary.get("status"),
            safe_copy.get("acceptance_status"),
            safe_copy.get("status"),
            default="missing",
        )
    )


def _missing_packet(source: dict[str, Any]) -> list[str]:
    # packet status 来自上游摘要；本 gate 不打开真实材料文件。
    missing: list[str] = []
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "acceptance_brief_summary")
    raw_missing = (
        source.get("missing_evidence_packet")
        or source.get("missing_materials")
        or summary.get("missing_evidence_packet")
        or summary.get("missing_materials")
        or safe_copy.get("missing_evidence_packet")
    )
    for item in _safe_list(raw_missing, limit=len(REQUIRED_EVIDENCE_PACKET)):
        if item in REQUIRED_EVIDENCE_PACKET and item not in missing:
            missing.append(item)
    for item in source.get("required_evidence_packet", summary.get("required_evidence_packet", [])):
        if not isinstance(item, dict):
            continue
        name = brief.pack._safe_text(item.get("name", ""))
        status = brief.pack._safe_text(item.get("current_status", ""))
        if name in REQUIRED_EVIDENCE_PACKET and "missing" in status and name not in missing:
            missing.append(name)
    return missing


def _owner_handoff_present(source: dict[str, Any]) -> bool:
    # owner handoff 必须有可消费字段，Robot/mobile 才能安全展示下一步。
    handoff = source.get("owner_handoff") or _dict(source, "acceptance_brief_summary").get("owner_handoff")
    if not isinstance(handoff, dict) or not handoff:
        return False
    required_keys = {"autonomy_owner", "robot_owner", "full_stack_owner", "product_owner"}
    return bool(required_keys.intersection(handoff.keys()))


def _unsafe_source(source: dict[str, Any]) -> bool:
    # 复用 brief 的禁词/路径/成功文案扫描，危险输入不能被清洗成 ready。
    return brief._unsafe_copy(source)


def _review_decision(
    load_issue: str,
    source_status: dict[str, str],
    source_ref: str,
    requested_ref: str,
    same_ref_required: Any,
    unsafe: bool,
    acceptance_status: str,
    missing_packet: list[str],
    owner_handoff_present: bool,
) -> str:
    # fail-closed 顺序固定，危险输入和主键不一致不会被普通缺项遮住。
    if unsafe:
        return "rejected_unsafe_acceptance_brief_claim_not_proven"
    if load_issue or source_status["schema_status"] != "supported":
        return "unsupported_acceptance_brief_schema_not_proven"
    if not source_ref or (requested_ref and source_ref != requested_ref) or same_ref_required is not True:
        return "evidence_ref_mismatch_rerun_not_proven"
    if acceptance_status != "ready_for_field_retest_acceptance_brief_not_proven":
        return "blocked_acceptance_brief_not_ready"
    if missing_packet:
        return "needs_route_elevator_material_backfill_not_proven"
    if not owner_handoff_present:
        return "needs_owner_handoff_not_proven"
    return "ready_for_controlled_field_retest_not_proven"


def _material_status(decision: str, missing_packet: list[str]) -> str:
    # material_status 给 Robot/mobile 展示材料动作，不表达真实材料有效性。
    if decision == "ready_for_controlled_field_retest_not_proven":
        return "acceptance_packet_reviewed_for_controlled_retest_not_proven"
    if decision == "needs_route_elevator_material_backfill_not_proven" or missing_packet:
        return "missing_route_elevator_packet_metadata_not_proven"
    if decision == "needs_owner_handoff_not_proven":
        return "owner_handoff_metadata_missing_not_proven"
    if decision == "evidence_ref_mismatch_rerun_not_proven":
        return "same_evidence_ref_rerun_required_not_proven"
    if decision == "unsupported_acceptance_brief_schema_not_proven":
        return "supported_acceptance_brief_required_not_proven"
    if decision == "rejected_unsafe_acceptance_brief_claim_not_proven":
        return "unsafe_acceptance_brief_rejected_not_proven"
    return "acceptance_brief_not_ready_not_proven"


def _next_required_evidence(decision: str, missing_packet: list[str], evidence_ref: str) -> list[str]:
    # next evidence 只列材料类别和元数据动作，不包含本机路径或 raw artifact。
    ref = evidence_ref or "<same_evidence_ref>"
    if decision == "ready_for_controlled_field_retest_not_proven":
        return [
            f"Keep evidence_ref={ref} unchanged during the controlled field retest.",
            "Collect sanitized summaries for every required packet item before result intake.",
            "Record blocked reason instead of success wording when any packet item is unavailable.",
        ]
    if decision == "needs_route_elevator_material_backfill_not_proven":
        return [f"Backfill missing packet metadata: {', '.join(missing_packet)}."]
    if decision == "needs_owner_handoff_not_proven":
        return ["Regenerate acceptance brief with Autonomy, Robot, Full-stack, and Product owner handoff metadata."]
    if decision == "evidence_ref_mismatch_rerun_not_proven":
        return [f"Rerun acceptance brief and review decision with one safe evidence_ref={ref}."]
    if decision == "rejected_unsafe_acceptance_brief_claim_not_proven":
        return ["Remove unsafe copy, success wording, raw paths, credentials, topics, serial/UART, or control claims."]
    return ["Regenerate a supported route_task_field_retest_acceptance_brief artifact or summary."]


def _owner_handoff(decision: str, evidence_ref: str) -> dict[str, Any]:
    # handoff 只交接只读职责，不授权真实路线、投放或取消动作。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "autonomy_owner": f"Review decision={decision} and keep route/elevator packet metadata on evidence_ref={ref}.",
        "robot_owner": "Consume summary/safe_copy only; keep collect/dropoff/cancel/ACK disabled.",
        "full_stack_owner": "Render review decision as read-only metadata without raw JSON export.",
        "product_owner": "Close this rung as software_proof only unless real field materials are attached.",
        "handoff_checks": [
            "same_evidence_ref_required remains true.",
            "delivery_success=false remains visible.",
            "primary_actions_enabled=false remains visible.",
        ],
    }


def _rerun_commands(decision: str, evidence_ref: str) -> list[str]:
    # commands 是人工复跑提示，不由本 gate 自动执行，也不触发机器人控制。
    ref = evidence_ref or "<same_evidence_ref>"
    commands = [
        "python3 pc-tools/evidence/route_task_field_retest_acceptance_brief.py "
        "--drill-console-json <drill_console_summary.json> "
        f"--evidence-ref {ref} --output <acceptance_brief.json> "
        "--summary-output <acceptance_brief_summary.json>",
        "python3 pc-tools/evidence/route_task_field_retest_acceptance_review_decision.py "
        "--acceptance-brief-json <acceptance_brief_summary.json> "
        f"--evidence-ref {ref} --output <acceptance_review_decision.json> "
        "--summary-output <acceptance_review_decision_summary.json>",
    ]
    if decision == "needs_route_elevator_material_backfill_not_proven":
        commands.append("Backfill the missing route/elevator packet metadata before field-entry review.")
    return [brief.pack._safe_text(command) for command in commands]


def _safe_copy(decision: str, evidence_ref: str, material_status: str, missing_packet: list[str]) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不包含 raw artifact 或本机路径。
    return {
        "schema": f"{DECISION_SUMMARY_SCHEMA}.safe_copy",
        "review_decision": decision,
        "status": decision,
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "evidence_ref": evidence_ref,
        "safe_evidence_ref": evidence_ref,
        "material_status": material_status,
        "missing_evidence_packet": list(missing_packet),
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    decision: str,
    evidence_ref: str,
    source_acceptance_status: str,
    source_status: dict[str, str],
    material_status: str,
    missing_packet: list[str],
    next_required_evidence: list[str],
    owner_handoff: dict[str, Any],
    rerun_commands: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是下游消费首选字段集，必须稳定且 phone-safe。
    return {
        "schema": DECISION_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": decision,
        "review_decision": decision,
        "source_acceptance_status": source_acceptance_status,
        "source_schema_status": source_status["schema_status"],
        "evidence_ref": evidence_ref,
        "safe_evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "material_status": material_status,
        "missing_evidence_packet": list(missing_packet),
        "required_evidence_packet": list(REQUIRED_EVIDENCE_PACKET),
        "next_required_evidence": next_required_evidence,
        "owner_handoff": owner_handoff,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def build_route_task_field_retest_acceptance_review_decision(
    acceptance_brief_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    # 主构建函数保持 CLI/unittest 共用，便于离线验证同一逻辑。
    payload, load_issue = _load_json(acceptance_brief_json)
    source = _find_source(payload) if payload else {}
    source_status = _source_status(load_issue, source)
    requested_ref = brief.pack._safe_ref(evidence_ref)
    source_ref = _source_evidence_ref(source)
    resolved_ref = requested_ref or source_ref
    same_ref_required = _same_ref_required(source)
    acceptance_status = _source_acceptance_status(source)
    missing_packet = _missing_packet(source)
    unsafe = _unsafe_source(source)
    owner_present = _owner_handoff_present(source)
    decision = _review_decision(
        load_issue,
        source_status,
        source_ref,
        requested_ref,
        same_ref_required,
        unsafe,
        acceptance_status,
        missing_packet,
        owner_present,
    )
    material_status = _material_status(decision, missing_packet)
    next_required_evidence = _next_required_evidence(decision, missing_packet, resolved_ref)
    owner_handoff = _owner_handoff(decision, resolved_ref)
    rerun_commands = _rerun_commands(decision, resolved_ref)
    safe_copy = _safe_copy(decision, resolved_ref, material_status, missing_packet)
    summary = _summary_payload(
        decision,
        resolved_ref,
        acceptance_status,
        source_status,
        material_status,
        missing_packet,
        next_required_evidence,
        owner_handoff,
        rerun_commands,
        safe_copy,
    )
    artifact = {
        "schema": DECISION_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": decision,
        "review_decision": decision,
        "source_acceptance_brief": {
            "schema": brief.pack._safe_text(source.get("schema", "")),
            "evidence_boundary": brief.pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
            "load_status": source_status["load_status"],
            "schema_status": source_status["schema_status"],
            "acceptance_status": acceptance_status,
            "unsafe_source": unsafe,
        },
        "same_evidence_ref_required": True,
        "evidence_ref": resolved_ref,
        "safe_evidence_ref": resolved_ref,
        "material_status": material_status,
        "missing_evidence_packet": list(missing_packet),
        "required_evidence_packet": list(REQUIRED_EVIDENCE_PACKET),
        "next_required_evidence": next_required_evidence,
        "owner_handoff": owner_handoff,
        "rerun_commands": rerun_commands,
        "route_task_field_retest_acceptance_review_decision_summary": summary,
        "safe_copy": safe_copy,
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
        "primary_actions_enabled": False,
        "delivery_success": False,
    }
    artifact = brief.pack._safe_value(artifact)
    summary = brief.pack._safe_value(summary)
    if _unsafe_source(summary):
        # 最终防线：summary 不安全时只保留 blocked 状态和安全边界字段。
        summary["status"] = "rejected_unsafe_acceptance_brief_claim_not_proven"
        summary["review_decision"] = "rejected_unsafe_acceptance_brief_claim_not_proven"
        artifact["status"] = "rejected_unsafe_acceptance_brief_claim_not_proven"
        artifact["review_decision"] = "rejected_unsafe_acceptance_brief_claim_not_proven"
        artifact["route_task_field_retest_acceptance_review_decision_summary"] = summary
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时创建父目录；不指定时由 --once-json/stdout 展示 artifact。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 不接触运行时系统，只把 acceptance brief JSON 转成 review decision。
    parser = argparse.ArgumentParser(description="Build route/task field retest acceptance review decision artifact")
    parser.add_argument("--acceptance-brief-json", required=True, help="acceptance brief artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for the acceptance review decision")
    parser.add_argument("--output", default="", help="optional acceptance review decision artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional acceptance review decision summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print acceptance review decision artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_acceptance_review_decision(
        args.acceptance_brief_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_acceptance_review_decision: artifact_file:{brief.pack._safe_ref(args.output)}")
        print(f"review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
