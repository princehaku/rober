"""Route task field retest diagnostics summary helpers.

本模块承接 operator_gateway_diagnostics 的 route_task_field_retest 只读诊断域。
这些摘要只证明 software_proof 元数据可读，不能升级为真实现场通过、
HIL、Nav2 runtime、WAVE ROVER 运动证明或 delivery success。
"""

import json
import os

EVIDENCE_SOURCE_SOFTWARE = "software_proof"


def _diagnostics():
    # 延迟读取 facade helper，避免兼容层导入本模块时形成初始化环。
    from ros2_trashbot_behavior import operator_gateway_diagnostics

    return operator_gateway_diagnostics


def _facade_helper(name, *args, **kwargs):
    # retest 域先独立承载业务逻辑，通用安全清洗 helper 暂由 facade 统一提供。
    return getattr(_diagnostics(), name)(*args, **kwargs)


def _redact_route_task_rehearsal_text(value):
    # 脱敏规则保持单一来源，避免拆分后 safe copy 输出发生兼容性漂移。
    return _facade_helper("_redact_route_task_rehearsal_text", value)


def _route_task_field_run_console_has_unsafe_fields(value):
    # console unsafe 规则属于跨域守卫，继续复用旧实现保证 fail-closed 条件一致。
    return _facade_helper("_route_task_field_run_console_has_unsafe_fields", value)


def _route_task_field_run_intake_has_unsafe_control_claims(value):
    # 控制授权敏感词保持跨域一致，Robot diagnostics 不新增任何可控动作入口。
    return _facade_helper("_route_task_field_run_intake_has_unsafe_control_claims", value)


def _route_task_field_run_readiness_copy_is_unsafe(value):
    # readiness safe copy 的危险措辞仍走共享判定，避免 metadata-only 摘要误报可控。
    return _facade_helper("_route_task_field_run_readiness_copy_is_unsafe", value)


def _route_task_field_run_readiness_has_unsafe_fields(value, key_path=""):
    # readiness unsafe 字段规则继续委托共享实现，保证嵌套字段过滤不变。
    return _facade_helper("_route_task_field_run_readiness_has_unsafe_fields", value, key_path)


def _safe_pc_route_debug_dict(value):
    # PC debug 字段只能保留短安全摘要，不能泄露本地路径或原始材料。
    return _facade_helper("_safe_pc_route_debug_dict", value)


def _safe_pc_route_debug_value(value, depth=0):
    # 与旧实现保持递归深度限制，避免嵌套原始 payload 透传。
    return _facade_helper("_safe_pc_route_debug_value", value, depth)


def _safe_route_task_rehearsal_list(value, limit=8):
    # 列表裁剪规则保持不变，避免 diagnostics payload 体积和字段语义漂移。
    return _facade_helper("_safe_route_task_rehearsal_list", value, limit)


def _safe_route_task_rehearsal_ref(value):
    # 引用清洗保持兼容，旧调用方依赖空字符串 fail-closed 语义。
    return _facade_helper("_safe_route_task_rehearsal_ref", value)


__all__ = [
    "ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_GATE",
    "ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_GATE",
    "ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_GATE",
    "ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_GATE",
    "ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_GATE",
    "ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_GATE",
    "ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_GATE",
    "ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_GATE",
    "ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_GATE",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_GATE",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_GATE",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_GATE",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_GATE",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_GATE",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_GATE",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_GATE",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_GATE",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_GATE",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_GATE",
    "ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_GATE",
    "ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_GATE",
    "ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_GATE",
    "ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_GATE",
    "ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_GATE",
    "ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_GATE",
    "ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_GATE",
    "ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH_GATE",
    "ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_GATE",
    "ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_GATE",
    "ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_GATE",
    "ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_GATE",
    "ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_GATE",
    "ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA",
    "ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_GATE",
    "_route_task_field_retest_execution_pack_not_proven",
    "_route_task_field_retest_session_handoff_not_proven",
    "_route_task_field_retest_result_intake_not_proven",
    "_route_task_field_retest_result_reconciliation_not_proven",
    "_route_task_field_retest_material_pack_not_proven",
    "_route_task_field_retest_material_callback_packet_not_proven",
    "_route_task_field_retest_material_callback_review_decision_not_proven",
    "_route_task_field_retest_operator_drill_not_proven",
    "_route_task_field_retest_drill_console_not_proven",
    "_route_task_field_retest_acceptance_brief_not_proven",
    "_route_task_field_retest_acceptance_review_decision_not_proven",
    "_route_task_field_retest_acceptance_execution_pack_not_proven",
    "_route_task_field_retest_acceptance_execution_callback_intake_not_proven",
    "_route_task_field_retest_evidence_dispatch_not_proven",
    "_route_task_field_retest_callback_intake_not_proven",
    "_route_task_field_retest_callback_review_decision_not_proven",
    "_route_task_field_retest_review_result_handoff_not_proven",
    "_route_task_field_retest_result_acceptance_packet_not_proven",
    "_route_task_field_retest_result_acceptance_backfill_not_proven",
    "_route_task_field_retest_result_backfill_review_decision_not_proven",
    "_route_task_field_retest_result_review_dispatch_not_proven",
    "_route_task_field_retest_result_review_decision_not_proven",
    "_route_task_field_retest_result_review_handoff_not_proven",
    "_route_task_field_retest_result_callback_intake_not_proven",
    "_route_task_field_retest_result_callback_review_decision_not_proven",
    "_route_task_field_retest_acceptance_execution_callback_review_decision_not_proven",
    "_route_task_field_retest_acceptance_execution_callback_review_handoff_not_proven",
    "_route_task_field_retest_result_callback_review_handoff_not_proven",
    "_route_task_field_retest_acceptance_execution_handoff_intake_not_proven",
    "_route_task_field_retest_acceptance_execution_rerun_queue_not_proven",
    "_route_task_field_retest_acceptance_execution_rerun_result_intake_not_proven",
    "_route_task_field_retest_acceptance_execution_rerun_result_review_decision_not_proven",
    "_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_not_proven",
    "_route_task_field_retest_result_review_intake_not_proven",
    "_default_route_task_field_retest_execution_pack_summary",
    "_default_route_task_field_retest_session_handoff_summary",
    "_default_route_task_field_retest_result_intake_summary",
    "_default_route_task_field_retest_result_reconciliation_summary",
    "_default_route_task_field_retest_material_pack_summary",
    "_default_route_task_field_retest_material_callback_packet_summary",
    "_default_route_task_field_retest_material_callback_review_decision_summary",
    "_default_route_task_field_retest_operator_drill_summary",
    "_default_route_task_field_retest_drill_console_summary",
    "_default_route_task_field_retest_acceptance_brief_summary",
    "_default_route_task_field_retest_acceptance_review_decision_summary",
    "_default_route_task_field_retest_acceptance_execution_pack_summary",
    "_default_route_task_field_retest_acceptance_execution_callback_intake_summary",
    "_default_route_task_field_retest_evidence_dispatch_summary",
    "_default_route_task_field_retest_callback_intake_summary",
    "_default_route_task_field_retest_callback_review_decision_summary",
    "_default_route_task_field_retest_review_result_handoff_summary",
    "_default_route_task_field_retest_result_acceptance_packet_summary",
    "_default_route_task_field_retest_result_acceptance_backfill_summary",
    "_default_route_task_field_retest_result_backfill_review_decision_summary",
    "_default_route_task_field_retest_result_review_dispatch_summary",
    "_default_route_task_field_retest_result_review_decision_summary",
    "_default_route_task_field_retest_result_review_handoff_summary",
    "_default_route_task_field_retest_result_callback_intake_summary",
    "_default_route_task_field_retest_result_callback_review_decision_summary",
    "_default_route_task_field_retest_acceptance_execution_callback_review_decision_summary",
    "_default_route_task_field_retest_acceptance_execution_callback_review_handoff_summary",
    "_default_route_task_field_retest_acceptance_execution_handoff_intake_summary",
    "_default_route_task_field_retest_acceptance_execution_rerun_queue_summary",
    "_default_route_task_field_retest_acceptance_execution_rerun_result_intake_summary",
    "_default_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary",
    "_default_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary",
    "_default_route_task_field_retest_result_callback_review_handoff_summary",
    "_default_route_task_field_retest_result_review_intake_summary",
    "_route_task_field_retest_execution_pack_has_success_wording",
    "_route_task_field_retest_operator_drill_has_unsafe_fields",
    "_route_task_field_retest_execution_pack_source_contract",
    "_route_task_field_retest_session_handoff_source_contract",
    "_route_task_field_retest_result_intake_source_contract",
    "_route_task_field_retest_result_reconciliation_source_contract",
    "_route_task_field_retest_result_reconciliation_flat_lineage",
    "_route_task_field_retest_result_reconciliation_lineage_item",
    "_route_task_field_retest_result_reconciliation_lineage",
    "_route_task_field_retest_material_pack_source_contract",
    "_route_task_field_retest_material_callback_packet_source_contract",
    "_route_task_field_retest_material_callback_review_decision_source_contract",
    "_route_task_field_retest_operator_drill_source_contract",
    "_route_task_field_retest_drill_console_source_contract",
    "_route_task_field_retest_acceptance_brief_source_contract",
    "_route_task_field_retest_acceptance_review_decision_source_contract",
    "_route_task_field_retest_acceptance_execution_pack_source_contract",
    "_route_task_field_retest_acceptance_execution_callback_intake_source_contract",
    "_route_task_field_retest_evidence_dispatch_source_contract",
    "_route_task_field_retest_callback_intake_source_contract",
    "_route_task_field_retest_callback_review_decision_source_contract",
    "_route_task_field_retest_review_result_handoff_source_contract",
    "_route_task_field_retest_result_acceptance_packet_source_contract",
    "_route_task_field_retest_result_acceptance_backfill_source_contract",
    "_route_task_field_retest_result_backfill_review_decision_source_contract",
    "_route_task_field_retest_result_review_dispatch_source_contract",
    "_route_task_field_retest_result_review_decision_source_contract",
    "_route_task_field_retest_result_review_handoff_source_contract",
    "_route_task_field_retest_result_callback_intake_source_contract",
    "_route_task_field_retest_result_review_intake_source_contract",
    "_route_task_field_retest_result_callback_review_decision_source_contract",
    "_route_task_field_retest_acceptance_execution_callback_review_decision_source_contract",
    "_route_task_field_retest_acceptance_execution_callback_review_handoff_source_contract",
    "_route_task_field_retest_result_callback_review_handoff_source_contract",
    "_route_task_field_retest_acceptance_execution_handoff_intake_source_contract",
    "_route_task_field_retest_acceptance_execution_rerun_queue_source_contract",
    "_route_task_field_retest_acceptance_execution_rerun_result_intake_source_contract",
    "_route_task_field_retest_acceptance_execution_rerun_result_review_decision_source_contract",
    "_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_source_contract",
    "_route_task_field_retest_execution_pack_requires_same_evidence_ref",
    "_route_task_field_retest_session_handoff_requires_same_evidence_ref",
    "_route_task_field_retest_result_intake_requires_same_evidence_ref",
    "_route_task_field_retest_result_reconciliation_requires_same_evidence_ref",
    "_route_task_field_retest_callback_intake_requires_same_evidence_ref",
    "_route_task_field_retest_review_result_handoff_requires_same_evidence_ref",
    "_route_task_field_retest_result_review_dispatch_requires_same_evidence_ref",
    "_route_task_field_retest_acceptance_review_decision_requires_same_evidence_ref",
    "_route_task_field_retest_acceptance_execution_pack_requires_same_evidence_ref",
    "_route_task_field_retest_acceptance_execution_callback_intake_requires_same_evidence_ref",
    "_route_task_field_retest_result_review_decision_requires_same_evidence_ref",
    "_route_task_field_retest_result_review_handoff_requires_same_evidence_ref",
    "_route_task_field_retest_result_callback_intake_requires_same_evidence_ref",
    "_route_task_field_retest_result_callback_review_decision_requires_same_evidence_ref",
    "_route_task_field_retest_acceptance_execution_callback_review_decision_requires_same_evidence_ref",
    "_route_task_field_retest_acceptance_execution_callback_review_handoff_requires_same_evidence_ref",
    "_route_task_field_retest_result_callback_review_handoff_requires_same_evidence_ref",
    "_route_task_field_retest_acceptance_execution_handoff_intake_requires_same_evidence_ref",
    "_route_task_field_retest_execution_pack_has_disabled_actions",
    "_route_task_field_retest_session_handoff_has_disabled_actions",
    "_route_task_field_retest_result_intake_has_disabled_actions",
    "_route_task_field_retest_result_reconciliation_has_disabled_actions",
    "_route_task_field_retest_material_pack_has_disabled_actions",
    "_route_task_field_retest_material_callback_packet_has_disabled_actions",
    "_route_task_field_retest_material_callback_review_decision_has_disabled_actions",
    "_route_task_field_retest_operator_drill_has_disabled_actions",
    "_route_task_field_retest_drill_console_has_disabled_actions",
    "_route_task_field_retest_acceptance_brief_has_disabled_actions",
    "_route_task_field_retest_acceptance_review_decision_has_disabled_actions",
    "_route_task_field_retest_acceptance_execution_pack_has_disabled_actions",
    "_route_task_field_retest_acceptance_execution_callback_intake_has_disabled_actions",
    "_route_task_field_retest_evidence_dispatch_has_disabled_actions",
    "_route_task_field_retest_callback_intake_has_disabled_actions",
    "_route_task_field_retest_callback_review_decision_has_disabled_actions",
    "_route_task_field_retest_review_result_handoff_has_disabled_actions",
    "_route_task_field_retest_result_acceptance_packet_has_disabled_actions",
    "_route_task_field_retest_result_acceptance_backfill_has_disabled_actions",
    "_route_task_field_retest_result_backfill_review_decision_has_disabled_actions",
    "_route_task_field_retest_result_review_dispatch_has_disabled_actions",
    "_route_task_field_retest_result_review_decision_has_disabled_actions",
    "_route_task_field_retest_result_review_handoff_has_disabled_actions",
    "_route_task_field_retest_result_callback_intake_has_disabled_actions",
    "_route_task_field_retest_result_callback_review_decision_has_disabled_actions",
    "_route_task_field_retest_acceptance_execution_callback_review_decision_has_disabled_actions",
    "_route_task_field_retest_acceptance_execution_callback_review_handoff_has_disabled_actions",
    "_route_task_field_retest_result_callback_review_handoff_has_disabled_actions",
    "_route_task_field_retest_acceptance_execution_handoff_intake_has_disabled_actions",
    "_route_task_field_retest_acceptance_execution_rerun_queue_has_disabled_actions",
    "_route_task_field_retest_acceptance_execution_rerun_result_intake_has_disabled_actions",
    "_route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material",
    "_route_task_field_retest_result_review_intake_has_disabled_actions",
    "summarize_route_task_field_retest_execution_pack",
    "summarize_route_task_field_retest_session_handoff",
    "summarize_route_task_field_retest_result_intake",
    "summarize_route_task_field_retest_result_reconciliation",
    "summarize_route_task_field_retest_material_pack",
    "summarize_route_task_field_retest_material_callback_packet",
    "summarize_route_task_field_retest_material_callback_review_decision",
    "summarize_route_task_field_retest_operator_drill",
    "summarize_route_task_field_retest_drill_console",
    "summarize_route_task_field_retest_acceptance_brief",
    "summarize_route_task_field_retest_acceptance_review_decision",
    "summarize_route_task_field_retest_acceptance_execution_pack",
    "summarize_route_task_field_retest_acceptance_execution_callback_intake",
    "summarize_route_task_field_retest_evidence_dispatch",
    "summarize_route_task_field_retest_callback_intake",
    "summarize_route_task_field_retest_callback_review_decision",
    "summarize_route_task_field_retest_review_result_handoff",
    "summarize_route_task_field_retest_result_acceptance_packet",
    "summarize_route_task_field_retest_result_acceptance_backfill",
    "summarize_route_task_field_retest_result_backfill_review_decision",
    "summarize_route_task_field_retest_result_review_dispatch",
    "summarize_route_task_field_retest_result_review_decision",
    "summarize_route_task_field_retest_result_review_handoff",
    "summarize_route_task_field_retest_result_review_intake",
    "summarize_route_task_field_retest_result_callback_intake",
    "summarize_route_task_field_retest_result_callback_review_decision",
    "summarize_route_task_field_retest_acceptance_execution_callback_review_decision",
    "summarize_route_task_field_retest_acceptance_execution_callback_review_handoff",
    "summarize_route_task_field_retest_acceptance_execution_handoff_intake",
    "summarize_route_task_field_retest_acceptance_execution_rerun_queue",
    "summarize_route_task_field_retest_acceptance_execution_rerun_result_intake",
    "summarize_route_task_field_retest_acceptance_execution_rerun_result_review_decision",
    "summarize_route_task_field_retest_acceptance_execution_rerun_result_review_handoff",
    "summarize_route_task_field_retest_result_callback_review_handoff",
]


ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_SCHEMA = (
    "trashbot.route_task_field_retest_execution_pack.v1"
)


ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_execution_pack_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_GATE = (
    "software_proof_docker_route_task_field_retest_execution_pack_gate"
)


ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_SCHEMA = (
    "trashbot.route_task_field_retest_session_handoff.v1"
)


ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_session_handoff_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_GATE = (
    "software_proof_docker_route_task_field_retest_session_handoff_gate"
)


ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_SCHEMA = (
    "trashbot.route_task_field_retest_result_intake.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_result_intake_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_GATE = (
    "software_proof_docker_route_task_field_retest_result_intake_gate"
)


ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_SCHEMA = (
    "trashbot.route_task_field_retest_result_reconciliation.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_result_reconciliation_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_GATE = (
    "software_proof_docker_route_task_field_retest_result_reconciliation_gate"
)


ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_SCHEMA = (
    "trashbot.route_task_field_retest_material_pack.v1"
)


ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_material_pack_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_GATE = (
    "software_proof_docker_route_task_field_retest_material_pack_gate"
)


ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_SCHEMA = (
    "trashbot.route_task_field_retest_material_callback_packet.v1"
)


ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_material_callback_packet_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_GATE = (
    "software_proof_docker_route_task_field_retest_material_callback_packet_gate"
)


ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_SCHEMA = (
    "trashbot.route_task_field_retest_material_callback_review_decision.v1"
)


ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_material_callback_review_decision_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_GATE = (
    "software_proof_docker_route_task_field_retest_material_callback_review_decision_gate"
)


ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_SCHEMA = (
    "trashbot.route_task_field_retest_operator_drill.v1"
)


ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_operator_drill_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_GATE = (
    "software_proof_docker_route_task_field_retest_operator_drill_gate"
)


ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_SCHEMA = (
    "trashbot.route_task_field_retest_drill_console.v1"
)


ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_drill_console_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_GATE = (
    "software_proof_docker_route_task_field_retest_drill_console_gate"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_brief.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_brief_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_GATE = (
    "software_proof_docker_route_task_field_retest_acceptance_brief_gate"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_review_decision.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_review_decision_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_GATE = (
    "software_proof_docker_route_task_field_retest_acceptance_review_decision_gate"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_pack.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_pack_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_GATE = (
    "software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_callback_intake.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_callback_intake_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_GATE = (
    "software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_callback_review_decision.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_callback_review_decision_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_GATE = (
    "software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_handoff_intake.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_handoff_intake_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_GATE = (
    "software_proof_docker_route_task_field_retest_acceptance_execution_handoff_intake_gate"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_rerun_queue.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_rerun_queue_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_GATE = (
    "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_GATE = (
    "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_intake_gate"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_decision.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_GATE = (
    "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate"
)


ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_SCHEMA = (
    "trashbot.route_task_field_retest_evidence_dispatch.v1"
)


ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_evidence_dispatch_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_GATE = (
    "software_proof_docker_route_task_field_retest_evidence_dispatch_gate"
)


ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_SCHEMA = (
    "trashbot.route_task_field_retest_callback_intake.v1"
)


ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_callback_intake_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_GATE = (
    "software_proof_docker_route_task_field_retest_callback_intake_gate"
)


ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_SCHEMA = (
    "trashbot.route_task_field_retest_callback_review_decision.v1"
)


ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_callback_review_decision_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_GATE = (
    "software_proof_docker_route_task_field_retest_callback_review_decision_gate"
)


ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_SCHEMA = (
    "trashbot.route_task_field_retest_review_result_handoff.v1"
)


ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_review_result_handoff_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_GATE = (
    "software_proof_docker_route_task_field_retest_review_result_handoff_gate"
)


ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_SCHEMA = (
    "trashbot.route_task_field_retest_result_acceptance_packet.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_result_acceptance_packet_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_GATE = (
    "software_proof_docker_route_task_field_retest_result_acceptance_packet_gate"
)


ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_SCHEMA = (
    "trashbot.route_task_field_retest_result_acceptance_backfill.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_result_acceptance_backfill_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_GATE = (
    "software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate"
)


ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_SCHEMA = (
    "trashbot.route_task_field_retest_result_backfill_review_decision.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_result_backfill_review_decision_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_GATE = (
    "software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate"
)


ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_result_review_dispatch_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH_GATE = (
    "software_proof_docker_route_task_field_retest_result_review_dispatch_gate"
)


ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_SCHEMA = (
    "trashbot.route_task_field_retest_result_review_intake.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_result_review_intake_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_GATE = (
    "software_proof_docker_route_task_field_retest_result_review_intake_gate"
)


ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_SCHEMA = (
    "trashbot.route_task_field_retest_result_review_decision.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_result_review_decision_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_GATE = (
    "software_proof_docker_route_task_field_retest_result_review_decision_gate"
)


ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.route_task_field_retest_result_review_handoff.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_result_review_handoff_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_route_task_field_retest_result_review_handoff_gate"
)


ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_SCHEMA = (
    "trashbot.route_task_field_retest_result_callback_intake.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_result_callback_intake_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_GATE = (
    "software_proof_docker_route_task_field_retest_result_callback_intake_gate"
)


ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_SCHEMA = (
    "trashbot.route_task_field_retest_result_callback_review_decision.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_result_callback_review_decision_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_GATE = (
    "software_proof_docker_route_task_field_retest_result_callback_review_decision_gate"
)


ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.route_task_field_retest_result_callback_review_handoff.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_retest_result_callback_review_handoff_summary.v1"
)


ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate"
)


def _route_task_field_retest_execution_pack_not_proven(pack=None, summary_fragment=None):
    # retest execution pack 是下一轮现场补测材料，不得把补测准备态误升为控制、ACK、Nav2/HIL 或送达证据。
    pack = pack if isinstance(pack, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(pack.get("not_proven"), list):
        source_values.extend(pack.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "production_readiness",
        "real_phone_device_or_browser_proof",
        "dropoff_or_cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _route_task_field_retest_session_handoff_not_proven(handoff=None, summary_fragment=None):
    # session handoff 只是现场交接准备材料；真实路线、电梯、手机/browser、硬件和送达结论都必须继续外部证明。
    handoff = handoff if isinstance(handoff, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(handoff.get("not_proven"), list):
        source_values.extend(handoff.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_session_pass",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_result_intake_not_proven(result=None, summary_fragment=None):
    # result intake 只摄取现场补测结果的安全摘要；真实路线、电梯、人协助、硬件和交付成功继续外部证明。
    result = result if isinstance(result, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(result.get("not_proven"), list):
        source_values.extend(result.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_result_reconciliation_not_proven(reconciliation=None, summary_fragment=None):
    # reconciliation 只核对 result intake 与补测材料摘要；不能升级成真实路线、ACK、Nav2、HIL 或送达结论。
    reconciliation = reconciliation if isinstance(reconciliation, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(reconciliation.get("not_proven"), list):
        source_values.extend(reconciliation.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_material_pack_not_proven(pack=None, summary_fragment=None):
    # material pack 只把补测材料包安全摘要投到 diagnostics；真实动作、ACK、Nav2/HIL 和送达结论继续外部证明。
    pack = pack if isinstance(pack, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(pack.get("not_proven"), list):
        source_values.extend(pack.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_material_callback_packet_not_proven(
    packet=None,
    summary_fragment=None,
):
    # callback packet 只证明“回执包摘要可被 Robot 读取”，不把任何动作、现场或硬件结论带入 diagnostics。
    packet = packet if isinstance(packet, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(packet.get("not_proven"), list):
        source_values.extend(packet.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "robot_command_control",
        "remote_completion",
        "navigation_or_hardware_proof",
        "real_world_delivery",
        "phone_action_enablement",
        "production_readiness",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _route_task_field_retest_material_callback_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # material callback review decision 只复核材料回执是否可继续补测；不能变成控制、现场或硬件证明。
    decision = decision if isinstance(decision, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(decision.get("not_proven"), list):
        source_values.extend(decision.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "material_callback_review_decision_only",
        "rerun_command_executed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_phone_device_or_browser_proof",
        "production_readiness",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _route_task_field_retest_operator_drill_not_proven(drill=None, summary_fragment=None):
    # operator drill 只描述下一步人工演练，不证明现场动作、ACK、Nav2、HIL 或交付结果。
    drill = drill if isinstance(drill, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(drill.get("not_proven"), list):
        source_values.extend(drill.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "operator_callback_completed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_drill_console_not_proven(console=None, summary_fragment=None):
    # drill console 只把 PC/Robot 可读摘要搬到 diagnostics；真实控制和现场通过必须继续由外部证据证明。
    console = console if isinstance(console, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(console.get("not_proven"), list):
        source_values.extend(console.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "operator_callback_completed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_acceptance_brief_not_proven(brief=None, summary_fragment=None):
    # acceptance brief 是现场验收前的 metadata-only 简报；它不能证明路线、电梯、投放或交付完成。
    brief = brief if isinstance(brief, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(brief.get("not_proven"), list):
        source_values.extend(brief.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "acceptance_pass",
        "required_evidence_packet_completed",
        "owner_handoff_completed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_acceptance_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # acceptance review decision 只把验收简报复核成下一步建议；不能证明现场验收、动作或交付完成。
    decision = decision if isinstance(decision, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(decision.get("not_proven"), list):
        source_values.extend(decision.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "acceptance_review_decision_only",
        "material_backfill_completed",
        "owner_handoff_completed",
        "rerun_command_executed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_acceptance_execution_pack_not_proven(
    pack=None,
    summary_fragment=None,
):
    # acceptance execution pack 只是现场复跑执行材料；Robot 侧不能把 checklist 或 rerun commands 当作实跑结果。
    pack = pack if isinstance(pack, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(pack.get("not_proven"), list):
        source_values.extend(pack.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "acceptance_execution_pack_only",
        "owner_checklist_executed",
        "safe_evidence_bundle_collected",
        "review_decision_source_verified",
        "rerun_command_executed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_acceptance_execution_callback_intake_not_proven(
    intake=None,
    summary_fragment=None,
):
    # acceptance execution callback intake 只摄取现场 owner 的安全回执；不能证明现场执行、ACK、Nav2 或 HIL。
    intake = intake if isinstance(intake, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(intake.get("not_proven"), list):
        source_values.extend(intake.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "acceptance_execution_callback_intake_only",
        "acceptance_execution_pack_executed",
        "safe_callback_packet_verified",
        "owner_next_steps_completed",
        "rerun_command_executed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_evidence_dispatch_not_proven(dispatch=None, summary_fragment=None):
    # evidence dispatch 只分发现场证据包责任和文件名建议；Robot diagnostics 不把它升级为动作或交付结论。
    dispatch = dispatch if isinstance(dispatch, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(dispatch.get("not_proven"), list):
        source_values.extend(dispatch.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "acceptance_pass",
        "evidence_packet_dispatched_to_field_team",
        "operator_callback_completed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_callback_intake_not_proven(intake=None, summary_fragment=None):
    # callback intake 只摄取已消毒的现场回执元数据；收到文件名不等于真实路线、电梯、投放或交付通过。
    intake = intake if isinstance(intake, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(intake.get("not_proven"), list):
        source_values.extend(intake.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "acceptance_pass",
        "operator_callback_completed",
        "sanitized_callback_only",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_callback_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # review decision 只复核回执摘要是否能进入下一层 result intake；它不是动作、ACK、Nav2/HIL 或送达证明。
    decision = decision if isinstance(decision, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(decision.get("not_proven"), list):
        source_values.extend(decision.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "operator_callback_completed",
        "callback_review_decision_only",
        "result_intake_completion",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_review_result_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # review-result handoff 只是把复核结论交给后续材料/结果回填 owner；它不能证明动作、送达或现场补测完成。
    handoff = handoff if isinstance(handoff, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(handoff.get("not_proven"), list):
        source_values.extend(handoff.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "review_result_handoff_only",
        "result_intake_completion",
        "owner_handoff_completion",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_result_acceptance_packet_not_proven(packet=None, summary_fragment=None):
    # acceptance packet 只是把 result reconciliation 缺口转成现场验收包；真实通过、ACK、控制和交付结果继续外部证明。
    packet = packet if isinstance(packet, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(packet.get("not_proven"), list):
        source_values.extend(packet.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "acceptance_packet_pass",
        "pass_fail_criteria_result",
        "rerun_command_executed",
        "owner_handoff_completed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_result_acceptance_backfill_not_proven(
    backfill=None,
    summary_fragment=None,
):
    # backfill 只是把现场材料缺口回填到同一 evidence_ref 摘要；真实现场、动作和送达仍必须外部证明。
    backfill = backfill if isinstance(backfill, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(backfill.get("not_proven"), list):
        source_values.extend(backfill.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "acceptance_packet_pass",
        "acceptance_backfill_pass",
        "material_backfill_completed",
        "rerun_command_executed",
        "owner_handoff_completed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_result_backfill_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # review decision 只读复核材料是否可进入下一轮证据收集；真实交付和机器人动作仍必须外部证明。
    decision = decision if isinstance(decision, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(decision.get("not_proven"), list):
        source_values.extend(decision.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "review_decision_execution",
        "owner_handoff_completed",
        "rerun_command_executed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_result_review_dispatch_not_proven(summary_fragment=None):
    # result review dispatch 只读分发复核材料和回调要求；真实动作、ACK、HIL 和送达仍必须由外部证据证明。
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "result_review_dispatch_pass",
        "callback_packet_completed",
        "owner_work_order_completed",
        "rerun_command_executed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_result_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # result review decision 只把 review intake 复核成下一步建议；不能变成真实现场或控制证明。
    decision = decision if isinstance(decision, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(decision.get("not_proven"), list):
        source_values.extend(decision.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "result_review_decision_only",
        "result_acceptance_backfill_completed",
        "owner_handoff_completed",
        "rerun_command_executed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_result_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # result review handoff 只把复核结论交接给 owner；不能证明现场、ACK、控制、Nav2/HIL 或交付完成。
    handoff = handoff if isinstance(handoff, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(handoff.get("not_proven"), list):
        source_values.extend(handoff.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "result_review_handoff_only",
        "owner_work_order_completed",
        "material_callback_completed",
        "rerun_package_executed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_result_callback_intake_not_proven(summary_fragment=None):
    # result callback intake 只读回执摄取摘要；ready 也不能代表现场送达、ACK、Nav2 或 HIL 成立。
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "result_callback_intake_pass",
        "result_review_decision_pass",
        "owner_follow_up_completed",
        "review_decision_handoff_completed",
        "rerun_command_executed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_result_callback_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # result callback review decision 只把回执摄取结果转成复核建议；不能变成动作、ACK、Nav2/HIL 或交付证明。
    decision = decision if isinstance(decision, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(decision.get("not_proven"), list):
        source_values.extend(decision.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "result_callback_review_decision_only",
        "result_review_completion",
        "owner_handoff_completed",
        "rerun_command_executed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_acceptance_execution_callback_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # acceptance execution callback review decision 只把回执 intake 转成复核建议，不能代表真实送达或动作授权。
    decision = decision if isinstance(decision, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(decision.get("not_proven"), list):
        source_values.extend(decision.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "acceptance_execution_callback_review_decision_only",
        "acceptance_execution_review_completion",
        "owner_handoff_completed",
        "next_required_evidence_collected",
        "rerun_command_executed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_acceptance_execution_callback_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # callback review handoff 只把复核决策交给后续 owner；不能证明现场、ACK、控制或交付完成。
    handoff = handoff if isinstance(handoff, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(handoff.get("not_proven"), list):
        source_values.extend(handoff.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "acceptance_execution_callback_review_handoff_only",
        "acceptance_execution_review_completion",
        "owner_handoff_completed",
        "next_required_evidence_collected",
        "rerun_command_executed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_result_callback_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # handoff 只把 result callback review decision 交给后续 owner；不能证明现场、ACK、控制或交付完成。
    handoff = handoff if isinstance(handoff, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(handoff.get("not_proven"), list):
        source_values.extend(handoff.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "result_callback_review_handoff_only",
        "result_review_completion",
        "owner_follow_up_completed",
        "review_ready_package_executed",
        "rerun_package_executed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_acceptance_execution_handoff_intake_not_proven(
    intake=None,
    summary_fragment=None,
):
    # handoff intake 只摄取 owner 交接元数据；真实交付、控制面、ACK 和现场结果必须继续外部证明。
    intake = intake if isinstance(intake, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(intake.get("not_proven"), list):
        source_values.extend(intake.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_retest_pass",
        "route_elevator_field_result",
        "handoff_intake_only",
        "owner_acknowledgement_completed",
        "next_required_evidence_collected",
        "rerun_command_executed",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_acceptance_execution_rerun_queue_not_proven(
    queue=None,
    summary_fragment=None,
):
    # rerun queue 只是把 Autonomy 的受控复跑排队元数据带给 Robot diagnostics，不代表现场复跑已经发生。
    queue = queue if isinstance(queue, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(queue.get("not_proven"), list):
        source_values.extend(queue.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "controlled_field_rerun_executed",
        "rerun_queue_execution",
        "rerun_command_executed",
        "route_elevator_field_result",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_acceptance_execution_rerun_result_intake_not_proven(
    intake=None,
    summary_fragment=None,
):
    # rerun result intake 只转发 Autonomy 的安全摘要；真实复跑、投放和取消结果仍必须外部证明。
    intake = intake if isinstance(intake, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(intake.get("not_proven"), list):
        source_values.extend(intake.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "controlled_field_rerun_executed",
        "rerun_result_intake_only",
        "route_elevator_field_result",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_acceptance_execution_rerun_result_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # review decision 只把 Autonomy 的复跑结果判定带到 diagnostics，不代表 Robot 已执行或验收现场结果。
    decision = decision if isinstance(decision, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(decision.get("not_proven"), list):
        source_values.extend(decision.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "human_assistance_outcome",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "controlled_field_rerun_executed",
        "rerun_result_review_decision_only",
        "route_elevator_field_result",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _route_task_field_retest_acceptance_execution_rerun_result_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # handoff 只转发 Autonomy 安全摘要；source=software_proof 不等于 Robot runtime 或交付结果。
    values = _route_task_field_retest_acceptance_execution_rerun_result_review_decision_not_proven(
        handoff,
        summary_fragment,
    )
    for item in (
        "rerun_result_review_handoff_only",
        "acceptance_execution_rerun_result_owner_handoff_only",
        "route_completion_not_verified",
    ):
        if item not in values:
            values.append(item)
    return values


def _route_task_field_retest_result_review_intake_not_proven(
    intake=None,
    summary_fragment=None,
):
    # review intake 只消费 Autonomy 的安全摘要；不能证明路线、电梯、ACK、硬件或交付完成。
    intake = intake if isinstance(intake, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(intake.get("not_proven"), list):
        source_values.extend(intake.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "route_task_result_review_completion",
        "route_task_completion_real_world",
        "real_fixed_route_collection",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_phone_device_or_browser_proof",
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


def _default_route_task_field_retest_execution_pack_summary(
    path,
    execution_status="blocked_missing_route_task_field_retest_execution_pack",
    read_error="",
):
    # retest execution pack 默认就是 fail-closed；缺 source 时也必须输出完整 false 栅栏，方便手机/diagnostics 只读展示。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "execution_status": execution_status,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "required_field_materials_summary": {
            "status": "blocked",
            "reason": "route-task field retest execution pack is not configured",
            "items": [],
        },
        "rerun_commands_summary": [],
        "operator_handoff": {},
        "field_retest_checklist": [],
        "boundary": ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_GATE,
        "not_proven": _route_task_field_retest_execution_pack_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field retest execution pack is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        "safe_phone_copy": "Route-task field retest execution pack is metadata-only; delivery_success=false; primary_actions_enabled=false.",
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_session_handoff_summary(
    path,
    handoff_status="blocked_missing_route_task_field_retest_session_handoff",
    read_error="",
):
    # session handoff 默认 fail-closed，避免缺少 Task A artifact 时手机端误以为可以继续现场动作。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "handoff_status": {
            "status": handoff_status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field retest session handoff is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "session_owner": "",
        "required_field_materials_summary": {
            "status": "blocked",
            "reason": "route-task field retest session handoff is not configured",
            "items": [],
        },
        "material_placeholders_summary": [],
        "rerun_commands_summary": [],
        "operator_next_steps": [],
        "field_callback_checklist": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest session handoff is not configured",
        },
        "mobile_readonly_summary": {
            "safe_copy": "Route-task field retest session handoff is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_phone_copy": "Route-task field retest session handoff is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_GATE,
        "not_proven": _route_task_field_retest_session_handoff_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field retest session handoff is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        "safe_phone_copy": "Route-task field retest session handoff is metadata-only; delivery_success=false; primary_actions_enabled=false.",
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_result_intake_summary(
    path,
    result_status="blocked_missing_route_task_field_retest_result_intake",
    read_error="",
):
    # result intake 默认关闭所有动作，因为它只用于现场结果回填摘要，不是机器人控制或成功凭据。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "result_status": {
            "status": result_status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field retest result intake is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "door_state": "not_proven",
        "target_floor_confirmation": "not_proven",
        "human_assistance_note": "",
        "result_materials_summary": {
            "status": "blocked",
            "reason": "route-task field retest result intake is not configured",
            "items": [],
        },
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest result intake is not configured",
        },
        "mobile_readonly_summary": {
            "safe_copy": "Route-task field retest result intake is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_phone_copy": "Route-task field retest result intake is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_GATE,
        "not_proven": _route_task_field_retest_result_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field retest result intake is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        "safe_phone_copy": "Route-task field retest result intake is metadata-only; delivery_success=false; primary_actions_enabled=false.",
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_result_reconciliation_summary(
    path,
    result_status="blocked_missing_route_task_field_retest_result_reconciliation",
    read_error="",
):
    # result reconciliation 默认就是 fail-closed；缺 artifact 时也不能暴露 raw result 或激活动作面。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "reconciliation_status": {
            "status": result_status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field retest result reconciliation is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "result_intake_summary": {
            "status": "blocked",
            "reason": "route-task field retest result reconciliation is not configured",
        },
        "result_reconciliation_summary": {
            "status": "blocked",
            "reason": "route-task field retest result reconciliation is not configured",
        },
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest result reconciliation is not configured",
        },
        "mobile_readonly_summary": {
            "safe_copy": "Route-task field retest result reconciliation is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_phone_copy": "Route-task field retest result reconciliation is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_GATE,
        "not_proven": _route_task_field_retest_result_reconciliation_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field retest result reconciliation is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        "safe_phone_copy": "Route-task field retest result reconciliation is metadata-only; delivery_success=false; primary_actions_enabled=false.",
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_material_pack_summary(
    path,
    material_status="blocked_missing_route_task_field_retest_material_pack",
    read_error="",
):
    # material pack 默认 fail-closed，因为缺少现场材料摘要时不能推导 collect/dropoff/cancel 或 Nav2/HIL 成功。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "material_status": {
            "status": material_status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field retest material pack is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "material_completeness": {
            "status": "blocked",
            "reason": "route-task field retest material pack is not configured",
        },
        "missing_materials": [],
        "rejected_materials": [],
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest material pack is not configured",
        },
        "mobile_readonly_summary": {
            "safe_copy": "Route-task field retest material pack is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_phone_copy": "Route-task field retest material pack is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_GATE,
        "not_proven": _route_task_field_retest_material_pack_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field retest material pack is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        "safe_phone_copy": "Route-task field retest material pack is metadata-only; delivery_success=false; primary_actions_enabled=false.",
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_material_callback_packet_summary(
    path,
    packet_status="blocked_missing_route_task_field_retest_material_callback_packet",
    read_error="",
):
    # callback packet 默认只给 blocked metadata；缺 summary 时不能推导现场回执、动作放行或交付完成。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "packet_status": {
            "status": packet_status,
            "verdict": "not_proven",
            "reason": (
                read_error
                or "route-task field retest material callback packet is not configured"
            ),
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "owner_follow_up": [],
        "review_decision_handoff": {},
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest material callback packet is not configured",
        },
        "mobile_readonly_summary": {
            "safe_copy": (
                "Route-task field retest material callback packet is metadata-only; "
                "same_evidence_ref_required=true; delivery_success=false; "
                "primary_actions_enabled=false."
            ),
            "safe_phone_copy": (
                "Route-task field retest material callback packet is metadata-only; "
                "same_evidence_ref_required=true; delivery_success=false; "
                "primary_actions_enabled=false."
            ),
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_GATE,
        "not_proven": _route_task_field_retest_material_callback_packet_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest material callback packet is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; "
            "primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest material callback packet is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; "
            "primary_actions_enabled=false."
        ),
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _default_route_task_field_retest_material_callback_review_decision_summary(
    path,
    decision_status="blocked_missing_route_task_field_retest_material_callback_review_decision",
    read_error="",
):
    # 缺 review decision 时必须默认 blocked；Robot 不能凭空推导 Start/Confirm/Cancel 或现场补测结论。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "review_status": {
            "status": decision_status,
            "verdict": "not_proven",
            "reason": (
                read_error
                or "route-task field retest material callback review decision is not configured"
            ),
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "review_decision": "blocked_material_callback_review_not_proven",
        "material_callback_review_summary": {
            "status": "blocked",
            "reason": "route-task field retest material callback review decision is not configured",
        },
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "owner_acknowledgement": {
            "status": "blocked",
            "reason": "route-task field retest material callback review decision is not configured",
        },
        "owner_next_steps": [],
        "next_required_evidence": [],
        "rerun_commands": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest material callback review decision is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_GATE,
        "not_proven": _route_task_field_retest_material_callback_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest material callback review decision is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; "
            "primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest material callback review decision is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; "
            "primary_actions_enabled=false."
        ),
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "production_ready": False,
    }


def _default_route_task_field_retest_operator_drill_summary(
    path,
    drill_status="blocked_missing_route_task_field_retest_operator_drill",
    read_error="",
):
    # operator drill 默认 fail closed；缺失演练摘要时，Robot diagnostics 不能推导任何可执行动作。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "drill_status": {
            "status": drill_status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field retest operator drill is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "next_command_labels": [],
        "missing_material_prompts": [],
        "operator_callback_checklist": [],
        "safe_summary": {
            "summary": "Route-task field retest operator drill is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_copy": "Route-task field retest operator drill is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_phone_copy": "Route-task field retest operator drill is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        },
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest operator drill is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_GATE,
        "not_proven": _route_task_field_retest_operator_drill_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field retest operator drill is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        "safe_phone_copy": "Route-task field retest operator drill is metadata-only; delivery_success=false; primary_actions_enabled=false.",
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_drill_console_summary(
    path,
    console_status="blocked_missing_route_task_field_retest_drill_console",
    read_error="",
):
    # drill console 默认 fail closed；缺 artifact 或缺摘要时不能让 diagnostics 推导任何机器人动作。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "console_status": {
            "status": console_status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field retest drill console is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "command_labels": [],
        "safe_checklist": [],
        "missing_material_prompts": [],
        "operator_callback_checklist": [],
        "safe_summary": {
            "summary": "Route-task field retest drill console is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_copy": "Route-task field retest drill console is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_phone_copy": "Route-task field retest drill console is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        },
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest drill console is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_GATE,
        "not_proven": _route_task_field_retest_drill_console_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field retest drill console is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        "safe_phone_copy": "Route-task field retest drill console is metadata-only; delivery_success=false; primary_actions_enabled=false.",
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_acceptance_brief_summary(
    path,
    acceptance_status="blocked_missing_route_task_field_retest_acceptance_brief",
    read_error="",
):
    # acceptance brief 默认 fail closed；缺简报时 diagnostics 只能说明未证明，不能触发任何机器人动作。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "acceptance_status": {
            "status": acceptance_status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field retest acceptance brief is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "safe_summary": {
            "summary": "Route-task field retest acceptance brief is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_copy": "Route-task field retest acceptance brief is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_phone_copy": "Route-task field retest acceptance brief is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        },
        "pass_fail_criteria": [],
        "required_evidence_packet": [],
        "owner_handoff": {},
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest acceptance brief is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_GATE,
        "not_proven": _route_task_field_retest_acceptance_brief_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field retest acceptance brief is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        "safe_phone_copy": "Route-task field retest acceptance brief is metadata-only; delivery_success=false; primary_actions_enabled=false.",
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_acceptance_review_decision_summary(
    path,
    decision_status="blocked_missing_route_task_field_retest_acceptance_review_decision",
    read_error="",
):
    # acceptance review decision 默认 fail closed；缺 review 决策时不能把验收简报升级成现场结果。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "decision_status": {
            "status": decision_status,
            "verdict": "not_proven",
            "reason": read_error
            or "route-task field retest acceptance review decision is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "source_acceptance_brief_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": "route-task field retest acceptance review decision is not configured",
        },
        "review_decision": "blocked_missing_acceptance_brief_not_proven",
        "material_backfill_status": {},
        "missing_materials": [],
        "owner_handoff": {},
        "next_required_evidence": [],
        "rerun_commands": [],
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest acceptance review decision is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_GATE,
        "not_proven": _route_task_field_retest_acceptance_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest acceptance review decision is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest acceptance review decision is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_acceptance_execution_pack_summary(
    path,
    execution_pack_status="blocked_missing_route_task_field_retest_acceptance_execution_pack",
    read_error="",
):
    # execution pack 默认保持 blocked；没有 Autonomy 安全摘要时，Robot 不能推断现场复跑可执行或已通过。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "execution_pack_status": {
            "status": execution_pack_status,
            "verdict": "not_proven",
            "reason": read_error
            or "route-task field retest acceptance execution pack is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "review_decision_source": {},
        "owner_checklist": [],
        "rerun_commands": [],
        "safe_evidence_bundle": {},
        "required_route_elevator_materials": [],
        "handoff_owner": "",
        "next_required_evidence": [],
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest acceptance execution pack is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_GATE,
        "not_proven": _route_task_field_retest_acceptance_execution_pack_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest acceptance execution pack is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest acceptance execution pack is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_acceptance_execution_callback_intake_summary(
    path,
    intake_status="blocked_missing_route_task_field_retest_acceptance_execution_callback_intake",
    read_error="",
):
    # 默认 blocked 是为了让 diagnostics 在缺少 Autonomy 回执时保持只读，不推断现场验收或动作授权。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "callback_intake_status": {
            "status": intake_status,
            "verdict": "not_proven",
            "reason": read_error
            or "route-task field retest acceptance execution callback intake is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "source_execution_pack": {},
        "safe_callback_packet": {},
        "evidence_ref_status": {},
        "received_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "owner_next_steps": [],
        "next_required_evidence": [],
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": (
                "route-task field retest acceptance execution callback intake is not configured"
            ),
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_GATE,
        "not_proven": _route_task_field_retest_acceptance_execution_callback_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest acceptance execution callback intake is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest acceptance execution callback intake is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_evidence_dispatch_summary(
    path,
    dispatch_status="blocked_missing_route_task_field_retest_evidence_dispatch",
    read_error="",
):
    # 默认 summary 必须 fail closed；缺少派发材料时，只能说明 not_proven，不能打开任何机器人动作入口。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "dispatch_status": {
            "status": dispatch_status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field retest evidence dispatch is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "safe_summary": {
            "summary": "Route-task field retest evidence dispatch is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_copy": "Route-task field retest evidence dispatch is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_phone_copy": "Route-task field retest evidence dispatch is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        },
        "material_owners": {},
        "recommended_filenames": [],
        "backfill_order": [],
        "callback_checklist": [],
        "fail_closed_rerun_notes": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest evidence dispatch is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_GATE,
        "not_proven": _route_task_field_retest_evidence_dispatch_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field retest evidence dispatch is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        "safe_phone_copy": "Route-task field retest evidence dispatch is metadata-only; delivery_success=false; primary_actions_enabled=false.",
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_callback_intake_summary(
    path,
    intake_status="blocked_missing_route_task_field_retest_callback_intake",
    read_error="",
):
    # callback intake 默认 fail closed：没有安全回执摘要时，Robot 只能展示 metadata-only 缺口，不能打开动作面。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "intake_status": {
            "status": intake_status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field retest callback intake is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "same_evidence_ref_match": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": "route-task field retest callback intake is not configured",
        },
        "safe_summary": {
            "summary": "Route-task field retest callback intake is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_copy": "Route-task field retest callback intake is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_phone_copy": "Route-task field retest callback intake is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        },
        "received_filenames_summary": [],
        "missing_materials": [],
        "next_backfill_action": "not_proven",
        "callback_checklist_result": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": "route-task field retest callback intake is not configured",
        },
        "robot_compatible_summary": {
            "status": "blocked",
            "reason": "route-task field retest callback intake is not configured",
        },
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest callback intake is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_GATE,
        "not_proven": _route_task_field_retest_callback_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field retest callback intake is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        "safe_phone_copy": "Route-task field retest callback intake is metadata-only; delivery_success=false; primary_actions_enabled=false.",
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_callback_review_decision_summary(
    path,
    decision_status="blocked_missing_route_task_field_retest_callback_review_decision",
    read_error="",
):
    # review decision 默认 fail closed；缺少安全摘要时只能说明 blocked/not_proven，不能解锁 result intake 或机器人动作。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "review_status": {
            "status": decision_status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field retest callback review decision is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "source_intake_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": "route-task field retest callback review decision is not configured",
        },
        "review_decision": "unsupported_callback_schema",
        "blocked_reasons": ["blocked_missing_route_task_field_retest_callback_review_decision"],
        "next_required_evidence": [],
        "result_intake_readiness": {
            "status": "blocked",
            "reason": "route-task field retest callback review decision is not configured",
        },
        "owner_handoff": "Robot",
        "safe_summary": {
            "summary": "Route-task field retest callback review decision is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_copy": "Route-task field retest callback review decision is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_phone_copy": "Route-task field retest callback review decision is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        },
        "robot_compatible_summary": {
            "status": "blocked",
            "reason": "route-task field retest callback review decision is not configured",
        },
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest callback review decision is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_GATE,
        "not_proven": _route_task_field_retest_callback_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field retest callback review decision is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        "safe_phone_copy": "Route-task field retest callback review decision is metadata-only; delivery_success=false; primary_actions_enabled=false.",
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_review_result_handoff_summary(
    path,
    handoff_status="blocked_missing_route_task_field_retest_review_result_handoff",
    read_error="",
):
    # handoff 默认缺材料时必须 fail closed；Robot 只能展示交接缺口，不能把它当成 result、ACK 或动作授权。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "handoff_status": {
            "status": handoff_status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field retest review result handoff is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "same_evidence_ref_match": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": "route-task field retest review result handoff is not configured",
        },
        "source_review_decision": "unsupported_review_result_handoff_schema",
        "result_intake_readiness": {
            "status": "blocked",
            "reason": "route-task field retest review result handoff is not configured",
        },
        "required_materials": [],
        "owner_handoff": "Robot",
        "blocked_reasons": ["blocked_missing_route_task_field_retest_review_result_handoff"],
        "safe_summary": {
            "summary": "Route-task field retest review result handoff is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_copy": "Route-task field retest review result handoff is metadata-only; delivery_success=false; primary_actions_enabled=false.",
            "safe_phone_copy": "Route-task field retest review result handoff is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        },
        "control_boundary": {
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        "robot_compatible_summary": {
            "status": "blocked",
            "reason": "route-task field retest review result handoff is not configured",
        },
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest review result handoff is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_GATE,
        "not_proven": _route_task_field_retest_review_result_handoff_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field retest review result handoff is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        "safe_phone_copy": "Route-task field retest review result handoff is metadata-only; delivery_success=false; primary_actions_enabled=false.",
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_result_acceptance_packet_summary(
    path,
    packet_status="blocked_missing_route_task_field_retest_result_acceptance_packet",
    read_error="",
):
    # acceptance packet 默认 fail closed；缺 packet 时只能展示未证明，不能推导现场验收或送达结果。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "packet_status": {
            "status": packet_status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field retest result acceptance packet is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "missing_material_summary": {
            "status": "blocked",
            "reason": "route-task field retest result acceptance packet is not configured",
        },
        "owner_handoff": {},
        "rerun_command_summary": [],
        "pass_fail_criteria_summary": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest result acceptance packet is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_GATE,
        "not_proven": _route_task_field_retest_result_acceptance_packet_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field retest result acceptance packet is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        "safe_phone_copy": "Route-task field retest result acceptance packet is metadata-only; delivery_success=false; primary_actions_enabled=false.",
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_result_acceptance_backfill_summary(
    path,
    backfill_status="blocked_missing_route_task_field_retest_result_acceptance_backfill",
    read_error="",
):
    # backfill 默认 fail closed；缺 artifact/summary 时只能暴露 blocked/not_proven 诊断元数据。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "backfill_status": {
            "status": backfill_status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field retest result acceptance backfill is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "material_completeness_summary": {
            "status": "blocked",
            "reason": "route-task field retest result acceptance backfill is not configured",
        },
        "alignment_status": {
            "status": "blocked",
            "reason": "route-task field retest result acceptance backfill is not configured",
        },
        "missing_rejected_category_summary": {
            "missing": [],
            "rejected": [],
            "reason": "route-task field retest result acceptance backfill is not configured",
        },
        "owner_handoff": {},
        "rerun_command_summary": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest result acceptance backfill is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_GATE,
        "not_proven": _route_task_field_retest_result_acceptance_backfill_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field retest result acceptance backfill is metadata-only; delivery_success=false; primary_actions_enabled=false.",
        "safe_phone_copy": "Route-task field retest result acceptance backfill is metadata-only; delivery_success=false; primary_actions_enabled=false.",
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_result_backfill_review_decision_summary(
    path,
    decision_status="blocked_missing_route_task_field_retest_result_backfill_review_decision",
    read_error="",
):
    # review decision 默认保持 fail closed，避免缺输入时被误当成可执行的复测结论。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "review_decision": {
            "status": decision_status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field retest result backfill review decision is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "material_status": {
            "status": "blocked",
            "reason": "route-task field retest result backfill review decision is not configured",
        },
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "owner_handoff": {},
        "next_required_evidence": [],
        "rerun_commands": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest result backfill review decision is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_GATE,
        "not_proven": _route_task_field_retest_result_backfill_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest result backfill review decision is metadata-only; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest result backfill review decision is metadata-only; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_result_review_dispatch_summary(
    path,
    dispatch_status="blocked_missing_route_task_field_retest_result_review_dispatch",
    read_error="",
):
    # dispatch 默认 fail closed；没有 Autonomy 安全 summary 时只能提供 blocked/not_proven 元数据。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "dispatch_status": {
            "status": dispatch_status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field retest result review dispatch is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "owner_work_orders": {},
        "callback_packet_requirements": {},
        "rerun_commands": [],
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest result review dispatch is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH_GATE,
        "not_proven": _route_task_field_retest_result_review_dispatch_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest result review dispatch is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest result review dispatch is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_result_review_decision_summary(
    path,
    decision_status="blocked_missing_route_task_field_retest_result_review_decision",
    read_error="",
):
    # result review decision 默认 fail closed；缺 source 时不能把 review intake 推成真实验收或机器人动作。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "decision_status": {
            "status": decision_status,
            "verdict": "not_proven",
            "reason": read_error
            or "route-task field retest result review decision is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "source_review_intake_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": "route-task field retest result review decision is not configured",
        },
        "review_decision": "blocked_missing_result_review_intake_not_proven",
        "missing_materials": [],
        "owner_handoff": {},
        "next_required_evidence": [],
        "rerun_commands": [],
        "review_ready_package": {},
        "rerun_package": {},
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest result review decision is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_GATE,
        "not_proven": _route_task_field_retest_result_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest result review decision is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest result review decision is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_result_review_handoff_summary(
    path,
    handoff_status="blocked_missing_route_task_field_retest_result_review_handoff",
    read_error="",
):
    # result review handoff 默认 fail closed；Robot diagnostics 只呈现 owner 交接元数据，不打开控制路径。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "handoff_status": {
            "status": handoff_status,
            "verdict": "not_proven",
            "reason": read_error
            or "route-task field retest result review handoff is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "source_review_decision_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": "route-task field retest result review handoff is not configured",
        },
        "owner_work_orders": [],
        "accepted_reasons": [],
        "blocked_reasons": ["blocked_missing_route_task_field_retest_result_review_handoff"],
        "rerun_reasons": [],
        "same_evidence_ref_package": {},
        "next_material_callback_requirements": [],
        "next_required_evidence": [],
        "rerun_commands": [],
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest result review handoff is not configured",
        },
        "robot_compatible_summary": {
            "status": "blocked",
            "reason": "route-task field retest result review handoff is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_GATE,
        "not_proven": _route_task_field_retest_result_review_handoff_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest result review handoff is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest result review handoff is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_result_callback_intake_summary(
    path,
    intake_status="blocked_missing_route_task_field_retest_result_callback_intake",
    read_error="",
):
    # callback intake 默认 fail closed；没有 PC 安全 summary 时只暴露不可操作的 diagnostics 元数据。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "intake_status": {
            "status": intake_status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field retest result callback intake is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "accepted_materials": [],
        "accepted_updates": [],
        "missing_materials": [],
        "missing_updates": [],
        "rejected_materials": [],
        "rejected_updates": [],
        "owner_follow_up": [],
        "review_decision_handoff": {},
        "rerun_commands": [],
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest result callback intake is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_GATE,
        "not_proven": _route_task_field_retest_result_callback_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest result callback intake is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest result callback intake is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_result_callback_review_decision_summary(
    path,
    review_status="blocked_missing_route_task_field_retest_result_callback_review_decision",
    read_error="",
):
    # result callback review decision 默认缺源时 fail closed；Robot 只展示下一步建议，不解锁任何控制链路。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "review_status": {
            "status": review_status,
            "verdict": "not_proven",
            "reason": read_error
            or "route-task field retest result callback review decision is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "source_callback_intake_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": "route-task field retest result callback review decision is not configured",
        },
        "review_decision": "needs_callback_rerun",
        "material_status": {
            "status": "blocked",
            "reason": "route-task field retest result callback review decision is not configured",
        },
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "owner_handoff": {},
        "next_required_evidence": [],
        "rerun_commands": [],
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest result callback review decision is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_GATE,
        "not_proven": _route_task_field_retest_result_callback_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest result callback review decision is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest result callback review decision is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_acceptance_execution_callback_review_decision_summary(
    path,
    review_status=(
        "blocked_missing_route_task_field_retest_acceptance_execution_callback_review_decision"
    ),
    read_error="",
):
    # acceptance execution callback review decision 默认只读；缺源时必须保持 not_proven 和动作关闭。
    return {
        "schema": (
            ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_GATE
        ),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "review_status": {
            "status": review_status,
            "verdict": "not_proven",
            "reason": read_error
            or (
                "route-task field retest acceptance execution callback review decision "
                "is not configured"
            ),
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "source_callback_intake_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": (
                "route-task field retest acceptance execution callback review decision "
                "is not configured"
            ),
        },
        "review_decision": "needs_acceptance_execution_callback_rerun",
        "owner_handoff": {},
        "next_required_evidence": [],
        "rerun_commands": [],
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": (
                "route-task field retest acceptance execution callback review decision "
                "is not configured"
            ),
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_GATE,
        "not_proven": (
            _route_task_field_retest_acceptance_execution_callback_review_decision_not_proven()
        ),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest acceptance execution callback review decision "
            "is metadata-only; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest acceptance execution callback review decision "
            "is metadata-only; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_acceptance_execution_callback_review_handoff_summary(
    path,
    handoff_status=(
        "blocked_missing_route_task_field_retest_acceptance_execution_callback_review_handoff"
    ),
    read_error="",
):
    # callback review handoff 默认缺源时必须 fail-closed，避免被前端或 diagnostics 当成现场闭环。
    return {
        "schema": (
            ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE
        ),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "handoff_status": {
            "status": handoff_status,
            "verdict": "not_proven",
            "reason": read_error
            or (
                "route-task field retest acceptance execution callback review handoff "
                "is not configured"
            ),
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "source_review_decision_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": (
                "route-task field retest acceptance execution callback review handoff "
                "is not configured"
            ),
        },
        "source_review_decision": "needs_acceptance_execution_callback_rerun",
        "owner_handoff": {},
        "next_required_evidence": [],
        "safe_rerun_hint": [],
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": (
                "route-task field retest acceptance execution callback review handoff "
                "is not configured"
            ),
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE,
        "not_proven": (
            _route_task_field_retest_acceptance_execution_callback_review_handoff_not_proven()
        ),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest acceptance execution callback review handoff "
            "is metadata-only; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest acceptance execution callback review handoff "
            "is metadata-only; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_acceptance_execution_handoff_intake_summary(
    path,
    intake_status="blocked_missing_route_task_field_retest_acceptance_execution_handoff_intake",
    read_error="",
):
    # 默认摘要固定 fail-closed，避免缺源时让 diagnostics 或手机端误认为已经有现场执行结果。
    reason = read_error or "route-task field retest acceptance execution handoff intake is not configured"
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "intake_status": {"status": intake_status, "verdict": "not_proven", "reason": reason},
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "owner_acknowledgement": {},
        "next_evidence_flags": [],
        "next_required_evidence": [],
        "safe_rerun_hint": [],
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_GATE,
        "not_proven": _route_task_field_retest_acceptance_execution_handoff_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest acceptance execution handoff intake is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest acceptance execution handoff intake is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_acceptance_execution_rerun_queue_summary(
    path,
    queue_status="blocked_missing_route_task_field_retest_acceptance_execution_rerun_queue",
    read_error="",
):
    # 缺少 Autonomy queue summary 时必须 fail-closed，Robot diagnostics 不能自行补造复跑队列状态。
    reason = read_error or "route-task field retest acceptance execution rerun queue is not configured"
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "queue_status": {"status": queue_status, "verdict": "not_proven", "reason": reason},
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "source_handoff_intake_status": {},
        "owner_handoff": {},
        "next_required_evidence": [],
        "safe_rerun_hint": [],
        "blocked_reason": reason,
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_GATE,
        "not_proven": _route_task_field_retest_acceptance_execution_rerun_queue_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest acceptance execution rerun queue is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest acceptance execution rerun queue is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_acceptance_execution_rerun_result_intake_summary(
    path,
    intake_status="blocked_missing_route_task_field_retest_acceptance_execution_rerun_result_intake",
    read_error="",
):
    # 缺少 Autonomy sanitized summary 时默认 blocked；Robot 不读取 raw artifact 也不推断复跑结果。
    reason = (
        read_error
        or "route-task field retest acceptance execution rerun result intake is not configured"
    )
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "intake_status": {"status": intake_status, "verdict": "not_proven", "reason": reason},
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "owner_handoff": {},
        "next_required_evidence": [],
        "boundary_flags": {
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "raw_artifact_consumed": False,
            "control_entrypoint_enabled": False,
        },
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_GATE,
        "not_proven": (
            _route_task_field_retest_acceptance_execution_rerun_result_intake_not_proven()
        ),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest acceptance execution rerun result intake is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest acceptance execution rerun result intake is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary(
    path,
    decision_status=(
        "blocked_missing_route_task_field_retest_acceptance_execution_rerun_result_review_decision"
    ),
    read_error="",
):
    # 缺少 Autonomy sanitized decision 时默认 blocked；Robot 不读取 raw artifact，也不开放复跑控制。
    reason = (
        read_error
        or (
            "route-task field retest acceptance execution rerun result review decision "
            "is not configured"
        )
    )
    return {
        "schema": (
            ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_GATE
        ),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "decision_status": {"status": decision_status, "verdict": "not_proven", "reason": reason},
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "review_decision": "blocked_missing_acceptance_execution_rerun_result_review_decision",
        "owner_handoff": {},
        "next_required_evidence": [],
        "boundary_flags": {
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "raw_artifact_consumed": False,
            "control_entrypoint_enabled": False,
        },
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "boundary": (
            ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_GATE
        ),
        "not_proven": (
            _route_task_field_retest_acceptance_execution_rerun_result_review_decision_not_proven()
        ),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest acceptance execution rerun result review decision "
            "is metadata-only; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest acceptance execution rerun result review decision "
            "is metadata-only; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary(
    path,
    handoff_status=(
        "blocked_missing_route_task_field_retest_acceptance_execution_rerun_result_review_handoff"
    ),
    read_error="",
):
    # 缺省值必须 fail closed；Robot diagnostics 不读取 raw artifact，也不新增 Start/Dropoff/Cancel 入口。
    reason = (
        read_error
        or (
            "route-task field retest acceptance execution rerun result review handoff "
            "is not configured"
        )
    )
    return {
        "schema": (
            ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_GATE
        ),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "handoff_status": {"status": handoff_status, "verdict": "not_proven", "reason": reason},
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "owner_role": "",
        "owner_handoff": {},
        "next_required_evidence": [],
        "boundary_flags": {
            "metadata_only": True,
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "raw_artifact_consumed": False,
            "control_entrypoint_enabled": False,
        },
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "boundary": (
            ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_GATE
        ),
        "not_proven": (
            _route_task_field_retest_acceptance_execution_rerun_result_review_handoff_not_proven()
        ),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest acceptance execution rerun result review handoff "
            "is metadata-only; source=software_proof; not_proven; delivery_success=false; "
            "primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest acceptance execution rerun result review handoff "
            "is metadata-only; source=software_proof; not_proven; delivery_success=false; "
            "primary_actions_enabled=false."
        ),
        "metadata_only": True,
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_result_callback_review_handoff_summary(
    path,
    handoff_status="blocked_missing_route_task_field_retest_result_callback_review_handoff",
    read_error="",
):
    # handoff 默认缺源时必须 blocked；Robot diagnostics 只展示安全元数据，不推动 result review 或控制链路。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "handoff_status": {
            "status": handoff_status,
            "verdict": "not_proven",
            "reason": read_error
            or "route-task field retest result callback review handoff is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "source_review_decision": "needs_callback_rerun",
        "owner_follow_up": [],
        "review_ready_package": {},
        "rerun_package": {},
        "next_required_evidence": [],
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest result callback review handoff is not configured",
        },
        "robot_compatible_summary": {
            "status": "blocked",
            "reason": "route-task field retest result callback review handoff is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_GATE,
        "not_proven": _route_task_field_retest_result_callback_review_handoff_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest result callback review handoff is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest result callback review handoff is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_retest_result_review_intake_summary(
    path,
    intake_status="blocked_missing_route_task_field_retest_result_review_intake",
    read_error="",
):
    # 缺少 Autonomy summary 时默认 blocked/not_proven，避免 Robot diagnostics 猜测现场复核状态。
    return {
        "schema": ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "intake_status": {
            "status": intake_status,
            "verdict": "not_proven",
            "reason": read_error
            or "route-task field retest result review intake summary is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "missing_materials": [],
        "owner_follow_up": [],
        "review_ready_package": {},
        "rerun_package": {},
        "next_required_evidence": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field retest result review intake summary is not configured",
        },
        "robot_compatible_summary": {
            "status": "blocked",
            "reason": "route-task field retest result review intake summary is not configured",
        },
        "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_GATE,
        "not_proven": _route_task_field_retest_result_review_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Route-task field retest result review intake is metadata-only; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Route-task field retest result review intake is metadata-only; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _route_task_field_retest_execution_pack_has_success_wording(value):
    # 补测包允许解释 blocked/not_proven/false，但任何未防护的成功、ACK、Nav2/HIL 或完成措辞都要 fail closed。
    if isinstance(value, dict):
        return any(_route_task_field_retest_execution_pack_has_success_wording(item) for item in value.values())
    if isinstance(value, list):
        return any(_route_task_field_retest_execution_pack_has_success_wording(item) for item in value)
    if not isinstance(value, str):
        return False
    redacted = _redact_route_task_rehearsal_text(value)
    guarded = redacted.lower()
    for phrase in (
        "not delivery success",
        "delivery_success=false",
        "primary_actions_enabled=false",
        "not_proven",
        "not proven",
        "metadata-only",
        "must not",
        "not real",
        "不证明",
    ):
        guarded = guarded.replace(phrase, "")
    return (
        "delivery success" in guarded
        or "ack posted" in guarded
        or "remote ack" in guarded
        or "terminal ack" in guarded
        or "cursor advanced" in guarded
        or "nav2 started" in guarded
        or "hil pass" in guarded
        or "dropoff complete" in guarded
        or "cancel complete" in guarded
        or "primary actions enabled" in guarded
    )


def _route_task_field_retest_operator_drill_has_unsafe_fields(value):
    # operator drill 只能进入 Robot diagnostics 白名单摘要；review-decision 派生 raw 字段一律不透传。
    unsafe_key_fragments = (
        "authorization",
        "token",
        "secret",
        "access_key",
        "password",
        "credential",
        "checksum",
        "traceback",
        "raw_artifact",
        "raw_json",
        "raw_payload",
        "raw_response",
        "raw_robot",
        "raw_command",
        "raw_ack",
        "raw_route_log",
        "raw_nav2_log",
        "local_path",
        "file_path",
        "artifact_path",
        "ros_topic",
        "topic_name",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "command_envelope",
        "status_envelope",
    )
    unsafe_true_keys = {
        "delivery_success",
        "primary_actions_enabled",
        "ack_post_allowed",
        "remote_ack_allowed",
        "cursor_updates_allowed",
        "persistence_updates_allowed",
        "terminal_ack_allowed",
        "nav2_triggered",
        "hil_pass",
        "production_ready",
        "collect_triggered",
        "dropoff_triggered",
        "cancel_triggered",
        "dropoff_completion",
        "cancel_completion",
        "remote_ack_posted",
        "terminal_ack_posted",
        "start_enabled",
        "confirm_enabled",
        "cancel_enabled",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "not_proven":
                # not_proven 允许列出 real_serial_or_uart_feedback 等未证明项；它本身不是 raw 设备泄漏。
                continue
            if key_text in unsafe_true_keys and bool(item):
                return True
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _route_task_field_retest_operator_drill_has_unsafe_fields(item):
                return True
        return False
    if isinstance(value, list):
        return any(_route_task_field_retest_operator_drill_has_unsafe_fields(item) for item in value)
    if isinstance(value, str):
        redacted = _redact_route_task_rehearsal_text(value)
        lowered = redacted.lower()
        return (
            "/api/collect" in lowered
            or "/api/dropoff" in lowered
            or "/api/cancel" in lowered
            or "ack posted" in lowered
            or "remote ack" in lowered
            or "terminal ack" in lowered
            or "cursor advanced" in lowered
            or "raw artifact" in lowered
            or "raw command" in lowered
            or "ros topic" in lowered
            or "/cmd_vel" in lowered
            or "credential" in lowered
            or "serial" in lowered
            or "uart" in lowered
            or "nav2 started" in lowered
            or any(marker in redacted for marker in (
                "[REDACTED_AUTH_HEADER]",
                "Bearer [REDACTED]",
                "[REDACTED_URL]",
                "/dev/[REDACTED_SERIAL]",
                "[REDACTED_BAUD]",
                "[REDACTED_TRACEBACK]",
                "[REDACTED_LOCAL_PATH]",
            ))
        )
    return False


def _route_task_field_retest_execution_pack_source_contract(value):
    # retest execution pack 支持直接 artifact 或 summary wrapper；wrapper 必须回指同一 source/boundary 才能被 diagnostics 消费。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_session_handoff_source_contract(value):
    # 支持直接 artifact 或 summary wrapper；wrapper 必须回指本 handoff source/gate，不能混入 execution pack。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_result_intake_source_contract(value):
    # result intake 可来自直接 artifact 或已消毒 summary；wrapper 必须回指本 gate，避免混入 handoff/pack。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_result_reconciliation_source_contract(value):
    # result reconciliation 可直接消费 artifact 或 summary wrapper；wrapper 必须保留新 gate 的来源，避免误接旧 field-run reconciliation。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_result_reconciliation_flat_lineage(value, prefix):
    # Task A 可能输出扁平 lineage 字段；这里只把 schema/status/ref 这类安全字段还原成 summary。
    value = value if isinstance(value, dict) else {}
    fields = {
        "schema": value.get(f"{prefix}_schema"),
        "evidence_boundary": value.get(f"{prefix}_evidence_boundary"),
        "status": value.get(f"{prefix}_status"),
        "evidence_ref": value.get(f"{prefix}_evidence_ref"),
        "same_evidence_ref_required": value.get(f"{prefix}_same_evidence_ref_required"),
    }
    return {key: item for key, item in fields.items() if item not in ("", None)}


def _route_task_field_retest_result_reconciliation_lineage_item(value):
    # lineage item 是 Robot diagnostics 的只读视图；强制附带 false flags，避免被 UI 当成授权。
    value = value if isinstance(value, dict) else {}
    evidence_ref = _safe_route_task_rehearsal_ref(
        value.get("safe_evidence_ref") or value.get("evidence_ref") or ""
    )
    summary = {
        "schema": _redact_route_task_rehearsal_text(value.get("schema")),
        "evidence_boundary": _redact_route_task_rehearsal_text(
            value.get("evidence_boundary") or value.get("boundary")
        ),
        "status": _redact_route_task_rehearsal_text(
            value.get("status") or value.get("overall_status") or value.get("verdict")
        ),
        "safe_evidence_ref": evidence_ref,
        "same_evidence_ref_required": value.get("same_evidence_ref_required", True) is True,
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    return {key: item for key, item in summary.items() if item not in ("", None)}


def _route_task_field_retest_result_reconciliation_lineage(
    reconciliation,
    summary_fragment,
    result_intake_source,
    safe_evidence_ref,
):
    # 只在 source lineage 明确出现时透传；旧 artifact 没有 lineage 时保持兼容，不额外降级。
    reconciliation = reconciliation if isinstance(reconciliation, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    result_intake_source = result_intake_source if isinstance(result_intake_source, dict) else {}
    holders = (summary_fragment, reconciliation)
    explicit_intake = next(
        (
            holder.get("source_result_intake")
            for holder in holders
            if isinstance(holder.get("source_result_intake"), dict)
        ),
        {},
    )
    explicit_handoff = next(
        (
            holder.get("source_review_result_handoff")
            for holder in holders
            if isinstance(holder.get("source_review_result_handoff"), dict)
        ),
        {},
    )
    flat_intake = next(
        (
            candidate
            for candidate in (
                _route_task_field_retest_result_reconciliation_flat_lineage(holder, "source_result_intake")
                for holder in holders
            )
            if candidate
        ),
        {},
    )
    flat_handoff = next(
        (
            candidate
            for candidate in (
                _route_task_field_retest_result_reconciliation_flat_lineage(
                    holder,
                    "source_review_result_handoff",
                )
                for holder in holders
            )
            if candidate
        ),
        {},
    )
    nested_source = (
        result_intake_source.get("source_result")
        if isinstance(result_intake_source.get("source_result"), dict)
        else result_intake_source.get("source_review_result_handoff")
        if isinstance(result_intake_source.get("source_review_result_handoff"), dict)
        else {}
    )
    if not (explicit_intake or explicit_handoff or flat_intake or flat_handoff or nested_source):
        return {}, ""

    source_result_intake = _route_task_field_retest_result_reconciliation_lineage_item(
        explicit_intake or flat_intake or result_intake_source
    )
    source_review_result_handoff = _route_task_field_retest_result_reconciliation_lineage_item(
        explicit_handoff or flat_handoff or nested_source
    )
    allowed_intake_schemas = {
        ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_SCHEMA,
        ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_SUMMARY_SCHEMA,
    }
    allowed_handoff_schemas = {
        ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_SCHEMA,
        ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_SUMMARY_SCHEMA,
    }
    intake_ref = source_result_intake.get("safe_evidence_ref", "")
    handoff_ref = source_review_result_handoff.get("safe_evidence_ref", "")
    refs = [ref for ref in (safe_evidence_ref, intake_ref, handoff_ref) if ref]
    if source_result_intake.get("schema") not in allowed_intake_schemas:
        return {}, "source_result_intake schema is missing or unsupported"
    if source_review_result_handoff.get("schema") not in allowed_handoff_schemas:
        return {}, "source_review_result_handoff schema is missing or unsupported"
    if not intake_ref or not handoff_ref:
        return {}, "safe lineage metadata is missing evidence_ref"
    if len(set(refs)) > 1:
        return {}, "safe lineage metadata evidence_ref does not match result reconciliation evidence_ref"
    if (
        not source_result_intake.get("same_evidence_ref_required")
        or not source_review_result_handoff.get("same_evidence_ref_required")
    ):
        return {}, "safe lineage metadata must keep same_evidence_ref_required=true"
    if (
        _route_task_field_run_console_has_unsafe_fields(explicit_intake or flat_intake)
        or _route_task_field_run_console_has_unsafe_fields(explicit_handoff or flat_handoff or nested_source)
    ):
        return {}, "safe lineage metadata contains unsafe fields or control claims"
    return {
        "lineage_status": {
            "status": "metadata_only",
            "reason": "review_result_handoff -> result_intake -> result_reconciliation lineage is safe metadata only",
        },
        "source_result_intake": source_result_intake,
        "source_review_result_handoff": source_review_result_handoff,
        "lineage_chain": [
            "route_task_field_retest_review_result_handoff",
            "route_task_field_retest_result_intake",
            "route_task_field_retest_result_reconciliation",
        ],
    }, ""


def _route_task_field_retest_material_pack_source_contract(value):
    # material pack 支持直接 artifact 或 summary wrapper；wrapper 必须回指 material_pack source，不能混入 result gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_material_callback_packet_source_contract(value):
    # callback packet 支持 artifact、summary wrapper 和 nested diagnostics；summary 必须回指同一 packet gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_material_callback_review_decision_source_contract(value):
    # material callback review decision 支持 artifact、summary wrapper 和 nested diagnostics；summary 必须回指本 gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_operator_drill_source_contract(value):
    # operator drill 支持直接 artifact 或 summary wrapper；wrapper 必须回指 drill source，避免误接 material pack。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_drill_console_source_contract(value):
    # drill console 支持直接 artifact 或 summary wrapper；wrapper 必须回指 console source，避免误接 operator_drill gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_acceptance_brief_source_contract(value):
    # acceptance brief 支持 artifact、summary wrapper 和 nested diagnostics；wrapper 必须回指 brief gate，避免误接 drill console。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_acceptance_review_decision_source_contract(value):
    # acceptance review decision 支持 artifact、summary wrapper 和 nested diagnostics；summary 缺 source 时回指本 gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_acceptance_execution_pack_source_contract(value):
    # acceptance execution pack 支持 artifact、summary wrapper 和 nested diagnostics；summary 缺 source 时回指本 gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_acceptance_execution_callback_intake_source_contract(value):
    # callback intake 支持 artifact、summary wrapper 和 nested diagnostics；summary 缺 source 时回指本轮 artifact。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_evidence_dispatch_source_contract(value):
    # evidence dispatch 支持 artifact、summary wrapper 和 nested diagnostics；wrapper 必须回指 dispatch gate，避免误接 acceptance brief。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_callback_intake_source_contract(value):
    # callback intake 支持 artifact、summary wrapper 和 nested diagnostics；wrapper 必须回指 callback gate，避免误接 dispatch。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_callback_review_decision_source_contract(value):
    # review decision 支持 artifact、summary wrapper 和 nested diagnostics；wrapper 必须回指 review gate，避免误接 intake。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_review_result_handoff_source_contract(value):
    # handoff 支持 artifact、summary wrapper 和 nested diagnostics；wrapper 必须回指本 gate，避免误接 callback review。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_result_acceptance_packet_source_contract(value):
    # acceptance packet 支持 artifact、summary wrapper 和 nested diagnostics；summary 必须回指 packet gate 才能进入 Robot 摘要。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_result_acceptance_backfill_source_contract(value):
    # backfill 支持 artifact、summary wrapper 和 nested diagnostics；summary 必须回指 backfill gate，避免误接 packet。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_result_backfill_review_decision_source_contract(value):
    # review decision 支持 artifact、summary wrapper 和 nested diagnostics；wrapper 必须回指同一 gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_result_review_dispatch_source_contract(value):
    # 本轮 Autonomy 产物就是 summary；只接受该 summary schema 和同一软件证据边界，防止串接旧 gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_result_review_decision_source_contract(value):
    # decision 可来自 direct artifact、summary wrapper 或 diagnostics 嵌套 summary；summary 缺 source 时回指本 gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema") or ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_result_review_handoff_source_contract(value):
    # result review handoff 支持 artifact、summary wrapper 和 nested diagnostics；summary 缺 source 时回指本轮 artifact。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema") or ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_result_callback_intake_source_contract(value):
    # result callback intake 可直接消费 artifact 或 summary；summary 缺 source 字段时回指本轮 artifact schema。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema") or ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_result_review_intake_source_contract(value):
    # result review intake 可直接消费 artifact 或 Autonomy summary；summary 缺 source 时回指本轮 artifact。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema") or ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_result_callback_review_decision_source_contract(value):
    # result callback review decision 支持 artifact、summary wrapper 和 nested diagnostics；summary 缺 source 时回指本轮 artifact。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_acceptance_execution_callback_review_decision_source_contract(
    value,
):
    # acceptance execution callback review decision 支持 artifact、summary wrapper 和 nested diagnostics。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if (
        source_schema
        == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA
    ):
        source_schema = str(
            value.get("source_schema")
            or ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_acceptance_execution_callback_review_handoff_source_contract(
    value,
):
    # callback review handoff 支持 artifact、summary wrapper 和 nested diagnostics；summary 缺 source 时回指本轮 artifact。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if (
        source_schema
        == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA
    ):
        source_schema = str(
            value.get("source_schema")
            or ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_result_callback_review_handoff_source_contract(value):
    # result callback review handoff 可直接消费 artifact 或 summary；summary 缺 source 时仍回指本轮 handoff artifact。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_acceptance_execution_handoff_intake_source_contract(value):
    # handoff intake 支持 artifact、summary wrapper 和 Robot alias；summary 缺 source 时回指本轮 artifact。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_acceptance_execution_rerun_queue_source_contract(value):
    # rerun queue 支持 artifact、summary wrapper 和 nested diagnostics；summary 缺 source 时回指本轮 queue artifact。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_acceptance_execution_rerun_result_intake_source_contract(value):
    # Robot 只接收 Autonomy sanitized summary；source 字段用于证明 summary 来自预期 result-intake gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_acceptance_execution_rerun_result_review_decision_source_contract(
    value,
):
    # Robot 只接收 Autonomy sanitized decision summary；summary 缺 source 时仍回指本轮 decision artifact。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if (
        source_schema
        == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_SUMMARY_SCHEMA
    ):
        source_schema = str(
            value.get("source_schema")
            or ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_acceptance_execution_rerun_result_review_handoff_source_contract(
    value,
):
    # Robot 只接收 Autonomy sanitized handoff summary；raw handoff artifact 必须停在 missing_summary。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if (
        source_schema
        == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_SUMMARY_SCHEMA
    ):
        source_schema = str(
            value.get("source_schema")
            or ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_task_field_retest_execution_pack_requires_same_evidence_ref(summary_fragment, pack):
    # 同 evidence_ref 是补测执行包的主约束；只接受 JSON boolean true，字符串真值不能算通过。
    value = (
        summary_fragment.get("same_evidence_ref_required")
        if isinstance(summary_fragment, dict) and "same_evidence_ref_required" in summary_fragment
        else pack.get("same_evidence_ref_required", True)
        if isinstance(pack, dict)
        else True
    )
    return value is True


def _route_task_field_retest_session_handoff_requires_same_evidence_ref(summary_fragment, handoff):
    # 同 evidence_ref 交接是现场复测 session 的核心约束；字符串 true/false 都不能当作 JSON boolean true。
    value = (
        summary_fragment.get("same_evidence_ref_required")
        if isinstance(summary_fragment, dict) and "same_evidence_ref_required" in summary_fragment
        else handoff.get("same_evidence_ref_required", True)
        if isinstance(handoff, dict)
        else True
    )
    return value is True


def _route_task_field_retest_result_intake_requires_same_evidence_ref(summary_fragment, result):
    # 现场结果回填必须保持同一 evidence_ref；只接受 JSON boolean true，字符串 true 仍按弱约束处理。
    value = (
        summary_fragment.get("same_evidence_ref_required")
        if isinstance(summary_fragment, dict) and "same_evidence_ref_required" in summary_fragment
        else result.get("same_evidence_ref_required", True)
        if isinstance(result, dict)
        else True
    )
    return value is True


def _route_task_field_retest_result_reconciliation_requires_same_evidence_ref(
    summary_fragment,
    reconciliation,
):
    # result reconciliation 必须维持 Task A 的同 evidence_ref 约束；只接受 JSON boolean true。
    value = (
        summary_fragment.get("same_evidence_ref_required")
        if isinstance(summary_fragment, dict) and "same_evidence_ref_required" in summary_fragment
        else reconciliation.get("same_evidence_ref_required", True)
        if isinstance(reconciliation, dict)
        else True
    )
    return value is True


def _route_task_field_retest_callback_intake_requires_same_evidence_ref(summary_fragment, intake):
    # callback intake 必须维持 dispatch 回填链路的同 evidence_ref；字符串 true/false 一律不算安全约束。
    value = (
        summary_fragment.get("same_evidence_ref_required")
        if isinstance(summary_fragment, dict) and "same_evidence_ref_required" in summary_fragment
        else intake.get("same_evidence_ref_required", True)
        if isinstance(intake, dict)
        else True
    )
    return value is True


def _route_task_field_retest_review_result_handoff_requires_same_evidence_ref(
    summary_fragment,
    handoff,
):
    # review-result handoff 必须保持 result-intake 链路同 evidence_ref；只接受 JSON boolean true。
    value = (
        summary_fragment.get("same_evidence_ref_required")
        if isinstance(summary_fragment, dict) and "same_evidence_ref_required" in summary_fragment
        else handoff.get("same_evidence_ref_required", True)
        if isinstance(handoff, dict)
        else True
    )
    return value is True


def _route_task_field_retest_result_review_dispatch_requires_same_evidence_ref(
    summary_fragment,
):
    # result review dispatch 必须声明同一 evidence_ref；字符串 true/false 都不能当成安全 JSON boolean。
    if not isinstance(summary_fragment, dict):
        return False
    return summary_fragment.get("same_evidence_ref_required") is True


def _route_task_field_retest_acceptance_review_decision_requires_same_evidence_ref(
    summary_fragment,
):
    # acceptance review decision 承接验收简报；必须明确同一 evidence_ref，防止跨 evidence packet 误接。
    if not isinstance(summary_fragment, dict):
        return False
    return summary_fragment.get("same_evidence_ref_required") is True


def _route_task_field_retest_acceptance_execution_pack_requires_same_evidence_ref(
    summary_fragment,
):
    # acceptance execution pack 是现场执行入口；同一 evidence_ref 必须是 JSON true，避免混用旧 review 决策材料。
    if not isinstance(summary_fragment, dict):
        return False
    return summary_fragment.get("same_evidence_ref_required") is True


def _route_task_field_retest_acceptance_execution_callback_intake_requires_same_evidence_ref(
    summary_fragment,
):
    # acceptance execution callback intake 必须复用同一个 evidence_ref，防止把其他现场回执串到本轮执行包。
    if not isinstance(summary_fragment, dict):
        return False
    return summary_fragment.get("same_evidence_ref_required") is True


def _route_task_field_retest_result_review_decision_requires_same_evidence_ref(
    summary_fragment,
):
    # result review decision 延续 review intake 的同证据链约束；只接受 JSON boolean true。
    if not isinstance(summary_fragment, dict):
        return False
    return summary_fragment.get("same_evidence_ref_required") is True


def _route_task_field_retest_result_review_handoff_requires_same_evidence_ref(
    summary_fragment,
):
    # result review handoff 是同一 evidence_ref 的 owner 交接；字符串 true/false 都不能当成安全布尔。
    if not isinstance(summary_fragment, dict):
        return False
    return summary_fragment.get("same_evidence_ref_required") is True


def _route_task_field_retest_result_callback_intake_requires_same_evidence_ref(
    summary_fragment,
):
    # result callback intake 是同一 evidence_ref 的回执复账；只接受 JSON boolean true。
    if not isinstance(summary_fragment, dict):
        return False
    return summary_fragment.get("same_evidence_ref_required") is True


def _route_task_field_retest_result_callback_review_decision_requires_same_evidence_ref(
    summary_fragment,
):
    # result callback review decision 仍是同 evidence_ref 复核链；字符串 true/false 都不能当成安全布尔。
    if not isinstance(summary_fragment, dict):
        return False
    return summary_fragment.get("same_evidence_ref_required") is True


def _route_task_field_retest_acceptance_execution_callback_review_decision_requires_same_evidence_ref(
    summary_fragment,
):
    # acceptance execution callback review decision 必须延续同一 evidence_ref；只接受 JSON boolean true。
    if not isinstance(summary_fragment, dict):
        return False
    return summary_fragment.get("same_evidence_ref_required") is True


def _route_task_field_retest_acceptance_execution_callback_review_handoff_requires_same_evidence_ref(
    summary_fragment,
):
    # handoff 必须延续同一 evidence_ref；字符串 true/false 都视为不安全，避免跨证据包误交接。
    if not isinstance(summary_fragment, dict):
        return False
    return summary_fragment.get("same_evidence_ref_required") is True


def _route_task_field_retest_result_callback_review_handoff_requires_same_evidence_ref(
    summary_fragment,
):
    # result callback review handoff 延续同 evidence_ref 的交接链；只接受 JSON boolean true。
    if not isinstance(summary_fragment, dict):
        return False
    return summary_fragment.get("same_evidence_ref_required") is True


def _route_task_field_retest_acceptance_execution_handoff_intake_requires_same_evidence_ref(
    summary_fragment,
):
    # handoff intake 必须延续同一 evidence_ref；字符串 true/false 都视为不安全。
    if not isinstance(summary_fragment, dict):
        return False
    return summary_fragment.get("same_evidence_ref_required") is True


def _route_task_field_retest_execution_pack_has_disabled_actions(pack):
    # source 必须显式保留 fail-closed 布尔值；缺失或字符串 false 都不能被手机端当作控制授权。
    if not isinstance(pack, dict):
        return False
    return (
        pack.get("delivery_success") is False
        and pack.get("primary_actions_enabled") is False
    )


def _route_task_field_retest_session_handoff_has_disabled_actions(handoff):
    # handoff source 必须显式保留两个 false，避免旧 summary 缺字段时被误判成可操作。
    if not isinstance(handoff, dict):
        return False
    return (
        handoff.get("delivery_success") is False
        and handoff.get("primary_actions_enabled") is False
    )


def _route_task_field_retest_result_intake_has_disabled_actions(result):
    # result intake 也必须显式保留两个 false；缺失或字符串 false 都不能算 fail-closed。
    if not isinstance(result, dict):
        return False
    return (
        result.get("delivery_success") is False
        and result.get("primary_actions_enabled") is False
    )


def _route_task_field_retest_result_reconciliation_has_disabled_actions(reconciliation):
    # reconciliation source 必须显式关闭动作和交付成功；否则 diagnostics 不能把它当作 phone-safe 摘要。
    if not isinstance(reconciliation, dict):
        return False
    return (
        reconciliation.get("delivery_success") is False
        and reconciliation.get("primary_actions_enabled") is False
    )


def _route_task_field_retest_material_pack_has_disabled_actions(pack, summary_fragment):
    # material pack 的 source 或 summary wrapper 必须显式关闭动作；缺字段不能被解释成安全授权。
    pack = pack if isinstance(pack, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else pack.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else pack.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _route_task_field_retest_material_callback_packet_has_disabled_actions(
    packet,
    summary_fragment,
):
    # packet source 与 summary 都必须显式关闭主动作；缺字段时不能默认当成安全回执或动作授权。
    packet = packet if isinstance(packet, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else packet.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else packet.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _route_task_field_retest_material_callback_review_decision_has_disabled_actions(
    decision,
    summary_fragment,
):
    # review decision source 和 summary 都必须显式 false；缺字段不能被解释成可点击或可 ACK。
    decision = decision if isinstance(decision, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else decision.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else decision.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _route_task_field_retest_operator_drill_has_disabled_actions(drill, summary_fragment):
    # drill source 和 summary 都必须显式关闭主动作；缺字段不能被解释成可点击或可 ACK。
    drill = drill if isinstance(drill, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else drill.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else drill.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _route_task_field_retest_drill_console_has_disabled_actions(console, summary_fragment):
    # console source 和 Robot-compatible summary 都必须显式关闭主动作；缺字段不能被解释成可点击或可 ACK。
    console = console if isinstance(console, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else console.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else console.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _route_task_field_retest_acceptance_brief_has_disabled_actions(brief, summary_fragment):
    # acceptance brief 只能进入 diagnostics 元数据面；缺少 false 布尔值时 fail closed，避免被 UI 当作动作授权。
    brief = brief if isinstance(brief, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else brief.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else brief.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _route_task_field_retest_acceptance_review_decision_has_disabled_actions(
    decision,
    summary_fragment,
):
    # acceptance review decision 只读消费 Autonomy 摘要；source 或 summary 缺少显式 false 就保持 blocked。
    decision = decision if isinstance(decision, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else decision.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else decision.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _route_task_field_retest_acceptance_execution_pack_has_disabled_actions(
    pack,
    summary_fragment,
):
    # execution pack 可以包含 rerun 命令文本，但不能携带任何 Start/ACK/Nav2/HIL 授权。
    pack = pack if isinstance(pack, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else pack.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else pack.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _route_task_field_retest_acceptance_execution_callback_intake_has_disabled_actions(
    intake,
    summary_fragment,
):
    # intake source 和 summary 都必须显式关闭主动作；缺字段不能被解释成 Start/Confirm/Cancel 授权。
    intake = intake if isinstance(intake, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else intake.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else intake.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _route_task_field_retest_evidence_dispatch_has_disabled_actions(dispatch, summary_fragment):
    # dispatch consumer 只服务 diagnostics metadata-only 读取；显式 false 是动作隔离的硬边界。
    dispatch = dispatch if isinstance(dispatch, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else dispatch.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else dispatch.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _route_task_field_retest_callback_intake_has_disabled_actions(intake, summary_fragment):
    # callback intake 只消费 sanitized callback metadata；source 或 summary 缺少 false 时不能被当作动作授权。
    intake = intake if isinstance(intake, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else intake.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else intake.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _route_task_field_retest_callback_review_decision_has_disabled_actions(
    decision,
    summary_fragment,
):
    # review decision 只给 diagnostics 读安全摘要；显式 false 是隔离 Start/Confirm/Cancel 和 result intake 的硬边界。
    decision = decision if isinstance(decision, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else decision.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else decision.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _route_task_field_retest_review_result_handoff_has_disabled_actions(
    handoff,
    summary_fragment,
):
    # handoff 只能进入 diagnostics 元数据面；source 或 summary 缺少 false 时必须 blocked，不能默认安全。
    handoff = handoff if isinstance(handoff, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else handoff.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else handoff.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _route_task_field_retest_result_acceptance_packet_has_disabled_actions(
    packet,
    summary_fragment,
):
    # packet 只能进入 diagnostics 元数据面；source 或 summary 缺少显式 false 时必须 blocked。
    packet = packet if isinstance(packet, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else packet.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else packet.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _route_task_field_retest_result_acceptance_backfill_has_disabled_actions(
    backfill,
    summary_fragment,
):
    # backfill 只是诊断元数据；source 或 summary 缺少显式 false 时必须 blocked，不能默认安全。
    backfill = backfill if isinstance(backfill, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else backfill.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else backfill.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _route_task_field_retest_result_backfill_review_decision_has_disabled_actions(
    decision,
    summary_fragment,
):
    # review decision 不授权 Robot 控制；source 或 summary 没有显式 false 就保持 blocked。
    decision = decision if isinstance(decision, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else decision.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else decision.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _route_task_field_retest_result_review_dispatch_has_disabled_actions(summary_fragment):
    # dispatch 是纯 diagnostics 元数据；summary 缺少显式 false 时必须 blocked，不能默认安全。
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    return (
        summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )


def _route_task_field_retest_result_review_decision_has_disabled_actions(summary_fragment):
    # decision 是纯只读元数据；显式 false 是隔离 Start/Confirm/Cancel/ACK/cursor 的硬边界。
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    return (
        summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )


def _route_task_field_retest_result_review_handoff_has_disabled_actions(
    summary_fragment,
):
    # handoff 只能进入 diagnostics 元数据面；显式 false 是隔离动作、ACK、cursor、Nav2/HIL 的硬边界。
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    return (
        summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )


def _route_task_field_retest_result_callback_intake_has_disabled_actions(summary_fragment):
    # callback intake 也是纯 diagnostics 元数据；显式 false 是隔离 Start/ACK/Nav2/HIL 的硬边界。
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    return (
        summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )


def _route_task_field_retest_result_callback_review_decision_has_disabled_actions(
    summary_fragment,
):
    # review decision 仍然只读；缺少显式 false 时必须 blocked，避免被解释成 result review 或机器人动作授权。
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    return (
        summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )


def _route_task_field_retest_acceptance_execution_callback_review_decision_has_disabled_actions(
    summary_fragment,
):
    # acceptance execution callback review decision 只能进 diagnostics；显式 false 是动作隔离硬边界。
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    return (
        summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )


def _route_task_field_retest_acceptance_execution_callback_review_handoff_has_disabled_actions(
    summary_fragment,
):
    # callback review handoff 只能进入 diagnostics；显式 false 是隔离控制、ACK、Nav2/HIL 的硬边界。
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    return (
        summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )


def _route_task_field_retest_result_callback_review_handoff_has_disabled_actions(
    summary_fragment,
):
    # handoff 只是 diagnostics 元数据；显式 false 是隔离 Start/Confirm/Cancel/ACK/Nav2/HIL 的硬边界。
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    return (
        summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )


def _route_task_field_retest_acceptance_execution_handoff_intake_has_disabled_actions(
    summary_fragment,
):
    # intake alias 只读展示交接元数据；显式 false 是隔离 API action、ACK、Nav2/HIL 的硬边界。
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    return (
        summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )


def _route_task_field_retest_acceptance_execution_rerun_queue_has_disabled_actions(
    summary_fragment,
):
    # rerun queue 只读进入 diagnostics；显式 false 是阻断 collect/dropoff/cancel/ACK/Nav2/HIL 的硬边界。
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    return (
        summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )


def _route_task_field_retest_acceptance_execution_rerun_result_intake_has_disabled_actions(
    summary_fragment,
):
    # result-intake summary 只能只读进 diagnostics；显式 false 是阻断 collect/dropoff/cancel 的硬边界。
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    return (
        summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )


def _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
    value,
):
    # safe fields 里不能夹带 raw artifact/path/secret/ROS topic/serial/UART/WAVE ROVER 材料。
    text = _redact_route_task_rehearsal_text(value).strip().lower()
    if not text:
        return False
    unsafe_markers = (
        "[redacted_auth_header]",
        "bearer [redacted]",
        "[redacted_url]",
        "/dev/[redacted_serial]",
        "[redacted_baud]",
        "[redacted_traceback]",
        "[redacted_local_path]",
        "raw artifact",
        "raw_artifact",
        "raw payload",
        "raw_payload",
        "ros topic",
        "/cmd_vel",
        "serial",
        "uart",
        "baudrate",
        "wave rover",
    )
    return any(marker in text for marker in unsafe_markers)


def _route_task_field_retest_result_review_intake_has_disabled_actions(summary_fragment):
    # review intake 是纯 diagnostics 摘要；显式 false 是隔离控制、ACK、Nav2/HIL 的硬边界。
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    return (
        summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )


def summarize_route_task_field_retest_execution_pack(source):
    """构建 route-task field retest execution pack 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        pack = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_execution_pack_summary(
            source_path,
            read_error="route-task field retest execution pack is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "execution_status": "missing",
                    "read_error": "route-task field retest execution pack not found",
                    "required_field_materials_summary": {
                        "status": "blocked",
                        "reason": "route-task field retest execution pack artifact missing",
                        "items": [],
                    },
                    "safe_copy": "Route-task field retest execution pack is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest execution pack is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                pack = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "execution_status": "read_error",
                    "read_error": _redact_route_task_rehearsal_text(
                        f"failed reading route-task field retest execution pack: {exc}"
                    ),
                    "required_field_materials_summary": {
                        "status": "blocked",
                        "reason": "route-task field retest execution pack JSON read error",
                        "items": [],
                    },
                    "safe_copy": "Route-task field retest execution pack could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest execution pack could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_execution_pack_summary(
        source_path,
        read_error="route-task field retest execution pack is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(pack, dict):
        summary.update(
            {
                "execution_status": "read_error",
                "read_error": "route-task field retest execution pack JSON must be an object",
                "required_field_materials_summary": {
                    "status": "blocked",
                    "reason": "route-task field retest execution pack shape is invalid",
                    "items": [],
                },
                "safe_copy": "Route-task field retest execution pack shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest execution pack shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = pack.get("diagnostics") if isinstance(pack.get("diagnostics"), dict) else {}
    # summary wrapper 本身就是已消毒摘要，必须优先读取它的 safe_evidence_ref 和白名单字段。
    summary_fragment = pack if str(pack.get("schema") or "") == ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_SUMMARY_SCHEMA else {}
    for candidate in (
        pack.get("route_task_field_retest_execution_pack_summary"),
        pack.get("route_task_field_retest_execution_pack"),
        pack.get("phone_readiness"),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
        diagnostics.get("route_task_field_retest_execution_pack_summary"),
        diagnostics.get("route_task_field_retest_execution_pack"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break

    source_schema, source_boundary = _route_task_field_retest_execution_pack_source_contract(pack)
    execution_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("execution_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or pack.get("execution_status")
        or pack.get("status")
        or pack.get("overall_status")
        or "blocked"
    )
    field_materials_source = (
        summary_fragment.get("required_field_materials_summary")
        if "required_field_materials_summary" in summary_fragment
        else summary_fragment.get("required_field_materials")
        if "required_field_materials" in summary_fragment
        else pack.get("required_field_materials_summary")
        if "required_field_materials_summary" in pack
        else pack.get("required_field_materials")
    )
    rerun_source = (
        summary_fragment.get("rerun_commands_summary")
        if "rerun_commands_summary" in summary_fragment
        else summary_fragment.get("rerun_commands")
        if "rerun_commands" in summary_fragment
        else pack.get("rerun_commands_summary")
        if "rerun_commands_summary" in pack
        else pack.get("rerun_commands")
    )
    checklist_source = (
        summary_fragment.get("field_retest_checklist")
        if "field_retest_checklist" in summary_fragment
        else pack.get("field_retest_checklist")
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or pack.get("safe_copy")
        or pack.get("safe_phone_copy")
        or "Route-task field retest execution pack is metadata-only; delivery_success=false; primary_actions_enabled=false."
    )
    source_ref = str(pack.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    safe_evidence_ref = _safe_route_task_rehearsal_ref(summary_ref or source_ref)
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": pack.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "execution_status": execution_status or "blocked",
            "safe_evidence_ref": safe_evidence_ref,
            "same_evidence_ref_required": _route_task_field_retest_execution_pack_requires_same_evidence_ref(
                summary_fragment,
                pack,
            ),
            "required_field_materials_summary": _safe_pc_route_debug_value(field_materials_source)
            or {
                "status": execution_status or "blocked",
                "reason": "route-task field retest execution pack lacks required field materials summary",
                "items": [],
            },
            "rerun_commands_summary": _safe_pc_route_debug_value(rerun_source),
            "operator_handoff": _safe_pc_route_debug_value(
                summary_fragment.get("operator_handoff", pack.get("operator_handoff", {}))
            ),
            "field_retest_checklist": _safe_pc_route_debug_value(checklist_source),
            "boundary": ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_GATE,
            "not_proven": _route_task_field_retest_execution_pack_not_proven(pack, summary_fragment),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    if source_schema != ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_SCHEMA or source_boundary != ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_GATE:
        summary.update(
            {
                "execution_status": "unsupported_schema",
                "read_error": "route-task field retest execution pack schema or evidence boundary is unsupported",
                "required_field_materials_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                    "items": [],
                },
                "safe_copy": "Route-task field retest execution pack is not a supported diagnostics source; no delivery result is proven.",
                "safe_phone_copy": "Route-task field retest execution pack is not a supported diagnostics source; no delivery result is proven.",
            }
        )
        return summary
    if not safe_evidence_ref:
        summary.update(
            {
                "execution_status": "missing_evidence_ref",
                "read_error": "route-task field retest execution pack is missing evidence_ref",
                "required_field_materials_summary": {
                    "status": "blocked",
                    "reason": "missing evidence_ref",
                    "items": [],
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "execution_status": "evidence_ref_mismatch",
                "read_error": "route-task field retest execution pack summary evidence_ref does not match source evidence_ref",
                "required_field_materials_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                    "items": [],
                },
            }
        )
        return summary
    if (
        not summary["same_evidence_ref_required"]
        or not _route_task_field_retest_execution_pack_has_disabled_actions(pack)
        or _route_task_field_run_readiness_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_has_unsafe_fields(pack)
        or _route_task_field_run_intake_has_unsafe_control_claims(pack)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(pack)
    ):
        summary.update(
            {
                "execution_status": "unsafe_fields",
                "read_error": "route-task field retest execution pack contains unsafe fields, weak evidence_ref constraints, enabled actions, or success wording",
                "required_field_materials_summary": {
                    "status": "blocked",
                    "reason": "unsafe route-task field retest execution pack summary fields",
                    "items": [],
                },
                "safe_copy": "Route-task field retest execution pack was blocked because summary fields could imply control, ACK, Nav2/HIL, or delivery success.",
                "safe_phone_copy": "Route-task field retest execution pack was blocked because summary fields could imply control, ACK, Nav2/HIL, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_session_handoff(source):
    """构建 route-task field retest session handoff 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        handoff = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_session_handoff_summary(
            source_path,
            read_error="route-task field retest session handoff is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "handoff_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest session handoff artifact missing",
                    },
                    "required_field_materials_summary": {
                        "status": "blocked",
                        "reason": "route-task field retest session handoff artifact missing",
                        "items": [],
                    },
                    "robot_diagnostics_summary": {"status": "blocked", "reason": "handoff artifact missing"},
                    "safe_copy": "Route-task field retest session handoff is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest session handoff is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "handoff_status": {
                        "status": "blocked_missing_review_decision",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest session handoff: {exc}"
                        ),
                    },
                    "required_field_materials_summary": {
                        "status": "blocked",
                        "reason": "route-task field retest session handoff JSON read error",
                        "items": [],
                    },
                    "robot_diagnostics_summary": {"status": "blocked", "reason": "handoff JSON read error"},
                    "safe_copy": "Route-task field retest session handoff could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest session handoff could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_session_handoff_summary(
        source_path,
        read_error="route-task field retest session handoff is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(handoff, dict):
        summary.update(
            {
                    "handoff_status": {
                    "status": "blocked_missing_review_decision",
                    "verdict": "not_proven",
                    "reason": "route-task field retest session handoff JSON must be an object",
                },
                "required_field_materials_summary": {
                    "status": "blocked",
                    "reason": "route-task field retest session handoff shape is invalid",
                    "items": [],
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "handoff JSON shape is invalid"},
                "safe_copy": "Route-task field retest session handoff shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest session handoff shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = handoff.get("diagnostics") if isinstance(handoff.get("diagnostics"), dict) else {}
    # 只接受已消毒 summary 片段；raw artifact 仅用于 schema/boundary/ref/false 栅栏等契约校验。
    summary_fragment = handoff if str(handoff.get("schema") or "") == ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_SUMMARY_SCHEMA else {}
    for candidate in (
        handoff.get("route_task_field_retest_session_handoff_summary"),
        handoff.get("route_task_field_retest_session_handoff"),
        handoff.get("robot_diagnostics_summary"),
        handoff.get("mobile_readonly_summary"),
        handoff.get("phone_safe_summary"),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
        diagnostics.get("route_task_field_retest_session_handoff_summary"),
        diagnostics.get("route_task_field_retest_session_handoff"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break

    source_schema, source_boundary = _route_task_field_retest_session_handoff_source_contract(handoff)
    status_source = summary_fragment.get("handoff_status")
    if not isinstance(status_source, dict):
        status_source = handoff.get("handoff_status")
    if not isinstance(status_source, dict):
        status_source = {}
    handoff_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("handoff_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or handoff.get("handoff_status")
        or handoff.get("status")
        or handoff.get("overall_status")
        or "blocked"
    )
    handoff_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or handoff.get("verdict")
        or "not_proven"
    )
    handoff_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or handoff.get("reason")
        or "route-task field retest session handoff consumed without explicit reason"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or handoff.get("safe_copy")
        or handoff.get("safe_phone_copy")
        or "Route-task field retest session handoff is metadata-only; delivery_success=false; primary_actions_enabled=false."
    )
    mobile_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            mobile_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    mobile_summary["safe_copy"] = safe_copy
    mobile_summary["safe_phone_copy"] = safe_copy
    source_ref = str(handoff.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    safe_evidence_ref = _safe_route_task_rehearsal_ref(summary_ref or source_ref)
    field_materials_source = (
        summary_fragment.get("required_field_materials_summary")
        if "required_field_materials_summary" in summary_fragment
        else summary_fragment.get("required_field_materials")
        if "required_field_materials" in summary_fragment
        else handoff.get("required_field_materials_summary")
        if "required_field_materials_summary" in handoff
        else handoff.get("required_field_materials")
    )
    material_placeholders_source = (
        summary_fragment.get("material_placeholders_summary")
        if "material_placeholders_summary" in summary_fragment
        else handoff.get("material_placeholders_summary")
        if "material_placeholders_summary" in handoff
        else handoff.get("material_placeholders")
    )
    rerun_source = (
        summary_fragment.get("rerun_commands_summary")
        if "rerun_commands_summary" in summary_fragment
        else summary_fragment.get("rerun_commands")
        if "rerun_commands" in summary_fragment
        else handoff.get("rerun_commands_summary")
        if "rerun_commands_summary" in handoff
        else handoff.get("rerun_commands")
    )
    callback_source = (
        summary_fragment.get("field_callback_checklist")
        if "field_callback_checklist" in summary_fragment
        else summary_fragment.get("field_retest_checklist")
        if "field_retest_checklist" in summary_fragment
        else handoff.get("field_callback_checklist")
        if "field_callback_checklist" in handoff
        else handoff.get("field_retest_checklist")
    )
    operator_steps_source = (
        summary_fragment.get("operator_next_steps")
        if "operator_next_steps" in summary_fragment
        else handoff.get("operator_next_steps")
        if "operator_next_steps" in handoff
        else handoff.get("operator_handoff", {}).get("operator_next_steps")
        if isinstance(handoff.get("operator_handoff"), dict)
        else []
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else handoff.get("robot_diagnostics_summary")
        if isinstance(handoff.get("robot_diagnostics_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": handoff.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "handoff_status": {
                "status": handoff_status or "blocked",
                "verdict": handoff_verdict or "not_proven",
                "reason": handoff_reason,
            },
            "safe_evidence_ref": safe_evidence_ref,
            "same_evidence_ref_required": _route_task_field_retest_session_handoff_requires_same_evidence_ref(
                summary_fragment,
                handoff,
            ),
            "session_owner": _redact_route_task_rehearsal_text(
                summary_fragment.get("session_owner")
                or handoff.get("session_owner")
                or (
                    handoff.get("operator_handoff", {}).get("owner")
                    if isinstance(handoff.get("operator_handoff"), dict)
                    else ""
                )
            ),
            "required_field_materials_summary": _safe_pc_route_debug_value(field_materials_source)
            or {
                "status": handoff_status or "blocked",
                "reason": "route-task field retest session handoff lacks required field materials summary",
                "items": [],
            },
            "material_placeholders_summary": _safe_pc_route_debug_value(material_placeholders_source),
            "rerun_commands_summary": _safe_pc_route_debug_value(rerun_source),
            "operator_next_steps": _safe_pc_route_debug_value(operator_steps_source),
            "field_callback_checklist": _safe_pc_route_debug_value(callback_source),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status or "blocked",
                "reason": "handoff consumed without explicit robot diagnostics summary",
            },
            "mobile_readonly_summary": mobile_summary,
            "boundary": ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_GATE,
            "not_proven": _route_task_field_retest_session_handoff_not_proven(
                handoff,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_GATE
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest session handoff schema or evidence boundary is unsupported",
                },
                "required_field_materials_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                    "items": [],
                },
                "material_placeholders_summary": [],
                "rerun_commands_summary": [],
                "operator_next_steps": [],
                "field_callback_checklist": [],
                "robot_diagnostics_summary": {"status": "blocked", "reason": "unsupported schema or evidence boundary"},
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field retest session handoff is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task field retest session handoff is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary
    if not safe_evidence_ref:
        summary.update(
            {
                "handoff_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest session handoff is missing evidence_ref",
                },
                "required_field_materials_summary": {
                    "status": "blocked",
                    "reason": "missing evidence_ref",
                    "items": [],
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "handoff_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest session handoff summary evidence_ref does not match source evidence_ref",
                },
                "required_field_materials_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                    "items": [],
                },
            }
        )
        return summary
    if (
        not summary["same_evidence_ref_required"]
        or not _route_task_field_retest_session_handoff_has_disabled_actions(handoff)
        or _route_task_field_run_console_has_unsafe_fields(handoff)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(handoff)
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest session handoff contains unsafe fields, weak evidence_ref constraints, enabled actions, or success wording",
                },
                "required_field_materials_summary": {
                    "status": "blocked",
                    "reason": "unsafe route-task field retest session handoff summary fields",
                    "items": [],
                },
                "material_placeholders_summary": [],
                "rerun_commands_summary": [],
                "operator_next_steps": [],
                "field_callback_checklist": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe handoff summary fields",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field retest session handoff was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                    "safe_phone_copy": "Route-task field retest session handoff was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                },
                "safe_copy": "Route-task field retest session handoff was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest session handoff was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_result_intake(source):
    """构建 route-task field retest result intake 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        result = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_result_intake_summary(
            source_path,
            read_error="route-task field retest result intake is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "result_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest result intake artifact missing",
                    },
                    "result_materials_summary": {
                        "status": "blocked",
                        "reason": "route-task field retest result intake artifact missing",
                        "items": [],
                    },
                    "robot_diagnostics_summary": {"status": "blocked", "reason": "result intake artifact missing"},
                    "safe_copy": "Route-task field retest result intake is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result intake is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                result = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "result_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest result intake: {exc}"
                        ),
                    },
                    "result_materials_summary": {
                        "status": "blocked",
                        "reason": "route-task field retest result intake JSON read error",
                        "items": [],
                    },
                    "robot_diagnostics_summary": {"status": "blocked", "reason": "result intake JSON read error"},
                    "safe_copy": "Route-task field retest result intake could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result intake could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_result_intake_summary(
        source_path,
        read_error="route-task field retest result intake is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(result, dict):
        summary.update(
            {
                "result_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result intake JSON must be an object",
                },
                "result_materials_summary": {
                    "status": "blocked",
                    "reason": "route-task field retest result intake shape is invalid",
                    "items": [],
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "result intake JSON shape is invalid"},
                "safe_copy": "Route-task field retest result intake shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest result intake shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = result.get("diagnostics") if isinstance(result.get("diagnostics"), dict) else {}
    # raw result artifact 只用于契约校验；面向手机和 Robot 的字段全部来自白名单 summary 片段。
    summary_fragment = result if str(result.get("schema") or "") == ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_SUMMARY_SCHEMA else {}
    for candidate in (
        result.get("route_task_field_retest_result_intake_summary"),
        result.get("route_task_field_retest_result_intake"),
        result.get("robot_diagnostics_summary"),
        result.get("mobile_readonly_summary"),
        result.get("phone_safe_summary"),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
        diagnostics.get("route_task_field_retest_result_intake_summary"),
        diagnostics.get("route_task_field_retest_result_intake"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break

    source_schema, source_boundary = _route_task_field_retest_result_intake_source_contract(result)
    status_source = summary_fragment.get("result_status")
    if not isinstance(status_source, dict):
        status_source = result.get("result_status")
    if not isinstance(status_source, dict):
        status_source = {}
    result_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("result_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or result.get("result_status")
        or result.get("status")
        or result.get("overall_status")
        or "blocked"
    )
    result_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or result.get("verdict")
        or "not_proven"
    )
    result_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or result.get("reason")
        or "route-task field retest result intake consumed without explicit reason"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or result.get("safe_copy")
        or result.get("safe_phone_copy")
        or "Route-task field retest result intake is metadata-only; delivery_success=false; primary_actions_enabled=false."
    )
    mobile_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            mobile_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    mobile_summary["safe_copy"] = safe_copy
    mobile_summary["safe_phone_copy"] = safe_copy
    source_ref = str(result.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    safe_evidence_ref = _safe_route_task_rehearsal_ref(summary_ref or source_ref)
    materials_source = (
        summary_fragment.get("result_materials_summary")
        if "result_materials_summary" in summary_fragment
        else summary_fragment.get("required_field_materials_summary")
        if "required_field_materials_summary" in summary_fragment
        else summary_fragment.get("result_materials")
        if "result_materials" in summary_fragment
        else result.get("result_materials_summary")
        if "result_materials_summary" in result
        else result.get("required_field_materials_summary")
        if "required_field_materials_summary" in result
        else result.get("result_materials")
    )
    operator_steps_source = (
        summary_fragment.get("operator_next_steps")
        if "operator_next_steps" in summary_fragment
        else result.get("operator_next_steps")
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else result.get("robot_diagnostics_summary")
        if isinstance(result.get("robot_diagnostics_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": result.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "result_status": {
                "status": result_status or "blocked",
                "verdict": result_verdict or "not_proven",
                "reason": result_reason,
            },
            "safe_evidence_ref": safe_evidence_ref,
            "same_evidence_ref_required": _route_task_field_retest_result_intake_requires_same_evidence_ref(
                summary_fragment,
                result,
            ),
            "door_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("door_state") or result.get("door_state") or "not_proven"
            ),
            "target_floor_confirmation": _redact_route_task_rehearsal_text(
                summary_fragment.get("target_floor_confirmation")
                or result.get("target_floor_confirmation")
                or "not_proven"
            ),
            "human_assistance_note": _redact_route_task_rehearsal_text(
                summary_fragment.get("human_assistance_note") or result.get("human_assistance_note") or ""
            ),
            "result_materials_summary": _safe_pc_route_debug_value(materials_source)
            or {
                "status": result_status or "blocked",
                "reason": "route-task field retest result intake lacks result materials summary",
                "items": [],
            },
            "operator_next_steps": _safe_pc_route_debug_value(operator_steps_source),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": result_status or "blocked",
                "reason": "result intake consumed without explicit robot diagnostics summary",
            },
            "mobile_readonly_summary": mobile_summary,
            "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_GATE,
            "not_proven": _route_task_field_retest_result_intake_not_proven(
                result,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    if source_schema != ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_SCHEMA or source_boundary != ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_GATE:
        summary.update(
            {
                "result_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result intake schema or evidence boundary is unsupported",
                },
                "result_materials_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                    "items": [],
                },
                "operator_next_steps": [],
                "robot_diagnostics_summary": {"status": "blocked", "reason": "unsupported schema or evidence boundary"},
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field retest result intake is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task field retest result intake is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary
    if not safe_evidence_ref:
        summary.update(
            {
                "result_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result intake is missing evidence_ref",
                },
                "result_materials_summary": {
                    "status": "blocked",
                    "reason": "missing evidence_ref",
                    "items": [],
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "result_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result intake summary evidence_ref does not match source evidence_ref",
                },
                "result_materials_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                    "items": [],
                },
            }
        )
        return summary
    if (
        not summary["same_evidence_ref_required"]
        or not _route_task_field_retest_result_intake_has_disabled_actions(result)
        or _route_task_field_run_console_has_unsafe_fields(result)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(result)
    ):
        summary.update(
            {
                "result_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result intake contains unsafe fields, weak evidence_ref constraints, enabled actions, or success wording",
                },
                "result_materials_summary": {
                    "status": "blocked",
                    "reason": "unsafe route-task field retest result intake summary fields",
                    "items": [],
                },
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe result intake summary fields",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field retest result intake was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                    "safe_phone_copy": "Route-task field retest result intake was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                },
                "safe_copy": "Route-task field retest result intake was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest result intake was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_result_reconciliation(source):
    """构建 route-task field retest result reconciliation 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        reconciliation = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_result_reconciliation_summary(
            source_path,
            read_error="route-task field retest result reconciliation is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "reconciliation_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest result reconciliation artifact missing",
                    },
                    "result_intake_summary": {
                        "status": "blocked",
                        "reason": "route-task field retest result reconciliation artifact missing",
                    },
                    "result_reconciliation_summary": {
                        "status": "blocked",
                        "reason": "route-task field retest result reconciliation artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "result reconciliation artifact missing",
                    },
                    "safe_copy": "Route-task field retest result reconciliation is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result reconciliation is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                reconciliation = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "reconciliation_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest result reconciliation: {exc}"
                        ),
                    },
                    "result_intake_summary": {
                        "status": "blocked",
                        "reason": "route-task field retest result reconciliation JSON read error",
                    },
                    "result_reconciliation_summary": {
                        "status": "blocked",
                        "reason": "route-task field retest result reconciliation JSON read error",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "result reconciliation JSON read error",
                    },
                    "safe_copy": "Route-task field retest result reconciliation could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result reconciliation could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_result_reconciliation_summary(
        source_path,
        read_error="route-task field retest result reconciliation is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(reconciliation, dict):
        summary.update(
            {
                "reconciliation_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result reconciliation JSON must be an object",
                },
                "result_intake_summary": {
                    "status": "blocked",
                    "reason": "route-task field retest result reconciliation shape is invalid",
                },
                "result_reconciliation_summary": {
                    "status": "blocked",
                    "reason": "route-task field retest result reconciliation shape is invalid",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "result reconciliation JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest result reconciliation shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest result reconciliation shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = reconciliation.get("diagnostics") if isinstance(reconciliation.get("diagnostics"), dict) else {}
    # 该 gate 可能接到 raw artifact 或 summary wrapper；diagnostics 只读取白名单摘要，避免完整现场材料泄漏到手机面。
    summary_fragment = (
        reconciliation
        if str(reconciliation.get("schema") or "") == ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_SUMMARY_SCHEMA
        else {}
    )
    for candidate in (
        reconciliation.get("route_task_field_retest_result_reconciliation_summary"),
        reconciliation.get("route_task_field_retest_result_reconciliation"),
        reconciliation.get("robot_diagnostics_summary"),
        reconciliation.get("mobile_readonly_summary"),
        reconciliation.get("phone_safe_summary"),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
        diagnostics.get("route_task_field_retest_result_reconciliation_summary"),
        diagnostics.get("route_task_field_retest_result_reconciliation"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break

    source_schema, source_boundary = _route_task_field_retest_result_reconciliation_source_contract(
        reconciliation
    )
    status_source = summary_fragment.get("reconciliation_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("result_reconciliation_status")
    if not isinstance(status_source, dict):
        status_source = reconciliation.get("reconciliation_status")
    if not isinstance(status_source, dict):
        status_source = reconciliation.get("result_reconciliation_status")
    if not isinstance(status_source, dict):
        status_source = {}
    reconciliation_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("reconciliation_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or reconciliation.get("reconciliation_status")
        or reconciliation.get("status")
        or reconciliation.get("overall_status")
        or "blocked"
    )
    reconciliation_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or reconciliation.get("verdict")
        or "not_proven"
    )
    reconciliation_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or reconciliation.get("reason")
        or "route-task field retest result reconciliation consumed without explicit reason"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or reconciliation.get("safe_copy")
        or reconciliation.get("safe_phone_copy")
        or "Route-task field retest result reconciliation is metadata-only; delivery_success=false; primary_actions_enabled=false."
    )
    mobile_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            mobile_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    mobile_summary["safe_copy"] = safe_copy
    mobile_summary["safe_phone_copy"] = safe_copy
    source_ref = str(reconciliation.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    safe_evidence_ref = _safe_route_task_rehearsal_ref(summary_ref or source_ref)
    result_intake_source = (
        summary_fragment.get("result_intake_summary")
        if "result_intake_summary" in summary_fragment
        else summary_fragment.get("route_task_field_retest_result_intake_summary")
        if "route_task_field_retest_result_intake_summary" in summary_fragment
        else reconciliation.get("result_intake_summary")
        if "result_intake_summary" in reconciliation
        else reconciliation.get("route_task_field_retest_result_intake_summary")
    )
    result_reconciliation_source = (
        summary_fragment.get("result_reconciliation_summary")
        if "result_reconciliation_summary" in summary_fragment
        else summary_fragment.get("reconciliation_summary")
        if "reconciliation_summary" in summary_fragment
        else reconciliation.get("result_reconciliation_summary")
        if "result_reconciliation_summary" in reconciliation
        else reconciliation.get("reconciliation_summary")
    )
    operator_steps_source = (
        summary_fragment.get("operator_next_steps")
        if "operator_next_steps" in summary_fragment
        else reconciliation.get("operator_next_steps")
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else reconciliation.get("robot_diagnostics_summary")
        if isinstance(reconciliation.get("robot_diagnostics_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    lineage_summary, lineage_error = _route_task_field_retest_result_reconciliation_lineage(
        reconciliation,
        summary_fragment,
        result_intake_source,
        safe_evidence_ref,
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": reconciliation.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "reconciliation_status": {
                "status": reconciliation_status or "blocked",
                "verdict": reconciliation_verdict or "not_proven",
                "reason": reconciliation_reason,
            },
            "safe_evidence_ref": safe_evidence_ref,
            "same_evidence_ref_required": (
                _route_task_field_retest_result_reconciliation_requires_same_evidence_ref(
                    summary_fragment,
                    reconciliation,
                )
            ),
            "result_intake_summary": _safe_pc_route_debug_value(result_intake_source)
            or {
                "status": reconciliation_status or "blocked",
                "reason": "route-task field retest result reconciliation lacks intake summary",
            },
            "result_reconciliation_summary": _safe_pc_route_debug_value(result_reconciliation_source)
            or {
                "status": reconciliation_status or "blocked",
                "reason": "route-task field retest result reconciliation lacks reconciliation summary",
            },
            "operator_next_steps": _safe_pc_route_debug_value(operator_steps_source),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": reconciliation_status or "blocked",
                "reason": "result reconciliation consumed without explicit robot diagnostics summary",
            },
            "mobile_readonly_summary": mobile_summary,
            "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_GATE,
            "not_proven": _route_task_field_retest_result_reconciliation_not_proven(
                reconciliation,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )
    if lineage_summary:
        summary.update(lineage_summary)

    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_GATE
    ):
        summary.update(
            {
                "reconciliation_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result reconciliation schema or evidence boundary is unsupported",
                },
                "result_intake_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "result_reconciliation_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field retest result reconciliation is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task field retest result reconciliation is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary
    if not safe_evidence_ref:
        summary.update(
            {
                "reconciliation_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result reconciliation is missing evidence_ref",
                },
                "result_intake_summary": {
                    "status": "blocked",
                    "reason": "missing evidence_ref",
                },
                "result_reconciliation_summary": {
                    "status": "blocked",
                    "reason": "missing evidence_ref",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "reconciliation_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result reconciliation summary evidence_ref does not match source evidence_ref",
                },
                "result_intake_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
                "result_reconciliation_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if (
        not summary["same_evidence_ref_required"]
        or bool(lineage_error)
        or not _route_task_field_retest_result_reconciliation_has_disabled_actions(reconciliation)
        or _route_task_field_run_console_has_unsafe_fields(reconciliation)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(reconciliation)
    ):
        summary.update(
            {
                "reconciliation_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result reconciliation contains unsafe fields, weak evidence_ref constraints, enabled actions, or success wording",
                },
                "result_intake_summary": {
                    "status": "blocked",
                    "reason": "unsafe route-task field retest result reconciliation summary fields",
                },
                "result_reconciliation_summary": {
                    "status": "blocked",
                    "reason": "unsafe route-task field retest result reconciliation summary fields",
                },
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": lineage_error or "unsafe result reconciliation summary fields",
                },
                "lineage_status": {
                    "status": "blocked",
                    "reason": lineage_error or "unsafe result reconciliation summary fields",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field retest result reconciliation was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                    "safe_phone_copy": "Route-task field retest result reconciliation was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                },
                "safe_copy": "Route-task field retest result reconciliation was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest result reconciliation was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_material_pack(source):
    """构建 route-task field retest material pack 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        pack = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_material_pack_summary(
            source_path,
            read_error="route-task field retest material pack is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "material_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest material pack artifact missing",
                    },
                    "material_completeness": {
                        "status": "blocked",
                        "reason": "route-task field retest material pack artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "material pack artifact missing",
                    },
                    "safe_copy": "Route-task field retest material pack is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest material pack is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                pack = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "material_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest material pack: {exc}"
                        ),
                    },
                    "material_completeness": {
                        "status": "blocked",
                        "reason": "route-task field retest material pack JSON read error",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "material pack JSON read error",
                    },
                    "safe_copy": "Route-task field retest material pack could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest material pack could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_material_pack_summary(
        source_path,
        read_error="route-task field retest material pack is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(pack, dict):
        summary.update(
            {
                "material_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest material pack JSON must be an object",
                },
                "material_completeness": {
                    "status": "blocked",
                    "reason": "route-task field retest material pack shape is invalid",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "material pack JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest material pack shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest material pack shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = pack.get("diagnostics") if isinstance(pack.get("diagnostics"), dict) else {}
    # raw material pack 只做契约校验；Robot diagnostics 只消费白名单 summary，避免 raw path/凭据/完整 artifact 泄漏。
    summary_fragment = (
        pack
        if str(pack.get("schema") or "") == ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_SUMMARY_SCHEMA
        else {}
    )
    for candidate in (
        pack.get("route_task_field_retest_material_pack_summary"),
        pack.get("route_task_field_retest_material_pack"),
        pack.get("robot_diagnostics_route_task_field_retest_material_pack_summary"),
        pack.get("robot_diagnostics_summary"),
        pack.get("mobile_readonly_summary"),
        pack.get("phone_safe_summary"),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
        diagnostics.get("route_task_field_retest_material_pack_summary"),
        diagnostics.get("route_task_field_retest_material_pack"),
        diagnostics.get("robot_diagnostics_route_task_field_retest_material_pack_summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break

    source_schema, source_boundary = _route_task_field_retest_material_pack_source_contract(pack)
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": pack.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "material_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest material pack lacks a safe diagnostics summary",
                },
                "material_completeness": {
                    "status": "blocked",
                    "reason": "missing safe material pack summary",
                },
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe material pack summary",
                },
                "safe_copy": "Route-task field retest material pack is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest material pack is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("material_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("pack_status")
    if not isinstance(status_source, dict):
        status_source = {}
    material_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    material_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    material_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest material pack consumed without explicit reason"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or "Route-task field retest material pack is metadata-only; delivery_success=false; primary_actions_enabled=false."
    )
    mobile_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            mobile_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    mobile_summary["safe_copy"] = safe_copy
    mobile_summary["safe_phone_copy"] = safe_copy
    source_ref = str(pack.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    material_completeness_source = (
        summary_fragment.get("material_completeness")
        if "material_completeness" in summary_fragment
        else summary_fragment.get("materials_status")
        if "materials_status" in summary_fragment
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": pack.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "material_status": {
                "status": material_status or "blocked",
                "verdict": material_verdict or "not_proven",
                "reason": material_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required")
                if "same_evidence_ref_required" in summary_fragment
                else pack.get("same_evidence_ref_required", True)
            )
            is True,
            "material_completeness": _safe_pc_route_debug_dict(material_completeness_source)
            or {
                "status": material_status or "blocked",
                "reason": "route-task field retest material pack lacks material completeness summary",
            },
            "missing_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials")
                if isinstance(summary_fragment.get("missing_materials"), list)
                else summary_fragment.get("missing")
            ),
            "rejected_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials")
                if isinstance(summary_fragment.get("rejected_materials"), list)
                else summary_fragment.get("rejected")
            ),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                summary_fragment.get("operator_next_steps")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": material_status or "blocked",
                "reason": "material pack consumed without explicit robot diagnostics summary",
            },
            "mobile_readonly_summary": mobile_summary,
            "boundary": ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_GATE,
            "not_proven": _route_task_field_retest_material_pack_not_proven(pack, summary_fragment),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_GATE
    ):
        summary.update(
            {
                "material_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest material pack schema or evidence boundary is unsupported",
                },
                "material_completeness": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "missing_materials": [],
                "rejected_materials": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field retest material pack is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task field retest material pack is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "material_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest material pack is missing evidence_ref",
                },
                "material_completeness": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "material_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest material pack summary evidence_ref does not match source evidence_ref",
                },
                "material_completeness": {"status": "blocked", "reason": "same evidence_ref mismatch"},
            }
        )
        return summary
    if (
        not summary["same_evidence_ref_required"]
        or not _route_task_field_retest_material_pack_has_disabled_actions(pack, summary_fragment)
        or _route_task_field_run_console_has_unsafe_fields(pack)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(pack)
    ):
        summary.update(
            {
                "material_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest material pack contains unsafe fields, weak evidence_ref constraints, enabled actions, or success wording",
                },
                "material_completeness": {
                    "status": "blocked",
                    "reason": "unsafe material pack summary fields",
                },
                "missing_materials": [],
                "rejected_materials": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe material pack summary fields",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field retest material pack was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                    "safe_phone_copy": "Route-task field retest material pack was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                },
                "safe_copy": "Route-task field retest material pack was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest material pack was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_material_callback_packet(source):
    """构建 route-task field retest material callback packet 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        packet = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_material_callback_packet_summary(
            source_path,
            read_error="route-task field retest material callback packet is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "packet_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest material callback packet artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "material callback packet artifact missing",
                    },
                    "safe_copy": (
                        "Route-task field retest material callback packet is missing; "
                        "metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest material callback packet is missing; "
                        "metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                packet = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "packet_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading route-task field retest material callback "
                            f"packet: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "material callback packet JSON read error",
                    },
                    "safe_copy": (
                        "Route-task field retest material callback packet could not be read; "
                        "metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest material callback packet could not be read; "
                        "metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
    summary = _default_route_task_field_retest_material_callback_packet_summary(
        source_path,
        read_error="route-task field retest material callback packet is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(packet, dict):
        summary.update(
            {
                "packet_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest material callback packet JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "material callback packet JSON shape is invalid",
                },
                "safe_copy": (
                    "Route-task field retest material callback packet shape is invalid; "
                    "metadata remains blocked/not_proven."
                ),
                "safe_phone_copy": (
                    "Route-task field retest material callback packet shape is invalid; "
                    "metadata remains blocked/not_proven."
                ),
            }
        )
        return summary

    diagnostics = packet.get("diagnostics") if isinstance(packet.get("diagnostics"), dict) else {}
    # Robot 只消费 callback packet 的白名单 summary；raw artifact 仅用于 schema/boundary/ref 校验。
    summary_fragment = (
        packet
        if str(packet.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            packet.get("route_task_field_retest_material_callback_packet_summary"),
            packet.get("route_task_field_retest_material_callback_packet"),
            packet.get(
                "robot_diagnostics_route_task_field_retest_material_callback_packet_summary"
            ),
            packet.get("robot_diagnostics_summary"),
            packet.get("mobile_readonly_summary"),
            packet.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("route_task_field_retest_material_callback_packet_summary"),
            diagnostics.get("route_task_field_retest_material_callback_packet"),
            diagnostics.get(
                "robot_diagnostics_route_task_field_retest_material_callback_packet_summary"
            ),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else packet
    source_schema, source_boundary = (
        _route_task_field_retest_material_callback_packet_source_contract(contract_source)
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": packet.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "packet_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest material callback packet lacks a safe "
                        "diagnostics summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe material callback packet summary",
                },
                "safe_copy": (
                    "Route-task field retest material callback packet is blocked because "
                    "no safe summary was provided."
                ),
                "safe_phone_copy": (
                    "Route-task field retest material callback packet is blocked because "
                    "no safe summary was provided."
                ),
            }
        )
        return summary

    status_source = summary_fragment.get("packet_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("callback_packet_status")
    if not isinstance(status_source, dict):
        status_source = {}
    packet_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    packet_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    packet_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest material callback packet consumed without explicit reason"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Route-task field retest material callback packet is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    )
    if "delivery_success=false" not in safe_copy:
        # summary copy 必须保留 literal false，便于 Robot/mobile 侧围栏核对没有动作放行。
        safe_copy = (
            f"{safe_copy}; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    mobile_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            mobile_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    mobile_summary["safe_copy"] = safe_copy
    mobile_summary["safe_phone_copy"] = safe_copy
    source_ref = str(
        packet.get("safe_evidence_ref") or packet.get("evidence_ref") or ""
    ).strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "packet_status": {
                "status": packet_status or "blocked",
                "verdict": packet_verdict or "not_proven",
                "reason": packet_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "accepted_materials": _safe_pc_route_debug_value(
                summary_fragment.get("accepted_materials", summary_fragment.get("accepted_updates"))
            ),
            "missing_materials": _safe_pc_route_debug_value(
                summary_fragment.get("missing_materials", summary_fragment.get("missing_updates"))
            ),
            "rejected_materials": _safe_pc_route_debug_value(
                summary_fragment.get("rejected_materials", summary_fragment.get("rejected_updates"))
            ),
            "owner_follow_up": _safe_pc_route_debug_value(summary_fragment.get("owner_follow_up")),
            "review_decision_handoff": _safe_pc_route_debug_value(
                summary_fragment.get("review_decision_handoff")
            ),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required")
                if "same_evidence_ref_required" in summary_fragment
                else packet.get("same_evidence_ref_required")
            )
            is True,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": packet_status or "blocked",
                "reason": "material callback packet consumed without explicit robot summary",
            },
            "mobile_readonly_summary": mobile_summary,
            "boundary": ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_GATE,
            "not_proven": _route_task_field_retest_material_callback_packet_not_proven(
                packet,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    required_summary_fields = (
        isinstance(summary["accepted_materials"], list),
        isinstance(summary["missing_materials"], list),
        isinstance(summary["rejected_materials"], list),
        isinstance(summary["owner_follow_up"], list),
        isinstance(summary["review_decision_handoff"], dict),
        bool(summary["safe_copy"]),
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_GATE
    ):
        summary.update(
            {
                "packet_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest material callback packet schema or "
                        "evidence boundary is unsupported"
                    ),
                },
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "owner_follow_up": [],
                "review_decision_handoff": {},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "packet_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest material callback packet is missing "
                        "evidence_ref"
                    ),
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "packet_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest material callback packet summary "
                        "evidence_ref does not match source evidence_ref"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "packet_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest material callback packet is missing "
                        "required safe summary fields"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required material callback packet summary fields",
                },
            }
        )
        return summary
    if (
        not summary["same_evidence_ref_required"]
        or not _route_task_field_retest_material_callback_packet_has_disabled_actions(
            packet,
            summary_fragment,
        )
        or _route_task_field_run_console_has_unsafe_fields(packet)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(packet)
    ):
        summary.update(
            {
                "packet_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest material callback packet contains unsafe "
                        "fields, weak evidence_ref constraints, enabled actions, or success wording"
                    ),
                },
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "owner_follow_up": [],
                "review_decision_handoff": {},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe material callback packet summary fields",
                },
                "mobile_readonly_summary": {
                    "safe_copy": (
                        "Route-task field retest material callback packet was blocked "
                        "because summary fields could imply control, raw artifact access, "
                        "or delivery success."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest material callback packet was blocked "
                        "because summary fields could imply control, raw artifact access, "
                        "or delivery success."
                    ),
                },
                "safe_copy": (
                    "Route-task field retest material callback packet was blocked because "
                    "summary fields could imply control, raw artifact access, or delivery success."
                ),
                "safe_phone_copy": (
                    "Route-task field retest material callback packet was blocked because "
                    "summary fields could imply control, raw artifact access, or delivery success."
                ),
            }
        )
    return summary


def summarize_route_task_field_retest_material_callback_review_decision(source):
    """构建 route-task field retest material callback review decision 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        decision = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_material_callback_review_decision_summary(
            source_path,
            read_error=(
                "route-task field retest material callback review decision is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "review_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": (
                            "route-task field retest material callback review decision artifact missing"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "material callback review decision artifact missing",
                    },
                    "safe_copy": (
                        "Route-task field retest material callback review decision is "
                        "missing; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest material callback review decision is "
                        "missing; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "review_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading route-task field retest material callback "
                            f"review decision: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "material callback review decision JSON read error",
                    },
                    "safe_copy": (
                        "Route-task field retest material callback review decision could "
                        "not be read; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest material callback review decision could "
                        "not be read; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
    summary = _default_route_task_field_retest_material_callback_review_decision_summary(
        source_path,
        read_error="route-task field retest material callback review decision is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(decision, dict):
        summary.update(
            {
                "review_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest material callback review decision JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "material callback review decision JSON shape is invalid",
                },
                "safe_copy": (
                    "Route-task field retest material callback review decision shape is "
                    "invalid; metadata remains blocked/not_proven."
                ),
                "safe_phone_copy": (
                    "Route-task field retest material callback review decision shape is "
                    "invalid; metadata remains blocked/not_proven."
                ),
            }
        )
        return summary

    diagnostics = decision.get("diagnostics") if isinstance(decision.get("diagnostics"), dict) else {}
    # Robot 只消费本 gate 的 sanitized summary；raw artifact 只用于 schema/boundary/ref/false 栅栏校验。
    summary_fragment = (
        decision
        if str(decision.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            decision.get("route_task_field_retest_material_callback_review_decision_summary"),
            decision.get("route_task_field_retest_material_callback_review_decision"),
            decision.get(
                "robot_diagnostics_route_task_field_retest_material_callback_review_decision_summary"
            ),
            decision.get("material_callback_review_summary"),
            decision.get("robot_diagnostics_summary"),
            decision.get("robot_compatible_summary"),
            decision.get("mobile_readonly_summary"),
            decision.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("route_task_field_retest_material_callback_review_decision_summary"),
            diagnostics.get("route_task_field_retest_material_callback_review_decision"),
            diagnostics.get(
                "robot_diagnostics_route_task_field_retest_material_callback_review_decision_summary"
            ),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else decision
    source_schema, source_boundary = (
        _route_task_field_retest_material_callback_review_decision_source_contract(
            contract_source
        )
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": decision.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "review_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest material callback review decision lacks "
                        "a safe diagnostics summary"
                    ),
                },
                "review_decision": "blocked_material_callback_review_not_proven",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe material callback review decision summary",
                },
                "safe_copy": (
                    "Route-task field retest material callback review decision is blocked "
                    "because no safe summary was provided."
                ),
                "safe_phone_copy": (
                    "Route-task field retest material callback review decision is blocked "
                    "because no safe summary was provided."
                ),
            }
        )
        return summary

    status_source = summary_fragment.get("review_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    review_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("review_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    review_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    review_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest material callback review decision consumed without explicit reason"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Route-task field retest material callback review decision is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    )
    if "delivery_success=false" not in safe_copy:
        # copy 里保留 literal false，方便 Robot/mobile grep 围栏确认没有控制动作放行。
        safe_copy = (
            f"{safe_copy}; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(
        decision.get("safe_evidence_ref") or decision.get("evidence_ref") or ""
    ).strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    callback_review_summary = _safe_pc_route_debug_value(
        summary_fragment.get("material_callback_review_summary")
        if "material_callback_review_summary" in summary_fragment
        else summary_fragment.get("review_summary")
    )
    owner_acknowledgement = _safe_pc_route_debug_value(
        summary_fragment.get("owner_acknowledgement")
        if "owner_acknowledgement" in summary_fragment
        else decision.get("owner_acknowledgement")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "review_status": {
                "status": review_status or "blocked",
                "verdict": review_verdict or "not_proven",
                "reason": review_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required")
                if "same_evidence_ref_required" in summary_fragment
                else decision.get("same_evidence_ref_required")
            )
            is True,
            "review_decision": _redact_route_task_rehearsal_text(
                summary_fragment.get("review_decision")
                or summary_fragment.get("decision")
                or decision.get("review_decision")
                or decision.get("decision")
                or "blocked_material_callback_review_not_proven"
            ),
            "material_callback_review_summary": callback_review_summary
            or {
                "status": review_status or "blocked",
                "reason": "material callback review decision lacks review summary",
            },
            "accepted_materials": _safe_pc_route_debug_value(
                summary_fragment.get("accepted_materials", decision.get("accepted_materials"))
            ),
            "missing_materials": _safe_pc_route_debug_value(
                summary_fragment.get("missing_materials", decision.get("missing_materials"))
            ),
            "rejected_materials": _safe_pc_route_debug_value(
                summary_fragment.get("rejected_materials", decision.get("rejected_materials"))
            ),
            "owner_acknowledgement": owner_acknowledgement
            or {
                "status": "blocked",
                "reason": "material callback review decision lacks owner acknowledgement",
            },
            "owner_next_steps": _safe_pc_route_debug_value(
                summary_fragment.get("owner_next_steps", decision.get("owner_next_steps"))
            ),
            "next_required_evidence": _safe_pc_route_debug_value(
                summary_fragment.get(
                    "next_required_evidence",
                    decision.get("next_required_evidence"),
                )
            ),
            "rerun_commands": _safe_pc_route_debug_value(
                summary_fragment.get("rerun_commands", decision.get("rerun_commands"))
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": review_status or "blocked",
                "reason": (
                    "material callback review decision consumed without explicit robot "
                    "diagnostics summary"
                ),
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_GATE,
            "not_proven": _route_task_field_retest_material_callback_review_decision_not_proven(
                decision,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    required_summary_fields = (
        isinstance(summary["material_callback_review_summary"], (dict, str)),
        bool(summary["review_decision"]),
        isinstance(summary["accepted_materials"], list),
        isinstance(summary["missing_materials"], list),
        isinstance(summary["rejected_materials"], list),
        isinstance(summary["owner_acknowledgement"], (dict, list, str)),
        isinstance(summary["owner_next_steps"], list),
        isinstance(summary["next_required_evidence"], list),
        isinstance(summary["rerun_commands"], list),
        bool(summary["safe_copy"]),
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "review_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest material callback review decision schema "
                        "or evidence boundary is unsupported"
                    ),
                },
                "review_decision": "unsupported_material_callback_packet_schema_not_proven",
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "owner_next_steps": [],
                "next_required_evidence": [],
                "rerun_commands": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "review_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest material callback review decision is "
                        "missing evidence_ref"
                    ),
                },
                "review_decision": "blocked_material_callback_review_not_proven",
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "review_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest material callback review decision summary "
                        "evidence_ref does not match source evidence_ref"
                    ),
                },
                "review_decision": "evidence_ref_mismatch_rerun_not_proven",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "review_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest material callback review decision is "
                        "missing required safe summary fields"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required material callback review decision summary fields",
                },
            }
        )
        return summary
    if (
        not summary["same_evidence_ref_required"]
        or not _route_task_field_retest_material_callback_review_decision_has_disabled_actions(
            decision,
            summary_fragment,
        )
        or _route_task_field_run_console_has_unsafe_fields(decision)
        or _route_task_field_run_console_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(decision)
    ):
        summary.update(
            {
                "review_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest material callback review decision contains "
                        "unsafe fields, weak evidence_ref constraints, enabled actions, or "
                        "success wording"
                    ),
                },
                "review_decision": "unsafe_success_claim_rejected_not_proven",
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "owner_next_steps": [],
                "next_required_evidence": [],
                "rerun_commands": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe material callback review decision summary fields",
                },
                "safe_copy": (
                    "Route-task field retest material callback review decision was blocked "
                    "because summary fields could imply control actions, raw artifact "
                    "access, or delivery success."
                ),
                "safe_phone_copy": (
                    "Route-task field retest material callback review decision was blocked "
                    "because summary fields could imply control actions, raw artifact "
                    "access, or delivery success."
                ),
            }
        )
    return summary


def summarize_route_task_field_retest_operator_drill(source):
    """构建 route-task field retest operator drill 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        drill = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_operator_drill_summary(
            source_path,
            read_error="route-task field retest operator drill is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "drill_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest operator drill artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "operator drill artifact missing",
                    },
                    "safe_copy": "Route-task field retest operator drill is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest operator drill is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                drill = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "drill_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest operator drill: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "operator drill JSON read error",
                    },
                    "safe_copy": "Route-task field retest operator drill could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest operator drill could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_operator_drill_summary(
        source_path,
        read_error="route-task field retest operator drill is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(drill, dict):
        summary.update(
            {
                "drill_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest operator drill JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "operator drill JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest operator drill shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest operator drill shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = drill.get("diagnostics") if isinstance(drill.get("diagnostics"), dict) else {}
    # Robot 只消费 drill 的安全摘要，不转发 PC artifact 内的 raw command、路径、材料或现场记录。
    summary_fragment = (
        drill
        if str(drill.get("schema") or "") == ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_SUMMARY_SCHEMA
        else {}
    )
    for candidate in (
        drill.get("route_task_field_retest_operator_drill_summary"),
        drill.get("route_task_field_retest_operator_drill"),
        drill.get("robot_diagnostics_summary"),
        drill.get("robot_diagnostics_route_task_field_retest_operator_drill_summary"),
        drill.get("mobile_readonly_summary"),
        drill.get("phone_safe_summary"),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
        diagnostics.get("route_task_field_retest_operator_drill_summary"),
        diagnostics.get("route_task_field_retest_operator_drill"),
        diagnostics.get("robot_diagnostics_route_task_field_retest_operator_drill_summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break

    source_schema, source_boundary = _route_task_field_retest_operator_drill_source_contract(drill)
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": drill.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "drill_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest operator drill lacks a safe diagnostics summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe operator drill summary",
                },
                "safe_copy": "Route-task field retest operator drill is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest operator drill is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("drill_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    drill_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    drill_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    drill_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest operator drill consumed without explicit reason"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or "Route-task field retest operator drill is metadata-only; delivery_success=false; primary_actions_enabled=false."
    )
    safe_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            safe_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    safe_summary["safe_copy"] = safe_copy
    safe_summary["safe_phone_copy"] = safe_copy
    source_ref = str(drill.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": drill.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "drill_status": {
                "status": drill_status or "blocked",
                "verdict": drill_verdict or "not_proven",
                "reason": drill_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required")
                if "same_evidence_ref_required" in summary_fragment
                else drill.get("same_evidence_ref_required", True)
            )
            is True,
            "next_command_labels": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_command_labels")
                if isinstance(summary_fragment.get("next_command_labels"), list)
                else summary_fragment.get("command_labels")
            ),
            "missing_material_prompts": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_material_prompts")
                if isinstance(summary_fragment.get("missing_material_prompts"), list)
                else summary_fragment.get("missing_materials")
            ),
            "operator_callback_checklist": _safe_route_task_rehearsal_list(
                summary_fragment.get("operator_callback_checklist")
                if isinstance(summary_fragment.get("operator_callback_checklist"), list)
                else summary_fragment.get("callback_checklist")
            ),
            "safe_summary": safe_summary,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": drill_status or "blocked",
                "reason": "operator drill consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_GATE,
            "not_proven": _route_task_field_retest_operator_drill_not_proven(
                drill,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_GATE
    ):
        summary.update(
            {
                "drill_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest operator drill schema or evidence boundary is unsupported",
                },
                "next_command_labels": [],
                "missing_material_prompts": [],
                "operator_callback_checklist": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "safe_summary": {
                    "safe_copy": "Route-task field retest operator drill is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task field retest operator drill is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "drill_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest operator drill is missing evidence_ref",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "drill_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest operator drill summary evidence_ref does not match source evidence_ref",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if (
        not summary["same_evidence_ref_required"]
        or not _route_task_field_retest_operator_drill_has_disabled_actions(drill, summary_fragment)
        or _route_task_field_retest_operator_drill_has_unsafe_fields(drill)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(drill)
    ):
        summary.update(
            {
                "drill_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest operator drill contains unsafe fields, weak evidence_ref constraints, enabled actions, or success wording",
                },
                "next_command_labels": [],
                "missing_material_prompts": [],
                "operator_callback_checklist": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe operator drill summary fields",
                },
                "safe_summary": {
                    "safe_copy": "Route-task field retest operator drill was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                    "safe_phone_copy": "Route-task field retest operator drill was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                },
                "safe_copy": "Route-task field retest operator drill was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest operator drill was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_drill_console(source):
    """构建 route-task field retest drill console 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        console = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_drill_console_summary(
            source_path,
            read_error="route-task field retest drill console is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "console_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest drill console artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "drill console artifact missing",
                    },
                    "safe_copy": "Route-task field retest drill console is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest drill console is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                console = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "console_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest drill console: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "drill console JSON read error",
                    },
                    "safe_copy": "Route-task field retest drill console could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest drill console could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_drill_console_summary(
        source_path,
        read_error="route-task field retest drill console is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(console, dict):
        summary.update(
            {
                "console_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest drill console JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "drill console JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest drill console shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest drill console shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = console.get("diagnostics") if isinstance(console.get("diagnostics"), dict) else {}
    # Robot 只消费 console 的白名单摘要；raw command、ACK、路径、材料和现场记录不能穿过 diagnostics 边界。
    summary_fragment = (
        console
        if str(console.get("schema") or "") == ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_SUMMARY_SCHEMA
        else {}
    )
    # 完整 summary schema 已经是安全消费对象；不能再被内部 robot_diagnostics_summary 子对象覆盖。
    if not summary_fragment:
        for candidate in (
            console.get("route_task_field_retest_drill_console_summary"),
            console.get("route_task_field_retest_drill_console"),
            console.get("robot_diagnostics_route_task_field_retest_drill_console_summary"),
            console.get("robot_compatible_summary"),
            console.get("robot_diagnostics_summary"),
            console.get("mobile_readonly_summary"),
            console.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("route_task_field_retest_drill_console_summary"),
            diagnostics.get("route_task_field_retest_drill_console"),
            diagnostics.get("robot_diagnostics_route_task_field_retest_drill_console_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    source_schema, source_boundary = _route_task_field_retest_drill_console_source_contract(console)
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": console.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "console_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest drill console lacks a safe diagnostics summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe drill console summary",
                },
                "safe_copy": "Route-task field retest drill console is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest drill console is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("console_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("drill_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    console_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    console_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    console_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest drill console consumed without explicit reason"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or "Route-task field retest drill console is metadata-only; delivery_success=false; primary_actions_enabled=false."
    )
    safe_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            safe_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    safe_summary["safe_copy"] = safe_copy
    safe_summary["safe_phone_copy"] = safe_copy
    source_ref = str(console.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": console.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "console_status": {
                "status": console_status or "blocked",
                "verdict": console_verdict or "not_proven",
                "reason": console_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required")
                if "same_evidence_ref_required" in summary_fragment
                else console.get("same_evidence_ref_required", True)
            )
            is True,
            "command_labels": _safe_route_task_rehearsal_list(
                summary_fragment.get("command_labels")
                if isinstance(summary_fragment.get("command_labels"), list)
                else summary_fragment.get("next_command_labels")
            ),
            "safe_checklist": _safe_route_task_rehearsal_list(
                summary_fragment.get("safe_checklist")
                if isinstance(summary_fragment.get("safe_checklist"), list)
                else summary_fragment.get("operator_checklist")
            ),
            "missing_material_prompts": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_material_prompts")
                if isinstance(summary_fragment.get("missing_material_prompts"), list)
                else summary_fragment.get("missing_materials")
            ),
            "operator_callback_checklist": _safe_route_task_rehearsal_list(
                summary_fragment.get("operator_callback_checklist")
                if isinstance(summary_fragment.get("operator_callback_checklist"), list)
                else summary_fragment.get("callback_checklist")
            ),
            "safe_summary": safe_summary,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": console_status or "blocked",
                "reason": "drill console consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_GATE,
            "not_proven": _route_task_field_retest_drill_console_not_proven(
                console,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_GATE
    ):
        summary.update(
            {
                "console_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest drill console schema or evidence boundary is unsupported",
                },
                "command_labels": [],
                "safe_checklist": [],
                "missing_material_prompts": [],
                "operator_callback_checklist": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "safe_summary": {
                    "safe_copy": "Route-task field retest drill console is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task field retest drill console is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "console_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest drill console is missing evidence_ref",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "console_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest drill console summary evidence_ref does not match source evidence_ref",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if (
        not summary["same_evidence_ref_required"]
        or not _route_task_field_retest_drill_console_has_disabled_actions(
            console,
            summary_fragment,
        )
        or _route_task_field_run_console_has_unsafe_fields(console)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(console)
    ):
        summary.update(
            {
                "console_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest drill console contains unsafe fields, weak evidence_ref constraints, enabled actions, or success wording",
                },
                "command_labels": [],
                "safe_checklist": [],
                "missing_material_prompts": [],
                "operator_callback_checklist": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe drill console summary fields",
                },
                "safe_summary": {
                    "safe_copy": "Route-task field retest drill console was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                    "safe_phone_copy": "Route-task field retest drill console was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                },
                "safe_copy": "Route-task field retest drill console was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest drill console was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_acceptance_brief(source):
    """构建 route-task field retest acceptance brief 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        brief = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_acceptance_brief_summary(
            source_path,
            read_error="route-task field retest acceptance brief is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "acceptance_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest acceptance brief artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance brief artifact missing",
                    },
                    "safe_copy": "Route-task field retest acceptance brief is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest acceptance brief is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                brief = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "acceptance_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest acceptance brief: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance brief JSON read error",
                    },
                    "safe_copy": "Route-task field retest acceptance brief could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest acceptance brief could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_acceptance_brief_summary(
        source_path,
        read_error="route-task field retest acceptance brief is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(brief, dict):
        summary.update(
            {
                "acceptance_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance brief JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "acceptance brief JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest acceptance brief shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest acceptance brief shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = brief.get("diagnostics") if isinstance(brief.get("diagnostics"), dict) else {}
    # Robot 只读取 brief 的安全摘要字段；验收材料、raw artifact 和任何控制语义都留在 PC gate 外部。
    summary_fragment = (
        brief
        if str(brief.get("schema") or "") == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_SUMMARY_SCHEMA
        else {}
    )
    for candidate in (
        brief.get("route_task_field_retest_acceptance_brief_summary"),
        brief.get("route_task_field_retest_acceptance_brief"),
        brief.get("robot_compatible_summary"),
        brief.get("robot_diagnostics_summary"),
        brief.get("mobile_readonly_summary"),
        brief.get("phone_safe_summary"),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
        diagnostics.get("route_task_field_retest_acceptance_brief_summary"),
        diagnostics.get("route_task_field_retest_acceptance_brief"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break

    source_schema, source_boundary = _route_task_field_retest_acceptance_brief_source_contract(brief)
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": brief.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "acceptance_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance brief lacks a safe diagnostics summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe acceptance brief summary",
                },
                "safe_copy": "Route-task field retest acceptance brief is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest acceptance brief is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("acceptance_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    acceptance_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    acceptance_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    acceptance_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest acceptance brief consumed without explicit reason"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or "Route-task field retest acceptance brief is metadata-only; delivery_success=false; primary_actions_enabled=false."
    )
    safe_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            safe_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    safe_summary["safe_copy"] = safe_copy
    safe_summary["safe_phone_copy"] = safe_copy
    source_ref = str(brief.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    owner_handoff = (
        summary_fragment.get("owner_handoff")
        if isinstance(summary_fragment.get("owner_handoff"), dict)
        else summary_fragment.get("handoff")
        if isinstance(summary_fragment.get("handoff"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": brief.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "acceptance_status": {
                "status": acceptance_status or "blocked",
                "verdict": acceptance_verdict or "not_proven",
                "reason": acceptance_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required")
                if "same_evidence_ref_required" in summary_fragment
                else brief.get("same_evidence_ref_required", True)
            )
            is True,
            "safe_summary": safe_summary,
            "pass_fail_criteria": _safe_route_task_rehearsal_list(
                summary_fragment.get("pass_fail_criteria")
            ),
            "required_evidence_packet": _safe_route_task_rehearsal_list(
                summary_fragment.get("required_evidence_packet")
                if isinstance(summary_fragment.get("required_evidence_packet"), list)
                else summary_fragment.get("required_evidence")
            ),
            "owner_handoff": _safe_pc_route_debug_dict(owner_handoff),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": acceptance_status or "blocked",
                "reason": "acceptance brief consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_GATE,
            "not_proven": _route_task_field_retest_acceptance_brief_not_proven(
                brief,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_GATE
    ):
        summary.update(
            {
                "acceptance_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance brief schema or evidence boundary is unsupported",
                },
                "pass_fail_criteria": [],
                "required_evidence_packet": [],
                "owner_handoff": {},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "safe_summary": {
                    "safe_copy": "Route-task field retest acceptance brief is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task field retest acceptance brief is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "acceptance_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance brief is missing evidence_ref",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "acceptance_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance brief summary evidence_ref does not match source evidence_ref",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if (
        not summary["same_evidence_ref_required"]
        or not _route_task_field_retest_acceptance_brief_has_disabled_actions(
            brief,
            summary_fragment,
        )
        or _route_task_field_run_console_has_unsafe_fields(brief)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(brief)
    ):
        summary.update(
            {
                "acceptance_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance brief contains unsafe fields, weak evidence_ref constraints, enabled actions, or success wording",
                },
                "pass_fail_criteria": [],
                "required_evidence_packet": [],
                "owner_handoff": {},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe acceptance brief summary fields",
                },
                "safe_summary": {
                    "safe_copy": "Route-task field retest acceptance brief was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                    "safe_phone_copy": "Route-task field retest acceptance brief was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                },
                "safe_copy": "Route-task field retest acceptance brief was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest acceptance brief was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_acceptance_review_decision(source):
    """构建 route-task field retest acceptance review decision 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        decision = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_acceptance_review_decision_summary(
            source_path,
            read_error="route-task field retest acceptance review decision is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "decision_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest acceptance review decision artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance review decision artifact missing",
                    },
                    "safe_copy": "Route-task field retest acceptance review decision is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest acceptance review decision is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "decision_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest acceptance review decision: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance review decision JSON read error",
                    },
                    "safe_copy": "Route-task field retest acceptance review decision could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest acceptance review decision could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_acceptance_review_decision_summary(
        source_path,
        read_error="route-task field retest acceptance review decision is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(decision, dict):
        summary.update(
            {
                "decision_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance review decision JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "acceptance review decision JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest acceptance review decision shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest acceptance review decision shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = decision.get("diagnostics") if isinstance(decision.get("diagnostics"), dict) else {}
    # Robot 只消费 Autonomy 产出的安全 summary；artifact 原文、材料正文和控制语义不能进入 diagnostics。
    summary_fragment = (
        decision
        if str(decision.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            decision.get("route_task_field_retest_acceptance_review_decision_summary"),
            decision.get("route_task_field_retest_acceptance_review_decision"),
            decision.get(
                "robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary"
            ),
            decision.get("robot_compatible_summary"),
            decision.get("robot_diagnostics_summary"),
            decision.get("mobile_readonly_summary"),
            decision.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("route_task_field_retest_acceptance_review_decision_summary"),
            diagnostics.get("route_task_field_retest_acceptance_review_decision"),
            diagnostics.get(
                "robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary"
            ),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else decision
    source_schema, source_boundary = (
        _route_task_field_retest_acceptance_review_decision_source_contract(contract_source)
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": decision.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "decision_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance review decision lacks a safe diagnostics summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe acceptance review decision summary",
                },
                "safe_copy": "Route-task field retest acceptance review decision is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest acceptance review decision is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("decision_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("review_decision_status")
    if not isinstance(status_source, dict):
        status_source = {}
    source_acceptance_status = summary_fragment.get("source_acceptance_brief_status")
    if not isinstance(source_acceptance_status, dict):
        source_acceptance_status = summary_fragment.get("acceptance_brief_status")
    if not isinstance(source_acceptance_status, dict):
        source_acceptance_status = {}
    decision_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("decision_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    decision_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    decision_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest acceptance review decision consumed without explicit reason"
    )
    review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("review_decision")
        or status_source.get("decision")
        or decision_verdict
        or "not_proven"
    )
    safe_copy_source = summary_fragment.get("safe_copy") or summary_fragment.get("safe_phone_copy")
    safe_copy = _safe_pc_route_debug_value(
        safe_copy_source
        or (
            "Route-task field retest acceptance review decision is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # grep 围栏必须留在输出里，避免 safe alias 被误读成 Start/Confirm/Cancel 授权。
        safe_copy_text = (
            f"{safe_copy_text}; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(decision.get("safe_evidence_ref") or decision.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "decision_status": {
                "status": decision_status or "blocked",
                "verdict": decision_verdict or "not_proven",
                "reason": decision_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "source_acceptance_brief_status": _safe_pc_route_debug_dict(
                source_acceptance_status
            )
            or {
                "status": "blocked",
                "verdict": "not_proven",
                "reason": "acceptance review decision lacks source acceptance brief status",
            },
            "review_decision": review_decision or "not_proven",
            "material_backfill_status": _safe_pc_route_debug_value(
                summary_fragment.get("material_backfill_status")
            ),
            "missing_materials": _safe_pc_route_debug_value(summary_fragment.get("missing_materials")),
            "owner_handoff": _safe_pc_route_debug_value(summary_fragment.get("owner_handoff")),
            "next_required_evidence": _safe_pc_route_debug_value(
                summary_fragment.get("next_required_evidence")
            ),
            "rerun_commands": _safe_pc_route_debug_value(summary_fragment.get("rerun_commands")),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": decision_status or "blocked",
                "reason": "acceptance review decision consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_GATE,
            "not_proven": _route_task_field_retest_acceptance_review_decision_not_proven(
                decision,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )

    required_summary_fields = (
        bool(summary["source_acceptance_brief_status"]),
        bool(summary["review_decision"]),
        bool(summary["material_backfill_status"]),
        isinstance(summary["missing_materials"], list),
        bool(summary["owner_handoff"]),
        isinstance(summary["next_required_evidence"], list),
        isinstance(summary["rerun_commands"], list),
        bool(summary["safe_copy"]),
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "decision_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance review decision schema or evidence boundary is unsupported",
                },
                "material_backfill_status": {},
                "missing_materials": [],
                "owner_handoff": {},
                "next_required_evidence": [],
                "rerun_commands": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "decision_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance review decision is missing evidence_ref",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "decision_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance review decision summary evidence_ref does not match source evidence_ref",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not _route_task_field_retest_acceptance_review_decision_requires_same_evidence_ref(
        summary_fragment
    ):
        summary.update(
            {
                "decision_status": {
                    "status": "same_evidence_ref_required_false",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance review decision must require the same evidence_ref",
                },
                "same_evidence_ref_required": False,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "decision_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance review decision is missing required safe summary fields",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required acceptance review decision summary fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_acceptance_review_decision_has_disabled_actions(
            decision,
            summary_fragment,
        )
        or _route_task_field_run_console_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "decision_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance review decision contains unsafe fields, enabled actions, raw details, or success wording",
                },
                "material_backfill_status": {},
                "missing_materials": [],
                "owner_handoff": {},
                "next_required_evidence": [],
                "rerun_commands": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe acceptance review decision summary fields",
                },
                "safe_copy": "Route-task field retest acceptance review decision was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest acceptance review decision was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_acceptance_execution_pack(source):
    """构建 route-task field retest acceptance execution pack 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        pack = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_acceptance_execution_pack_summary(
            source_path,
            read_error="route-task field retest acceptance execution pack is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "execution_pack_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest acceptance execution pack artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution pack artifact missing",
                    },
                    "safe_copy": "Route-task field retest acceptance execution pack is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest acceptance execution pack is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                pack = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "execution_pack_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest acceptance execution pack: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution pack JSON read error",
                    },
                    "safe_copy": "Route-task field retest acceptance execution pack could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest acceptance execution pack could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_acceptance_execution_pack_summary(
        source_path,
        read_error="route-task field retest acceptance execution pack is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(pack, dict):
        summary.update(
            {
                "execution_pack_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance execution pack JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "acceptance execution pack JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest acceptance execution pack shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest acceptance execution pack shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = pack.get("diagnostics") if isinstance(pack.get("diagnostics"), dict) else {}
    # Robot 只接收安全摘要；执行包原文里的现场命令、材料目录或控制语义不能透传到 status。
    summary_fragment = (
        pack
        if str(pack.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            pack.get("route_task_field_retest_acceptance_execution_pack_summary"),
            pack.get("route_task_field_retest_acceptance_execution_pack"),
            pack.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary"
            ),
            pack.get("robot_compatible_summary"),
            pack.get("robot_diagnostics_summary"),
            pack.get("mobile_readonly_summary"),
            pack.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("route_task_field_retest_acceptance_execution_pack_summary"),
            diagnostics.get("route_task_field_retest_acceptance_execution_pack"),
            diagnostics.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary"
            ),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else pack
    source_schema, source_boundary = (
        _route_task_field_retest_acceptance_execution_pack_source_contract(contract_source)
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": pack.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "execution_pack_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance execution pack lacks a safe diagnostics summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe acceptance execution pack summary",
                },
                "safe_copy": "Route-task field retest acceptance execution pack is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest acceptance execution pack is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("execution_pack_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("pack_status")
    if not isinstance(status_source, dict):
        status_source = {}
    execution_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("execution_pack_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    execution_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    execution_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest acceptance execution pack consumed without explicit reason"
    )
    safe_copy_source = summary_fragment.get("safe_copy") or summary_fragment.get("safe_phone_copy")
    safe_copy = _safe_pc_route_debug_value(
        safe_copy_source
        or (
            "Route-task field retest acceptance execution pack is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # grep 围栏必须跟随 safe alias，避免现场执行包文案被误解为已完成交付。
        safe_copy_text = (
            f"{safe_copy_text}; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(pack.get("safe_evidence_ref") or pack.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    review_decision_source = summary_fragment.get("review_decision_source")
    if not isinstance(review_decision_source, dict):
        review_decision_source = summary_fragment.get("source_acceptance_review_decision")
    if not isinstance(review_decision_source, dict):
        review_decision_source = {}
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "execution_pack_status": {
                "status": execution_status or "blocked",
                "verdict": execution_verdict or "not_proven",
                "reason": execution_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "review_decision_source": _safe_pc_route_debug_dict(review_decision_source),
            "owner_checklist": _safe_pc_route_debug_value(summary_fragment.get("owner_checklist")),
            "rerun_commands": _safe_pc_route_debug_value(summary_fragment.get("rerun_commands")),
            "safe_evidence_bundle": _safe_pc_route_debug_value(
                summary_fragment.get("safe_evidence_bundle")
            ),
            "required_route_elevator_materials": _safe_pc_route_debug_value(
                summary_fragment.get("required_route_elevator_materials")
            ),
            "handoff_owner": _safe_pc_route_debug_value(summary_fragment.get("handoff_owner")),
            "next_required_evidence": _safe_pc_route_debug_value(
                summary_fragment.get("next_required_evidence")
            ),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": execution_status or "blocked",
                "reason": "acceptance execution pack consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_GATE,
            "not_proven": _route_task_field_retest_acceptance_execution_pack_not_proven(
                pack,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )

    required_summary_fields = (
        bool(summary["review_decision_source"]),
        isinstance(summary["owner_checklist"], list) and bool(summary["owner_checklist"]),
        isinstance(summary["rerun_commands"], list) and bool(summary["rerun_commands"]),
        bool(summary["safe_evidence_bundle"]),
        isinstance(summary["required_route_elevator_materials"], list)
        and bool(summary["required_route_elevator_materials"]),
        bool(summary["handoff_owner"]),
        isinstance(summary["next_required_evidence"], list),
        bool(summary["safe_copy"]),
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_GATE
    ):
        summary.update(
            {
                "execution_pack_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance execution pack schema or evidence boundary is unsupported",
                },
                "owner_checklist": [],
                "rerun_commands": [],
                "safe_evidence_bundle": {},
                "required_route_elevator_materials": [],
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "execution_pack_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance execution pack is missing evidence_ref",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "execution_pack_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance execution pack summary evidence_ref does not match source evidence_ref",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not _route_task_field_retest_acceptance_execution_pack_requires_same_evidence_ref(
        summary_fragment
    ):
        summary.update(
            {
                "execution_pack_status": {
                    "status": "same_evidence_ref_required_false",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance execution pack must require the same evidence_ref",
                },
                "same_evidence_ref_required": False,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "execution_pack_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance execution pack is missing required safe summary fields",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required acceptance execution pack summary fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_acceptance_execution_pack_has_disabled_actions(
            pack,
            summary_fragment,
        )
        or _route_task_field_run_console_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "execution_pack_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance execution pack contains unsafe fields, enabled actions, raw details, or success wording",
                },
                "owner_checklist": [],
                "rerun_commands": [],
                "safe_evidence_bundle": {},
                "required_route_elevator_materials": [],
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe acceptance execution pack summary fields",
                },
                "safe_copy": "Route-task field retest acceptance execution pack was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest acceptance execution pack was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_acceptance_execution_callback_intake(source):
    """构建 route-task field retest acceptance execution callback intake 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        intake = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_acceptance_execution_callback_intake_summary(
            source_path,
            read_error=(
                "route-task field retest acceptance execution callback intake is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "callback_intake_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": (
                            "route-task field retest acceptance execution callback intake "
                            "summary missing"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution callback intake summary missing",
                    },
                    "safe_copy": (
                        "Route-task field retest acceptance execution callback intake is "
                        "missing; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest acceptance execution callback intake is "
                        "missing; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "callback_intake_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading route-task field retest acceptance "
                            f"execution callback intake: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution callback intake JSON read error",
                    },
                    "safe_copy": (
                        "Route-task field retest acceptance execution callback intake "
                        "could not be read; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest acceptance execution callback intake "
                        "could not be read; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
    summary = _default_route_task_field_retest_acceptance_execution_callback_intake_summary(
        source_path,
        read_error=(
            "route-task field retest acceptance execution callback intake is not configured"
        ),
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(intake, dict):
        summary.update(
            {
                "callback_intake_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback intake JSON "
                        "must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "acceptance execution callback intake JSON shape is invalid",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution callback intake shape is "
                    "invalid; metadata remains blocked/not_proven."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution callback intake shape is "
                    "invalid; metadata remains blocked/not_proven."
                ),
            }
        )
        return summary

    diagnostics = intake.get("diagnostics") if isinstance(intake.get("diagnostics"), dict) else {}
    # 本 gate 名字很长；只消费完全匹配的 key，避免误接旧 callback_intake 或 result_callback_intake。
    summary_fragment = (
        intake
        if str(intake.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            intake.get("route_task_field_retest_acceptance_execution_callback_intake_summary"),
            intake.get("route_task_field_retest_acceptance_execution_callback_intake"),
            intake.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_intake_summary"
            ),
            intake.get("robot_compatible_summary"),
            intake.get("robot_diagnostics_summary"),
            intake.get("mobile_readonly_summary"),
            intake.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get(
                "route_task_field_retest_acceptance_execution_callback_intake_summary"
            ),
            diagnostics.get("route_task_field_retest_acceptance_execution_callback_intake"),
            diagnostics.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_intake_summary"
            ),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if (
        str(intake.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SCHEMA
        and not str(summary_fragment.get("schema") or "")
    ):
        # 直接 artifact 可作为安全摘要消费；泛用 robot_diagnostics_summary 不能覆盖 artifact contract。
        summary_fragment = intake
    if not summary_fragment and (intake.get("schema") or intake.get("evidence_boundary")):
        # artifact 或带 contract 的对象要进入 contract 检查；unsupported source 也能给出明确失败原因。
        summary_fragment = intake

    contract_source = summary_fragment if summary_fragment else intake
    source_schema, source_boundary = (
        _route_task_field_retest_acceptance_execution_callback_intake_source_contract(
            contract_source
        )
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": intake.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "callback_intake_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback intake lacks "
                        "a safe diagnostics summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe acceptance execution callback intake summary",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution callback intake is blocked "
                    "because no safe summary was provided."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution callback intake is blocked "
                    "because no safe summary was provided."
                ),
            }
        )
        return summary

    status_source = summary_fragment.get("callback_intake_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("intake_status")
    if not isinstance(status_source, dict):
        status_source = {}
    callback_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("callback_intake_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    callback_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    callback_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or (
            "route-task field retest acceptance execution callback intake consumed "
            "without explicit reason"
        )
    )
    safe_copy_source = summary_fragment.get("safe_copy") or summary_fragment.get("safe_phone_copy")
    safe_copy = _safe_pc_route_debug_value(
        safe_copy_source
        or (
            "Route-task field retest acceptance execution callback intake is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # phone/mobile copy 保留 literal boundary，方便围栏确认不会启用主动作。
        safe_copy_text = (
            f"{safe_copy_text}; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(intake.get("safe_evidence_ref") or intake.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    source_pack = summary_fragment.get("source_execution_pack")
    if not isinstance(source_pack, dict):
        source_pack = summary_fragment.get("source_acceptance_execution_pack")
    if not isinstance(source_pack, dict):
        source_pack = {}
    safe_callback_packet = summary_fragment.get("safe_callback_packet")
    if not isinstance(safe_callback_packet, dict):
        safe_callback_packet = summary_fragment.get("callback_packet")
    if not isinstance(safe_callback_packet, dict):
        safe_callback_packet = {}
    evidence_ref_status = summary_fragment.get("evidence_ref_status")
    if not isinstance(evidence_ref_status, dict):
        evidence_ref_status = summary_fragment.get("same_evidence_ref_status")
    if not isinstance(evidence_ref_status, dict):
        evidence_ref_status = {}
    received_materials = _safe_pc_route_debug_value(
        summary_fragment.get("received_materials", summary_fragment.get("accepted_materials"))
    )
    missing_materials = _safe_pc_route_debug_value(summary_fragment.get("missing_materials"))
    rejected_materials = _safe_pc_route_debug_value(summary_fragment.get("rejected_materials"))
    owner_next_steps = _safe_pc_route_debug_value(
        summary_fragment.get("owner_next_steps", summary_fragment.get("owner_follow_up"))
    )
    next_required_evidence = _safe_pc_route_debug_value(
        summary_fragment.get("next_required_evidence")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "callback_intake_status": {
                "status": callback_status or "blocked",
                "verdict": callback_verdict or "not_proven",
                "reason": callback_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "source_execution_pack": _safe_pc_route_debug_dict(source_pack),
            "safe_callback_packet": _safe_pc_route_debug_dict(safe_callback_packet),
            "evidence_ref_status": _safe_pc_route_debug_dict(evidence_ref_status),
            "received_materials": received_materials,
            "missing_materials": missing_materials,
            "rejected_materials": rejected_materials,
            "owner_next_steps": owner_next_steps,
            "next_required_evidence": next_required_evidence,
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": callback_status or "blocked",
                "reason": (
                    "acceptance execution callback intake consumed without explicit "
                    "robot diagnostics summary"
                ),
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_GATE,
            "not_proven": (
                _route_task_field_retest_acceptance_execution_callback_intake_not_proven(
                    intake,
                    summary_fragment,
                )
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )

    required_summary_fields = (
        bool(summary["source_execution_pack"]),
        bool(summary["safe_callback_packet"]),
        bool(summary["evidence_ref_status"]),
        isinstance(summary["received_materials"], list),
        isinstance(summary["missing_materials"], list),
        isinstance(summary["rejected_materials"], list),
        isinstance(summary["owner_next_steps"], list),
        isinstance(summary["next_required_evidence"], list),
        bool(summary["safe_copy"]),
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_GATE
    ):
        summary.update(
            {
                "callback_intake_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback intake "
                        "schema or evidence boundary is unsupported"
                    ),
                },
                "source_execution_pack": {},
                "safe_callback_packet": {},
                "evidence_ref_status": {},
                "received_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "owner_next_steps": [],
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "callback_intake_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback intake is "
                        "missing evidence_ref"
                    ),
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "callback_intake_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback intake "
                        "summary evidence_ref does not match source evidence_ref"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not _route_task_field_retest_acceptance_execution_callback_intake_requires_same_evidence_ref(
        summary_fragment
    ):
        summary.update(
            {
                "callback_intake_status": {
                    "status": "same_evidence_ref_required_false",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback intake must "
                        "require the same evidence_ref"
                    ),
                },
                "same_evidence_ref_required": False,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "callback_intake_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback intake is "
                        "missing required safe summary fields"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required acceptance execution callback intake summary fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_acceptance_execution_callback_intake_has_disabled_actions(
            intake,
            summary_fragment,
        )
        or _route_task_field_run_console_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "callback_intake_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback intake "
                        "contains unsafe fields, enabled actions, raw details, or success wording"
                    ),
                },
                "source_execution_pack": {},
                "safe_callback_packet": {},
                "evidence_ref_status": {},
                "received_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "owner_next_steps": [],
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe acceptance execution callback intake summary fields",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution callback intake was "
                    "blocked because summary fields could imply control, ACK, Nav2/HIL, "
                    "raw artifact access, or delivery success."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution callback intake was "
                    "blocked because summary fields could imply control, ACK, Nav2/HIL, "
                    "raw artifact access, or delivery success."
                ),
            }
        )
    return summary


def summarize_route_task_field_retest_evidence_dispatch(source):
    """构建 route-task field retest evidence dispatch 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        dispatch = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_evidence_dispatch_summary(
            source_path,
            read_error="route-task field retest evidence dispatch is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "dispatch_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest evidence dispatch artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "evidence dispatch artifact missing",
                    },
                    "safe_copy": "Route-task field retest evidence dispatch is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest evidence dispatch is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                dispatch = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "dispatch_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest evidence dispatch: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "evidence dispatch JSON read error",
                    },
                    "safe_copy": "Route-task field retest evidence dispatch could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest evidence dispatch could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_evidence_dispatch_summary(
        source_path,
        read_error="route-task field retest evidence dispatch is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(dispatch, dict):
        summary.update(
            {
                "dispatch_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest evidence dispatch JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "evidence dispatch JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest evidence dispatch shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest evidence dispatch shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = dispatch.get("diagnostics") if isinstance(dispatch.get("diagnostics"), dict) else {}
    # Robot diagnostics 只消费 dispatch 的安全摘要，避免 recommended filenames 或 backfill 文案被误用成命令。
    summary_fragment = (
        dispatch
        if str(dispatch.get("schema") or "") == ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_SUMMARY_SCHEMA
        else {}
    )
    for candidate in (
        dispatch.get("route_task_field_retest_evidence_dispatch_summary"),
        dispatch.get("route_task_field_retest_evidence_dispatch"),
        dispatch.get("robot_compatible_summary"),
        dispatch.get("robot_diagnostics_summary"),
        dispatch.get("mobile_readonly_summary"),
        dispatch.get("phone_safe_summary"),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
        diagnostics.get("route_task_field_retest_evidence_dispatch_summary"),
        diagnostics.get("route_task_field_retest_evidence_dispatch"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break

    source_schema, source_boundary = _route_task_field_retest_evidence_dispatch_source_contract(dispatch)
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": dispatch.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "dispatch_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest evidence dispatch lacks a safe diagnostics summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe evidence dispatch summary",
                },
                "safe_copy": "Route-task field retest evidence dispatch is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest evidence dispatch is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("dispatch_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    dispatch_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    dispatch_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    dispatch_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest evidence dispatch consumed without explicit reason"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or "Route-task field retest evidence dispatch is metadata-only; delivery_success=false; primary_actions_enabled=false."
    )
    safe_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            safe_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    safe_summary["safe_copy"] = safe_copy
    safe_summary["safe_phone_copy"] = safe_copy
    source_ref = str(dispatch.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": dispatch.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "dispatch_status": {
                "status": dispatch_status or "blocked",
                "verdict": dispatch_verdict or "not_proven",
                "reason": dispatch_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "safe_summary": safe_summary,
            "material_owners": _safe_pc_route_debug_value(
                summary_fragment.get("material_owners")
                if "material_owners" in summary_fragment
                else dispatch.get("material_owners", {})
            ),
            "recommended_filenames": _safe_route_task_rehearsal_list(
                summary_fragment.get("recommended_filenames")
                if isinstance(summary_fragment.get("recommended_filenames"), list)
                else dispatch.get("recommended_filenames")
            ),
            "backfill_order": _safe_route_task_rehearsal_list(
                summary_fragment.get("backfill_order")
                if isinstance(summary_fragment.get("backfill_order"), list)
                else dispatch.get("backfill_order")
            ),
            "callback_checklist": _safe_route_task_rehearsal_list(
                summary_fragment.get("callback_checklist")
                if isinstance(summary_fragment.get("callback_checklist"), list)
                else dispatch.get("callback_checklist")
            ),
            "fail_closed_rerun_notes": _safe_route_task_rehearsal_list(
                summary_fragment.get("fail_closed_rerun_notes")
                if isinstance(summary_fragment.get("fail_closed_rerun_notes"), list)
                else summary_fragment.get("rerun_notes")
                if isinstance(summary_fragment.get("rerun_notes"), list)
                else dispatch.get("fail_closed_rerun_notes")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": dispatch_status or "blocked",
                "reason": "evidence dispatch consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_GATE,
            "not_proven": _route_task_field_retest_evidence_dispatch_not_proven(
                dispatch,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_GATE
    ):
        summary.update(
            {
                "dispatch_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest evidence dispatch schema or evidence boundary is unsupported",
                },
                "material_owners": {},
                "recommended_filenames": [],
                "backfill_order": [],
                "callback_checklist": [],
                "fail_closed_rerun_notes": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "safe_summary": {
                    "safe_copy": "Route-task field retest evidence dispatch is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task field retest evidence dispatch is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "dispatch_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest evidence dispatch is missing evidence_ref",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "dispatch_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest evidence dispatch summary evidence_ref does not match source evidence_ref",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_evidence_dispatch_has_disabled_actions(
            dispatch,
            summary_fragment,
        )
        or _route_task_field_run_console_has_unsafe_fields(dispatch)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(dispatch)
    ):
        summary.update(
            {
                "dispatch_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest evidence dispatch contains unsafe fields, enabled actions, or success wording",
                },
                "material_owners": {},
                "recommended_filenames": [],
                "backfill_order": [],
                "callback_checklist": [],
                "fail_closed_rerun_notes": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe evidence dispatch summary fields",
                },
                "safe_summary": {
                    "safe_copy": "Route-task field retest evidence dispatch was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                    "safe_phone_copy": "Route-task field retest evidence dispatch was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                },
                "safe_copy": "Route-task field retest evidence dispatch was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest evidence dispatch was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_callback_intake(source):
    """构建 route-task field retest callback intake 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        intake = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_callback_intake_summary(
            source_path,
            read_error="route-task field retest callback intake is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "intake_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest callback intake artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "callback intake artifact missing",
                    },
                    "safe_copy": "Route-task field retest callback intake is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest callback intake is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "intake_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest callback intake: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "callback intake JSON read error",
                    },
                    "safe_copy": "Route-task field retest callback intake could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest callback intake could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_callback_intake_summary(
        source_path,
        read_error="route-task field retest callback intake is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(intake, dict):
        summary.update(
            {
                "intake_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest callback intake JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "callback intake JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest callback intake shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest callback intake shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = intake.get("diagnostics") if isinstance(intake.get("diagnostics"), dict) else {}
    # Robot 只消费 sanitized callback 摘要；raw callback artifact 仅用于 schema/boundary/ref/false 栅栏校验。
    summary_fragment = (
        intake
        if str(intake.get("schema") or "") == ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            intake.get("route_task_field_retest_callback_intake_summary"),
            intake.get("route_task_field_retest_callback_intake"),
            intake.get("robot_compatible_summary"),
            intake.get("robot_diagnostics_summary"),
            intake.get("mobile_readonly_summary"),
            intake.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("route_task_field_retest_callback_intake_summary"),
            diagnostics.get("route_task_field_retest_callback_intake"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    source_schema, source_boundary = _route_task_field_retest_callback_intake_source_contract(intake)
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": intake.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "intake_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest callback intake lacks a safe diagnostics summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe callback intake summary",
                },
                "safe_copy": "Route-task field retest callback intake is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest callback intake is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("intake_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    intake_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    intake_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    intake_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest callback intake consumed without explicit reason"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or "Route-task field retest callback intake is metadata-only; delivery_success=false; primary_actions_enabled=false."
    )
    safe_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            safe_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    safe_summary["safe_copy"] = safe_copy
    safe_summary["safe_phone_copy"] = safe_copy
    source_ref = str(intake.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    same_ref_match_source = (
        summary_fragment.get("same_evidence_ref_match")
        if "same_evidence_ref_match" in summary_fragment
        else summary_fragment.get("same_evidence_ref_result")
        if "same_evidence_ref_result" in summary_fragment
        else intake.get("same_evidence_ref_match")
        if "same_evidence_ref_match" in intake
        else intake.get("same_evidence_ref_result")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": intake.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "intake_status": {
                "status": intake_status or "blocked",
                "verdict": intake_verdict or "not_proven",
                "reason": intake_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "same_evidence_ref_required": _route_task_field_retest_callback_intake_requires_same_evidence_ref(
                summary_fragment,
                intake,
            ),
            "same_evidence_ref_match": _safe_pc_route_debug_value(same_ref_match_source)
            or {
                "status": intake_status or "blocked",
                "verdict": "not_proven",
                "reason": "callback intake lacks same evidence_ref match result",
            },
            "safe_summary": safe_summary,
            "received_filenames_summary": _safe_pc_route_debug_value(
                summary_fragment.get("received_filenames_summary")
                if "received_filenames_summary" in summary_fragment
                else summary_fragment.get("received_filenames")
                if "received_filenames" in summary_fragment
                else intake.get("received_filenames_summary")
                if "received_filenames_summary" in intake
                else intake.get("received_filenames")
            ),
            "missing_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials")
                if isinstance(summary_fragment.get("missing_materials"), list)
                else intake.get("missing_materials")
            ),
            "next_backfill_action": _redact_route_task_rehearsal_text(
                summary_fragment.get("next_backfill_action")
                or summary_fragment.get("next_required_backfill")
                or intake.get("next_backfill_action")
                or intake.get("next_required_backfill")
                or "not_proven"
            ),
            "callback_checklist_result": _safe_pc_route_debug_value(
                summary_fragment.get("callback_checklist_result")
                if "callback_checklist_result" in summary_fragment
                else summary_fragment.get("callback_checklist")
                if "callback_checklist" in summary_fragment
                else intake.get("callback_checklist_result")
                if "callback_checklist_result" in intake
                else intake.get("callback_checklist")
            )
            or {
                "status": intake_status or "blocked",
                "verdict": "not_proven",
                "reason": "callback intake lacks checklist result",
            },
            "robot_compatible_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status or "blocked",
                "reason": "callback intake consumed without explicit robot-compatible summary",
            },
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status or "blocked",
                "reason": "callback intake consumed without explicit robot-compatible summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_GATE,
            "not_proven": _route_task_field_retest_callback_intake_not_proven(
                intake,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_GATE
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest callback intake schema or evidence boundary is unsupported",
                },
                "received_filenames_summary": [],
                "missing_materials": [],
                "next_backfill_action": "not_proven",
                "callback_checklist_result": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "safe_summary": {
                    "safe_copy": "Route-task field retest callback intake is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task field retest callback intake is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "intake_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest callback intake is missing evidence_ref",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
                "robot_compatible_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "intake_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest callback intake summary evidence_ref does not match source evidence_ref",
                },
                "same_evidence_ref_match": {
                    "status": "mismatch",
                    "verdict": "not_proven",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if (
        not summary["same_evidence_ref_required"]
        or not _route_task_field_retest_callback_intake_has_disabled_actions(
            intake,
            summary_fragment,
        )
        or _route_task_field_run_console_has_unsafe_fields(intake)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(intake)
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest callback intake contains unsafe fields, weak evidence_ref constraints, enabled actions, or success wording",
                },
                "received_filenames_summary": [],
                "missing_materials": [],
                "next_backfill_action": "not_proven",
                "callback_checklist_result": {
                    "status": "blocked",
                    "reason": "unsafe callback intake summary fields",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "unsafe callback intake summary fields",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe callback intake summary fields",
                },
                "safe_summary": {
                    "safe_copy": "Route-task field retest callback intake was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                    "safe_phone_copy": "Route-task field retest callback intake was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                },
                "safe_copy": "Route-task field retest callback intake was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest callback intake was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_callback_review_decision(source):
    """构建 route-task field retest callback review decision 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        decision = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_callback_review_decision_summary(
            source_path,
            read_error="route-task field retest callback review decision is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "review_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest callback review decision artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "callback review decision artifact missing",
                    },
                    "safe_copy": "Route-task field retest callback review decision is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest callback review decision is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "review_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest callback review decision: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "callback review decision JSON read error",
                    },
                    "safe_copy": "Route-task field retest callback review decision could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest callback review decision could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_callback_review_decision_summary(
        source_path,
        read_error="route-task field retest callback review decision is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(decision, dict):
        summary.update(
            {
                "review_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest callback review decision JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "callback review decision JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest callback review decision shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest callback review decision shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = decision.get("diagnostics") if isinstance(decision.get("diagnostics"), dict) else {}
    # Robot diagnostics 只拿复核决策的 safe summary；raw artifact 仅用于 schema/boundary/ref/false 栅栏校验。
    summary_fragment = (
        decision
        if str(decision.get("schema") or "") == ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            decision.get("route_task_field_retest_callback_review_decision_summary"),
            decision.get("route_task_field_retest_callback_review_decision"),
            decision.get("review_decision_summary"),
            decision.get("robot_compatible_summary"),
            decision.get("robot_diagnostics_summary"),
            decision.get("mobile_readonly_summary"),
            decision.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("route_task_field_retest_callback_review_decision_summary"),
            diagnostics.get("route_task_field_retest_callback_review_decision"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    source_schema, source_boundary = _route_task_field_retest_callback_review_decision_source_contract(
        decision
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": decision.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "review_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest callback review decision lacks a safe diagnostics summary",
                },
                "review_decision": "unsupported_callback_schema",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe callback review decision summary",
                },
                "safe_copy": "Route-task field retest callback review decision is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest callback review decision is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("review_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    review_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    review_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    review_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest callback review decision consumed without explicit reason"
    )
    review_decision_value = _redact_route_task_rehearsal_text(
        summary_fragment.get("review_decision")
        or summary_fragment.get("decision")
        or decision.get("review_decision")
        or decision.get("decision")
        or "unsupported_callback_schema"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or "Route-task field retest callback review decision is metadata-only; delivery_success=false; primary_actions_enabled=false."
    )
    safe_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            safe_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    safe_summary["safe_copy"] = safe_copy
    safe_summary["safe_phone_copy"] = safe_copy
    source_ref = str(decision.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    result_readiness = (
        summary_fragment.get("result_intake_readiness")
        if "result_intake_readiness" in summary_fragment
        else summary_fragment.get("result_intake_summary")
        if "result_intake_summary" in summary_fragment
        else decision.get("result_intake_readiness")
        if "result_intake_readiness" in decision
        else decision.get("result_intake_summary")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": decision.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "review_status": {
                "status": review_status or "blocked",
                "verdict": review_verdict or "not_proven",
                "reason": review_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "source_intake_status": _safe_pc_route_debug_value(
                summary_fragment.get("source_intake_status")
                if "source_intake_status" in summary_fragment
                else summary_fragment.get("intake_status")
                if "intake_status" in summary_fragment
                else decision.get("source_intake_status")
                if "source_intake_status" in decision
                else decision.get("intake_status")
            )
            or {
                "status": review_status or "blocked",
                "verdict": "not_proven",
                "reason": "callback review decision lacks source intake status",
            },
            "review_decision": review_decision_value or "unsupported_callback_schema",
            "blocked_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocked_reasons")
                if isinstance(summary_fragment.get("blocked_reasons"), list)
                else summary_fragment.get("blockers")
                if isinstance(summary_fragment.get("blockers"), list)
                else decision.get("blocked_reasons")
                if isinstance(decision.get("blocked_reasons"), list)
                else decision.get("blockers")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
                if isinstance(summary_fragment.get("next_required_evidence"), list)
                else decision.get("next_required_evidence")
            ),
            "result_intake_readiness": _safe_pc_route_debug_value(result_readiness)
            or {
                "status": "blocked",
                "reason": "callback review decision lacks result intake readiness",
            },
            "owner_handoff": _safe_pc_route_debug_value(
                summary_fragment.get("owner_handoff")
                if "owner_handoff" in summary_fragment
                else decision.get("owner_handoff")
            )
            or "Robot",
            "safe_summary": safe_summary,
            "robot_compatible_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": review_status or "blocked",
                "reason": "callback review decision consumed without explicit robot-compatible summary",
            },
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": review_status or "blocked",
                "reason": "callback review decision consumed without explicit robot-compatible summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_GATE,
            "not_proven": _route_task_field_retest_callback_review_decision_not_proven(
                decision,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "review_status": {
                    "status": "unsupported_callback_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest callback review decision schema or evidence boundary is unsupported",
                },
                "review_decision": "unsupported_callback_schema",
                "blocked_reasons": ["unsupported_callback_schema"],
                "next_required_evidence": [],
                "result_intake_readiness": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "safe_summary": {
                    "safe_copy": "Route-task field retest callback review decision is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task field retest callback review decision is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "review_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest callback review decision is missing evidence_ref",
                },
                "review_decision": "unsupported_callback_schema",
                "result_intake_readiness": {"status": "blocked", "reason": "missing evidence_ref"},
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
                "robot_compatible_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "review_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest callback review decision summary evidence_ref does not match source evidence_ref",
                },
                "review_decision": "evidence_ref_mismatch_rerun",
                "blocked_reasons": ["evidence_ref_mismatch_rerun"],
                "result_intake_readiness": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_callback_review_decision_has_disabled_actions(
            decision,
            summary_fragment,
        )
        or _route_task_field_run_console_has_unsafe_fields(decision)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(decision)
    ):
        summary.update(
            {
                "review_status": {
                    "status": "blocked_unsafe_callback",
                    "verdict": "not_proven",
                    "reason": "route-task field retest callback review decision contains unsafe fields, enabled actions, or success wording",
                },
                "review_decision": "blocked_unsafe_callback",
                "blocked_reasons": ["blocked_unsafe_callback"],
                "next_required_evidence": [],
                "result_intake_readiness": {
                    "status": "blocked",
                    "reason": "unsafe callback review decision summary fields",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "unsafe callback review decision summary fields",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe callback review decision summary fields",
                },
                "safe_summary": {
                    "safe_copy": "Route-task field retest callback review decision was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                    "safe_phone_copy": "Route-task field retest callback review decision was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                },
                "safe_copy": "Route-task field retest callback review decision was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest callback review decision was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_review_result_handoff(source):
    """构建 route-task field retest review result handoff 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        handoff = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_review_result_handoff_summary(
            source_path,
            read_error="route-task field retest review result handoff is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "handoff_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest review result handoff artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "review result handoff artifact missing",
                    },
                    "safe_copy": "Route-task field retest review result handoff is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest review result handoff is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "handoff_status": {
                        "status": "blocked_missing_review_decision",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest review result handoff: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "review result handoff JSON read error",
                    },
                    "safe_copy": "Route-task field retest review result handoff could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest review result handoff could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_review_result_handoff_summary(
        source_path,
        read_error="route-task field retest review result handoff is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(handoff, dict):
        summary.update(
            {
                "handoff_status": {
                    "status": "blocked_missing_review_decision",
                    "verdict": "not_proven",
                    "reason": "route-task field retest review result handoff JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "review result handoff JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest review result handoff shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest review result handoff shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = handoff.get("diagnostics") if isinstance(handoff.get("diagnostics"), dict) else {}
    # Robot 只暴露 handoff 的 sanitized summary；raw source 仅用于 schema/boundary/ref/false 栅栏校验。
    summary_fragment = (
        handoff
        if str(handoff.get("schema") or "") == ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            handoff.get("route_task_field_retest_review_result_handoff_summary"),
            handoff.get("route_task_field_retest_review_result_handoff"),
            handoff.get("review_result_handoff_summary"),
            handoff.get("handoff_summary"),
            handoff.get("robot_compatible_summary"),
            handoff.get("robot_diagnostics_summary"),
            handoff.get("mobile_readonly_summary"),
            handoff.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("route_task_field_retest_review_result_handoff_summary"),
            diagnostics.get("route_task_field_retest_review_result_handoff"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    source_schema, source_boundary = _route_task_field_retest_review_result_handoff_source_contract(
        handoff
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": handoff.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "handoff_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest review result handoff lacks a safe diagnostics summary",
                },
                "source_review_decision": "unsupported_review_result_handoff_schema",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe review result handoff summary",
                },
                "safe_copy": "Route-task field retest review result handoff is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest review result handoff is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("handoff_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    handoff_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    handoff_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    handoff_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest review result handoff consumed without explicit reason"
    )
    source_review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("source_review_decision")
        or summary_fragment.get("review_decision")
        or handoff.get("source_review_decision")
        or handoff.get("review_decision")
        or "unsupported_review_result_handoff_schema"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or "Route-task field retest review result handoff is metadata-only; delivery_success=false; primary_actions_enabled=false."
    )
    safe_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            safe_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    safe_summary["safe_copy"] = safe_copy
    safe_summary["safe_phone_copy"] = safe_copy
    source_ref = str(handoff.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    result_readiness = (
        summary_fragment.get("result_intake_readiness")
        if "result_intake_readiness" in summary_fragment
        else handoff.get("result_intake_readiness")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": handoff.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "handoff_status": {
                "status": handoff_status or "blocked",
                "verdict": handoff_verdict or "not_proven",
                "reason": handoff_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "same_evidence_ref_required": _route_task_field_retest_review_result_handoff_requires_same_evidence_ref(
                summary_fragment,
                handoff,
            ),
            "same_evidence_ref_match": _safe_pc_route_debug_value(
                summary_fragment.get("same_evidence_ref_match")
                if "same_evidence_ref_match" in summary_fragment
                else handoff.get("same_evidence_ref_match")
            )
            or {
                "status": "matched" if (summary_ref or source_ref) else "blocked",
                "verdict": "not_proven",
                "reason": "review result handoff consumed with same evidence_ref requirement",
            },
            "source_review_decision": source_review_decision,
            "result_intake_readiness": _safe_pc_route_debug_value(result_readiness)
            or {
                "status": "blocked",
                "reason": "review result handoff lacks result-intake readiness",
            },
            "required_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("required_materials")
                if isinstance(summary_fragment.get("required_materials"), list)
                else summary_fragment.get("required_result_materials")
                if isinstance(summary_fragment.get("required_result_materials"), list)
                else handoff.get("required_materials")
                if isinstance(handoff.get("required_materials"), list)
                else handoff.get("required_result_materials")
            ),
            "owner_handoff": _safe_pc_route_debug_value(
                summary_fragment.get("owner_handoff")
                if "owner_handoff" in summary_fragment
                else handoff.get("owner_handoff")
            )
            or "Robot",
            "blocked_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocked_reasons")
                if isinstance(summary_fragment.get("blocked_reasons"), list)
                else summary_fragment.get("blockers")
                if isinstance(summary_fragment.get("blockers"), list)
                else handoff.get("blocked_reasons")
                if isinstance(handoff.get("blocked_reasons"), list)
                else handoff.get("blockers")
            ),
            "safe_summary": safe_summary,
            "control_boundary": _safe_pc_route_debug_dict(
                summary_fragment.get("control_boundary")
                if isinstance(summary_fragment.get("control_boundary"), dict)
                else handoff.get("control_boundary")
            )
            or {
                "metadata_only": True,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "robot_compatible_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status or "blocked",
                "reason": "review result handoff consumed without explicit robot-compatible summary",
            },
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status or "blocked",
                "reason": "review result handoff consumed without explicit robot-compatible summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_GATE,
            "not_proven": _route_task_field_retest_review_result_handoff_not_proven(
                handoff,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_GATE
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest review result handoff schema or evidence boundary is unsupported",
                },
                "source_review_decision": "unsupported_review_result_handoff_schema",
                "result_intake_readiness": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "required_materials": [],
                "blocked_reasons": ["unsupported_review_result_handoff_schema"],
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "safe_summary": {
                    "safe_copy": "Route-task field retest review result handoff is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task field retest review result handoff is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "handoff_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest review result handoff is missing evidence_ref",
                },
                "source_review_decision": "unsupported_review_result_handoff_schema",
                "result_intake_readiness": {"status": "blocked", "reason": "missing evidence_ref"},
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
                "robot_compatible_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "handoff_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest review result handoff summary evidence_ref does not match source evidence_ref",
                },
                "same_evidence_ref_match": {
                    "status": "mismatch",
                    "verdict": "not_proven",
                    "reason": "same evidence_ref mismatch",
                },
                "result_intake_readiness": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if (
        not summary["same_evidence_ref_required"]
        or not _route_task_field_retest_review_result_handoff_has_disabled_actions(
            handoff,
            summary_fragment,
        )
        or _route_task_field_run_console_has_unsafe_fields(handoff)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(handoff)
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "blocked_unsafe_review_result_handoff",
                    "verdict": "not_proven",
                    "reason": "route-task field retest review result handoff contains unsafe fields, weak evidence_ref constraints, enabled actions, or success wording",
                },
                "source_review_decision": "blocked_unsafe_review_result_handoff",
                "result_intake_readiness": {
                    "status": "blocked",
                    "reason": "unsafe review result handoff summary fields",
                },
                "required_materials": [],
                "blocked_reasons": ["blocked_unsafe_review_result_handoff"],
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "unsafe review result handoff summary fields",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe review result handoff summary fields",
                },
                "safe_summary": {
                    "safe_copy": "Route-task field retest review result handoff was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                    "safe_phone_copy": "Route-task field retest review result handoff was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                },
                "safe_copy": "Route-task field retest review result handoff was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest review result handoff was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_result_acceptance_packet(source):
    """构建 route-task field retest result acceptance packet 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        packet = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_result_acceptance_packet_summary(
            source_path,
            read_error="route-task field retest result acceptance packet is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "packet_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest result acceptance packet artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance packet artifact missing",
                    },
                    "safe_copy": "Route-task field retest result acceptance packet is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result acceptance packet is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                packet = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "packet_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest result acceptance packet: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance packet JSON read error",
                    },
                    "safe_copy": "Route-task field retest result acceptance packet could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result acceptance packet could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_result_acceptance_packet_summary(
        source_path,
        read_error="route-task field retest result acceptance packet is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(packet, dict):
        summary.update(
            {
                "packet_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result acceptance packet JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "acceptance packet JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest result acceptance packet shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest result acceptance packet shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = packet.get("diagnostics") if isinstance(packet.get("diagnostics"), dict) else {}
    # Robot 只读 packet 的安全摘要；raw artifact、路径、checksum、topic 和控制字段都不能穿透到 diagnostics。
    summary_fragment = (
        packet
        if str(packet.get("schema") or "") == ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_SUMMARY_SCHEMA
        or (
            str(packet.get("schema") or "") == ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_SCHEMA
            and any(
                key in packet
                for key in (
                    "packet_status",
                    "missing_material_summary",
                    "owner_handoff",
                    "rerun_command_summary",
                    "pass_fail_criteria_summary",
                )
            )
        )
        else {}
    )
    for candidate in (
        packet.get("route_task_field_retest_result_acceptance_packet_summary"),
        packet.get("route_task_field_retest_result_acceptance_packet"),
        packet.get("robot_diagnostics_summary"),
        packet.get("robot_compatible_summary"),
        packet.get("mobile_readonly_summary"),
        packet.get("phone_safe_summary"),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
        diagnostics.get("route_task_field_retest_result_acceptance_packet_summary"),
        diagnostics.get("route_task_field_retest_result_acceptance_packet"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break

    source_schema, source_boundary = _route_task_field_retest_result_acceptance_packet_source_contract(
        packet
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": packet.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "packet_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result acceptance packet lacks a safe diagnostics summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe acceptance packet summary",
                },
                "safe_copy": "Route-task field retest result acceptance packet is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest result acceptance packet is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("packet_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("acceptance_status")
    if not isinstance(status_source, dict):
        status_source = {}
    packet_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    packet_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    packet_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest result acceptance packet consumed without explicit reason"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or "Route-task field retest result acceptance packet is metadata-only; delivery_success=false; primary_actions_enabled=false."
    )
    source_ref = str(packet.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": packet.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "packet_status": {
                "status": packet_status or "blocked",
                "verdict": packet_verdict or "not_proven",
                "reason": packet_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "missing_material_summary": _safe_pc_route_debug_value(
                summary_fragment.get("missing_material_summary")
                if "missing_material_summary" in summary_fragment
                else summary_fragment.get("missing_materials_summary")
                if "missing_materials_summary" in summary_fragment
                else summary_fragment.get("missing_materials")
            ),
            "owner_handoff": _safe_pc_route_debug_value(summary_fragment.get("owner_handoff")),
            "rerun_command_summary": _safe_pc_route_debug_value(
                summary_fragment.get("rerun_command_summary")
                if "rerun_command_summary" in summary_fragment
                else summary_fragment.get("rerun_commands_summary")
                if "rerun_commands_summary" in summary_fragment
                else summary_fragment.get("rerun_commands")
            ),
            "pass_fail_criteria_summary": _safe_pc_route_debug_value(
                summary_fragment.get("pass_fail_criteria_summary")
                if "pass_fail_criteria_summary" in summary_fragment
                else summary_fragment.get("pass_fail_criteria")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": packet_status or "blocked",
                "reason": "acceptance packet consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_GATE,
            "not_proven": _route_task_field_retest_result_acceptance_packet_not_proven(
                packet,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    required_summary_fields = (
        summary["missing_material_summary"],
        summary["owner_handoff"],
        summary["rerun_command_summary"],
        summary["pass_fail_criteria_summary"],
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_GATE
    ):
        summary.update(
            {
                "packet_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result acceptance packet schema or evidence boundary is unsupported",
                },
                "missing_material_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "owner_handoff": {},
                "rerun_command_summary": [],
                "pass_fail_criteria_summary": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "packet_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result acceptance packet is missing evidence_ref",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "packet_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result acceptance packet summary evidence_ref does not match source evidence_ref",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "packet_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result acceptance packet is missing required safe summary fields",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required acceptance packet summary fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_result_acceptance_packet_has_disabled_actions(
            packet,
            summary_fragment,
        )
        or _route_task_field_run_console_has_unsafe_fields(packet)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(packet)
    ):
        summary.update(
            {
                "packet_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result acceptance packet contains unsafe fields, enabled actions, raw details, or success wording",
                },
                "missing_material_summary": {
                    "status": "blocked",
                    "reason": "unsafe acceptance packet summary fields",
                },
                "owner_handoff": {},
                "rerun_command_summary": [],
                "pass_fail_criteria_summary": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe acceptance packet summary fields",
                },
                "safe_copy": "Route-task field retest result acceptance packet was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest result acceptance packet was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_result_acceptance_backfill(source):
    """构建 route-task field retest result acceptance backfill 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        backfill = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_result_acceptance_backfill_summary(
            source_path,
            read_error="route-task field retest result acceptance backfill is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "backfill_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest result acceptance backfill artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance backfill artifact missing",
                    },
                    "safe_copy": "Route-task field retest result acceptance backfill is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result acceptance backfill is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                backfill = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "backfill_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest result acceptance backfill: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance backfill JSON read error",
                    },
                    "safe_copy": "Route-task field retest result acceptance backfill could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result acceptance backfill could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_result_acceptance_backfill_summary(
        source_path,
        read_error="route-task field retest result acceptance backfill is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(backfill, dict):
        summary.update(
            {
                "backfill_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result acceptance backfill JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "acceptance backfill JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest result acceptance backfill shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest result acceptance backfill shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = backfill.get("diagnostics") if isinstance(backfill.get("diagnostics"), dict) else {}
    # Robot 只读 backfill 的安全摘要；raw material、路径、checksum、topic 和控制字段都不能穿透。
    summary_fragment = (
        backfill
        if str(backfill.get("schema") or "") == ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_SUMMARY_SCHEMA
        or (
            str(backfill.get("schema") or "") == ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_SCHEMA
            and any(
                key in backfill
                for key in (
                    "backfill_status",
                    "material_completeness_summary",
                    "alignment_status",
                    "missing_rejected_category_summary",
                    "owner_handoff",
                    "rerun_command_summary",
                )
            )
        )
        else {}
    )
    for candidate in (
        backfill.get("route_task_field_retest_result_acceptance_backfill_summary"),
        backfill.get("route_task_field_retest_result_acceptance_backfill"),
        backfill.get("robot_diagnostics_summary"),
        backfill.get("robot_compatible_summary"),
        backfill.get("mobile_readonly_summary"),
        backfill.get("phone_safe_summary"),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
        diagnostics.get("route_task_field_retest_result_acceptance_backfill_summary"),
        diagnostics.get("route_task_field_retest_result_acceptance_backfill"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break

    source_schema, source_boundary = _route_task_field_retest_result_acceptance_backfill_source_contract(
        backfill
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": backfill.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "backfill_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result acceptance backfill lacks a safe diagnostics summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe acceptance backfill summary",
                },
                "safe_copy": "Route-task field retest result acceptance backfill is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest result acceptance backfill is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("backfill_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("acceptance_backfill_status")
    if not isinstance(status_source, dict):
        status_source = {}
    backfill_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    backfill_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    backfill_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest result acceptance backfill consumed without explicit reason"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or "Route-task field retest result acceptance backfill is metadata-only; delivery_success=false; primary_actions_enabled=false."
    )
    source_ref = str(backfill.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    material_summary = _safe_pc_route_debug_value(
        summary_fragment.get("material_completeness_summary")
        if "material_completeness_summary" in summary_fragment
        else summary_fragment.get("material_completeness")
        if "material_completeness" in summary_fragment
        else summary_fragment.get("materials_completeness")
    )
    alignment_status = _safe_pc_route_debug_value(
        summary_fragment.get("alignment_status")
        if "alignment_status" in summary_fragment
        else summary_fragment.get("same_evidence_ref_alignment")
        if "same_evidence_ref_alignment" in summary_fragment
        else summary_fragment.get("evidence_ref_alignment")
    )
    missing_rejected_summary = _safe_pc_route_debug_value(
        summary_fragment.get("missing_rejected_category_summary")
        if "missing_rejected_category_summary" in summary_fragment
        else summary_fragment.get("missing_rejected_categories")
        if "missing_rejected_categories" in summary_fragment
        else summary_fragment.get("missing_or_rejected_materials")
    )
    owner_handoff = _safe_pc_route_debug_value(summary_fragment.get("owner_handoff"))
    rerun_summary = _safe_pc_route_debug_value(
        summary_fragment.get("rerun_command_summary")
        if "rerun_command_summary" in summary_fragment
        else summary_fragment.get("rerun_commands_summary")
        if "rerun_commands_summary" in summary_fragment
        else summary_fragment.get("rerun_commands")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": backfill.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "backfill_status": {
                "status": backfill_status or "blocked",
                "verdict": backfill_verdict or "not_proven",
                "reason": backfill_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "material_completeness_summary": material_summary,
            "alignment_status": alignment_status,
            "missing_rejected_category_summary": missing_rejected_summary,
            "owner_handoff": owner_handoff,
            "rerun_command_summary": rerun_summary,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": backfill_status or "blocked",
                "reason": "acceptance backfill consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_GATE,
            "not_proven": _route_task_field_retest_result_acceptance_backfill_not_proven(
                backfill,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    required_summary_fields = (
        summary["material_completeness_summary"],
        summary["alignment_status"],
        summary["missing_rejected_category_summary"],
        summary["owner_handoff"],
        summary["rerun_command_summary"],
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_GATE
    ):
        summary.update(
            {
                "backfill_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result acceptance backfill schema or evidence boundary is unsupported",
                },
                "material_completeness_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "alignment_status": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "missing_rejected_category_summary": {"missing": [], "rejected": []},
                "owner_handoff": {},
                "rerun_command_summary": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "backfill_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result acceptance backfill is missing evidence_ref",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "backfill_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result acceptance backfill summary evidence_ref does not match source evidence_ref",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "backfill_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result acceptance backfill is missing required safe summary fields",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required acceptance backfill summary fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_result_acceptance_backfill_has_disabled_actions(
            backfill,
            summary_fragment,
        )
        or _route_task_field_run_console_has_unsafe_fields(backfill)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(backfill)
    ):
        summary.update(
            {
                "backfill_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result acceptance backfill contains unsafe fields, enabled actions, raw details, or success wording",
                },
                "material_completeness_summary": {
                    "status": "blocked",
                    "reason": "unsafe acceptance backfill summary fields",
                },
                "alignment_status": {
                    "status": "blocked",
                    "reason": "unsafe acceptance backfill summary fields",
                },
                "missing_rejected_category_summary": {"missing": [], "rejected": []},
                "owner_handoff": {},
                "rerun_command_summary": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe acceptance backfill summary fields",
                },
                "safe_copy": "Route-task field retest result acceptance backfill was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest result acceptance backfill was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_result_backfill_review_decision(source):
    """构建 route-task field retest result backfill review decision 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        decision = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_result_backfill_review_decision_summary(
            source_path,
            read_error="route-task field retest result backfill review decision is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "review_decision": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest result backfill review decision artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "backfill review decision artifact missing",
                    },
                    "safe_copy": "Route-task field retest result backfill review decision is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result backfill review decision is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "review_decision": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest result backfill review decision: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "backfill review decision JSON read error",
                    },
                    "safe_copy": "Route-task field retest result backfill review decision could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result backfill review decision could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_result_backfill_review_decision_summary(
        source_path,
        read_error="route-task field retest result backfill review decision is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(decision, dict):
        summary.update(
            {
                "review_decision": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result backfill review decision JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "backfill review decision JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest result backfill review decision shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest result backfill review decision shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = decision.get("diagnostics") if isinstance(decision.get("diagnostics"), dict) else {}
    # Robot 只消费白名单 review decision 摘要，不能透传 raw material、路径、命令执行结果或控制字段。
    summary_fragment = (
        decision
        if str(decision.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_SUMMARY_SCHEMA
        or (
            str(decision.get("schema") or "")
            == ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_SCHEMA
            and any(
                key in decision
                for key in (
                    "review_decision",
                    "material_status",
                    "accepted_materials",
                    "missing_materials",
                    "rejected_materials",
                    "owner_handoff",
                    "next_required_evidence",
                    "rerun_commands",
                )
            )
        )
        else {}
    )
    for candidate in (
        decision.get("route_task_field_retest_result_backfill_review_decision_summary"),
        decision.get("route_task_field_retest_result_backfill_review_decision"),
        decision.get("robot_diagnostics_summary"),
        decision.get("robot_compatible_summary"),
        decision.get("mobile_readonly_summary"),
        decision.get("phone_safe_summary"),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
        diagnostics.get("route_task_field_retest_result_backfill_review_decision_summary"),
        diagnostics.get("route_task_field_retest_result_backfill_review_decision"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break

    source_schema, source_boundary = _route_task_field_retest_result_backfill_review_decision_source_contract(
        decision
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": decision.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "review_decision": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result backfill review decision lacks a safe diagnostics summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe backfill review decision summary",
                },
                "safe_copy": "Route-task field retest result backfill review decision is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest result backfill review decision is blocked because no safe summary was provided.",
            }
        )
        return summary

    decision_source = summary_fragment.get("review_decision")
    if not isinstance(decision_source, dict):
        decision_source = summary_fragment.get("decision")
    if not isinstance(decision_source, dict):
        decision_source = {}
    decision_status = _redact_route_task_rehearsal_text(
        decision_source.get("status")
        or decision_source.get("verdict")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    decision_verdict = _redact_route_task_rehearsal_text(
        decision_source.get("verdict")
        or decision_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    decision_reason = _redact_route_task_rehearsal_text(
        decision_source.get("reason")
        or decision_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest result backfill review decision consumed without explicit reason"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or "Route-task field retest result backfill review decision is metadata-only; delivery_success=false; primary_actions_enabled=false."
    )
    source_ref = str(decision.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    material_status = _safe_pc_route_debug_value(
        summary_fragment.get("material_status")
        if "material_status" in summary_fragment
        else summary_fragment.get("materials_status")
    )
    accepted_materials = _safe_pc_route_debug_value(summary_fragment.get("accepted_materials"))
    missing_materials = _safe_pc_route_debug_value(summary_fragment.get("missing_materials"))
    rejected_materials = _safe_pc_route_debug_value(summary_fragment.get("rejected_materials"))
    owner_handoff = _safe_pc_route_debug_value(summary_fragment.get("owner_handoff"))
    next_required_evidence = _safe_pc_route_debug_value(
        summary_fragment.get("next_required_evidence")
        if "next_required_evidence" in summary_fragment
        else summary_fragment.get("required_next_evidence")
    )
    rerun_commands = _safe_pc_route_debug_value(
        summary_fragment.get("rerun_commands")
        if "rerun_commands" in summary_fragment
        else summary_fragment.get("rerun_command_summary")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": decision.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "review_decision": {
                "status": decision_status or "blocked",
                "verdict": decision_verdict or "not_proven",
                "reason": decision_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "material_status": material_status,
            "accepted_materials": accepted_materials,
            "missing_materials": missing_materials,
            "rejected_materials": rejected_materials,
            "owner_handoff": owner_handoff,
            "next_required_evidence": next_required_evidence,
            "rerun_commands": rerun_commands,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": decision_status or "blocked",
                "reason": "backfill review decision consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_GATE,
            "not_proven": _route_task_field_retest_result_backfill_review_decision_not_proven(
                decision,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    required_summary_fields = (
        summary["material_status"],
        isinstance(summary["accepted_materials"], list),
        isinstance(summary["missing_materials"], list),
        isinstance(summary["rejected_materials"], list),
        summary["owner_handoff"],
        isinstance(summary["next_required_evidence"], list),
        isinstance(summary["rerun_commands"], list),
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "review_decision": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result backfill review decision schema or evidence boundary is unsupported",
                },
                "material_status": {"status": "blocked", "reason": "unsupported schema or evidence boundary"},
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "owner_handoff": {},
                "next_required_evidence": [],
                "rerun_commands": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "review_decision": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result backfill review decision is missing evidence_ref",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "review_decision": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result backfill review decision summary evidence_ref does not match source evidence_ref",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "review_decision": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result backfill review decision is missing required safe summary fields",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required backfill review decision summary fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_result_backfill_review_decision_has_disabled_actions(
            decision,
            summary_fragment,
        )
        or _route_task_field_run_console_has_unsafe_fields(decision)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _route_task_field_retest_execution_pack_has_success_wording(decision)
    ):
        summary.update(
            {
                "review_decision": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result backfill review decision contains unsafe fields, enabled actions, raw details, or success wording",
                },
                "material_status": {
                    "status": "blocked",
                    "reason": "unsafe backfill review decision summary fields",
                },
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "owner_handoff": {},
                "next_required_evidence": [],
                "rerun_commands": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe backfill review decision summary fields",
                },
                "safe_copy": "Route-task field retest result backfill review decision was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest result backfill review decision was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_result_review_dispatch(source):
    """构建 route-task field retest result review dispatch 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        dispatch = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_result_review_dispatch_summary(
            source_path,
            read_error="route-task field retest result review dispatch is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "dispatch_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest result review dispatch summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "result review dispatch summary missing",
                    },
                    "safe_copy": "Route-task field retest result review dispatch is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result review dispatch is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                dispatch = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "dispatch_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest result review dispatch: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "result review dispatch JSON read error",
                    },
                    "safe_copy": "Route-task field retest result review dispatch could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result review dispatch could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_result_review_dispatch_summary(
        source_path,
        read_error="route-task field retest result review dispatch is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(dispatch, dict):
        summary.update(
            {
                "dispatch_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review dispatch JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "result review dispatch JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest result review dispatch shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest result review dispatch shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = dispatch.get("diagnostics") if isinstance(dispatch.get("diagnostics"), dict) else {}
    # Robot 只消费 Autonomy 产出的安全 summary；raw result、命令输出、路径、topic 和控制字段都不能穿透。
    summary_fragment = (
        dispatch
        if str(dispatch.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            dispatch.get("route_task_field_retest_result_review_dispatch_summary"),
            dispatch.get("route_task_field_retest_result_review_dispatch"),
            dispatch.get("robot_compatible_summary"),
            dispatch.get("mobile_readonly_summary"),
            dispatch.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("route_task_field_retest_result_review_dispatch_summary"),
            diagnostics.get("route_task_field_retest_result_review_dispatch"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    source_schema, source_boundary = _route_task_field_retest_result_review_dispatch_source_contract(
        dispatch
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": dispatch.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "dispatch_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review dispatch lacks a safe diagnostics summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe result review dispatch summary",
                },
                "safe_copy": "Route-task field retest result review dispatch is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest result review dispatch is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("dispatch_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("review_dispatch_status")
    if not isinstance(status_source, dict):
        status_source = {}
    dispatch_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    dispatch_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    dispatch_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest result review dispatch consumed without explicit reason"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Route-task field retest result review dispatch is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        )
    )
    source_ref = str(dispatch.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    accepted_materials = _safe_pc_route_debug_value(summary_fragment.get("accepted_materials"))
    missing_materials = _safe_pc_route_debug_value(summary_fragment.get("missing_materials"))
    rejected_materials = _safe_pc_route_debug_value(summary_fragment.get("rejected_materials"))
    owner_work_orders = _safe_pc_route_debug_value(summary_fragment.get("owner_work_orders"))
    callback_packet_requirements = _safe_pc_route_debug_value(
        summary_fragment.get("callback_packet_requirements")
    )
    rerun_commands = _safe_pc_route_debug_value(summary_fragment.get("rerun_commands"))
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": dispatch.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "dispatch_status": {
                "status": dispatch_status or "blocked",
                "verdict": dispatch_verdict or "not_proven",
                "reason": dispatch_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "accepted_materials": accepted_materials,
            "missing_materials": missing_materials,
            "rejected_materials": rejected_materials,
            "owner_work_orders": owner_work_orders,
            "callback_packet_requirements": callback_packet_requirements,
            "rerun_commands": rerun_commands,
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": dispatch_status or "blocked",
                "reason": "result review dispatch consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH_GATE,
            "not_proven": _route_task_field_retest_result_review_dispatch_not_proven(
                summary_fragment
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )

    required_summary_fields = (
        isinstance(summary["accepted_materials"], list),
        isinstance(summary["missing_materials"], list),
        isinstance(summary["rejected_materials"], list),
        bool(summary["owner_work_orders"]),
        bool(summary["callback_packet_requirements"]),
        isinstance(summary["rerun_commands"], list),
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH_SUMMARY_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH_GATE
    ):
        summary.update(
            {
                "dispatch_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review dispatch schema or evidence boundary is unsupported",
                },
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "owner_work_orders": {},
                "callback_packet_requirements": {},
                "rerun_commands": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "dispatch_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review dispatch is missing evidence_ref",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "dispatch_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review dispatch summary evidence_ref does not match source evidence_ref",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not _route_task_field_retest_result_review_dispatch_requires_same_evidence_ref(
        summary_fragment
    ):
        summary.update(
            {
                "dispatch_status": {
                    "status": "same_evidence_ref_required_false",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review dispatch must require the same evidence_ref",
                },
                "same_evidence_ref_required": False,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "dispatch_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review dispatch is missing required safe summary fields",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required result review dispatch summary fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_result_review_dispatch_has_disabled_actions(
            summary_fragment
        )
        or _route_task_field_run_console_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "dispatch_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review dispatch contains unsafe fields, enabled actions, raw details, or success wording",
                },
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "owner_work_orders": {},
                "callback_packet_requirements": {},
                "rerun_commands": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe result review dispatch summary fields",
                },
                "safe_copy": "Route-task field retest result review dispatch was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest result review dispatch was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_result_review_decision(source):
    """构建 route-task field retest result review decision 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        decision = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_result_review_decision_summary(
            source_path,
            read_error="route-task field retest result review decision is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "decision_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest result review decision summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "result review decision summary missing",
                    },
                    "safe_copy": "Route-task field retest result review decision is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result review decision is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "decision_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest result review decision: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "result review decision JSON read error",
                    },
                    "safe_copy": "Route-task field retest result review decision could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result review decision could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_result_review_decision_summary(
        source_path,
        read_error="route-task field retest result review decision is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(decision, dict):
        summary.update(
            {
                "decision_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review decision JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "result review decision JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest result review decision shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest result review decision shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = decision.get("diagnostics") if isinstance(decision.get("diagnostics"), dict) else {}
    # 只读取 result_review_decision 自身安全 summary；status/diagnostics/nested aliases 都必须回指同一个 gate。
    summary_fragment = (
        decision
        if str(decision.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            decision.get("route_task_field_retest_result_review_decision_summary"),
            decision.get("route_task_field_retest_result_review_decision"),
            decision.get("robot_diagnostics_route_task_field_retest_result_review_decision_summary"),
            decision.get("robot_compatible_summary"),
            decision.get("robot_diagnostics_summary"),
            decision.get("mobile_readonly_summary"),
            decision.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("route_task_field_retest_result_review_decision_summary"),
            diagnostics.get("route_task_field_retest_result_review_decision"),
            diagnostics.get("robot_diagnostics_route_task_field_retest_result_review_decision_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else decision
    source_schema, source_boundary = _route_task_field_retest_result_review_decision_source_contract(
        contract_source
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": decision.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "decision_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review decision lacks a safe diagnostics summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe result review decision summary",
                },
                "safe_copy": "Route-task field retest result review decision is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest result review decision is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("decision_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("review_decision_status")
    if not isinstance(status_source, dict):
        status_source = {}
    source_intake_status = summary_fragment.get("source_review_intake_status")
    if not isinstance(source_intake_status, dict):
        source_intake_status = summary_fragment.get("review_intake_status")
    if not isinstance(source_intake_status, dict):
        source_intake_status = {}
    decision_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("decision_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    decision_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    decision_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest result review decision consumed without explicit reason"
    )
    review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("review_decision")
        or status_source.get("decision")
        or decision_verdict
        or "not_proven"
    )
    safe_copy_source = summary_fragment.get("safe_copy") or summary_fragment.get("safe_phone_copy")
    safe_copy = _safe_pc_route_debug_value(
        safe_copy_source
        or (
            "Route-task field retest result review decision is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # literal false 文案是本 gate 的 grep 围栏，防止只读 decision 被 UI/Robot 误读成控制授权。
        safe_copy_text = (
            f"{safe_copy_text}; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(decision.get("safe_evidence_ref") or decision.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "decision_status": {
                "status": decision_status or "blocked",
                "verdict": decision_verdict or "not_proven",
                "reason": decision_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "source_review_intake_status": _safe_pc_route_debug_dict(source_intake_status)
            or {
                "status": "blocked",
                "verdict": "not_proven",
                "reason": "result review decision lacks source review intake status",
            },
            "review_decision": review_decision or "not_proven",
            "missing_materials": _safe_pc_route_debug_value(summary_fragment.get("missing_materials")),
            "owner_handoff": _safe_pc_route_debug_value(summary_fragment.get("owner_handoff")),
            "next_required_evidence": _safe_pc_route_debug_value(
                summary_fragment.get("next_required_evidence")
            ),
            "rerun_commands": _safe_pc_route_debug_value(summary_fragment.get("rerun_commands")),
            "review_ready_package": _safe_pc_route_debug_value(
                summary_fragment.get("review_ready_package")
            ),
            "rerun_package": _safe_pc_route_debug_value(summary_fragment.get("rerun_package")),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": decision_status or "blocked",
                "reason": "result review decision consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_GATE,
            "not_proven": _route_task_field_retest_result_review_decision_not_proven(
                decision,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )

    required_summary_fields = (
        bool(summary["source_review_intake_status"]),
        bool(summary["review_decision"]),
        isinstance(summary["missing_materials"], list),
        bool(summary["owner_handoff"]),
        isinstance(summary["next_required_evidence"], list),
        isinstance(summary["rerun_commands"], list),
        bool(summary["review_ready_package"]),
        bool(summary["rerun_package"]),
        bool(summary["safe_copy"]),
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "decision_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review decision schema or evidence boundary is unsupported",
                },
                "missing_materials": [],
                "owner_handoff": {},
                "next_required_evidence": [],
                "rerun_commands": [],
                "review_ready_package": {},
                "rerun_package": {},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "decision_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review decision is missing evidence_ref",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "decision_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review decision summary evidence_ref does not match source evidence_ref",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not _route_task_field_retest_result_review_decision_requires_same_evidence_ref(
        summary_fragment
    ):
        summary.update(
            {
                "decision_status": {
                    "status": "same_evidence_ref_required_false",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review decision must require the same evidence_ref",
                },
                "same_evidence_ref_required": False,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "decision_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review decision is missing required safe summary fields",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required result review decision summary fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_result_review_decision_has_disabled_actions(
            summary_fragment
        )
        or _route_task_field_run_console_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "decision_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review decision contains unsafe fields, enabled actions, raw details, or success wording",
                },
                "missing_materials": [],
                "owner_handoff": {},
                "next_required_evidence": [],
                "rerun_commands": [],
                "review_ready_package": {},
                "rerun_package": {},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe result review decision summary fields",
                },
                "safe_copy": "Route-task field retest result review decision was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest result review decision was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_result_review_handoff(source):
    """构建 route-task field retest result review handoff 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        handoff = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_result_review_handoff_summary(
            source_path,
            read_error="route-task field retest result review handoff is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "handoff_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest result review handoff summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "result review handoff summary missing",
                    },
                    "robot_compatible_summary": {
                        "status": "blocked",
                        "reason": "result review handoff summary missing",
                    },
                    "safe_copy": "Route-task field retest result review handoff is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result review handoff is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "handoff_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest result review handoff: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "result review handoff JSON read error",
                    },
                    "robot_compatible_summary": {
                        "status": "blocked",
                        "reason": "result review handoff JSON read error",
                    },
                    "safe_copy": "Route-task field retest result review handoff could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result review handoff could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_result_review_handoff_summary(
        source_path,
        read_error="route-task field retest result review handoff is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(handoff, dict):
        summary.update(
            {
                "handoff_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review handoff JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "result review handoff JSON shape is invalid",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "result review handoff JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest result review handoff shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest result review handoff shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = handoff.get("diagnostics") if isinstance(handoff.get("diagnostics"), dict) else {}
    # 只消费 result_review_handoff 自己的 summary/robot alias，避免串到 decision、callback 或旧 review-result gate。
    summary_fragment = (
        handoff
        if str(handoff.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            handoff.get("route_task_field_retest_result_review_handoff_summary"),
            handoff.get("route_task_field_retest_result_review_handoff"),
            handoff.get("robot_diagnostics_route_task_field_retest_result_review_handoff_summary"),
            handoff.get("robot_compatible_summary"),
            handoff.get("robot_diagnostics_summary"),
            handoff.get("mobile_readonly_summary"),
            handoff.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("route_task_field_retest_result_review_handoff_summary"),
            diagnostics.get("route_task_field_retest_result_review_handoff"),
            diagnostics.get("robot_diagnostics_route_task_field_retest_result_review_handoff_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else handoff
    source_schema, source_boundary = _route_task_field_retest_result_review_handoff_source_contract(
        contract_source
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": handoff.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "handoff_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review handoff lacks a safe diagnostics summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe result review handoff summary",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "missing safe result review handoff summary",
                },
                "safe_copy": "Route-task field retest result review handoff is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest result review handoff is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("handoff_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    source_decision_status = summary_fragment.get("source_review_decision_status")
    if not isinstance(source_decision_status, dict):
        source_decision_status = summary_fragment.get("source_decision_status")
    if not isinstance(source_decision_status, dict):
        source_decision_status = {}
    handoff_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("handoff_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    handoff_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    handoff_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest result review handoff consumed without explicit reason"
    )
    safe_copy_source = summary_fragment.get("safe_copy") or summary_fragment.get("safe_phone_copy")
    safe_copy = _safe_pc_route_debug_value(
        safe_copy_source
        or (
            "Route-task field retest result review handoff is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # literal false 文案是本 gate 的 grep 围栏，防止只读 handoff 被 UI/Robot 误读成控制授权。
        safe_copy_text = (
            f"{safe_copy_text}; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(handoff.get("safe_evidence_ref") or handoff.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    owner_work_orders = _safe_pc_route_debug_value(summary_fragment.get("owner_work_orders"))
    accepted_reasons = _safe_pc_route_debug_value(summary_fragment.get("accepted_reasons"))
    blocked_reasons = _safe_pc_route_debug_value(summary_fragment.get("blocked_reasons"))
    rerun_reasons = _safe_pc_route_debug_value(summary_fragment.get("rerun_reasons"))
    same_evidence_ref_package = _safe_pc_route_debug_value(
        summary_fragment.get("same_evidence_ref_package")
    )
    next_material_callback_requirements = _safe_pc_route_debug_value(
        summary_fragment.get("next_material_callback_requirements")
    )
    next_required_evidence = _safe_pc_route_debug_value(
        summary_fragment.get("next_required_evidence")
    )
    rerun_commands = _safe_pc_route_debug_value(summary_fragment.get("rerun_commands"))
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "handoff_status": {
                "status": handoff_status or "blocked",
                "verdict": handoff_verdict or "not_proven",
                "reason": handoff_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "source_review_decision_status": _safe_pc_route_debug_dict(source_decision_status)
            or {
                "status": "blocked",
                "verdict": "not_proven",
                "reason": "result review handoff lacks source review decision status",
            },
            "owner_work_orders": owner_work_orders,
            "accepted_reasons": accepted_reasons,
            "blocked_reasons": blocked_reasons,
            "rerun_reasons": rerun_reasons,
            "same_evidence_ref_package": same_evidence_ref_package,
            "next_material_callback_requirements": next_material_callback_requirements,
            "next_required_evidence": next_required_evidence,
            "rerun_commands": rerun_commands,
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status or "blocked",
                "reason": "result review handoff consumed without explicit robot diagnostics summary",
            },
            "robot_compatible_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status or "blocked",
                "reason": "result review handoff consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_GATE,
            "not_proven": _route_task_field_retest_result_review_handoff_not_proven(
                handoff,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )

    required_summary_fields = (
        bool(summary["source_review_decision_status"]),
        isinstance(summary["owner_work_orders"], (dict, list)),
        isinstance(summary["accepted_reasons"], list),
        isinstance(summary["blocked_reasons"], list),
        isinstance(summary["rerun_reasons"], list),
        isinstance(summary["same_evidence_ref_package"], dict),
        isinstance(summary["next_material_callback_requirements"], list),
        isinstance(summary["next_required_evidence"], list),
        isinstance(summary["rerun_commands"], list),
        bool(summary["safe_copy"]),
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_GATE
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "unsupported_result_review_decision_schema_not_proven",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review handoff schema or evidence boundary is unsupported",
                },
                "owner_work_orders": [],
                "accepted_reasons": [],
                "blocked_reasons": ["unsupported_result_review_decision_schema_not_proven"],
                "rerun_reasons": [],
                "same_evidence_ref_package": {},
                "next_material_callback_requirements": [],
                "next_required_evidence": [],
                "rerun_commands": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "handoff_status": {
                    "status": "blocked_missing_result_review_decision_not_proven",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review handoff is missing evidence_ref",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
                "robot_compatible_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "handoff_status": {
                    "status": "evidence_ref_mismatch_rerun_not_proven",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review handoff summary evidence_ref does not match source evidence_ref",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not _route_task_field_retest_result_review_handoff_requires_same_evidence_ref(
        summary_fragment
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "same_evidence_ref_required_false",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review handoff must require the same evidence_ref",
                },
                "same_evidence_ref_required": False,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "handoff_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review handoff is missing required safe summary fields",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required result review handoff summary fields",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "missing required result review handoff summary fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_result_review_handoff_has_disabled_actions(
            summary_fragment
        )
        or _route_task_field_run_console_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "blocked_unsafe_result_review_handoff",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review handoff contains unsafe fields, enabled actions, raw details, or success wording",
                },
                "owner_work_orders": [],
                "accepted_reasons": [],
                "blocked_reasons": ["blocked_unsafe_result_review_handoff"],
                "rerun_reasons": [],
                "same_evidence_ref_package": {},
                "next_material_callback_requirements": [],
                "next_required_evidence": [],
                "rerun_commands": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe result review handoff summary fields",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "unsafe result review handoff summary fields",
                },
                "safe_copy": "Route-task field retest result review handoff was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest result review handoff was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_result_review_intake(source):
    """构建 route-task field retest result review intake 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        intake = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_result_review_intake_summary(
            source_path,
            read_error="route-task field retest result review intake summary is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "intake_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest result review intake summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "result review intake summary missing",
                    },
                    "safe_copy": "Route-task field retest result review intake is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result review intake is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "intake_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest result review intake: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "result review intake JSON read error",
                    },
                    "safe_copy": "Route-task field retest result review intake could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result review intake could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_result_review_intake_summary(
        source_path,
        read_error="route-task field retest result review intake summary is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(intake, dict):
        summary.update(
            {
                "intake_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review intake JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "result review intake JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest result review intake shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest result review intake shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = intake.get("diagnostics") if isinstance(intake.get("diagnostics"), dict) else {}
    # 只消费 result review intake 自己的安全 summary/robot alias，避免串到 dispatch 或 callback gate。
    summary_fragment = (
        intake
        if str(intake.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            intake.get("route_task_field_retest_result_review_intake_summary"),
            intake.get("route_task_field_retest_result_review_intake"),
            intake.get("robot_diagnostics_route_task_field_retest_result_review_intake_summary"),
            intake.get("robot_compatible_summary"),
            intake.get("robot_diagnostics_summary"),
            intake.get("mobile_readonly_summary"),
            intake.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("route_task_field_retest_result_review_intake_summary"),
            diagnostics.get("route_task_field_retest_result_review_intake"),
            diagnostics.get("robot_diagnostics_route_task_field_retest_result_review_intake_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else intake
    source_schema, source_boundary = _route_task_field_retest_result_review_intake_source_contract(
        contract_source
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": intake.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "intake_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review intake lacks a safe diagnostics summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe result review intake summary",
                },
                "safe_copy": "Route-task field retest result review intake is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest result review intake is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("intake_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("review_intake_status")
    if not isinstance(status_source, dict):
        status_source = {}
    intake_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("intake_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    intake_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    intake_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest result review intake consumed without explicit reason"
    )
    safe_copy_source = summary_fragment.get("safe_copy") or summary_fragment.get("safe_phone_copy")
    safe_copy = _safe_pc_route_debug_value(
        safe_copy_source
        or (
            "Route-task field retest result review intake is metadata-only; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # phone copy 保留 literal false，方便 diagnostics/mobile grep 围栏确认没有动作授权。
        safe_copy_text = f"{safe_copy_text}; delivery_success=false; primary_actions_enabled=false."
    source_ref = str(intake.get("safe_evidence_ref") or intake.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "intake_status": {
                "status": intake_status or "blocked",
                "verdict": intake_verdict or "not_proven",
                "reason": intake_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "missing_materials": _safe_pc_route_debug_value(summary_fragment.get("missing_materials")),
            "owner_follow_up": _safe_pc_route_debug_value(summary_fragment.get("owner_follow_up")),
            "review_ready_package": _safe_pc_route_debug_value(summary_fragment.get("review_ready_package")),
            "rerun_package": _safe_pc_route_debug_value(summary_fragment.get("rerun_package")),
            "next_required_evidence": _safe_pc_route_debug_value(summary_fragment.get("next_required_evidence")),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status or "blocked",
                "reason": "result review intake consumed without explicit robot diagnostics summary",
            },
            "robot_compatible_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status or "blocked",
                "reason": "result review intake consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_GATE,
            "not_proven": _route_task_field_retest_result_review_intake_not_proven(
                intake,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )

    required_summary_fields = (
        isinstance(summary["missing_materials"], list),
        bool(summary["owner_follow_up"]),
        bool(summary["review_ready_package"]),
        bool(summary["rerun_package"]),
        isinstance(summary["next_required_evidence"], list),
        bool(summary["safe_copy"]),
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_GATE
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review intake schema or evidence boundary is unsupported",
                },
                "missing_materials": [],
                "owner_follow_up": [],
                "review_ready_package": {},
                "rerun_package": {},
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "intake_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review intake is missing evidence_ref",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
                "robot_compatible_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "intake_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review intake summary evidence_ref does not match source evidence_ref",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "intake_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review intake is missing required safe summary fields",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required result review intake summary fields",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "missing required result review intake summary fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_result_review_intake_has_disabled_actions(
            summary_fragment
        )
        or _route_task_field_run_console_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "blocked_unsafe_review_intake",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result review intake contains unsafe fields, enabled actions, raw details, or success wording",
                },
                "missing_materials": [],
                "owner_follow_up": [],
                "review_ready_package": {},
                "rerun_package": {},
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe result review intake summary fields",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "unsafe result review intake summary fields",
                },
                "safe_copy": "Route-task field retest result review intake was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest result review intake was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_result_callback_intake(source):
    """构建 route-task field retest result callback intake 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        intake = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_result_callback_intake_summary(
            source_path,
            read_error="route-task field retest result callback intake is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "intake_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest result callback intake summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "result callback intake summary missing",
                    },
                    "safe_copy": "Route-task field retest result callback intake is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result callback intake is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "intake_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading route-task field retest result callback intake: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "result callback intake JSON read error",
                    },
                    "safe_copy": "Route-task field retest result callback intake could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result callback intake could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_result_callback_intake_summary(
        source_path,
        read_error="route-task field retest result callback intake is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(intake, dict):
        summary.update(
            {
                "intake_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback intake JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "result callback intake JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest result callback intake shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest result callback intake shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = intake.get("diagnostics") if isinstance(intake.get("diagnostics"), dict) else {}
    # 本轮名字包含 result_callback_intake；这里故意不读取旧 callback_intake key，避免串接上一条链路。
    summary_fragment = (
        intake
        if str(intake.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            intake.get("route_task_field_retest_result_callback_intake_summary"),
            intake.get("route_task_field_retest_result_callback_intake"),
            intake.get("robot_diagnostics_route_task_field_retest_result_callback_intake_summary"),
            intake.get("robot_diagnostics_summary"),
            intake.get("mobile_readonly_summary"),
            intake.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("route_task_field_retest_result_callback_intake_summary"),
            diagnostics.get("route_task_field_retest_result_callback_intake"),
            diagnostics.get("robot_diagnostics_route_task_field_retest_result_callback_intake_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else intake
    source_schema, source_boundary = _route_task_field_retest_result_callback_intake_source_contract(
        contract_source
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": intake.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "intake_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback intake lacks a safe diagnostics summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe result callback intake summary",
                },
                "safe_copy": "Route-task field retest result callback intake is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest result callback intake is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("intake_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("callback_intake_status")
    if not isinstance(status_source, dict):
        status_source = {}
    intake_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("intake_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    intake_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    intake_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest result callback intake consumed without explicit reason"
    )
    safe_copy_source = summary_fragment.get("safe_copy") or summary_fragment.get("safe_phone_copy")
    safe_copy = _safe_pc_route_debug_value(
        safe_copy_source
        or (
            "Route-task field retest result callback intake is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # phone copy 保留 literal boundary，便于 mobile/rg 围栏确认没有动作放行。
        safe_copy_text = (
            f"{safe_copy_text}; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(intake.get("safe_evidence_ref") or intake.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    accepted_updates = _safe_pc_route_debug_value(
        summary_fragment.get("accepted_updates", summary_fragment.get("accepted_materials"))
    )
    missing_updates = _safe_pc_route_debug_value(
        summary_fragment.get("missing_updates", summary_fragment.get("missing_materials"))
    )
    rejected_updates = _safe_pc_route_debug_value(
        summary_fragment.get("rejected_updates", summary_fragment.get("rejected_materials"))
    )
    owner_follow_up = _safe_pc_route_debug_value(summary_fragment.get("owner_follow_up"))
    review_decision_handoff = _safe_pc_route_debug_value(
        summary_fragment.get("review_decision_handoff")
    )
    rerun_commands = _safe_pc_route_debug_value(summary_fragment.get("rerun_commands"))
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "intake_status": {
                "status": intake_status or "blocked",
                "verdict": intake_verdict or "not_proven",
                "reason": intake_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "accepted_materials": accepted_updates,
            "accepted_updates": accepted_updates,
            "missing_materials": missing_updates,
            "missing_updates": missing_updates,
            "rejected_materials": rejected_updates,
            "rejected_updates": rejected_updates,
            "owner_follow_up": owner_follow_up,
            "review_decision_handoff": review_decision_handoff,
            "rerun_commands": rerun_commands,
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status or "blocked",
                "reason": "result callback intake consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_GATE,
            "not_proven": _route_task_field_retest_result_callback_intake_not_proven(
                summary_fragment
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )

    required_summary_fields = (
        isinstance(summary["accepted_updates"], list),
        isinstance(summary["missing_updates"], list),
        isinstance(summary["rejected_updates"], list),
        isinstance(summary["owner_follow_up"], list),
        isinstance(summary["review_decision_handoff"], dict),
        isinstance(summary["rerun_commands"], list),
        bool(summary["safe_copy"]),
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_GATE
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback intake schema or evidence boundary is unsupported",
                },
                "accepted_materials": [],
                "accepted_updates": [],
                "missing_materials": [],
                "missing_updates": [],
                "rejected_materials": [],
                "rejected_updates": [],
                "owner_follow_up": [],
                "review_decision_handoff": {},
                "rerun_commands": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "intake_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback intake is missing evidence_ref",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "intake_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback intake summary evidence_ref does not match source evidence_ref",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not _route_task_field_retest_result_callback_intake_requires_same_evidence_ref(
        summary_fragment
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "same_evidence_ref_required_false",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback intake must require the same evidence_ref",
                },
                "same_evidence_ref_required": False,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "intake_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback intake is missing required safe summary fields",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required result callback intake summary fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_result_callback_intake_has_disabled_actions(
            summary_fragment
        )
        or _route_task_field_run_console_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback intake contains unsafe fields, enabled actions, raw details, or success wording",
                },
                "accepted_materials": [],
                "accepted_updates": [],
                "missing_materials": [],
                "missing_updates": [],
                "rejected_materials": [],
                "rejected_updates": [],
                "owner_follow_up": [],
                "review_decision_handoff": {},
                "rerun_commands": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe result callback intake summary fields",
                },
                "safe_copy": "Route-task field retest result callback intake was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest result callback intake was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_result_callback_review_decision(source):
    """构建 route-task field retest result callback review decision 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        decision = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_result_callback_review_decision_summary(
            source_path,
            read_error=(
                "route-task field retest result callback review decision is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "review_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": (
                            "route-task field retest result callback review decision summary missing"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "result callback review decision summary missing",
                    },
                    "safe_copy": "Route-task field retest result callback review decision is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result callback review decision is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "review_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading route-task field retest result callback "
                            f"review decision: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "result callback review decision JSON read error",
                    },
                    "safe_copy": "Route-task field retest result callback review decision could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result callback review decision could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_result_callback_review_decision_summary(
        source_path,
        read_error="route-task field retest result callback review decision is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(decision, dict):
        summary.update(
            {
                "review_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest result callback review decision JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "result callback review decision JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest result callback review decision shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest result callback review decision shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = decision.get("diagnostics") if isinstance(decision.get("diagnostics"), dict) else {}
    # 只接受 result_callback_review_decision 自己的 summary key，避免误读旧 callback_review_decision gate。
    summary_fragment = (
        decision
        if str(decision.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            decision.get("route_task_field_retest_result_callback_review_decision_summary"),
            decision.get("route_task_field_retest_result_callback_review_decision"),
            decision.get("robot_diagnostics_route_task_field_retest_result_callback_review_decision_summary"),
            decision.get("robot_diagnostics_summary"),
            decision.get("mobile_readonly_summary"),
            decision.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("route_task_field_retest_result_callback_review_decision_summary"),
            diagnostics.get("route_task_field_retest_result_callback_review_decision"),
            diagnostics.get("robot_diagnostics_route_task_field_retest_result_callback_review_decision_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else decision
    source_schema, source_boundary = (
        _route_task_field_retest_result_callback_review_decision_source_contract(
            contract_source
        )
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": decision.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "review_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest result callback review decision lacks a safe diagnostics summary"
                    ),
                },
                "review_decision": "needs_callback_rerun",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe result callback review decision summary",
                },
                "safe_copy": "Route-task field retest result callback review decision is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest result callback review decision is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("review_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    review_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("review_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    review_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    review_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest result callback review decision consumed without explicit reason"
    )
    safe_copy_source = summary_fragment.get("safe_copy") or summary_fragment.get("safe_phone_copy")
    safe_copy = _safe_pc_route_debug_value(
        safe_copy_source
        or (
            "Route-task field retest result callback review decision is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # phone copy 保留 literal boundary，便于 UI 和 grep 围栏确认仍是不可操作元数据。
        safe_copy_text = (
            f"{safe_copy_text}; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(decision.get("safe_evidence_ref") or decision.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    source_callback_intake_status = _safe_pc_route_debug_value(
        summary_fragment.get("source_callback_intake_status")
        if "source_callback_intake_status" in summary_fragment
        else summary_fragment.get("source_intake_status")
        if "source_intake_status" in summary_fragment
        else summary_fragment.get("intake_status")
    )
    material_status = _safe_pc_route_debug_value(summary_fragment.get("material_status"))
    accepted_materials = _safe_pc_route_debug_value(
        summary_fragment.get("accepted_materials", summary_fragment.get("accepted_updates"))
    )
    missing_materials = _safe_pc_route_debug_value(
        summary_fragment.get("missing_materials", summary_fragment.get("missing_updates"))
    )
    rejected_materials = _safe_pc_route_debug_value(
        summary_fragment.get("rejected_materials", summary_fragment.get("rejected_updates"))
    )
    owner_handoff = _safe_pc_route_debug_value(summary_fragment.get("owner_handoff"))
    next_required_evidence = _safe_pc_route_debug_value(
        summary_fragment.get("next_required_evidence")
    )
    rerun_commands = _safe_pc_route_debug_value(summary_fragment.get("rerun_commands"))
    review_decision_value = _redact_route_task_rehearsal_text(
        summary_fragment.get("review_decision")
        or summary_fragment.get("decision")
        or decision.get("review_decision")
        or decision.get("decision")
        or "needs_callback_rerun"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "review_status": {
                "status": review_status or "blocked",
                "verdict": review_verdict or "not_proven",
                "reason": review_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "source_callback_intake_status": source_callback_intake_status
            or {
                "status": review_status or "blocked",
                "verdict": "not_proven",
                "reason": "callback review decision lacks source callback intake status",
            },
            "review_decision": review_decision_value or "needs_callback_rerun",
            "material_status": material_status
            or {
                "status": "blocked",
                "reason": "callback review decision lacks material status",
            },
            "accepted_materials": accepted_materials,
            "missing_materials": missing_materials,
            "rejected_materials": rejected_materials,
            "owner_handoff": owner_handoff,
            "next_required_evidence": next_required_evidence,
            "rerun_commands": rerun_commands,
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": review_status or "blocked",
                "reason": "result callback review decision consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_GATE,
            "not_proven": _route_task_field_retest_result_callback_review_decision_not_proven(
                decision,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )

    required_summary_fields = (
        isinstance(summary["source_callback_intake_status"], (dict, str)),
        bool(summary["review_decision"]),
        isinstance(summary["material_status"], (dict, str)),
        isinstance(summary["accepted_materials"], list),
        isinstance(summary["missing_materials"], list),
        isinstance(summary["rejected_materials"], list),
        isinstance(summary["owner_handoff"], (dict, list, str)),
        isinstance(summary["next_required_evidence"], list),
        isinstance(summary["rerun_commands"], list),
        bool(summary["safe_copy"]),
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "review_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback review decision schema or evidence boundary is unsupported",
                },
                "review_decision": "needs_callback_rerun",
                "material_status": {"status": "blocked", "reason": "unsupported schema"},
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "owner_handoff": {},
                "next_required_evidence": [],
                "rerun_commands": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "review_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback review decision is missing evidence_ref",
                },
                "review_decision": "needs_callback_rerun",
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "review_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback review decision summary evidence_ref does not match source evidence_ref",
                },
                "review_decision": "evidence_ref_mismatch_rerun",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not _route_task_field_retest_result_callback_review_decision_requires_same_evidence_ref(
        summary_fragment
    ):
        summary.update(
            {
                "review_status": {
                    "status": "same_evidence_ref_required_false",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback review decision must require the same evidence_ref",
                },
                "same_evidence_ref_required": False,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "review_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback review decision is missing required safe summary fields",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required result callback review decision summary fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_result_callback_review_decision_has_disabled_actions(
            summary_fragment
        )
        or _route_task_field_run_console_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "review_status": {
                    "status": "rejected_unsafe_callback",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback review decision contains unsafe fields, enabled actions, raw details, or success wording",
                },
                "review_decision": "rejected_unsafe_callback",
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "owner_handoff": {},
                "next_required_evidence": [],
                "rerun_commands": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe result callback review decision summary fields",
                },
                "safe_copy": "Route-task field retest result callback review decision was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest result callback review decision was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary


def summarize_route_task_field_retest_acceptance_execution_callback_review_decision(source):
    """构建 route-task acceptance execution callback review decision 的 metadata-only 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        decision = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = (
            _default_route_task_field_retest_acceptance_execution_callback_review_decision_summary(
                source_path,
                read_error=(
                    "route-task field retest acceptance execution callback review decision "
                    "is not configured"
                ),
            )
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "review_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": (
                            "route-task field retest acceptance execution callback "
                            "review decision summary missing"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution callback review decision missing",
                    },
                    "safe_copy": (
                        "Route-task field retest acceptance execution callback review "
                        "decision is missing; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest acceptance execution callback review "
                        "decision is missing; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "review_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading route-task field retest acceptance execution "
                            f"callback review decision: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution callback review decision JSON read error",
                    },
                    "safe_copy": (
                        "Route-task field retest acceptance execution callback review "
                        "decision could not be read; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest acceptance execution callback review "
                        "decision could not be read; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
    summary = (
        _default_route_task_field_retest_acceptance_execution_callback_review_decision_summary(
            source_path,
            read_error=(
                "route-task field retest acceptance execution callback review decision "
                "is not configured"
            ),
        )
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(decision, dict):
        summary.update(
            {
                "review_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback review "
                        "decision JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "acceptance execution callback review decision JSON shape is invalid",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution callback review decision "
                    "shape is invalid; metadata remains blocked/not_proven."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution callback review decision "
                    "shape is invalid; metadata remains blocked/not_proven."
                ),
            }
        )
        return summary

    diagnostics = decision.get("diagnostics") if isinstance(decision.get("diagnostics"), dict) else {}
    # 只消费本 gate 的 artifact/summary/robot alias，避免把 intake 或 result callback 决策误投给 Robot。
    summary_fragment = (
        decision
        if str(decision.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            decision.get(
                "route_task_field_retest_acceptance_execution_callback_review_decision_summary"
            ),
            decision.get("route_task_field_retest_acceptance_execution_callback_review_decision"),
            decision.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary"
            ),
            decision.get("robot_diagnostics_summary"),
            decision.get("robot_compatible_summary"),
            decision.get("diagnostics_compatible_summary"),
            decision.get("mobile_readonly_summary"),
            decision.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get(
                "route_task_field_retest_acceptance_execution_callback_review_decision_summary"
            ),
            diagnostics.get("route_task_field_retest_acceptance_execution_callback_review_decision"),
            diagnostics.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary"
            ),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else decision
    source_schema, source_boundary = (
        _route_task_field_retest_acceptance_execution_callback_review_decision_source_contract(
            contract_source
        )
    )
    if (
        source_schema
        != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SCHEMA
        or source_boundary
        != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": contract_source.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "review_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback review "
                        "decision schema or evidence boundary is unsupported"
                    ),
                },
                "review_decision": "needs_acceptance_execution_callback_rerun",
                "owner_handoff": {},
                "next_required_evidence": [],
                "safe_rerun_command_summary": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": decision.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "review_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback review "
                        "decision lacks a safe diagnostics summary"
                    ),
                },
                "review_decision": "needs_acceptance_execution_callback_rerun",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe acceptance execution callback review summary",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution callback review decision "
                    "is blocked because no safe summary was provided."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution callback review decision "
                    "is blocked because no safe summary was provided."
                ),
            }
        )
        return summary

    status_source = summary_fragment.get("review_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    review_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("review_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    review_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    review_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or (
            "route-task field retest acceptance execution callback review decision "
            "consumed without explicit reason"
        )
    )
    safe_copy_source = summary_fragment.get("safe_copy") or summary_fragment.get("safe_phone_copy")
    safe_copy = _safe_pc_route_debug_value(
        safe_copy_source
        or (
            "Route-task field retest acceptance execution callback review decision "
            "is metadata-only; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # literal boundary 让 diagnostics/mobile grep 能证明本 alias 没有放行动作。
        safe_copy_text = (
            f"{safe_copy_text}; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(decision.get("safe_evidence_ref") or decision.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else summary_fragment.get("diagnostics_compatible_summary")
        if isinstance(summary_fragment.get("diagnostics_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    source_callback_intake_status = _safe_pc_route_debug_value(
        summary_fragment.get("source_callback_intake_status")
        if "source_callback_intake_status" in summary_fragment
        else summary_fragment.get("source_intake_status")
        if "source_intake_status" in summary_fragment
        else summary_fragment.get("callback_intake_status")
        if "callback_intake_status" in summary_fragment
        else summary_fragment.get("intake_status")
    )
    review_decision_value = _redact_route_task_rehearsal_text(
        summary_fragment.get("review_decision")
        or summary_fragment.get("decision")
        or decision.get("review_decision")
        or decision.get("decision")
        or "needs_acceptance_execution_callback_rerun"
    )
    rerun_summary = _safe_pc_route_debug_value(
        summary_fragment.get("safe_rerun_command_summary")
        if "safe_rerun_command_summary" in summary_fragment
        else summary_fragment.get("rerun_commands_summary")
        if "rerun_commands_summary" in summary_fragment
        else summary_fragment.get("rerun_commands")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "review_status": {
                "status": review_status or "blocked",
                "verdict": review_verdict or "not_proven",
                "reason": review_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "source_callback_intake_status": source_callback_intake_status
            or {
                "status": review_status or "blocked",
                "verdict": "not_proven",
                "reason": "acceptance execution callback review lacks source intake status",
            },
            "review_decision": review_decision_value
            or "needs_acceptance_execution_callback_rerun",
            "owner_handoff": _safe_pc_route_debug_value(summary_fragment.get("owner_handoff")),
            "next_required_evidence": _safe_pc_route_debug_value(
                summary_fragment.get("next_required_evidence")
            ),
            "safe_rerun_command_summary": rerun_summary,
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": review_status or "blocked",
                "reason": (
                    "acceptance execution callback review decision consumed without "
                    "explicit robot diagnostics summary"
                ),
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_GATE,
            "not_proven": (
                _route_task_field_retest_acceptance_execution_callback_review_decision_not_proven(
                    decision,
                    summary_fragment,
                )
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )

    required_summary_fields = (
        isinstance(summary["source_callback_intake_status"], (dict, str)),
        bool(summary["review_decision"]),
        isinstance(summary["owner_handoff"], (dict, list, str)),
        isinstance(summary["next_required_evidence"], list),
        isinstance(summary["safe_rerun_command_summary"], (dict, list, str)),
        bool(summary["safe_copy"]),
    )
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "review_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback review "
                        "decision is missing evidence_ref"
                    ),
                },
                "review_decision": "needs_acceptance_execution_callback_rerun",
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "review_status": {
                    "status": "evidence_ref_mismatch",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback review "
                        "decision summary evidence_ref does not match source evidence_ref"
                    ),
                },
                "review_decision": "evidence_ref_mismatch_rerun",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not _route_task_field_retest_acceptance_execution_callback_review_decision_requires_same_evidence_ref(
        summary_fragment
    ):
        summary.update(
            {
                "review_status": {
                    "status": "same_evidence_ref_required_false",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback review "
                        "decision must require the same evidence_ref"
                    ),
                },
                "same_evidence_ref_required": False,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "review_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback review "
                        "decision is missing required safe summary fields"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required acceptance callback review decision fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_acceptance_execution_callback_review_decision_has_disabled_actions(
            summary_fragment
        )
        or _route_task_field_run_console_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "review_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback review "
                        "decision contains unsafe fields, enabled actions, raw details, "
                        "or success wording"
                    ),
                },
                "review_decision": "rejected_unsafe_callback",
                "owner_handoff": {},
                "next_required_evidence": [],
                "safe_rerun_command_summary": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe acceptance execution callback review decision fields",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution callback review decision "
                    "was blocked because summary fields could imply control, ACK, "
                    "Nav2/HIL, raw artifact access, or delivery success."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution callback review decision "
                    "was blocked because summary fields could imply control, ACK, "
                    "Nav2/HIL, raw artifact access, or delivery success."
                ),
            }
        )
    return summary


def summarize_route_task_field_retest_acceptance_execution_callback_review_handoff(source):
    """构建 acceptance execution callback review handoff 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        handoff = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = (
            _default_route_task_field_retest_acceptance_execution_callback_review_handoff_summary(
                source_path,
                read_error=(
                    "route-task field retest acceptance execution callback review "
                    "handoff is not configured"
                ),
            )
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "handoff_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": (
                            "route-task field retest acceptance execution callback "
                            "review handoff summary missing"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution callback review handoff missing",
                    },
                    "safe_copy": (
                        "Route-task field retest acceptance execution callback review "
                        "handoff is missing; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest acceptance execution callback review "
                        "handoff is missing; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "handoff_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading route-task field retest acceptance execution "
                            f"callback review handoff: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution callback review handoff JSON read error",
                    },
                    "safe_copy": (
                        "Route-task field retest acceptance execution callback review "
                        "handoff could not be read; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest acceptance execution callback review "
                        "handoff could not be read; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
    summary = (
        _default_route_task_field_retest_acceptance_execution_callback_review_handoff_summary(
            source_path,
            read_error=(
                "route-task field retest acceptance execution callback review handoff "
                "is not configured"
            ),
        )
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(handoff, dict):
        summary.update(
            {
                "handoff_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback review "
                        "handoff JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "acceptance execution callback review handoff JSON shape is invalid",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution callback review handoff "
                    "shape is invalid; metadata remains blocked/not_proven."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution callback review handoff "
                    "shape is invalid; metadata remains blocked/not_proven."
                ),
            }
        )
        return summary

    diagnostics = handoff.get("diagnostics") if isinstance(handoff.get("diagnostics"), dict) else {}
    # 只消费本 gate 的 artifact、summary 或 Robot alias，防止 review decision / result handoff 串链。
    handoff_schema = str(handoff.get("schema") or "")
    summary_fragment = (
        handoff
        if handoff_schema
        == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            handoff.get(
                "route_task_field_retest_acceptance_execution_callback_review_handoff_summary"
            ),
            handoff.get("route_task_field_retest_acceptance_execution_callback_review_handoff"),
            handoff.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary"
            ),
            handoff.get("robot_diagnostics_summary"),
            handoff.get("robot_compatible_summary"),
            handoff.get("diagnostics_compatible_summary"),
            handoff.get("mobile_readonly_summary"),
            handoff.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get(
                "route_task_field_retest_acceptance_execution_callback_review_handoff_summary"
            ),
            diagnostics.get("route_task_field_retest_acceptance_execution_callback_review_handoff"),
            diagnostics.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary"
            ),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if (
        not summary_fragment
        and handoff_schema
        == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SCHEMA
    ):
        # artifact 允许直接作为安全摘要，但若存在 nested summary，上面的分支必须优先采用它。
        summary_fragment = handoff

    contract_source = summary_fragment if summary_fragment else handoff
    source_schema, source_boundary = (
        _route_task_field_retest_acceptance_execution_callback_review_handoff_source_contract(
            contract_source
        )
    )
    if (
        source_schema
        != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SCHEMA
        or source_boundary
        != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE
    ):
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": contract_source.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "handoff_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback review "
                        "handoff schema or evidence boundary is unsupported"
                    ),
                },
                "source_review_decision": "needs_acceptance_execution_callback_rerun",
                "owner_handoff": {},
                "next_required_evidence": [],
                "safe_rerun_hint": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": handoff.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "handoff_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback review "
                        "handoff lacks a safe diagnostics summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe acceptance execution callback review handoff summary",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution callback review handoff "
                    "is blocked because no safe summary was provided."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution callback review handoff "
                    "is blocked because no safe summary was provided."
                ),
            }
        )
        return summary

    status_source = summary_fragment.get("handoff_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    handoff_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("handoff_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    handoff_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    handoff_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or (
            "route-task field retest acceptance execution callback review handoff "
            "consumed without explicit reason"
        )
    )
    safe_copy_source = summary_fragment.get("safe_copy") or summary_fragment.get("safe_phone_copy")
    safe_copy = _safe_pc_route_debug_value(
        safe_copy_source
        or (
            "Route-task field retest acceptance execution callback review handoff "
            "is metadata-only; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # safe_phone_copy 保留 literal false，便于 diagnostics/mobile grep 证明没有动作授权。
        safe_copy_text = (
            f"{safe_copy_text}; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(handoff.get("safe_evidence_ref") or handoff.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else summary_fragment.get("diagnostics_compatible_summary")
        if isinstance(summary_fragment.get("diagnostics_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    source_review_decision_status = _safe_pc_route_debug_value(
        summary_fragment.get("source_review_decision_status")
        if "source_review_decision_status" in summary_fragment
        else summary_fragment.get("source_review_status")
        if "source_review_status" in summary_fragment
        else summary_fragment.get("review_status")
        if "review_status" in summary_fragment
        else summary_fragment.get("status_summary")
    )
    source_review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("source_review_decision")
        or summary_fragment.get("review_decision")
        or handoff.get("source_review_decision")
        or handoff.get("review_decision")
        or "needs_acceptance_execution_callback_rerun"
    )
    safe_rerun_hint = _safe_pc_route_debug_value(
        summary_fragment.get("safe_rerun_hint")
        if "safe_rerun_hint" in summary_fragment
        else summary_fragment.get("safe_rerun_command_summary")
        if "safe_rerun_command_summary" in summary_fragment
        else summary_fragment.get("rerun_commands_summary")
        if "rerun_commands_summary" in summary_fragment
        else summary_fragment.get("rerun_commands")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "handoff_status": {
                "status": handoff_status or "blocked",
                "verdict": handoff_verdict or "not_proven",
                "reason": handoff_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "source_review_decision_status": source_review_decision_status
            or {
                "status": handoff_status or "blocked",
                "verdict": "not_proven",
                "reason": "acceptance execution callback review handoff lacks source review status",
            },
            "source_review_decision": source_review_decision
            or "needs_acceptance_execution_callback_rerun",
            "owner_handoff": _safe_pc_route_debug_value(summary_fragment.get("owner_handoff")),
            "next_required_evidence": _safe_pc_route_debug_value(
                summary_fragment.get("next_required_evidence")
            ),
            "safe_rerun_hint": safe_rerun_hint,
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status or "blocked",
                "reason": (
                    "acceptance execution callback review handoff consumed without "
                    "explicit robot diagnostics summary"
                ),
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE,
            "not_proven": (
                _route_task_field_retest_acceptance_execution_callback_review_handoff_not_proven(
                    handoff,
                    summary_fragment,
                )
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )

    required_summary_fields = (
        isinstance(summary["source_review_decision_status"], (dict, str)),
        bool(summary["source_review_decision"]),
        isinstance(summary["owner_handoff"], (dict, list, str)),
        isinstance(summary["next_required_evidence"], list),
        isinstance(summary["safe_rerun_hint"], (dict, list, str)),
        bool(summary["safe_copy"]),
    )
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "handoff_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback review "
                        "handoff is missing evidence_ref"
                    ),
                },
                "source_review_decision": "needs_acceptance_execution_callback_rerun",
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "handoff_status": {
                    "status": "evidence_ref_mismatch_rerun",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback review "
                        "handoff summary evidence_ref does not match source evidence_ref"
                    ),
                },
                "source_review_decision": "evidence_ref_mismatch_rerun",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not _route_task_field_retest_acceptance_execution_callback_review_handoff_requires_same_evidence_ref(
        summary_fragment
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "same_evidence_ref_required_false",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback review "
                        "handoff must require the same evidence_ref"
                    ),
                },
                "same_evidence_ref_required": False,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "handoff_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback review "
                        "handoff is missing required safe summary fields"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required acceptance callback review handoff fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_acceptance_execution_callback_review_handoff_has_disabled_actions(
            summary_fragment
        )
        or _route_task_field_run_console_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "blocked_unsafe_review_handoff",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution callback review "
                        "handoff contains unsafe fields, enabled actions, raw details, "
                        "or success wording"
                    ),
                },
                "source_review_decision": "blocked_unsafe_review_handoff",
                "owner_handoff": {},
                "next_required_evidence": [],
                "safe_rerun_hint": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe acceptance execution callback review handoff fields",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution callback review handoff "
                    "was blocked because summary fields could imply control, ACK, "
                    "Nav2/HIL, raw artifact access, or delivery success."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution callback review handoff "
                    "was blocked because summary fields could imply control, ACK, "
                    "Nav2/HIL, raw artifact access, or delivery success."
                ),
            }
        )
    return summary


def summarize_route_task_field_retest_acceptance_execution_handoff_intake(source):
    """构建 acceptance execution handoff intake 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        intake = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_acceptance_execution_handoff_intake_summary(
            source_path,
            read_error="route-task field retest acceptance execution handoff intake is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "intake_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest acceptance execution handoff intake summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution handoff intake missing",
                    },
                    "safe_copy": (
                        "Route-task field retest acceptance execution handoff intake "
                        "is missing; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest acceptance execution handoff intake "
                        "is missing; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "intake_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading route-task field retest acceptance execution "
                            f"handoff intake: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution handoff intake JSON read error",
                    },
                    "safe_copy": (
                        "Route-task field retest acceptance execution handoff intake "
                        "could not be read; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest acceptance execution handoff intake "
                        "could not be read; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
    summary = _default_route_task_field_retest_acceptance_execution_handoff_intake_summary(
        source_path,
        read_error="route-task field retest acceptance execution handoff intake is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(intake, dict):
        summary.update(
            {
                "intake_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance execution handoff intake JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "acceptance execution handoff intake JSON shape is invalid",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution handoff intake "
                    "shape is invalid; metadata remains blocked/not_proven."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution handoff intake "
                    "shape is invalid; metadata remains blocked/not_proven."
                ),
            }
        )
        return summary

    diagnostics = intake.get("diagnostics") if isinstance(intake.get("diagnostics"), dict) else {}
    intake_schema = str(intake.get("schema") or "")
    # Autonomy 可能先交付主 summary，也可能嵌在 diagnostics/Robot alias；这里只消费白名单摘要。
    summary_fragment = (
        intake
        if intake_schema == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            intake.get("route_task_field_retest_acceptance_execution_handoff_intake_summary"),
            intake.get("route_task_field_retest_acceptance_execution_handoff_intake"),
            intake.get("robot_diagnostics_route_task_field_retest_acceptance_execution_handoff_intake_summary"),
            intake.get("robot_diagnostics_summary"),
            intake.get("robot_compatible_summary"),
            intake.get("diagnostics_compatible_summary"),
            intake.get("mobile_readonly_summary"),
            intake.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("route_task_field_retest_acceptance_execution_handoff_intake_summary"),
            diagnostics.get("route_task_field_retest_acceptance_execution_handoff_intake"),
            diagnostics.get("robot_diagnostics_route_task_field_retest_acceptance_execution_handoff_intake_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if (
        not summary_fragment
        and intake_schema == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SCHEMA
    ):
        # artifact 可直接作为安全摘要；若存在 nested summary，上面的白名单优先采用 nested 版本。
        summary_fragment = intake

    contract_source = summary_fragment if summary_fragment else intake
    source_schema, source_boundary = (
        _route_task_field_retest_acceptance_execution_handoff_intake_source_contract(contract_source)
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_GATE
    ):
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": contract_source.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "intake_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution handoff intake "
                        "schema or evidence boundary is unsupported"
                    ),
                },
                "owner_acknowledgement": {},
                "next_evidence_flags": [],
                "next_required_evidence": [],
                "safe_rerun_hint": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("intake_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("handoff_intake_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    intake_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("intake_status")
        or summary_fragment.get("handoff_intake_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    intake_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    intake_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest acceptance execution handoff intake consumed without explicit reason"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Route-task field retest acceptance execution handoff intake is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # safe_phone_copy 保留 literal false，便于 diagnostics/mobile grep 证明没有动作授权。
        safe_copy_text = (
            f"{safe_copy_text}; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(intake.get("safe_evidence_ref") or intake.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else summary_fragment.get("diagnostics_compatible_summary")
        if isinstance(summary_fragment.get("diagnostics_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    owner_acknowledgement = _safe_pc_route_debug_value(
        summary_fragment.get("owner_acknowledgement")
        if "owner_acknowledgement" in summary_fragment
        else summary_fragment.get("owner_ack")
        if "owner_ack" in summary_fragment
        else summary_fragment.get("owner_handoff")
    )
    next_evidence_flags = _safe_pc_route_debug_value(
        summary_fragment.get("next_evidence_flags")
        if "next_evidence_flags" in summary_fragment
        else summary_fragment.get("next_required_evidence")
    )
    next_required_evidence = _safe_pc_route_debug_value(
        summary_fragment.get("next_required_evidence")
        if "next_required_evidence" in summary_fragment
        else summary_fragment.get("next_evidence_flags")
    )
    safe_rerun_hint = _safe_pc_route_debug_value(
        summary_fragment.get("safe_rerun_hint")
        if "safe_rerun_hint" in summary_fragment
        else summary_fragment.get("safe_rerun_command_summary")
        if "safe_rerun_command_summary" in summary_fragment
        else summary_fragment.get("rerun_commands_summary")
        if "rerun_commands_summary" in summary_fragment
        else summary_fragment.get("rerun_commands")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "intake_status": {
                "status": intake_status or "blocked",
                "verdict": intake_verdict or "not_proven",
                "reason": intake_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "owner_acknowledgement": owner_acknowledgement,
            "next_evidence_flags": next_evidence_flags,
            "next_required_evidence": next_required_evidence,
            "safe_rerun_hint": safe_rerun_hint,
            "same_evidence_ref_required": summary_fragment.get("same_evidence_ref_required") is True,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status or "blocked",
                "reason": "acceptance execution handoff intake consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_GATE,
            "not_proven": _route_task_field_retest_acceptance_execution_handoff_intake_not_proven(
                intake,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )

    required_summary_fields = (
        isinstance(summary["owner_acknowledgement"], (dict, list, str)),
        isinstance(summary["next_evidence_flags"], list),
        isinstance(summary["next_required_evidence"], list),
        isinstance(summary["safe_rerun_hint"], (dict, list, str)),
        bool(summary["safe_copy"]),
    )
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "intake_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance execution handoff intake is missing evidence_ref",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "intake_status": {
                    "status": "evidence_ref_mismatch_rerun",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution handoff intake "
                        "summary evidence_ref does not match source evidence_ref"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not _route_task_field_retest_acceptance_execution_handoff_intake_requires_same_evidence_ref(
        summary_fragment
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "same_evidence_ref_required_false",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance execution handoff intake must require the same evidence_ref",
                },
                "same_evidence_ref_required": False,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "intake_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution handoff intake "
                        "is missing required safe summary fields"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required acceptance execution handoff intake fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_acceptance_execution_handoff_intake_has_disabled_actions(
            summary_fragment
        )
        or _route_task_field_run_console_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "blocked_unsafe_handoff_intake",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution handoff intake "
                        "contains unsafe fields, enabled actions, raw details, or success wording"
                    ),
                },
                "owner_acknowledgement": {},
                "next_evidence_flags": [],
                "next_required_evidence": [],
                "safe_rerun_hint": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe acceptance execution handoff intake fields",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution handoff intake was blocked "
                    "because summary fields could imply control, ACK, Nav2/HIL, raw artifact "
                    "access, or delivery success."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution handoff intake was blocked "
                    "because summary fields could imply control, ACK, Nav2/HIL, raw artifact "
                    "access, or delivery success."
                ),
            }
        )
    return summary


def summarize_route_task_field_retest_acceptance_execution_rerun_queue(source):
    """构建 acceptance execution rerun queue 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        queue = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_acceptance_execution_rerun_queue_summary(
            source_path,
            read_error="route-task field retest acceptance execution rerun queue is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "queue_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "route-task field retest acceptance execution rerun queue summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution rerun queue missing",
                    },
                    "safe_copy": (
                        "Route-task field retest acceptance execution rerun queue "
                        "is missing; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest acceptance execution rerun queue "
                        "is missing; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                queue = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "queue_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading route-task field retest acceptance execution "
                            f"rerun queue: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution rerun queue JSON read error",
                    },
                    "safe_copy": (
                        "Route-task field retest acceptance execution rerun queue "
                        "could not be read; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest acceptance execution rerun queue "
                        "could not be read; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
    summary = _default_route_task_field_retest_acceptance_execution_rerun_queue_summary(
        source_path,
        read_error="route-task field retest acceptance execution rerun queue is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(queue, dict):
        summary.update(
            {
                "queue_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance execution rerun queue JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "acceptance execution rerun queue JSON shape is invalid",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution rerun queue "
                    "shape is invalid; metadata remains blocked/not_proven."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution rerun queue "
                    "shape is invalid; metadata remains blocked/not_proven."
                ),
            }
        )
        return summary

    diagnostics = queue.get("diagnostics") if isinstance(queue.get("diagnostics"), dict) else {}
    queue_schema = str(queue.get("schema") or "")
    # Autonomy 可以传 summary、artifact 内嵌 summary、Robot alias 或 diagnostics wrapper；Robot 只消费白名单摘要。
    summary_fragment = (
        queue
        if queue_schema == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            queue.get("robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary"),
            queue.get("route_task_field_retest_acceptance_execution_rerun_queue_summary"),
            queue.get("route_task_field_retest_acceptance_execution_rerun_queue"),
            queue.get("robot_diagnostics_summary"),
            queue.get("robot_compatible_summary"),
            queue.get("diagnostics_compatible_summary"),
            queue.get("mobile_readonly_summary"),
            queue.get("phone_safe_summary"),
            diagnostics.get("robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary"),
            diagnostics.get("route_task_field_retest_acceptance_execution_rerun_queue_summary"),
            diagnostics.get("route_task_field_retest_acceptance_execution_rerun_queue"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if (
        not summary_fragment
        and queue_schema == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_SCHEMA
    ):
        # artifact 本身必须满足同一套安全字段；存在 nested summary 时上面的白名单优先。
        summary_fragment = queue

    contract_source = summary_fragment if summary_fragment else queue
    source_schema, source_boundary = (
        _route_task_field_retest_acceptance_execution_rerun_queue_source_contract(
            contract_source
        )
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_GATE
    ):
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": contract_source.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "queue_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun queue "
                        "schema or evidence boundary is unsupported"
                    ),
                },
                "blocked_reason": "unsupported schema or evidence boundary",
                "owner_handoff": {},
                "next_required_evidence": [],
                "safe_rerun_hint": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("queue_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("rerun_queue_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    queue_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("queue_status")
        or summary_fragment.get("rerun_queue_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    queue_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    queue_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("blocked_reason")
        or summary_fragment.get("reason")
        or "route-task field retest acceptance execution rerun queue consumed without explicit reason"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Route-task field retest acceptance execution rerun queue is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # safe_phone_copy 保留 literal false，便于 mobile/diagnostics 证明它不是动作授权。
        safe_copy_text = (
            f"{safe_copy_text}; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(queue.get("safe_evidence_ref") or queue.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else summary_fragment.get("diagnostics_compatible_summary")
        if isinstance(summary_fragment.get("diagnostics_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    source_handoff_status = _safe_pc_route_debug_value(
        summary_fragment.get("source_handoff_intake_status")
        if "source_handoff_intake_status" in summary_fragment
        else summary_fragment.get("handoff_intake_status")
    )
    owner_handoff = _safe_pc_route_debug_value(
        summary_fragment.get("owner_handoff")
        if "owner_handoff" in summary_fragment
        else summary_fragment.get("owner_acknowledgement")
    )
    next_required_evidence = _safe_pc_route_debug_value(
        summary_fragment.get("next_required_evidence")
        if "next_required_evidence" in summary_fragment
        else summary_fragment.get("next_evidence_flags")
    )
    safe_rerun_hint = _safe_pc_route_debug_value(
        summary_fragment.get("safe_rerun_hint")
        if "safe_rerun_hint" in summary_fragment
        else summary_fragment.get("safe_rerun_command_summary")
        if "safe_rerun_command_summary" in summary_fragment
        else summary_fragment.get("rerun_commands_summary")
        if "rerun_commands_summary" in summary_fragment
        else summary_fragment.get("rerun_commands")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "queue_status": {
                "status": queue_status or "blocked",
                "verdict": queue_verdict or "not_proven",
                "reason": queue_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "source_handoff_intake_status": source_handoff_status,
            "owner_handoff": owner_handoff,
            "next_required_evidence": next_required_evidence,
            "safe_rerun_hint": safe_rerun_hint,
            "blocked_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("blocked_reason") or queue_reason
            ),
            "same_evidence_ref_required": summary_fragment.get("same_evidence_ref_required") is True,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": queue_status or "blocked",
                "reason": "acceptance execution rerun queue consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_GATE,
            "not_proven": _route_task_field_retest_acceptance_execution_rerun_queue_not_proven(
                queue,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )

    required_summary_fields = (
        isinstance(summary["source_handoff_intake_status"], (dict, list, str)),
        isinstance(summary["owner_handoff"], (dict, list, str)),
        isinstance(summary["next_required_evidence"], list),
        isinstance(summary["safe_rerun_hint"], (dict, list, str)),
        bool(summary["safe_copy"]),
    )
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "queue_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance execution rerun queue is missing evidence_ref",
                },
                "blocked_reason": "missing evidence_ref",
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "queue_status": {
                    "status": "evidence_ref_mismatch_rerun_queue",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun queue "
                        "summary evidence_ref does not match source evidence_ref"
                    ),
                },
                "blocked_reason": "same evidence_ref mismatch",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not summary["same_evidence_ref_required"]:
        summary.update(
            {
                "queue_status": {
                    "status": "same_evidence_ref_required_false",
                    "verdict": "not_proven",
                    "reason": "route-task field retest acceptance execution rerun queue must require the same evidence_ref",
                },
                "blocked_reason": "same_evidence_ref_required must be JSON true",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "queue_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun queue "
                        "is missing required safe summary fields"
                    ),
                },
                "blocked_reason": "missing required acceptance execution rerun queue fields",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required acceptance execution rerun queue fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_acceptance_execution_rerun_queue_has_disabled_actions(
            summary_fragment
        )
        or _route_task_field_run_console_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "queue_status": {
                    "status": "blocked_unsafe_rerun_queue",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun queue "
                        "contains unsafe fields, enabled actions, raw details, or success wording"
                    ),
                },
                "owner_handoff": {},
                "next_required_evidence": [],
                "safe_rerun_hint": [],
                "blocked_reason": "unsafe acceptance execution rerun queue fields",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe acceptance execution rerun queue fields",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution rerun queue was blocked "
                    "because summary fields could imply control, ACK, Nav2/HIL, raw artifact "
                    "access, or delivery success."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution rerun queue was blocked "
                    "because summary fields could imply control, ACK, Nav2/HIL, raw artifact "
                    "access, or delivery success."
                ),
            }
        )
    return summary


def summarize_route_task_field_retest_acceptance_execution_rerun_result_intake(source):
    """构建 acceptance execution rerun result intake 的 sanitized metadata-only 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        intake = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_acceptance_execution_rerun_result_intake_summary(
            source_path,
            read_error=(
                "route-task field retest acceptance execution rerun result intake "
                "is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "intake_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": (
                            "route-task field retest acceptance execution rerun result "
                            "intake summary missing"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution rerun result intake summary missing",
                    },
                    "safe_copy": (
                        "Route-task field retest acceptance execution rerun result intake "
                        "is missing; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest acceptance execution rerun result intake "
                        "is missing; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "intake_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading route-task field retest acceptance execution "
                            f"rerun result intake: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution rerun result intake JSON read error",
                    },
                    "safe_copy": (
                        "Route-task field retest acceptance execution rerun result intake "
                        "could not be read; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest acceptance execution rerun result intake "
                        "could not be read; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
    summary = _default_route_task_field_retest_acceptance_execution_rerun_result_intake_summary(
        source_path,
        read_error=(
            "route-task field retest acceptance execution rerun result intake is not configured"
        ),
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(intake, dict):
        summary.update(
            {
                "intake_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result intake "
                        "JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "acceptance execution rerun result intake JSON shape is invalid",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution rerun result intake "
                    "shape is invalid; metadata remains blocked/not_proven."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution rerun result intake "
                    "shape is invalid; metadata remains blocked/not_proven."
                ),
            }
        )
        return summary

    diagnostics = intake.get("diagnostics") if isinstance(intake.get("diagnostics"), dict) else {}
    # 只寻找 Autonomy 提供的 sanitized summary；raw artifact 本体不能作为 safe summary 穿透。
    summary_fragment = (
        intake
        if str(intake.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            intake.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_intake_summary"
            ),
            intake.get("route_task_field_retest_acceptance_execution_rerun_result_intake_summary"),
            intake.get("robot_diagnostics_summary"),
            intake.get("robot_compatible_summary"),
            intake.get("diagnostics_compatible_summary"),
            intake.get("mobile_readonly_summary"),
            intake.get("phone_safe_summary"),
            diagnostics.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_intake_summary"
            ),
            diagnostics.get("route_task_field_retest_acceptance_execution_rerun_result_intake_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else intake
    source_schema, source_boundary = (
        _route_task_field_retest_acceptance_execution_rerun_result_intake_source_contract(
            contract_source
        )
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": intake.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "intake_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result intake "
                        "lacks a sanitized diagnostics summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing sanitized rerun result intake summary",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution rerun result intake is "
                    "blocked because no sanitized summary was provided."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution rerun result intake is "
                    "blocked because no sanitized summary was provided."
                ),
            }
        )
        return summary

    status_source = summary_fragment.get("intake_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("rerun_result_intake_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    intake_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("intake_status")
        or summary_fragment.get("rerun_result_intake_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    intake_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    intake_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("blocked_reason")
        or summary_fragment.get("reason")
        or (
            "route-task field retest acceptance execution rerun result intake "
            "consumed without explicit reason"
        )
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Route-task field retest acceptance execution rerun result intake is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # literal false 是 Robot/mobile 共同的围栏，避免安全摘要被误当成动作授权。
        safe_copy_text = (
            f"{safe_copy_text}; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(intake.get("safe_evidence_ref") or intake.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "intake_status": {
                "status": intake_status or "blocked",
                "verdict": intake_verdict or "not_proven",
                "reason": intake_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "owner_handoff": _safe_pc_route_debug_value(summary_fragment.get("owner_handoff")),
            "next_required_evidence": _safe_pc_route_debug_value(
                summary_fragment.get("next_required_evidence")
            ),
            "boundary_flags": dict(
                boundary_flags,
                metadata_only=True,
                delivery_success=False,
                primary_actions_enabled=False,
                control_entrypoint_enabled=False,
            ),
            "same_evidence_ref_required": summary_fragment.get("same_evidence_ref_required") is True,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status or "blocked",
                "reason": (
                    "rerun result intake consumed without explicit robot diagnostics summary"
                ),
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_GATE,
            "not_proven": (
                _route_task_field_retest_acceptance_execution_rerun_result_intake_not_proven(
                    intake,
                    summary_fragment,
                )
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )

    required_summary_fields = (
        isinstance(summary["owner_handoff"], (dict, list, str)),
        isinstance(summary["next_required_evidence"], list),
        bool(summary["boundary_flags"]),
        bool(summary["safe_copy"]),
    )
    unsafe_material = any(
        _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
            item
        )
        for item in (
            status_source,
            summary["owner_handoff"],
            summary["next_required_evidence"],
            safe_copy,
            safe_copy_text,
            robot_summary,
        )
    )
    if (
        source_schema
        != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_SCHEMA
        or source_boundary
        != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_GATE
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result intake "
                        "schema or evidence boundary is unsupported"
                    ),
                },
                "owner_handoff": {},
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "intake_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result intake "
                        "is missing evidence_ref"
                    ),
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "intake_status": {
                    "status": "evidence_ref_mismatch_rerun_result_intake",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result intake "
                        "summary evidence_ref does not match source evidence_ref"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not summary["same_evidence_ref_required"]:
        summary.update(
            {
                "intake_status": {
                    "status": "same_evidence_ref_required_false",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result intake "
                        "must require the same evidence_ref"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "intake_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result intake "
                        "is missing required safe summary fields"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required rerun result intake summary fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_acceptance_execution_rerun_result_intake_has_disabled_actions(
            summary_fragment
        )
        or bool(summary["boundary_flags"].get("raw_artifact_consumed"))
        or bool(summary["boundary_flags"].get("control_entrypoint_enabled"))
        or unsafe_material
        or _route_task_field_run_intake_has_unsafe_control_claims(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "blocked_unsafe_rerun_result_intake",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result intake "
                        "contains unsafe fields, enabled actions, raw details, or success wording"
                    ),
                },
                "owner_handoff": {},
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe acceptance execution rerun result intake fields",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution rerun result intake was "
                    "blocked because summary fields could imply control, ACK, Nav2/HIL, "
                    "raw artifact access, hardware material, or delivery success."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution rerun result intake was "
                    "blocked because summary fields could imply control, ACK, Nav2/HIL, "
                    "raw artifact access, hardware material, or delivery success."
                ),
            }
        )
    return summary


def summarize_route_task_field_retest_acceptance_execution_rerun_result_review_decision(source):
    """构建 acceptance execution rerun result review decision 的 sanitized metadata-only 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        decision = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = (
            _default_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary(
                source_path,
                read_error=(
                    "route-task field retest acceptance execution rerun result review decision "
                    "is not configured"
                ),
            )
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "decision_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": (
                            "route-task field retest acceptance execution rerun result "
                            "review decision summary missing"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution rerun result review decision summary missing",
                    },
                    "safe_copy": (
                        "Route-task field retest acceptance execution rerun result review "
                        "decision is missing; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest acceptance execution rerun result review "
                        "decision is missing; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "decision_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading route-task field retest acceptance execution "
                            f"rerun result review decision: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": (
                            "acceptance execution rerun result review decision JSON read error"
                        ),
                    },
                    "safe_copy": (
                        "Route-task field retest acceptance execution rerun result review "
                        "decision could not be read; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest acceptance execution rerun result review "
                        "decision could not be read; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
    summary = (
        _default_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary(
            source_path,
            read_error=(
                "route-task field retest acceptance execution rerun result review decision "
                "is not configured"
            ),
        )
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(decision, dict):
        summary.update(
            {
                "decision_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result review "
                        "decision JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": (
                        "acceptance execution rerun result review decision JSON shape is invalid"
                    ),
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution rerun result review "
                    "decision shape is invalid; metadata remains blocked/not_proven."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution rerun result review "
                    "decision shape is invalid; metadata remains blocked/not_proven."
                ),
            }
        )
        return summary

    diagnostics = decision.get("diagnostics") if isinstance(decision.get("diagnostics"), dict) else {}
    # 只寻找 Autonomy 提供的 sanitized decision summary；raw artifact schema 必须 fail closed。
    summary_fragment = (
        decision
        if str(decision.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            decision.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary"
            ),
            decision.get(
                "route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary"
            ),
            decision.get("robot_diagnostics_summary"),
            decision.get("robot_compatible_summary"),
            decision.get("diagnostics_compatible_summary"),
            decision.get("mobile_readonly_summary"),
            decision.get("phone_safe_summary"),
            diagnostics.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary"
            ),
            diagnostics.get(
                "route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else decision
    source_schema, source_boundary = (
        _route_task_field_retest_acceptance_execution_rerun_result_review_decision_source_contract(
            contract_source
        )
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": decision.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "decision_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result review "
                        "decision lacks a sanitized diagnostics summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing sanitized rerun result review decision summary",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution rerun result review decision "
                    "is blocked because no sanitized summary was provided."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution rerun result review decision "
                    "is blocked because no sanitized summary was provided."
                ),
            }
        )
        return summary

    status_source = summary_fragment.get("decision_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("review_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    decision_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("decision_status")
        or summary_fragment.get("review_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    decision_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    decision_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("blocked_reason")
        or summary_fragment.get("reason")
        or (
            "route-task field retest acceptance execution rerun result review "
            "decision consumed without explicit reason"
        )
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Route-task field retest acceptance execution rerun result review decision "
            "is metadata-only; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # literal false 是 Robot/mobile 共同围栏，避免 decision 摘要被误当成 Start/Dropoff/Cancel 授权。
        safe_copy_text = (
            f"{safe_copy_text}; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(decision.get("safe_evidence_ref") or decision.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "decision_status": {
                "status": decision_status or "blocked",
                "verdict": decision_verdict or "not_proven",
                "reason": decision_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "review_decision": _redact_route_task_rehearsal_text(
                summary_fragment.get("review_decision")
                or status_source.get("decision")
                or decision_status
                or "not_proven"
            ),
            "owner_handoff": _safe_pc_route_debug_value(summary_fragment.get("owner_handoff")),
            "next_required_evidence": _safe_pc_route_debug_value(
                summary_fragment.get("next_required_evidence")
            ),
            "boundary_flags": dict(
                boundary_flags,
                metadata_only=True,
                delivery_success=False,
                primary_actions_enabled=False,
                raw_artifact_consumed=False,
                control_entrypoint_enabled=False,
            ),
            "same_evidence_ref_required": summary_fragment.get("same_evidence_ref_required") is True,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": decision_status or "blocked",
                "reason": (
                    "rerun result review decision consumed without explicit robot diagnostics summary"
                ),
            },
            "boundary": (
                ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_GATE
            ),
            "not_proven": (
                _route_task_field_retest_acceptance_execution_rerun_result_review_decision_not_proven(
                    decision,
                    summary_fragment,
                )
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )

    required_summary_fields = (
        isinstance(summary["owner_handoff"], (dict, list, str)),
        isinstance(summary["next_required_evidence"], list),
        bool(summary["boundary_flags"]),
        bool(summary["safe_copy"]),
    )
    unsafe_material = any(
        _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
            item
        )
        for item in (
            status_source,
            summary["owner_handoff"],
            summary["next_required_evidence"],
            safe_copy,
            safe_copy_text,
            robot_summary,
        )
    )
    if (
        source_schema
        != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_SCHEMA
        or source_boundary
        != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "decision_status": {
                    "status": "blocked_unsupported_rerun_result_intake",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result review "
                        "decision schema or evidence boundary is unsupported"
                    ),
                },
                "owner_handoff": {},
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "decision_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result review "
                        "decision is missing evidence_ref"
                    ),
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "decision_status": {
                    "status": "evidence_ref_mismatch_rerun_result",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result review "
                        "decision summary evidence_ref does not match source evidence_ref"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not summary["same_evidence_ref_required"]:
        summary.update(
            {
                "decision_status": {
                    "status": "same_evidence_ref_required_false",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result review "
                        "decision must require the same evidence_ref"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "decision_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result review "
                        "decision is missing required safe summary fields"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required rerun result review decision summary fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_acceptance_execution_rerun_result_intake_has_disabled_actions(
            summary_fragment
        )
        or bool(summary["boundary_flags"].get("raw_artifact_consumed"))
        or bool(summary["boundary_flags"].get("control_entrypoint_enabled"))
        or unsafe_material
        or _route_task_field_run_intake_has_unsafe_control_claims(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "decision_status": {
                    "status": "blocked_unsafe_rerun_result",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result review "
                        "decision contains unsafe fields, enabled actions, raw details, or "
                        "success wording"
                    ),
                },
                "owner_handoff": {},
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe acceptance execution rerun result review decision fields",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution rerun result review decision "
                    "was blocked because summary fields could imply control, ACK, Nav2/HIL, "
                    "raw artifact access, hardware material, or delivery success."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution rerun result review decision "
                    "was blocked because summary fields could imply control, ACK, Nav2/HIL, "
                    "raw artifact access, hardware material, or delivery success."
                ),
            }
        )
    return summary


def summarize_route_task_field_retest_acceptance_execution_rerun_result_review_handoff(source):
    """构建 acceptance execution rerun result review handoff 的 sanitized metadata-only 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        handoff = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = (
            _default_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary(
                source_path,
                read_error=(
                    "route-task field retest acceptance execution rerun result review handoff "
                    "is not configured"
                ),
            )
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "handoff_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": (
                            "route-task field retest acceptance execution rerun result "
                            "review handoff summary missing"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution rerun result review handoff summary missing",
                    },
                    "safe_copy": (
                        "Route-task field retest acceptance execution rerun result review "
                        "handoff is missing; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest acceptance execution rerun result review "
                        "handoff is missing; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "handoff_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading route-task field retest acceptance execution "
                            f"rerun result review handoff: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "acceptance execution rerun result review handoff JSON read error",
                    },
                    "safe_copy": (
                        "Route-task field retest acceptance execution rerun result review "
                        "handoff could not be read; metadata remains blocked/not_proven."
                    ),
                    "safe_phone_copy": (
                        "Route-task field retest acceptance execution rerun result review "
                        "handoff could not be read; metadata remains blocked/not_proven."
                    ),
                }
            )
            return summary

    summary = (
        _default_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary(
            source_path,
            read_error=(
                "route-task field retest acceptance execution rerun result review handoff "
                "is not configured"
            ),
        )
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(handoff, dict):
        summary.update(
            {
                "handoff_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result review "
                        "handoff JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "acceptance execution rerun result review handoff JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = handoff.get("diagnostics") if isinstance(handoff.get("diagnostics"), dict) else {}
    # 只接收 Autonomy worker 产出的 sanitized summary，避免 Robot 侧打开 raw artifact 或材料目录。
    summary_fragment = (
        handoff
        if str(handoff.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            handoff.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary"
            ),
            handoff.get(
                "route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary"
            ),
            handoff.get("robot_diagnostics_summary"),
            handoff.get("robot_compatible_summary"),
            handoff.get("diagnostics_compatible_summary"),
            handoff.get("mobile_readonly_summary"),
            handoff.get("phone_safe_summary"),
            diagnostics.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary"
            ),
            diagnostics.get(
                "route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else handoff
    source_schema, source_boundary = (
        _route_task_field_retest_acceptance_execution_rerun_result_review_handoff_source_contract(
            contract_source
        )
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": handoff.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "handoff_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result review "
                        "handoff lacks a sanitized diagnostics summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing sanitized rerun result review handoff summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("handoff_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    handoff_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("handoff_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    handoff_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("blocked_reason")
        or summary_fragment.get("reason")
        or (
            "route-task field retest acceptance execution rerun result review "
            "handoff consumed without explicit reason"
        )
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Route-task field retest acceptance execution rerun result review handoff "
            "is metadata-only; source=software_proof; not_proven; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # literal false 是手机/diagnostics 的共同围栏，防止 handoff copy 被解释成控制授权。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(handoff.get("safe_evidence_ref") or handoff.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    owner_handoff = _safe_pc_route_debug_value(summary_fragment.get("owner_handoff"))
    owner_role = _redact_route_task_rehearsal_text(
        summary_fragment.get("owner_role")
        or (owner_handoff.get("owner_role") if isinstance(owner_handoff, dict) else "")
        or (owner_handoff.get("owner") if isinstance(owner_handoff, dict) else "")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "handoff_status": {
                "status": handoff_status or "blocked",
                "verdict": "not_proven",
                "reason": handoff_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "owner_role": owner_role,
            "owner_handoff": owner_handoff,
            "next_required_evidence": _safe_pc_route_debug_value(
                summary_fragment.get("next_required_evidence")
            ),
            "boundary_flags": dict(
                boundary_flags,
                metadata_only=True,
                source=EVIDENCE_SOURCE_SOFTWARE,
                delivery_success=False,
                primary_actions_enabled=False,
                raw_artifact_consumed=False,
                control_entrypoint_enabled=False,
            ),
            "same_evidence_ref_required": summary_fragment.get("same_evidence_ref_required") is True,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status or "blocked",
                "reason": "rerun result review handoff consumed without robot diagnostics summary",
            },
            "boundary": (
                ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_GATE
            ),
            "not_proven": (
                _route_task_field_retest_acceptance_execution_rerun_result_review_handoff_not_proven(
                    handoff,
                    summary_fragment,
                )
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )

    required_summary_fields = (
        bool(summary["safe_evidence_ref"]),
        bool(summary["owner_role"] or summary["owner_handoff"]),
        isinstance(summary["next_required_evidence"], list),
        bool(summary["boundary_flags"]),
    )
    unsafe_material = any(
        _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
            item
        )
        for item in (
            status_source,
            summary["owner_handoff"],
            summary["next_required_evidence"],
            safe_copy,
            safe_copy_text,
            robot_summary,
        )
    )
    if (
        source_schema
        != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_SCHEMA
        or source_boundary
        != ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_GATE
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "blocked_unsupported_rerun_result_review_decision",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result review "
                        "handoff schema or evidence boundary is unsupported"
                    ),
                },
                "owner_role": "",
                "owner_handoff": {},
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "handoff_status": {
                    "status": "evidence_ref_mismatch_rerun_result_handoff_blocked",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result review "
                        "handoff evidence_ref does not match source evidence_ref"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not summary["same_evidence_ref_required"] or not all(required_summary_fields):
        summary.update(
            {
                "handoff_status": {
                    "status": "needs_acceptance_execution_rerun_result_material_backfill",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result review "
                        "handoff is missing required safe metadata"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required safe handoff fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_acceptance_execution_rerun_result_intake_has_disabled_actions(
            summary_fragment
        )
        or bool(summary["boundary_flags"].get("raw_artifact_consumed"))
        or bool(summary["boundary_flags"].get("control_entrypoint_enabled"))
        or unsafe_material
        or _route_task_field_run_intake_has_unsafe_control_claims(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "blocked_unsafe_rerun_result_handoff_copy",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest acceptance execution rerun result review "
                        "handoff contains unsafe fields, enabled actions, raw details, or "
                        "success wording"
                    ),
                },
                "owner_role": "",
                "owner_handoff": {},
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe acceptance execution rerun result review handoff fields",
                },
                "safe_copy": (
                    "Route-task field retest acceptance execution rerun result review handoff "
                    "was blocked because summary fields could imply control, ACK, Nav2/HIL, "
                    "raw artifact access, hardware material, or delivery success."
                ),
                "safe_phone_copy": (
                    "Route-task field retest acceptance execution rerun result review handoff "
                    "was blocked because summary fields could imply control, ACK, Nav2/HIL, "
                    "raw artifact access, hardware material, or delivery success."
                ),
            }
        )
    return summary


def summarize_route_task_field_retest_result_callback_review_handoff(source):
    """构建 route-task field retest result callback review handoff 的 metadata-only diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        handoff = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_route_task_field_retest_result_callback_review_handoff_summary(
            source_path,
            read_error=(
                "route-task field retest result callback review handoff is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "handoff_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": (
                            "route-task field retest result callback review handoff summary missing"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "result callback review handoff summary missing",
                    },
                    "safe_copy": "Route-task field retest result callback review handoff is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result callback review handoff is missing; metadata remains blocked/not_proven.",
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "handoff_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading route-task field retest result callback "
                            f"review handoff: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "result callback review handoff JSON read error",
                    },
                    "safe_copy": "Route-task field retest result callback review handoff could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field retest result callback review handoff could not be read; metadata remains blocked/not_proven.",
                }
            )
            return summary
    summary = _default_route_task_field_retest_result_callback_review_handoff_summary(
        source_path,
        read_error="route-task field retest result callback review handoff is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(handoff, dict):
        summary.update(
            {
                "handoff_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest result callback review handoff JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "result callback review handoff JSON shape is invalid",
                },
                "safe_copy": "Route-task field retest result callback review handoff shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field retest result callback review handoff shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    diagnostics = handoff.get("diagnostics") if isinstance(handoff.get("diagnostics"), dict) else {}
    # 只消费 handoff 自己的 summary/robot alias，避免串到旧 review-result-handoff 或 review-decision gate。
    summary_fragment = (
        handoff
        if str(handoff.get("schema") or "")
        == ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            handoff.get("route_task_field_retest_result_callback_review_handoff_summary"),
            handoff.get("route_task_field_retest_result_callback_review_handoff"),
            handoff.get("robot_diagnostics_route_task_field_retest_result_callback_review_handoff_summary"),
            handoff.get("robot_compatible_summary"),
            handoff.get("robot_diagnostics_summary"),
            handoff.get("mobile_readonly_summary"),
            handoff.get("phone_safe_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("route_task_field_retest_result_callback_review_handoff_summary"),
            diagnostics.get("route_task_field_retest_result_callback_review_handoff"),
            diagnostics.get("robot_diagnostics_route_task_field_retest_result_callback_review_handoff_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else handoff
    source_schema, source_boundary = (
        _route_task_field_retest_result_callback_review_handoff_source_contract(
            contract_source
        )
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": handoff.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "handoff_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": (
                        "route-task field retest result callback review handoff lacks a safe diagnostics summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe result callback review handoff summary",
                },
                "safe_copy": "Route-task field retest result callback review handoff is blocked because no safe summary was provided.",
                "safe_phone_copy": "Route-task field retest result callback review handoff is blocked because no safe summary was provided.",
            }
        )
        return summary

    status_source = summary_fragment.get("handoff_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    handoff_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("handoff_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    handoff_verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict")
        or status_source.get("decision")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    handoff_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("reason")
        or "route-task field retest result callback review handoff consumed without explicit reason"
    )
    safe_copy_source = summary_fragment.get("safe_copy") or summary_fragment.get("safe_phone_copy")
    safe_copy = _safe_pc_route_debug_value(
        safe_copy_source
        or (
            "Route-task field retest result callback review handoff is metadata-only; "
            "same_evidence_ref_required=true; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # safe_phone_copy 保留 literal false，便于 ROS/mobile grep 围栏确认没有控制或交付成功语义。
        safe_copy_text = (
            f"{safe_copy_text}; same_evidence_ref_required=true; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(handoff.get("safe_evidence_ref") or handoff.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    owner_follow_up = _safe_pc_route_debug_value(summary_fragment.get("owner_follow_up"))
    review_ready_package = _safe_pc_route_debug_value(
        summary_fragment.get("review_ready_package")
    )
    rerun_package = _safe_pc_route_debug_value(summary_fragment.get("rerun_package"))
    next_required_evidence = _safe_pc_route_debug_value(
        summary_fragment.get("next_required_evidence")
    )
    source_review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("source_review_decision")
        or summary_fragment.get("review_decision")
        or handoff.get("source_review_decision")
        or handoff.get("review_decision")
        or "needs_callback_rerun"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "handoff_status": {
                "status": handoff_status or "blocked",
                "verdict": handoff_verdict or "not_proven",
                "reason": handoff_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "source_review_decision": source_review_decision or "needs_callback_rerun",
            "owner_follow_up": owner_follow_up,
            "review_ready_package": review_ready_package,
            "rerun_package": rerun_package,
            "next_required_evidence": next_required_evidence,
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status or "blocked",
                "reason": "result callback review handoff consumed without explicit robot diagnostics summary",
            },
            "robot_compatible_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status or "blocked",
                "reason": "result callback review handoff consumed without explicit robot diagnostics summary",
            },
            "boundary": ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_GATE,
            "not_proven": _route_task_field_retest_result_callback_review_handoff_not_proven(
                handoff,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )

    required_summary_fields = (
        bool(summary["source_review_decision"]),
        isinstance(summary["owner_follow_up"], (dict, list, str)),
        isinstance(summary["review_ready_package"], (dict, list, str)),
        isinstance(summary["rerun_package"], (dict, list, str)),
        isinstance(summary["next_required_evidence"], list),
        bool(summary["safe_copy"]),
    )
    if (
        source_schema != ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_SCHEMA
        or source_boundary != ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_GATE
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback review handoff schema or evidence boundary is unsupported",
                },
                "source_review_decision": "needs_callback_rerun",
                "owner_follow_up": [],
                "review_ready_package": {},
                "rerun_package": {},
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if not summary["safe_evidence_ref"]:
        summary.update(
            {
                "handoff_status": {
                    "status": "missing_evidence_ref",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback review handoff is missing evidence_ref",
                },
                "source_review_decision": "needs_callback_rerun",
                "robot_diagnostics_summary": {"status": "blocked", "reason": "missing evidence_ref"},
                "robot_compatible_summary": {"status": "blocked", "reason": "missing evidence_ref"},
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "handoff_status": {
                    "status": "evidence_ref_mismatch_rerun",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback review handoff summary evidence_ref does not match source evidence_ref",
                },
                "source_review_decision": "evidence_ref_mismatch_rerun",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not _route_task_field_retest_result_callback_review_handoff_requires_same_evidence_ref(
        summary_fragment
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "same_evidence_ref_required_false",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback review handoff must require the same evidence_ref",
                },
                "same_evidence_ref_required": False,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "same_evidence_ref_required must be JSON true",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "handoff_status": {
                    "status": "missing_required_summary_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback review handoff is missing required safe summary fields",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required result callback review handoff summary fields",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "missing required result callback review handoff summary fields",
                },
            }
        )
        return summary
    if (
        not _route_task_field_retest_result_callback_review_handoff_has_disabled_actions(
            summary_fragment
        )
        or _route_task_field_run_console_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "blocked_unsafe_review_handoff",
                    "verdict": "not_proven",
                    "reason": "route-task field retest result callback review handoff contains unsafe fields, enabled actions, raw details, or success wording",
                },
                "source_review_decision": "blocked_unsafe_review_handoff",
                "owner_follow_up": [],
                "review_ready_package": {},
                "rerun_package": {},
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe result callback review handoff summary fields",
                },
                "robot_compatible_summary": {
                    "status": "blocked",
                    "reason": "unsafe result callback review handoff summary fields",
                },
                "safe_copy": "Route-task field retest result callback review handoff was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
                "safe_phone_copy": "Route-task field retest result callback review handoff was blocked because summary fields could imply control, ACK, Nav2/HIL, raw artifact access, or delivery success.",
            }
        )
    return summary
