"""Route task terminal diagnostics summary helpers.

本模块只承接 operator_gateway_diagnostics 的 route task terminal completion
rehearsal 与 review decision 只读摘要逻辑。它不能把终态复账、复核决策
或 operator copy 升级成真实投放、取消完成、Nav2/HIL 证明或机器人可控状态。

边界说明：
- completion rehearsal 只表示终态材料进入了软件侧复账面。
- completion rehearsal 不能证明 dropoff 已完成。
- completion rehearsal 不能证明 cancel 已完成。
- completion rehearsal 不能触发 collect/dropoff/cancel 控制。
- completion rehearsal 不能触发 remote ACK。
- completion rehearsal 不能推进 cursor 或 persistence。
- completion rehearsal 不能发布 terminal ACK。
- completion rehearsal 不能替代真实 task record。
- completion rehearsal 不能替代真实 fixed-route run。
- completion rehearsal 不能替代真实 route collection。
- completion rehearsal 不能替代真实 route/elevator field pass。
- completion rehearsal 不能替代 WAVE ROVER motion 证据。
- completion rehearsal 不能替代 serial/UART feedback。
- completion rehearsal 不能替代 HIL pass。
- completion rehearsal 不能替代 Objective 5 external proof。
- completion rehearsal 的 evidence_ref 必须保持同一复账链路。
- completion rehearsal 的 route_progress 只作为安全摘要展示。
- completion rehearsal 的 dropoff_result 只保留 safe debug 片段。
- completion rehearsal 的 phone_safe_summary 必须经过统一脱敏。
- completion rehearsal 的 unsafe control wording 必须 fail closed。
- completion rehearsal 的 unsupported schema 必须 fail closed。
- completion rehearsal 的 unsupported boundary 必须 fail closed。
- completion rehearsal 的 JSON read_error 必须返回 blocked/not_proven。
- completion rehearsal 的 missing source 必须返回 blocked/not_proven。
- completion rehearsal 的 metadata_only 必须保持 true。
- completion rehearsal 的 delivery_success 必须保持 false。
- completion rehearsal 的 primary_actions_enabled 必须保持 false。
- review decision 只表示 route terminal 材料的人工复核决策摘要。
- review decision 不能证明真实终态动作完成。
- review decision 不能证明真实现场复跑完成。
- review decision 不能授权机器人控制。
- review decision 不能授权 remote ACK。
- review decision 不能授权 cursor update。
- review decision 不能授权 persistence update。
- review decision 不能授权 terminal ACK。
- review decision 不能授权 Nav2 action。
- review decision 不能授权 HIL pass。
- review decision 不能将 owner_handoff 解读为 owner 已验收。
- review decision 不能将 next_required_evidence 解读为证据已满足。
- review decision 不能将 field_retest_request_guidance 解读为现场已通过。
- review decision 不能将 robot_diagnostics_summary 解读为生产就绪。
- review decision 不能将 phone_safe_summary 解读为手机真机证明。
- review decision 的 wrapper 必须回指原始 schema。
- review decision 的 wrapper 必须回指原始 evidence boundary。
- review decision 的 evidence_ref 必须和摘要保持一致。
- review decision 的 same_evidence_ref_required 不能被 source 放宽。
- review decision 的 unsafe field 必须 fail closed。
- review decision 的 unsafe copy 必须 fail closed。
- review decision 的 unsupported schema 必须 fail closed。
- review decision 的 unsupported boundary 必须 fail closed。
- review decision 的 JSON read_error 必须返回 blocked/not_proven。
- review decision 的 missing source 必须返回 blocked/not_proven。
- review decision 的 metadata_only 必须保持 true。
- review decision 的 delivery_success 必须保持 false。
- review decision 的 primary_actions_enabled 必须保持 false。
- review decision 的 collect_triggered 必须保持 false。
- review decision 的 dropoff_triggered 必须保持 false。
- review decision 的 cancel_triggered 必须保持 false。
- review decision 的 ack_post_allowed 必须保持 false。
- review decision 的 remote_ack_allowed 必须保持 false。
- review decision 的 cursor_updates_allowed 必须保持 false。
- review decision 的 persistence_updates_allowed 必须保持 false。
- review decision 的 terminal_ack_allowed 必须保持 false。
- review decision 的 nav2_triggered 必须保持 false。
- review decision 的 hil_pass 必须保持 false。
- review decision 的 production_ready 必须保持 false。
- 本模块只复用 facade 的统一文本脱敏 helper。
- 本模块只复用 facade 的统一 evidence_ref 清洗 helper。
- 本模块只复用 facade 的统一 PC debug 字段清洗 helper。
- 本模块只复用 facade 的统一 route terminal 列表清洗 helper。
- 本模块只复用 facade 的 field-run unsafe guard。
- 本模块不复制 route field-run 的大块判定逻辑。
- 本模块不读取 elevator diagnostics 输入。
- 本模块不读取 mobile real device 输入。
- 本模块不读取 hardware/WAVE ROVER/PR5 输入。
- 本模块不读取 route field retest 输入。
- 本模块不改变 /api/status 的 public alias。
- 本模块不改变 /api/diagnostics 的 public alias。
- 本模块不改变 schema 字符串。
- 本模块不改变 gate 字符串。
- 本模块不改变 not_proven 必备缺口。
- 本模块不改变 safe copy 文案。
- 本模块不改变 false-state 字段。
- 本模块不改变 existing test import path。
- facade 仍负责 public compatibility。
- 新模块只负责 route terminal summary 内聚。
- 常量放在新模块是为了让 route terminal 边界独立可读。
- 默认摘要放在新模块是为了集中 fail-closed 默认值。
- not_proven helper 放在新模块是为了集中真实证据缺口。
- source contract helper 放在新模块是为了集中 wrapper/source 校验。
- evidence_ref match helper 放在新模块是为了集中同 ref 复账约束。
- summarize helper 放在新模块是为了让 facade 只做导入转发。
- 延迟访问 facade helper 是为了避免 Python 初始化环。
- 延迟访问 facade helper 也让现有 helper 成为唯一清洗实现。
- 读文件路径只支持本地 JSON artifact 或 dict source。
- 读文件失败不能抛给调用方形成 500。
- dict source 只消费白名单摘要字段。
- nested source 只选择已知 summary key。
- raw artifact sibling 不应出现在返回 payload。
- safe_copy 必须优先取安全摘要字段。
- safe_phone_copy 必须与 safe_copy 保持一致。
- source_schema 必须脱敏后返回。
- source_evidence_boundary 必须脱敏后返回。
- read_error 必须脱敏后返回。
- operator_next_steps 必须只保留安全文本。
- next_required_evidence 必须只保留安全文本。
- route_progress 必须只保留安全 debug 字段。
- review_summary 必须只保留安全 debug 字段。
- robot_diagnostics_summary 必须只保留安全 debug 字段。
- field_retest_request_guidance 必须只保留安全 debug 字段。
- owner_handoff 必须只保留安全文本。
- failure_reason 必须只保留安全文本。
- recovery_reason 必须只保留安全文本。
- cancel_reason 必须只保留安全文本。
- final_status 必须只保留安全文本。
- final_state 必须只保留安全文本。
- unsupported source 必须保留可读 reason。
- evidence_ref mismatch 必须保留可读 reason。
- unsafe field block 必须保留可读 reason。
- missing artifact 必须保留可读 reason。
- invalid JSON shape 必须保留可读 reason。
- source summary 缺字段时必须使用 blocked fallback。
- source summary 缺 phone copy 时必须使用 metadata-only fallback。
- source summary 缺 materials_status 时必须使用 blocked fallback。
- source summary 缺 review_summary 时必须使用 blocked fallback。
- source summary 缺 robot_diagnostics_summary 时必须使用 blocked fallback。
- source summary 缺 retest guidance 时必须使用 blocked fallback。
- route terminal summary 是软件证明边界。
- route terminal summary 不是硬件履约边界。
- route terminal summary 不是算法闭环边界。
- route terminal summary 不是手机真机验收边界。
- route terminal summary 不是产品 OKR 提升证据。
- route terminal summary 不是交付成功证据。
- route terminal summary 不是生产就绪证据。
- route terminal summary 不是外部云证据。
- route terminal summary 不是 PR reviewer resolution。
- route terminal summary 不是 owner material acceptance。
- route terminal summary 不是 route elevator field result。
- route terminal summary 不是 verified terminal delivery result。
- route terminal summary 不是 true browser evidence。
- route terminal summary 不是 OSS/CDN live proof。
- route terminal summary 不是 cloud ACK proof。
- route terminal summary 不是 robot command proof。
- route terminal summary 不是 serial feedback proof。
- route terminal summary 不是 HIL packet proof。
- route terminal summary 不是 WAVE ROVER feedback proof。
- route terminal summary 不是 Nav2 action proof。
- route terminal summary 不是 persistence mutation proof。
- route terminal summary 不是 cursor mutation proof。
- route terminal summary 不是 terminal ACK mutation proof。
- route terminal summary 不是 dropoff completion proof。
- route terminal summary 不是 cancel completion proof。
- route terminal summary 不是 collection proof。
- route terminal summary 不是 route retest proof。
- route terminal summary 不是 elevator trace proof。
- route terminal summary 不是 hardware procurement proof。
- route terminal summary 不是 PR5 vendor proof。
- route terminal summary 不是 mobile production proof。
- route terminal summary 不是 cloud worker cutover proof。
- route terminal summary 不是 cloud lifecycle replay proof。
- route terminal summary 不是 external evidence completion proof。
- route terminal summary 不是 field evidence resolution proof。
- route terminal summary 不是 verified terminal material proof。
- route terminal summary 不是 task terminal field material proof。
- route terminal summary 只是 route task terminal 的安全只读摘要。
- 以上约束使拆分保持结构性重构，不改变机器人运行行为。
"""

import json
import os


ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL_SCHEMA = (
    "trashbot.route_task_terminal_completion_rehearsal.v1"
)
ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL_SUMMARY_SCHEMA = (
    "trashbot.route_task_terminal_completion_rehearsal_summary.v1"
)
ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL_GATE = (
    "software_proof_docker_route_task_terminal_completion_rehearsal_gate"
)
ROUTE_TASK_TERMINAL_REVIEW_DECISION_SCHEMA = (
    "trashbot.route_task_terminal_review_decision.v1"
)
ROUTE_TASK_TERMINAL_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.route_task_terminal_review_decision_summary.v1"
)
ROUTE_TASK_TERMINAL_REVIEW_DECISION_GATE = (
    "software_proof_docker_route_task_terminal_review_decision_gate"
)

def _diagnostics():
    # 延迟读取 facade helper，避免 public 兼容层导入本模块时形成初始化环。
    from ros2_trashbot_behavior import operator_gateway_diagnostics

    return operator_gateway_diagnostics


def _redact_route_task_rehearsal_text(value):
    # route terminal 继续复用 facade 的统一脱敏策略，避免新模块产生第二套规则。
    return _diagnostics()._redact_route_task_rehearsal_text(value)


def _safe_route_task_rehearsal_ref(value):
    # evidence_ref 规范必须和 route/task 其他摘要一致，否则同 ref 复账会误判。
    return _diagnostics()._safe_route_task_rehearsal_ref(value)


def _safe_pc_route_debug_value(value):
    # PC debug 字段只允许走既有白名单，避免 terminal 摘要泄露 raw artifact。
    return _diagnostics()._safe_pc_route_debug_value(value)


def _safe_pc_route_debug_dict(value):
    # 嵌套 summary 字典复用 facade 的递归消毒，保证 public payload 兼容。
    return _diagnostics()._safe_pc_route_debug_dict(value)


def _safe_route_task_rehearsal_list(value):
    # operator_next_steps 和 next_required_evidence 只保留安全文本列表。
    return _diagnostics()._safe_route_task_rehearsal_list(value)


def _route_task_field_run_readiness_has_unsafe_fields(value):
    # terminal completion 可消费 field-run 摘要，因此沿用 field-run unsafe guard。
    return _diagnostics()._route_task_field_run_readiness_has_unsafe_fields(value)


def _route_task_completion_signal_has_unsafe_control_claims(value):
    # completion rehearsal 不能夹带控制成功声明，继续复用 completion signal guard。
    return _diagnostics()._route_task_completion_signal_has_unsafe_control_claims(value)


def _route_task_field_run_readiness_copy_is_unsafe(value):
    # safe_copy 检查必须统一，避免手机面出现 success/control 暗示。
    return _diagnostics()._route_task_field_run_readiness_copy_is_unsafe(value)


def _route_task_field_run_console_has_unsafe_fields(value):
    # review decision 可能携带 console/retest 片段，仍使用现有 unsafe 字段黑名单。
    return _diagnostics()._route_task_field_run_console_has_unsafe_fields(value)


def _route_task_terminal_completion_rehearsal_not_proven(source=None, summary=None):
    # terminal rehearsal 只核对终态材料是否可复账；真实投放、取消完成、Nav2/HIL 仍要外部材料证明。
    source = source if isinstance(source, dict) else {}
    summary = summary if isinstance(summary, dict) else {}
    values = []
    source_values = []
    if isinstance(source.get("not_proven"), list):
        source_values.extend(source.get("not_proven"))
    if isinstance(summary.get("not_proven"), list):
        source_values.extend(summary.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "real_route_collection",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "production_readiness",
        "real_dropoff_completion",
        "real_cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _route_task_terminal_review_decision_not_proven(source=None, summary=None):
    # terminal review 只给人工复核和 owner handoff 使用；真实控制、ACK、Nav2/HIL 和交付完成必须继续外部证明。
    source = source if isinstance(source, dict) else {}
    summary = summary if isinstance(summary, dict) else {}
    values = []
    source_values = []
    if isinstance(source.get("not_proven"), list):
        source_values.extend(source.get("not_proven"))
    if isinstance(summary.get("not_proven"), list):
        source_values.extend(summary.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "real_route_collection",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "production_readiness",
        "real_dropoff_completion",
        "real_cancel_completion",
        "dropoff_or_cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values

def _default_route_task_terminal_completion_rehearsal_summary(
    path,
    status="blocked_missing_route_task_terminal_completion_rehearsal",
    read_error="",
):
    # terminal completion rehearsal 默认就是 blocked/not_proven，缺 artifact 时不能给手机或 Robot 侧任何完成暗示。
    return {
        "schema": ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL_GATE,
        "source_schema": "",
        "source_evidence_boundary": "",
        "terminal_verdict": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "route/task terminal completion rehearsal source is not configured",
        },
        "final_status": "",
        "final_state": "",
        "dropoff_result": {"status": "not_proven"},
        "cancel_reason": "",
        "failure_reason": "",
        "recovery_reason": "",
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "route_progress": {"present": False, "evidence_ref": ""},
        "materials_status": {
            "status": "blocked",
            "reason": "route/task terminal completion rehearsal source is not configured",
        },
        "operator_next_steps": [],
        "phone_safe_summary": {
            "safe_copy": "Route/task terminal completion rehearsal is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_phone_copy": "Route/task terminal completion rehearsal is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        },
        "not_proven": _route_task_terminal_completion_rehearsal_not_proven(),
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _default_route_task_terminal_review_decision_summary(
    path,
    status="blocked_missing_route_task_terminal_review_decision",
    read_error="",
):
    # terminal review decision 默认保持 blocked/not_proven，避免缺 artifact 时被误读成终态 ACK 或交付完成。
    return {
        "schema": ROUTE_TASK_TERMINAL_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_TERMINAL_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "review_decision": {
            "status": status,
            "decision": "not_proven",
            "reason": read_error or "route-task terminal review decision is not configured",
        },
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "owner_handoff": "Robot",
        "next_required_evidence": [],
        "field_retest_request_guidance": {
            "status": "blocked",
            "reason": "route-task terminal review decision is not configured",
        },
        "review_summary": {
            "status": "blocked",
            "reason": "route-task terminal review decision is not configured",
        },
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task terminal review decision is not configured",
        },
        "phone_safe_summary": {
            "safe_copy": "Route-task terminal review decision is metadata-only; delivery_success=false.",
            "safe_phone_copy": "Route-task terminal review decision is metadata-only; delivery_success=false.",
        },
        "not_proven": _route_task_terminal_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
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
    }

def _route_task_terminal_review_decision_source_contract(value):
    # terminal review 支持直接 artifact 或 summary wrapper；wrapper 仍必须保留原始 source/boundary。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_TERMINAL_REVIEW_DECISION_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _route_task_terminal_completion_evidence_refs_match(source, source_summary):
    # 同一 evidence_ref 是本轮复账合同的核心；只比较安全摘要字段，不展开 raw artifact。
    refs = []
    for value in (
        source.get("safe_evidence_ref"),
        source.get("evidence_ref"),
        source_summary.get("safe_evidence_ref"),
        source_summary.get("evidence_ref"),
    ):
        safe_ref = _safe_route_task_rehearsal_ref(value)
        if safe_ref and safe_ref not in refs:
            refs.append(safe_ref)
    for container in (source.get("route_progress"), source_summary.get("route_progress")):
        if isinstance(container, dict):
            safe_ref = _safe_route_task_rehearsal_ref(container.get("evidence_ref"))
            if safe_ref and safe_ref not in refs:
                refs.append(safe_ref)
    return len(refs) <= 1


def summarize_route_task_terminal_completion_rehearsal(path):
    """构建 route/task 终态复账的 metadata-only diagnostics 摘要。"""
    source = path if isinstance(path, dict) else None
    source_path = "" if source is not None else os.path.expanduser(str(path or ""))
    summary = _default_route_task_terminal_completion_rehearsal_summary(source_path)
    if source is None:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "terminal_verdict": {
                        "status": "blocked_missing_route_task_terminal_completion_rehearsal",
                        "verdict": "not_proven",
                        "reason": "route/task terminal completion rehearsal source missing",
                    },
                    "materials_status": {
                        "status": "blocked",
                        "reason": "terminal completion rehearsal source missing",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                source = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading route/task terminal completion rehearsal source: {exc}"
            )
            summary.update(
                {
                    "terminal_verdict": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": safe_error,
                    },
                    "materials_status": {
                        "status": "blocked",
                        "reason": "terminal completion rehearsal JSON read error",
                    },
                }
            )
            return summary
    if not isinstance(source, dict):
        summary.update(
            {
                "terminal_verdict": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route/task terminal completion rehearsal JSON must be an object",
                },
                "materials_status": {
                    "status": "blocked",
                    "reason": "terminal completion rehearsal JSON shape is invalid",
                },
            }
        )
        return summary

    source_schema = str(source.get("schema") or "")
    source_boundary = str(source.get("evidence_boundary") or "")
    source_summary = source
    for candidate_key in (
        "route_task_terminal_completion_rehearsal_summary",
        "route_task_terminal_completion_rehearsal",
        "terminal_completion_rehearsal_summary",
        "summary",
    ):
        candidate = source.get(candidate_key)
        if isinstance(candidate, dict):
            source_summary = candidate
            break
    if source_schema == ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL_SUMMARY_SCHEMA:
        source_summary = source
    verdict = (
        source_summary.get("terminal_verdict")
        if isinstance(source_summary.get("terminal_verdict"), dict)
        else {}
    )
    phone_summary = (
        source_summary.get("phone_safe_summary")
        if isinstance(source_summary.get("phone_safe_summary"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        phone_summary.get("safe_copy")
        or phone_summary.get("safe_phone_copy")
        or "Route/task terminal completion rehearsal is metadata-only; delivery_success=false; primary_actions_enabled=false."
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "terminal_verdict": {
                "status": _redact_route_task_rehearsal_text(
                    verdict.get("status") or source_summary.get("status") or "route_task_terminal_completion_rehearsal"
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    verdict.get("verdict") or source_summary.get("verdict") or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    verdict.get("reason") or source_summary.get("reason") or "terminal completion rehearsal consumed"
                ),
            },
            "final_status": _redact_route_task_rehearsal_text(source_summary.get("final_status")),
            "final_state": _redact_route_task_rehearsal_text(source_summary.get("final_state")),
            "dropoff_result": _safe_pc_route_debug_value(
                source_summary.get("dropoff_result") or {"status": "not_proven"}
            ),
            "cancel_reason": _redact_route_task_rehearsal_text(source_summary.get("cancel_reason")),
            "failure_reason": _redact_route_task_rehearsal_text(source_summary.get("failure_reason")),
            "recovery_reason": _redact_route_task_rehearsal_text(source_summary.get("recovery_reason")),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                source_summary.get("safe_evidence_ref")
                or source_summary.get("evidence_ref")
                or source.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": bool(source_summary.get("same_evidence_ref_required", True)),
            "route_progress": _safe_pc_route_debug_dict(source_summary.get("route_progress"))
            or {"present": False, "evidence_ref": ""},
            "materials_status": _safe_pc_route_debug_dict(source_summary.get("materials_status"))
            or {
                "status": "not_proven",
                "reason": "terminal completion rehearsal consumed without explicit materials status",
            },
            "operator_next_steps": _safe_route_task_rehearsal_list(source_summary.get("operator_next_steps")),
            "phone_safe_summary": {
                "safe_copy": safe_copy,
                "safe_phone_copy": safe_copy,
            },
            "not_proven": _route_task_terminal_completion_rehearsal_not_proven(source, source_summary),
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    if source_schema not in (
        ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL_SCHEMA,
        ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL_SUMMARY_SCHEMA,
    ) or source_boundary != ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL_GATE:
        summary.update(
            {
                "terminal_verdict": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route/task terminal completion rehearsal schema or evidence boundary is unsupported",
                },
                "materials_status": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not _route_task_terminal_completion_evidence_refs_match(source, source_summary):
        summary.update(
            {
                "terminal_verdict": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "terminal completion rehearsal evidence_ref values do not match",
                },
                "materials_status": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if (
        _route_task_field_run_readiness_has_unsafe_fields(source_summary)
        or _route_task_completion_signal_has_unsafe_control_claims(source)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "terminal_verdict": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "terminal completion rehearsal contains unsafe summary fields or control claims",
                },
                "materials_status": {
                    "status": "blocked",
                    "reason": "unsafe terminal completion rehearsal fields",
                },
            }
        )
        return summary
    return summary


def _route_task_terminal_review_decision_evidence_refs_match(source, source_summary):
    # terminal review 复核必须沿用同一 evidence_ref；只比较安全 ref 字段，避免展开 raw 现场材料。
    refs = []
    for value in (
        source.get("safe_evidence_ref"),
        source.get("evidence_ref"),
        source_summary.get("safe_evidence_ref"),
        source_summary.get("evidence_ref"),
    ):
        safe_ref = _safe_route_task_rehearsal_ref(value)
        if safe_ref and safe_ref not in refs:
            refs.append(safe_ref)
    return len(refs) <= 1


def summarize_route_task_terminal_review_decision(source):
    """构建 route-task terminal review decision 的 metadata-only diagnostics 摘要。"""
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_route_task_terminal_review_decision_summary(source_path)
    if isinstance(source, dict):
        review = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "review_decision": {
                        "status": "blocked_missing_route_task_terminal_review_decision",
                        "decision": "not_proven",
                        "reason": "route-task terminal review decision source missing",
                    },
                    "review_summary": {
                        "status": "blocked",
                        "reason": "route-task terminal review decision source missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "route-task terminal review decision source missing",
                    },
                    "phone_safe_summary": {
                        "safe_copy": "Route-task terminal review decision is missing; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Route-task terminal review decision is missing; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                review = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading route-task terminal review decision: {exc}"
            )
            summary.update(
                {
                    "review_decision": {
                        "status": "read_error",
                        "decision": "not_proven",
                        "reason": safe_error,
                    },
                    "review_summary": {"status": "blocked", "reason": "terminal review JSON read error"},
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "terminal review JSON read error",
                    },
                    "phone_safe_summary": {
                        "safe_copy": "Route-task terminal review decision could not be read; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Route-task terminal review decision could not be read; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary
    if not isinstance(review, dict):
        summary.update(
            {
                "review_decision": {
                    "status": "read_error",
                    "decision": "not_proven",
                    "reason": "route-task terminal review decision JSON must be an object",
                },
                "review_summary": {"status": "blocked", "reason": "terminal review JSON shape is invalid"},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "terminal review JSON shape is invalid",
                },
                "phone_safe_summary": {
                    "safe_copy": "Route-task terminal review decision shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task terminal review decision shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    # PC/Autonomy/Product 可能传 artifact、summary wrapper 或 diagnostics nested source；这里只消费白名单摘要字段。
    source_summary = review
    for candidate_key in (
        "route_task_terminal_review_decision_summary",
        "route_task_terminal_review_decision",
        "terminal_review_decision_summary",
        "robot_diagnostics_summary",
        "phone_safe_summary",
        "summary",
    ):
        candidate = review.get(candidate_key)
        if isinstance(candidate, dict):
            source_summary = candidate
            break
    if review.get("schema") == ROUTE_TASK_TERMINAL_REVIEW_DECISION_SUMMARY_SCHEMA:
        source_summary = review
    source_schema, source_boundary = _route_task_terminal_review_decision_source_contract(review)
    source_decision = (
        source_summary.get("review_decision")
        if isinstance(source_summary.get("review_decision"), dict)
        else review.get("review_decision")
        if isinstance(review.get("review_decision"), dict)
        else {}
    )
    decision_text = (
        review.get("review_decision")
        if not isinstance(review.get("review_decision"), dict)
        else source_summary.get("decision")
    )
    review_fragment = (
        source_summary.get("review_summary")
        if isinstance(source_summary.get("review_summary"), dict)
        else source_summary.get("summary")
        if isinstance(source_summary.get("summary"), dict)
        else review.get("review_summary")
        if isinstance(review.get("review_summary"), dict)
        else {}
    )
    robot_summary = (
        review.get("robot_diagnostics_summary")
        if isinstance(review.get("robot_diagnostics_summary"), dict)
        else source_summary.get("robot_diagnostics_summary")
        if isinstance(source_summary.get("robot_diagnostics_summary"), dict)
        else {}
    )
    phone_summary = (
        source_summary.get("phone_safe_summary")
        if isinstance(source_summary.get("phone_safe_summary"), dict)
        else source_summary.get("mobile_readonly_summary")
        if isinstance(source_summary.get("mobile_readonly_summary"), dict)
        else review.get("phone_safe_summary")
        if isinstance(review.get("phone_safe_summary"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        phone_summary.get("safe_copy")
        or phone_summary.get("safe_phone_copy")
        or source_summary.get("safe_copy")
        or review.get("safe_copy")
        or "Route-task terminal review decision is metadata-only; delivery_success=false."
    )
    safe_phone_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(phone_summary.get(key) or "").strip():
            safe_phone_summary[key] = _redact_route_task_rehearsal_text(phone_summary.get(key))
    safe_phone_summary["safe_copy"] = safe_copy
    safe_phone_summary["safe_phone_copy"] = safe_copy
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": review.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "review_decision": {
                "status": _redact_route_task_rehearsal_text(
                    source_decision.get("status") or source_summary.get("status") or review.get("status") or "blocked"
                ),
                "decision": _redact_route_task_rehearsal_text(
                    source_decision.get("decision")
                    or source_decision.get("verdict")
                    or decision_text
                    or source_summary.get("decision")
                    or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    source_decision.get("reason")
                    or source_decision.get("summary")
                    or source_summary.get("reason")
                    or review.get("reason")
                    or "route-task terminal review decision consumed without explicit reason"
                ),
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                source_summary.get("safe_evidence_ref")
                or source_summary.get("evidence_ref")
                or review.get("safe_evidence_ref")
                or review.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": bool(
                source_summary.get(
                    "same_evidence_ref_required",
                    review.get("same_evidence_ref_required", True),
                )
            ),
            "owner_handoff": _redact_route_task_rehearsal_text(
                source_summary.get("owner_handoff") or review.get("owner_handoff") or "Robot"
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                source_summary.get("next_required_evidence")
                if isinstance(source_summary.get("next_required_evidence"), list)
                else review.get("next_required_evidence")
            ),
            "field_retest_request_guidance": _safe_pc_route_debug_dict(
                source_summary.get("field_retest_request_guidance")
                if isinstance(source_summary.get("field_retest_request_guidance"), dict)
                else review.get("field_retest_request_guidance")
            )
            or {"status": "blocked", "reason": "terminal review decision consumed without explicit retest guidance"},
            "review_summary": _safe_pc_route_debug_dict(review_fragment)
            or {"status": "blocked", "reason": "terminal review decision consumed without explicit summary"},
            "operator_next_steps": _safe_route_task_rehearsal_list(
                source_summary.get("operator_next_steps")
                if isinstance(source_summary.get("operator_next_steps"), list)
                else review.get("operator_next_steps")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {"status": "blocked", "reason": "terminal review decision consumed without explicit robot diagnostics summary"},
            "phone_safe_summary": safe_phone_summary,
            "not_proven": _route_task_terminal_review_decision_not_proven(review, source_summary),
            "read_error": "",
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    if source_schema != ROUTE_TASK_TERMINAL_REVIEW_DECISION_SCHEMA or source_boundary != ROUTE_TASK_TERMINAL_REVIEW_DECISION_GATE:
        summary.update(
            {
                "review_decision": {
                    "status": "unsupported_schema",
                    "decision": "not_proven",
                    "reason": "route-task terminal review decision schema or evidence boundary is unsupported",
                },
                "next_required_evidence": [],
                "field_retest_request_guidance": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "review_summary": {"status": "blocked", "reason": "unsupported schema or evidence boundary"},
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "phone_safe_summary": {
                    "safe_copy": "Route-task terminal review decision is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task terminal review decision is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary
    if (
        not summary["same_evidence_ref_required"]
        or not _route_task_terminal_review_decision_evidence_refs_match(review, source_summary)
    ):
        summary.update(
            {
                "review_decision": {
                    "status": "evidence_ref_mismatch",
                    "decision": "not_proven",
                    "reason": "route-task terminal review decision evidence_ref constraints do not match",
                },
                "field_retest_request_guidance": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
                "review_summary": {"status": "blocked", "reason": "same evidence_ref mismatch"},
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if (
        _route_task_field_run_console_has_unsafe_fields(review)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "review_decision": {
                    "status": "unsafe_fields",
                    "decision": "not_proven",
                    "reason": "route-task terminal review decision contains unsafe summary fields or control claims",
                },
                "next_required_evidence": [],
                "field_retest_request_guidance": {
                    "status": "blocked",
                    "reason": "unsafe terminal review decision fields",
                },
                "review_summary": {"status": "blocked", "reason": "unsafe terminal review decision fields"},
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe terminal review decision fields",
                },
                "phone_safe_summary": {
                    "safe_copy": "Route-task terminal review decision was blocked because fields could expose control data, weaken evidence_ref constraints, or imply delivery success.",
                    "safe_phone_copy": "Route-task terminal review decision was blocked because fields could expose control data, weaken evidence_ref constraints, or imply delivery success.",
                },
            }
        )
        return summary
    return summary
