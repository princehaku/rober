"""Task terminal diagnostics summary helpers.

本模块只承接 operator_gateway_diagnostics 的 task terminal 只读摘要逻辑。
它不能把终态材料、现场材料入口或复核决策升级成真实投放完成、取消完成、
Nav2/HIL 证明或机器人可控状态。
"""

TASK_TERMINAL_COMPLETION_MAINLINE_SCHEMA = "trashbot.task_terminal_completion_mainline.v1"
TASK_TERMINAL_COMPLETION_MAINLINE_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_task_terminal_completion_mainline_summary.v1"
)
TASK_TERMINAL_COMPLETION_MAINLINE_GATE = (
    "software_proof_docker_task_terminal_completion_mainline_gate"
)
TASK_TERMINAL_FIELD_MATERIAL_INTAKE_SCHEMA = (
    "trashbot.task_terminal_field_material_intake.v1"
)
TASK_TERMINAL_FIELD_MATERIAL_INTAKE_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.task_terminal_field_material_intake_summary.v1"
)
TASK_TERMINAL_FIELD_MATERIAL_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_task_terminal_field_material_intake_summary.v1"
)
TASK_TERMINAL_FIELD_MATERIAL_INTAKE_GATE = (
    "software_proof_docker_task_terminal_field_material_intake_gate"
)
TASK_TERMINAL_FIELD_MATERIAL_REVIEW_DECISION_SCHEMA = (
    "trashbot.task_terminal_field_material_review_decision.v1"
)
TASK_TERMINAL_FIELD_MATERIAL_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.task_terminal_field_material_review_decision_summary.v1"
)
TASK_TERMINAL_FIELD_MATERIAL_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_task_terminal_field_material_review_decision_summary.v1"
)
TASK_TERMINAL_FIELD_MATERIAL_REVIEW_DECISION_GATE = (
    "software_proof_docker_task_terminal_field_material_review_decision_gate"
)


def _diagnostics():
    # 延迟读取 facade helper，避免 public 兼容层导入本模块时形成初始化环。
    from ros2_trashbot_behavior import operator_gateway_diagnostics

    return operator_gateway_diagnostics


def _task_terminal_completion_mainline_not_proven(source=None, summary=None):
    # mainline 只解释 dropoff/cancel 终态缺口，不能把 task_record 或 diagnostics 当成真实完成材料。
    source = source if isinstance(source, dict) else {}
    summary = summary if isinstance(summary, dict) else {}
    values = []
    source_values = []
    if isinstance(source.get("not_proven"), list):
        source_values.extend(source.get("not_proven"))
    if isinstance(summary.get("not_proven"), list):
        source_values.extend(summary.get("not_proven"))
    required = (
        "real_task_record",
        "real_dropoff_completion_material",
        "real_cancel_completion_material",
        "same_evidence_ref_field_replay",
        "real_nav2_fixed_route_run",
        "real_route_elevator_field_pass",
        "real_phone_device_or_browser",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "objective_5_external_proof",
        "delivery_success",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _task_terminal_field_material_intake_not_proven(source=None, summary=None):
    # 现场材料入口只列出下一步缺口；不能把 accepted refs 当成现场通过或控制授权。
    source = source if isinstance(source, dict) else {}
    summary = summary if isinstance(summary, dict) else {}
    values = []
    source_values = []
    if isinstance(source.get("not_proven"), list):
        source_values.extend(source.get("not_proven"))
    if isinstance(summary.get("not_proven"), list):
        source_values.extend(summary.get("not_proven"))
    required = (
        "real_task_record",
        "real_dropoff_or_cancel_terminal_material",
        "real_route_elevator_field_material",
        "real_phone_browser_evidence",
        "real_nav2_fixed_route_run",
        "real_route_elevator_field_pass",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "objective_5_external_proof",
        "delivery_success",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _task_terminal_field_material_review_decision_not_proven(source=None, summary=None):
    # 复核决策只说明材料审核状态；accepted metadata 仍不能升级成现场通过或 HIL 证据。
    source = source if isinstance(source, dict) else {}
    summary = summary if isinstance(summary, dict) else {}
    values = []
    source_values = []
    if isinstance(source.get("not_proven"), list):
        source_values.extend(source.get("not_proven"))
    if isinstance(summary.get("not_proven"), list):
        source_values.extend(summary.get("not_proven"))
    required = (
        "real_task_record",
        "real_dropoff_or_cancel_terminal_material",
        "real_route_elevator_field_material",
        "real_phone_browser_evidence",
        "real_nav2_fixed_route_run",
        "real_route_elevator_field_pass",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "objective_5_external_proof",
        "delivery_success",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _default_task_terminal_completion_mainline_summary(
    status="blocked_missing_task_terminal_completion_mainline",
    read_error="",
):
    # 缺少 task_record/mainline 时默认 blocked，避免 mobile 把空摘要当成可操作终态。
    return {
        "schema": TASK_TERMINAL_COMPLETION_MAINLINE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "source_schema": "",
        "source_evidence_boundary": "",
        "evidence_boundary": TASK_TERMINAL_COMPLETION_MAINLINE_GATE,
        "status": status,
        "source": "software_proof",
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "terminal_action": "",
        "terminal_status": "missing_materials",
        "operator_confirmation_required": True,
        "operator_confirmation_status": "missing",
        "dropoff_completion_proven": False,
        "cancel_completion_proven": False,
        "failure_reason": read_error or "task terminal completion mainline source is not configured",
        "missing_required_materials": [
            "real_task_record",
            "real_dropoff_or_cancel_completion_material",
            "same_evidence_ref_field_replay",
        ],
        "next_required_evidence": [
            "真实 task record",
            "真实 dropoff/cancel completion 材料",
            "同一 evidence_ref 的现场复账",
        ],
        "evidence_boundary_flags": [
            "software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
        ],
        "phone_safe_summary": {
            "safe_copy": "Task terminal completion mainline is not configured; delivery_success=false; primary_actions_enabled=false.",
            "safe_phone_copy": "任务终态主链路未配置；delivery_success=false；primary_actions_enabled=false。",
        },
        "not_proven": _task_terminal_completion_mainline_not_proven(),
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
    }


def _default_task_terminal_field_material_intake_summary(
    status="blocked_missing_task_terminal_field_material_intake",
    read_error="",
):
    # 缺少现场材料入口时仍输出完整 false 栅栏，方便 Robot/mobile 只读展示且不能触发控制。
    return {
        "schema": TASK_TERMINAL_FIELD_MATERIAL_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "source_schema": "",
        "source_evidence_boundary": "",
        "evidence_boundary": TASK_TERMINAL_FIELD_MATERIAL_INTAKE_GATE,
        "status": status,
        "source": "software_proof",
        "safe_evidence_ref": "",
        "accepted_safe_refs": [],
        "missing_materials": [
            "real_task_record",
            "real_dropoff_or_cancel_terminal_material",
            "real_route_elevator_field_material",
            "real_phone_browser_evidence",
        ],
        "next_required_evidence": [
            "同一 safe evidence_ref 的真实 task record",
            "真实 dropoff/cancel terminal materials",
            "真实 route/elevator field materials",
            "真实手机/browser evidence",
        ],
        "phone_safe_copy": (
            "现场材料尚未回填，当前只能查看缺口和下一步证据要求；"
            "software_proof；not_proven；delivery_success=false；"
            "primary_actions_enabled=false；safe_to_control=false。"
        ),
        "phone_safe_summary": {
            "safe_copy": "Task terminal field material intake is not configured; delivery_success=false; primary_actions_enabled=false; safe_to_control=false.",
            "safe_phone_copy": "现场材料回填入口未配置；delivery_success=false；primary_actions_enabled=false；safe_to_control=false。",
        },
        "evidence_boundary_flags": [
            "software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
        ],
        "not_proven": _task_terminal_field_material_intake_not_proven(),
        "failure_reason": read_error or "task terminal field material intake source is not configured",
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "remote_ack_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_task_terminal_field_material_review_decision_summary(
    status="blocked_missing_task_terminal_field_material_review_decision",
    read_error="",
):
    # 缺少复核决策时也返回完整只读摘要，避免消费者转读 raw artifact 或猜测现场通过。
    return {
        "schema": TASK_TERMINAL_FIELD_MATERIAL_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "source_schema": "",
        "source_evidence_boundary": "",
        "evidence_boundary": TASK_TERMINAL_FIELD_MATERIAL_REVIEW_DECISION_GATE,
        "status": status,
        "source": "software_proof",
        "review_decision": "blocked_missing_or_unsupported_intake_not_proven",
        "safe_evidence_ref": "",
        "accepted_materials": [],
        "missing_materials": [
            "real_task_record",
            "real_dropoff_or_cancel_terminal_material",
            "real_route_elevator_field_material",
            "real_phone_browser_evidence",
        ],
        "rejected_materials": [],
        "blocked_materials": [
            "missing_task_terminal_field_material_review_decision",
        ],
        "owner_handoff": [
            "现场 owner 补齐同一 safe evidence_ref 下的真实 task record 和 terminal materials",
            "Autonomy 复核 route/elevator/Nav2 runtime log 和 route completion signal",
            "Full-Stack 复核真实手机/browser evidence",
        ],
        "next_required_evidence": [
            "同一 safe evidence_ref 的真实 task record",
            "真实 dropoff/cancel terminal materials",
            "真实 Nav2/fixed-route runtime log",
            "真实 route completion signal",
            "真实电梯门状态、目标楼层确认和人工协助记录",
            "真实手机/browser evidence",
        ],
        "rerun_guidance": [
            "补齐缺失材料后重新运行 task_terminal_field_material_intake",
            "保持同一 safe evidence_ref 后再运行 task_terminal_field_material_review_decision",
        ],
        "phone_safe_copy": (
            "现场材料复核决策缺失；当前只能查看下一步证据要求，不能控制机器人；"
            "software_proof；not_proven；delivery_success=false；"
            "primary_actions_enabled=false；safe_to_control=false。"
        ),
        "phone_safe_summary": {
            "safe_copy": "Task terminal field material review decision is missing; software_proof; not_proven; delivery_success=false; primary_actions_enabled=false; safe_to_control=false.",
            "safe_phone_copy": "现场材料复核决策缺失；delivery_success=false；primary_actions_enabled=false；safe_to_control=false。",
        },
        "evidence_boundary_flags": [
            "software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
        ],
        "not_proven": _task_terminal_field_material_review_decision_not_proven(),
        "failure_reason": read_error or "task terminal field material review decision payload is not configured",
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "remote_ack_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _task_terminal_completion_mainline_refs_match(source, summary):
    # 同一 evidence_ref 约束只看安全字段，不能展开真实 task_record 或现场 artifact。
    d = _diagnostics()
    refs = []
    for value in (
        source.get("safe_evidence_ref"),
        source.get("evidence_ref"),
        summary.get("safe_evidence_ref"),
        summary.get("evidence_ref"),
    ):
        safe_ref = d._safe_route_task_rehearsal_ref(value)
        if safe_ref and safe_ref not in refs:
            refs.append(safe_ref)
    route_progress = summary.get("route_progress")
    if isinstance(route_progress, dict):
        safe_ref = d._safe_route_task_rehearsal_ref(route_progress.get("evidence_ref"))
        if safe_ref and safe_ref not in refs:
            refs.append(safe_ref)
    return len(refs) <= 1


def _task_terminal_completion_mainline_source_from_payloads(*payloads):
    # 只从已净化的 status/diagnostics/task_record 字段取 mainline，不扫描 raw artifact。
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        for key in (
            "task_terminal_completion_mainline",
            "task_terminal_completion_mainline_summary",
            "robot_diagnostics_task_terminal_completion_mainline_summary",
        ):
            candidate = payload.get(key)
            if isinstance(candidate, dict):
                return candidate
    return {}


def _task_terminal_field_material_intake_source_from_payloads(*payloads):
    # 只消费已净化的 terminal/material-intake 摘要，避免 diagnostics 主链路展开 raw artifact。
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        for key in (
            "task_terminal_field_material_intake",
            "task_terminal_field_material_intake_summary",
            "robot_diagnostics_task_terminal_field_material_intake_summary",
        ):
            candidate = payload.get(key)
            if isinstance(candidate, dict):
                return candidate
    return {}


def _task_terminal_field_material_review_decision_source_from_payloads(*payloads):
    # 复核决策只从已净化 payload 取值；不扫描路径或完整 artifact，避免泄露现场 raw 材料。
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        for key in (
            "task_terminal_field_material_review_decision",
            "task_terminal_field_material_review_decision_summary",
            "robot_diagnostics_task_terminal_field_material_review_decision_summary",
        ):
            candidate = payload.get(key)
            if isinstance(candidate, dict):
                return candidate
    return {}


def summarize_task_terminal_completion_mainline(source=None):
    # diagnostics 对 mainline 做二次白名单化，保证它仍是只读解释层。
    d = _diagnostics()
    source = source if isinstance(source, dict) else {}
    summary = _default_task_terminal_completion_mainline_summary()
    source_summary = source
    for key in (
        "task_terminal_completion_mainline",
        "task_terminal_completion_mainline_summary",
        "robot_diagnostics_task_terminal_completion_mainline_summary",
        "summary",
    ):
        candidate = source.get(key)
        if isinstance(candidate, dict):
            source_summary = candidate
            break
    source_schema = str(source_summary.get("schema") or source.get("schema") or "")
    source_boundary = str(
        source_summary.get("evidence_boundary")
        or source_summary.get("source_evidence_boundary")
        or source.get("evidence_boundary")
        or ""
    )
    phone_summary = (
        source_summary.get("phone_safe_summary")
        if isinstance(source_summary.get("phone_safe_summary"), dict)
        else {}
    )
    safe_copy = d._redact_route_task_rehearsal_text(
        phone_summary.get("safe_copy")
        or phone_summary.get("safe_phone_copy")
        or "Task terminal completion mainline is software_proof/not_proven; delivery_success=false; primary_actions_enabled=false."
    )
    summary.update(
        {
            "source_schema": d._redact_route_task_rehearsal_text(source_schema),
            "source_evidence_boundary": d._redact_route_task_rehearsal_text(source_boundary),
            "status": d._redact_route_task_rehearsal_text(
                source_summary.get("status") or "blocked_not_proven"
            ),
            "source": "software_proof",
            "safe_evidence_ref": d._safe_route_task_rehearsal_ref(
                source_summary.get("safe_evidence_ref")
                or source_summary.get("evidence_ref")
                or source.get("evidence_ref")
            ),
            "same_evidence_ref_required": bool(source_summary.get("same_evidence_ref_required", True)),
            "terminal_action": d._redact_route_task_rehearsal_text(source_summary.get("terminal_action")),
            "terminal_status": d._redact_route_task_rehearsal_text(
                source_summary.get("terminal_status") or "missing_materials"
            ),
            "operator_confirmation_required": bool(
                source_summary.get("operator_confirmation_required", True)
            ),
            "operator_confirmation_status": d._redact_route_task_rehearsal_text(
                source_summary.get("operator_confirmation_status") or "missing"
            ),
            "dropoff_completion_proven": False,
            "cancel_completion_proven": False,
            "failure_reason": d._redact_route_task_rehearsal_text(
                source_summary.get("failure_reason")
            ),
            "missing_required_materials": d._safe_route_task_rehearsal_list(
                source_summary.get("missing_required_materials")
            ),
            "next_required_evidence": d._safe_route_task_rehearsal_list(
                source_summary.get("next_required_evidence")
            ),
            "evidence_boundary_flags": d._safe_route_task_rehearsal_list(
                source_summary.get("evidence_boundary_flags")
            )
            or [
                "software_proof",
                "not_proven",
                "delivery_success=false",
                "primary_actions_enabled=false",
            ],
            "route_progress": d._safe_pc_route_debug_dict(source_summary.get("route_progress"))
            or {"present": False, "evidence_ref": ""},
            "phone_safe_summary": {
                "safe_copy": safe_copy,
                "safe_phone_copy": safe_copy,
            },
            "not_proven": _task_terminal_completion_mainline_not_proven(source, source_summary),
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "collect_triggered": False,
            "dropoff_triggered": False,
            "cancel_triggered": False,
            "ack_post_allowed": False,
            "cursor_updates_allowed": False,
            "terminal_ack_allowed": False,
            "nav2_triggered": False,
            "hil_pass": False,
        }
    )
    if source_schema not in (
        TASK_TERMINAL_COMPLETION_MAINLINE_SCHEMA,
        TASK_TERMINAL_COMPLETION_MAINLINE_SUMMARY_SCHEMA,
    ) or source_boundary != TASK_TERMINAL_COMPLETION_MAINLINE_GATE:
        summary.update(
            {
                "status": "unsupported_schema",
                "failure_reason": "task terminal completion mainline schema or evidence boundary is unsupported",
            }
        )
        return summary
    if not _task_terminal_completion_mainline_refs_match(source, source_summary):
        summary.update(
            {
                "status": "evidence_ref_mismatch",
                "failure_reason": "task terminal completion mainline evidence_ref values do not match",
            }
        )
        return summary
    if (
        d._route_task_field_run_readiness_has_unsafe_fields(source_summary)
        or d._route_task_completion_signal_has_unsafe_control_claims(source)
        or d._route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or bool(source_summary.get("delivery_success"))
        or bool(source_summary.get("primary_actions_enabled"))
    ):
        summary.update(
            {
                "status": "unsafe_fields",
                "failure_reason": "task terminal completion mainline contains unsafe success or control fields",
            }
        )
        return summary
    return summary


def summarize_task_terminal_field_material_intake(source=None):
    # Robot alias 只把现场材料入口转成安全摘要；任何控制、成功或 raw 材料都 fail closed。
    d = _diagnostics()
    source = source if isinstance(source, dict) else {}
    summary = _default_task_terminal_field_material_intake_summary()
    if not source:
        return summary
    source_summary = source
    for key in (
        "task_terminal_field_material_intake",
        "task_terminal_field_material_intake_summary",
        "robot_diagnostics_task_terminal_field_material_intake_summary",
        "summary",
    ):
        candidate = source.get(key)
        if isinstance(candidate, dict):
            source_summary = candidate
            break
    source_schema = str(source_summary.get("schema") or source.get("schema") or "")
    source_boundary = str(
        source_summary.get("evidence_boundary")
        or source_summary.get("source_evidence_boundary")
        or source.get("evidence_boundary")
        or ""
    )
    phone_summary = (
        source_summary.get("phone_safe_summary")
        if isinstance(source_summary.get("phone_safe_summary"), dict)
        else source_summary.get("robot_diagnostics_summary")
        if isinstance(source_summary.get("robot_diagnostics_summary"), dict)
        else {}
    )
    safe_copy = d._redact_route_task_rehearsal_text(
        source_summary.get("phone_safe_copy")
        or phone_summary.get("safe_copy")
        or phone_summary.get("safe_phone_copy")
        or "Task terminal field material intake is software_proof/not_proven; delivery_success=false; primary_actions_enabled=false; safe_to_control=false."
    )
    safe_evidence_ref = d._safe_route_task_rehearsal_ref(
        source_summary.get("safe_evidence_ref")
        or source_summary.get("evidence_ref")
        or source.get("safe_evidence_ref")
        or source.get("evidence_ref")
    )
    accepted_safe_refs = d._dedupe_ordered(
        d._safe_route_task_rehearsal_list(source_summary.get("accepted_safe_refs"))
    )
    summary.update(
        {
            "source_schema": d._redact_route_task_rehearsal_text(source_schema),
            "source_evidence_boundary": d._redact_route_task_rehearsal_text(source_boundary),
            "status": d._redact_route_task_rehearsal_text(
                source_summary.get("status") or "blocked_missing_field_materials"
            ),
            "source": "software_proof",
            "safe_evidence_ref": safe_evidence_ref,
            "accepted_safe_refs": accepted_safe_refs,
            "missing_materials": d._dedupe_ordered(
                d._safe_route_task_rehearsal_list(source_summary.get("missing_materials"))
            )
            or summary["missing_materials"],
            "next_required_evidence": d._safe_route_task_rehearsal_list(
                source_summary.get("next_required_evidence")
            )
            or summary["next_required_evidence"],
            "phone_safe_copy": safe_copy,
            "phone_safe_summary": {
                "safe_copy": safe_copy,
                "safe_phone_copy": safe_copy,
            },
            "evidence_boundary_flags": d._safe_route_task_rehearsal_list(
                source_summary.get("evidence_boundary")
                if isinstance(source_summary.get("evidence_boundary"), list)
                else source_summary.get("evidence_boundary_flags")
            )
            or [
                "software_proof",
                "not_proven",
                "delivery_success=false",
                "primary_actions_enabled=false",
                "safe_to_control=false",
            ],
            "not_proven": _task_terminal_field_material_intake_not_proven(
                source,
                source_summary,
            ),
            "failure_reason": d._redact_route_task_rehearsal_text(
                source_summary.get("failure_reason")
            ),
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
            "collect_triggered": False,
            "dropoff_triggered": False,
            "cancel_triggered": False,
            "ack_post_allowed": False,
            "remote_ack_allowed": False,
            "cursor_updates_allowed": False,
            "persistence_updates_allowed": False,
            "terminal_ack_allowed": False,
            "nav2_triggered": False,
            "hil_pass": False,
            "production_ready": False,
            "dropoff_completion": False,
            "cancel_completion": False,
        }
    )
    accepted_schemas = {
        TASK_TERMINAL_FIELD_MATERIAL_INTAKE_SCHEMA,
        TASK_TERMINAL_FIELD_MATERIAL_INTAKE_SOURCE_SUMMARY_SCHEMA,
        TASK_TERMINAL_FIELD_MATERIAL_INTAKE_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != TASK_TERMINAL_FIELD_MATERIAL_INTAKE_GATE:
        summary.update(
            {
                "status": "unsupported_schema",
                "failure_reason": "task terminal field material intake schema or evidence boundary is unsupported",
                "safe_evidence_ref": "",
                "accepted_safe_refs": [],
            }
        )
        return summary
    if (
        d._route_task_field_run_readiness_has_unsafe_fields(source)
        or d._route_task_field_run_readiness_has_unsafe_fields(source_summary)
        or d._route_task_completion_signal_has_unsafe_control_claims(source)
        or d._task_terminal_field_material_intake_copy_is_unsafe(safe_copy)
        or bool(source_summary.get("delivery_success"))
        or bool(source_summary.get("primary_actions_enabled"))
        or bool(source_summary.get("safe_to_control"))
        or bool(source_summary.get("control_grant"))
        or not safe_evidence_ref
        or safe_evidence_ref.startswith("local_path_redacted:")
    ):
        # 安全摘要宁可缺失，也不能把现场材料、ACK 或控制授权误传播到 Robot command 面。
        blocked_copy = (
            "Task terminal field material intake was blocked because the summary "
            "could expose raw material/control data or imply success; "
            "software_proof; not_proven; delivery_success=false; "
            "primary_actions_enabled=false; safe_to_control=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_task_terminal_field_material_intake_summary",
                "failure_reason": "task terminal field material intake contains unsafe fields, success wording, weak evidence_ref, or enabled actions",
                "safe_evidence_ref": "",
                "accepted_safe_refs": [],
                "phone_safe_copy": blocked_copy,
                "phone_safe_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary


def summarize_task_terminal_field_material_review_decision(source=None):
    # Robot alias 只暴露复核决策摘要；不能从 accepted 材料推导 field pass 或机器人可控状态。
    d = _diagnostics()
    source = source if isinstance(source, dict) else {}
    summary = _default_task_terminal_field_material_review_decision_summary()
    if not source:
        return summary
    source_summary = source
    for key in (
        "task_terminal_field_material_review_decision",
        "task_terminal_field_material_review_decision_summary",
        "robot_diagnostics_task_terminal_field_material_review_decision_summary",
        "summary",
    ):
        candidate = source.get(key)
        if isinstance(candidate, dict):
            source_summary = candidate
            break
    source_schema = str(source_summary.get("schema") or source.get("schema") or "")
    source_boundary = str(
        source_summary.get("evidence_boundary")
        or source_summary.get("source_evidence_boundary")
        or source.get("evidence_boundary")
        or ""
    )
    phone_summary = (
        source_summary.get("phone_safe_summary")
        if isinstance(source_summary.get("phone_safe_summary"), dict)
        else source_summary.get("robot_diagnostics_summary")
        if isinstance(source_summary.get("robot_diagnostics_summary"), dict)
        else {}
    )
    safe_copy = d._redact_route_task_rehearsal_text(
        source_summary.get("phone_safe_copy")
        or phone_summary.get("safe_copy")
        or phone_summary.get("safe_phone_copy")
        or "Task terminal field material review decision is software_proof/not_proven; delivery_success=false; primary_actions_enabled=false; safe_to_control=false."
    )
    safe_evidence_ref = d._safe_route_task_rehearsal_ref(
        source_summary.get("safe_evidence_ref")
        or source_summary.get("evidence_ref")
        or source.get("safe_evidence_ref")
        or source.get("evidence_ref")
    )
    summary.update(
        {
            "source_schema": d._redact_route_task_rehearsal_text(source_schema),
            "source_evidence_boundary": d._redact_route_task_rehearsal_text(source_boundary),
            "status": d._redact_route_task_rehearsal_text(
                source_summary.get("status") or "blocked_not_proven"
            ),
            "source": "software_proof",
            "review_decision": d._redact_route_task_rehearsal_text(
                source_summary.get("review_decision")
                or "blocked_missing_or_unsupported_intake_not_proven"
            ),
            "safe_evidence_ref": safe_evidence_ref,
            "accepted_materials": d._dedupe_ordered(
                d._safe_route_task_rehearsal_list(source_summary.get("accepted_materials"))
            ),
            "missing_materials": d._dedupe_ordered(
                d._safe_route_task_rehearsal_list(source_summary.get("missing_materials"))
            )
            or summary["missing_materials"],
            "rejected_materials": d._dedupe_ordered(
                d._safe_route_task_rehearsal_list(source_summary.get("rejected_materials"))
            ),
            "blocked_materials": d._dedupe_ordered(
                d._safe_route_task_rehearsal_list(source_summary.get("blocked_materials"))
            ),
            "owner_handoff": d._safe_route_task_rehearsal_list(
                source_summary.get("owner_handoff")
            )
            or summary["owner_handoff"],
            "next_required_evidence": d._safe_route_task_rehearsal_list(
                source_summary.get("next_required_evidence")
            )
            or summary["next_required_evidence"],
            "rerun_guidance": d._safe_route_task_rehearsal_list(
                source_summary.get("rerun_guidance")
            )
            or summary["rerun_guidance"],
            "phone_safe_copy": safe_copy,
            "phone_safe_summary": {
                "safe_copy": safe_copy,
                "safe_phone_copy": safe_copy,
            },
            "evidence_boundary_flags": d._safe_route_task_rehearsal_list(
                source_summary.get("evidence_boundary")
                if isinstance(source_summary.get("evidence_boundary"), list)
                else source_summary.get("evidence_boundary_flags")
            )
            or [
                "software_proof",
                "not_proven",
                "delivery_success=false",
                "primary_actions_enabled=false",
                "safe_to_control=false",
            ],
            "not_proven": _task_terminal_field_material_review_decision_not_proven(
                source,
                source_summary,
            ),
            "failure_reason": d._redact_route_task_rehearsal_text(
                source_summary.get("failure_reason")
            ),
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
            "collect_triggered": False,
            "dropoff_triggered": False,
            "cancel_triggered": False,
            "ack_post_allowed": False,
            "remote_ack_allowed": False,
            "cursor_updates_allowed": False,
            "persistence_updates_allowed": False,
            "terminal_ack_allowed": False,
            "nav2_triggered": False,
            "hil_pass": False,
            "production_ready": False,
            "dropoff_completion": False,
            "cancel_completion": False,
        }
    )
    accepted_schemas = {
        TASK_TERMINAL_FIELD_MATERIAL_REVIEW_DECISION_SCHEMA,
        TASK_TERMINAL_FIELD_MATERIAL_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        TASK_TERMINAL_FIELD_MATERIAL_REVIEW_DECISION_SUMMARY_SCHEMA,
    }
    if (
        source_schema not in accepted_schemas
        or source_boundary != TASK_TERMINAL_FIELD_MATERIAL_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "status": "unsupported_schema",
                "review_decision": "blocked_missing_or_unsupported_intake_not_proven",
                "failure_reason": "task terminal field material review decision schema or evidence boundary is unsupported",
                "safe_evidence_ref": "",
                "accepted_materials": [],
                "rejected_materials": [],
                "blocked_materials": ["unsupported_schema_or_evidence_boundary"],
            }
        )
        return summary
    if (
        d._route_task_field_run_readiness_has_unsafe_fields(source)
        or d._route_task_field_run_readiness_has_unsafe_fields(source_summary)
        or d._route_task_completion_signal_has_unsafe_control_claims(source)
        or d._task_terminal_field_material_intake_copy_is_unsafe(safe_copy)
        or bool(source_summary.get("delivery_success"))
        or bool(source_summary.get("primary_actions_enabled"))
        or bool(source_summary.get("safe_to_control"))
        or bool(source_summary.get("control_grant"))
        or not safe_evidence_ref
        or safe_evidence_ref.startswith("local_path_redacted:")
    ):
        # 任一 raw、路径、checksum、凭证、成功或控制暗示都直接降级，防止 Robot diagnostics 变成控制入口。
        blocked_copy = (
            "Task terminal field material review decision was blocked because "
            "the summary could expose raw material/control data or imply success; "
            "software_proof; not_proven; delivery_success=false; "
            "primary_actions_enabled=false; safe_to_control=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_task_terminal_field_material_review_decision_summary",
                "review_decision": "blocked_missing_or_unsupported_intake_not_proven",
                "failure_reason": "task terminal field material review decision contains unsafe fields, success wording, weak evidence_ref, or enabled actions",
                "safe_evidence_ref": "",
                "accepted_materials": [],
                "rejected_materials": [],
                "blocked_materials": ["unsafe_task_terminal_field_material_review_decision"],
                "phone_safe_copy": blocked_copy,
                "phone_safe_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary
