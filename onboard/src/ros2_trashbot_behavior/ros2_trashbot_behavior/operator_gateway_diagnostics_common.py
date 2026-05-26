import json
import os

from ros2_trashbot_behavior.operator_gateway_diagnostics_route_rehearsal import (
    _redact_route_task_rehearsal_text,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_vision_review import REVIEW_DECISION_VALUES


# 本模块只放跨 diagnostics 子域复用的轻量 helper。
# 它不持有 ROS2 topic/action/service 契约，也不改任何硬件参数。
# facade 继续从这里 re-export 名称，保护历史测试和外部导入路径。
# hardware proof 相关 helper 必须保持保守语义：软件证据不能升级成实机通过。
# review decision log 相关 helper 必须复用 vision review 的合法决策集合。
# log refs 和 safe_int 是 payload 构建入口的兼容 helper，不引入新字段。
# 这里的错误文本是前端和测试可见契约，组织代码时不能顺手改写。
# 这里的默认值是缺证据时的安全边界，不能因为拆模块而放宽。


# 这些状态值已经被手机端和测试固定引用，拆模块时只移动定义位置。
HARDWARE_PROOF_STATUSES = {"software_proof", "needs_hil", "invalid_config", "read_error"}


def _task_terminal_field_material_intake_copy_is_unsafe(value):
    # 材料入口 copy 面向手机/diagnostics，任何现场通过、HIL、O5 或控制授权暗示都必须整体阻断。
    text = _redact_route_task_rehearsal_text(value).strip().lower()
    if not text:
        return True
    guarded_phrases = (
        "not delivery success",
        "not a delivery success",
        "delivery_success=false",
        "primary_actions_enabled=false",
        "safe_to_control=false",
        "not field pass",
        "not real field pass",
        "not route/elevator field pass",
        "not hil",
        "not proven",
        "not_proven",
        "metadata-only",
        "software_proof",
        "must not",
    )
    unsafe_phrases = (
        "delivery success",
        "field pass",
        "field-pass",
        "route/elevator field pass",
        "route elevator field pass",
        "hil pass",
        "real hil",
        "o5 external proof",
        "external proof passed",
        "control grant",
        "safe to control",
        "start delivery enabled",
        "confirm dropoff enabled",
        "cancel enabled",
        "ack posted",
        "terminal ack",
        "cursor advanced",
        "nav2 started",
        "dropoff complete",
        "cancel complete",
    )
    guarded_text = text
    for guard in guarded_phrases:
        guarded_text = guarded_text.replace(guard, "")
    for phrase in unsafe_phrases:
        if phrase in guarded_text:
            return True
    return False


def _default_hardware_proof_summary(path, status="read_error", read_error=""):
    # 默认摘要必须 fail-closed，避免缺少 artifact 时被误读成硬件已经通过。
    return {
        # status 是 operator gateway 自己的降级结果，不直接等同 artifact status。
        "status": status,
        # artifact_ref 保留用户输入文本，便于前端显示缺失路径。
        "artifact_ref": str(path or ""),
        # source_status 只有读到有效 artifact 后才填充，避免暗示已有来源。
        "source_status": "",
        # exists 明确区分未配置、路径不存在、读取失败三类情况。
        "exists": False,
        # read_error 是用户可读错误，不抛异常给诊断 payload 构建链路。
        "read_error": str(read_error or ""),
        # summary 文案明确禁止把离线 proof 当作硬件 pass。
        "summary": "Hardware diagnostics proof is not available; no hardware pass can be inferred.",
        # next_step 指向 HIL，提醒软件 proof 只是前置证据。
        "next_step": "Run hardware_diagnostics_proof and then complete WAVE ROVER hardware-in-loop validation.",
        # vendor_sources 只透传 artifact 明示来源，不在这里推断资料。
        "vendor_sources": [],
        # risk_flags 默认空，但缺 artifact 时仍由 status/read_error 表示不可用。
        "risk_flags": [],
        # hil_recipe 是后续人工/硬件同学执行 HIL 的提示，不是验证结果。
        "hil_recipe": {},
    }


def _hardware_proof_risk_text(flag):
    # risk flag 既可能是字符串也可能是对象，统一转成文本以复用旧的 HIL 风险判定。
    if isinstance(flag, dict):
        # 字段顺序沿用旧逻辑，避免同一 flag 得到不同文本匹配结果。
        parts = [
            flag.get("id", ""),
            flag.get("severity", ""),
            flag.get("detail", ""),
            flag.get("message", ""),
        ]
        # 空字段不能进入拼接结果，否则会改变旧摘要中的关键字匹配行为。
        return " ".join(str(part) for part in parts if part)
    return str(flag)


def _has_hil_risk(risk_flags):
    # 非 list 输入说明 artifact 不可信，必须按仍需 HIL 处理。
    if not isinstance(risk_flags, list):
        return True
    for flag in risk_flags:
        # 兼容旧 artifact 的字符串风险和新 artifact 的结构化风险对象。
        text = _hardware_proof_risk_text(flag).lower()
        # severity 缺失时不擅自假设为高危，除非 flag id 直接声明 hil_required。
        severity = str(flag.get("severity", "")).lower() if isinstance(flag, dict) else ""
        # 字符串 flag 用全文本作为 id，保持旧版本字符串风险的判定通路。
        flag_id = str(flag.get("id", "")).lower() if isinstance(flag, dict) else text
        if flag_id == "hil_required":
            return True
        # 只有 high/critical 的 HIL 文本风险才阻塞，保持原软件 proof 降级口径。
        if ("hil" in text or "hardware-in-loop" in text) and severity in {"high", "critical"}:
            return True
    return False


def summarize_hardware_proof(path):
    """返回离线 WAVE ROVER proof artifact 的手机端安全摘要。"""
    # artifact 来自硬件包；operator gateway 只读取并降级，不发明硬件通过结论。
    proof_path = os.path.expanduser(str(path or ""))
    # 先构造完整默认对象，后续每个提前返回都能保持字段集完整。
    summary = _default_hardware_proof_summary(
        proof_path,
        read_error="hardware diagnostics proof is not configured",
    )
    if not proof_path:
        return summary
    if not os.path.exists(proof_path):
        # 缺文件是配置/采集问题，不抛异常，前端展示 next_step 即可。
        summary["read_error"] = f"hardware diagnostics proof not found: {proof_path}"
        return summary

    summary["exists"] = True
    try:
        # 使用 UTF-8 读取，兼容仓库内 evidence JSON 和跨平台开发环境。
        with open(proof_path, "r", encoding="utf-8") as f:
            artifact = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary["read_error"] = f"failed reading hardware diagnostics proof: {exc}"
        return summary

    if not isinstance(artifact, dict):
        # 非对象 JSON 没有可验证 schema，必须保持 read_error。
        summary["read_error"] = "hardware diagnostics proof JSON must be an object"
        return summary

    source_status = str(artifact.get("status") or "")
    summary["source_status"] = source_status
    # 只透传 list 类型，避免脏 JSON 把字符串拆成逐字符列表。
    summary["vendor_sources"] = (
        list(artifact.get("vendor_sources")) if isinstance(artifact.get("vendor_sources"), list) else []
    )
    summary["risk_flags"] = (
        list(artifact.get("risk_flags")) if isinstance(artifact.get("risk_flags"), list) else []
    )
    # hil_recipe 是给后续实机验证看的结构化提示，非对象时按空对象处理。
    summary["hil_recipe"] = artifact.get("hil_recipe") if isinstance(artifact.get("hil_recipe"), dict) else {}

    if not source_status:
        # source status 缺失时不能根据其他字段猜测 proof 状态。
        summary["read_error"] = "hardware diagnostics proof is missing status"
        return summary

    if source_status == "invalid_config":
        # invalid_config 是软件配置失败，不允许被提升为软件 proof 或 HIL pass。
        summary.update(
            {
                "status": "invalid_config",
                "summary": "Hardware diagnostics proof found an invalid bridge configuration.",
                "next_step": "Fix the reported bridge configuration, rerun software proof, then run WAVE ROVER HIL.",
                "read_error": str((artifact.get("config_validation") or {}).get("error", "")),
            }
        )
        return summary

    if source_status == "software_proof_ready":
        if _has_hil_risk(summary["risk_flags"]):
            # 软件 proof 就绪但 HIL 仍阻塞时，手机端必须看到 needs_hil。
            summary.update(
                {
                    "status": "needs_hil",
                    "summary": "Software proof exists, hardware-in-loop still required before treating the robot as validated.",
                    "next_step": "Run the WAVE ROVER HIL recipe on a prepared robot and capture UART, motion, IMU, and battery evidence.",
                    "read_error": "",
                }
            )
            return summary
        # 没有高危 HIL flag 也只能说明软件 proof，不代表真实硬件已经验证。
        summary.update(
            {
                "status": "software_proof",
                "summary": "Software proof is ready only; this does not validate real UART, wheel motion, IMU, battery, or HIL.",
                "next_step": "Use this artifact as software evidence, then schedule WAVE ROVER hardware-in-loop validation.",
                "read_error": "",
            }
        )
        return summary

    if source_status == "feedback_parse_failed":
        # feedback 解析失败不能视为无风险，它仍需要有效反馈样本和实机 HIL。
        summary.update(
            {
                "status": "needs_hil",
                "summary": "Software artifact exists but feedback parsing failed; hardware-in-loop validation is still required.",
                "next_step": "Inspect the feedback sample, rerun proof with valid T=1001 feedback, then run WAVE ROVER HIL.",
                "read_error": "feedback sample did not parse as trusted hardware feedback",
            }
        )
        return summary

    # 未知 source status 保持 read_error，便于新增 artifact 状态时显式补映射。
    summary["read_error"] = f"unsupported hardware diagnostics proof status: {source_status}"
    return summary


def normalize_log_refs(value):
    # API 参数历史上支持 list/tuple 和逗号字符串，这里保留宽松输入兼容性。
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        # list/tuple 模式不 strip，沿用旧行为，只过滤空字符串化结果。
        return [str(item) for item in value if str(item)]
    text = str(value).strip()
    if not text:
        return []
    # 字符串路径按逗号拆分，和原 CLI/HTTP 参数解析保持一致。
    return [item.strip() for item in text.split(",") if item.strip()]


def default_review_decision_log(path, status="read_error", read_error=""):
    # 失败默认值保留完整字段集，前端和测试不用按状态补字段。
    return {
        # status 表示日志读取状态，不表示每个样本的人工审核状态。
        "status": status,
        # decision_log_ref 保留展开后的路径，方便定位配置来源。
        "decision_log_ref": str(path or ""),
        # exists 只表示文件存在且进入读取流程，不表示 JSONL 全部有效。
        "exists": False,
        # decision_count 统计有效决策行，重复 sample_id 仍计数。
        "decision_count": 0,
        # sample_count 统计最终索引里的 sample_id 去重数量。
        "sample_count": 0,
        # read_error 为空代表读取流程成功，非法行会写入具体行号。
        "read_error": str(read_error or ""),
    }


def review_decision_entry(record):
    # 只复制公开字段，避免 JSONL 里额外字段泄漏到诊断 payload。
    return {
        # decision_id 缺失时保留空字符串，兼容旧前端固定字段展示。
        "decision_id": str(record.get("decision_id", "")),
        # decision 已在调用方校验合法集合，这里只做字符串化。
        "decision": str(record.get("decision", "")),
        # comment/option/operator 都是人工输入，缺失时不能返回 None。
        "comment": str(record.get("comment", "")),
        "option": str(record.get("option", "")),
        "operator": str(record.get("operator", "")),
        # timestamp 允许保持原始类型，避免破坏历史 JSONL 的时间格式。
        "timestamp": record.get("timestamp"),
    }


def load_review_decision_log(path):
    # REVIEW_DECISION_VALUES 来自 vision review 模块，确保有效决策集合只有一个来源。
    decision_log_path = os.path.expanduser(str(path or ""))
    # not_configured 是空路径的稳定状态，和 missing 文件路径区分开。
    summary = default_review_decision_log(
        decision_log_path,
        status="not_configured",
        read_error="review decision log is not configured",
    )
    decision_index = {}
    if not decision_log_path:
        return summary, decision_index
    if not os.path.exists(decision_log_path):
        # missing 仍返回空索引，让 vision summary 能继续生成 pending 队列。
        summary["status"] = "missing"
        summary["read_error"] = f"review decision log not found: {decision_log_path}"
        return summary, decision_index

    summary["exists"] = True
    # 进入读取流程后先清空默认错误，后续解析失败会写入更具体原因。
    summary["read_error"] = ""
    try:
        with open(decision_log_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                text = line.strip()
                if not text:
                    # 空行对人工维护 JSONL 友好，旧行为是静默跳过。
                    continue
                try:
                    record = json.loads(text)
                except json.JSONDecodeError as exc:
                    # JSON 语法错误会中止读取，避免部分脏日志被误认为完整。
                    summary["status"] = "read_error"
                    summary["read_error"] = f"invalid decision JSONL at line {line_number}: {exc}"
                    return summary, {}
                if not isinstance(record, dict):
                    # 非对象行没有 sample_id/decision，按旧语义忽略。
                    continue
                sample_id = str(record.get("sample_id", "")).strip()
                decision = str(record.get("decision", "")).strip()
                # 无 sample_id 或非法 decision 的行按旧语义静默跳过。
                if not sample_id or decision not in REVIEW_DECISION_VALUES:
                    continue
                summary["decision_count"] += 1
                # 同一 sample_id 后写入的有效行覆盖旧行，保留“最后决策”语义。
                decision_index[sample_id] = review_decision_entry(record)
    except OSError as exc:
        # 文件系统错误也要降级成 payload 字段，避免状态接口整体失败。
        summary["status"] = "read_error"
        summary["read_error"] = f"failed reading review decision log: {exc}"
        return summary, {}

    # sample_count 统计去重后的 sample_id，decision_count 统计有效行数。
    summary["sample_count"] = len(decision_index)
    summary["status"] = "ok"
    return summary, decision_index


def safe_int(value, default=0):
    # 诊断摘要要容忍脏状态文件，转换失败时按调用方默认值返回。
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
