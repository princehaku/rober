import re


ELEVATOR_ASSIST_PROMPT = "你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,"
ELEVATOR_ASSIST_PROOF_GATE = "software_proof_docker_elevator_assist_default_mainline_gate"
ELEVATOR_ASSIST_REHEARSAL_SCHEMA = "trashbot.elevator_assist_rehearsal_evidence.v1"
ELEVATOR_ASSIST_REHEARSAL_PROOF_GATE = "software_proof_docker_elevator_evidence_driven_mainline_gate"
ELEVATOR_ASSIST_BOUNDARY = (
    "software proof dry-run only; not real elevator, not real speaker/TTS, "
    "not real Nav2/fixed-route, not HIL; 不证明真实电梯、真实喇叭、真实 Nav2、HIL 或送达成功"
)
ELEVATOR_ASSIST_NOT_PROVEN = (
    "real_elevator",
    "real_speaker_tts",
    "real_nav2_or_fixed_route",
    "hil",
    "delivery_success",
)
ELEVATOR_ASSIST_RERUN_GUIDANCE = (
    "Keep elevator_assist_enabled=true with elevator_assist_mode=dry_run for the "
    "default software proof gate; only disable it with an operator-visible reason."
)
ELEVATOR_ASSIST_DRY_RUN_PHASES = (
    "approaching_elevator",
    "waiting_elevator_open",
    "entering_elevator",
    "requesting_floor_help",
    "waiting_target_floor",
    "exiting_elevator",
    "resume_delivery",
)
ELEVATOR_ASSIST_FEEDBACK_MESSAGES = {
    "approaching_elevator": "已进入电梯辅助流程，正在接近电梯厅。",
    "waiting_elevator_open": "已到电梯厅，等待电梯开门。",
    "entering_elevator": "电梯门可进入，正在进入电梯。",
    "requesting_floor_help": "已进入电梯，正在请求帮忙按楼层。",
    "waiting_target_floor": "正在等待目标楼层，请保持通道安全。",
    "exiting_elevator": "已到目标楼层，准备驶出电梯。",
    "resume_delivery": "已驶出电梯，继续送往垃圾站。",
    "elevator_rehearsal_evidence_validation": "电梯演练证据未通过校验，需要人工接管。",
}
ELEVATOR_ASSIST_REHEARSAL_REQUIRED_PHASES = (
    "waiting_elevator_open",
    "entering_elevator",
    "requesting_floor_help",
    "waiting_target_floor",
    "exiting_elevator",
)
ELEVATOR_ASSIST_REHEARSAL_REQUIRED_NOT_PROVEN = (
    "real_elevator",
    "hil",
    "delivery_success",
)
ELEVATOR_ASSIST_REHEARSAL_EVIDENCE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")
ELEVATOR_ASSIST_DRY_RUN_EVIDENCE = {
    "approaching_elevator": "door_closed_or_unknown",
    "waiting_elevator_open": "door_open",
    "entering_elevator": "inside_elevator",
    "requesting_floor_help": "inside_elevator",
    "waiting_target_floor": "target_floor_confirmed",
    "exiting_elevator": "safe_to_exit",
    "resume_delivery": "safe_to_exit",
}
ELEVATOR_ASSIST_FAILURES = {
    "door_timeout": {
        "phase": "waiting_elevator_open",
        "evidence": "door_closed_or_unknown",
        "reason": "elevator door did not open before dry-run timeout",
    },
    "target_floor_unconfirmed": {
        "phase": "waiting_target_floor",
        "evidence": "target_floor_unconfirmed",
        "reason": "target floor was not confirmed by dry-run evidence",
    },
    "unsafe_to_exit": {
        "phase": "exiting_elevator",
        "evidence": "unsafe_to_exit",
        "reason": "dry-run evidence marked elevator exit unsafe",
    },
}


def with_elevator_assist_boundary(payload, *, phone_copy):
    # boundary 字段集中写入，避免 dry-run、artifact 成功、artifact 失败三条路径
    # 在 delivery_success / primary_actions_enabled 上出现不一致。
    payload.update(
        {
            "proof_gate": payload.get("proof_gate") or ELEVATOR_ASSIST_PROOF_GATE,
            "evidence_boundary": payload.get("evidence_boundary") or ELEVATOR_ASSIST_PROOF_GATE,
            "boundary": ELEVATOR_ASSIST_BOUNDARY,
            "not_proven": list(ELEVATOR_ASSIST_NOT_PROVEN),
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_phone_copy": phone_copy,
            "rerun_guidance": ELEVATOR_ASSIST_RERUN_GUIDANCE,
        }
    )
    return payload


def is_safe_elevator_evidence_ref(value):
    if not isinstance(value, str):
        return False
    # 证据锚点允许 run id 常见字符，但禁止路径分隔符和空白进入 task_record 顶层。
    return ELEVATOR_ASSIST_REHEARSAL_EVIDENCE_REF_RE.fullmatch(value.strip()) is not None


def validate_rehearsal_artifact(payload):
    # artifact 是 software-proof 输入材料，校验失败必须 fail-closed，
    # 不能回退成“已完成电梯”或“可控制”状态。
    if not isinstance(payload, dict):
        return "elevator rehearsal evidence artifact must be a JSON object"
    if payload.get("schema") != ELEVATOR_ASSIST_REHEARSAL_SCHEMA:
        return "elevator rehearsal evidence artifact schema mismatch"
    if payload.get("evidence_boundary") != ELEVATOR_ASSIST_REHEARSAL_PROOF_GATE:
        return "elevator rehearsal evidence artifact boundary mismatch"
    if payload.get("source") != "software_proof":
        return "elevator rehearsal evidence artifact source must be software_proof"
    if payload.get("delivery_success") is not False:
        return "elevator rehearsal evidence artifact must keep delivery_success=false"
    if payload.get("primary_actions_enabled") is not False:
        return "elevator rehearsal evidence artifact must keep primary_actions_enabled=false"
    if payload.get("same_evidence_ref_required") is not True:
        return "elevator rehearsal evidence artifact must keep same_evidence_ref_required=true"
    if not is_safe_elevator_evidence_ref(payload.get("evidence_ref")):
        return "elevator rehearsal evidence artifact evidence_ref must be a non-empty safe string"
    phase_evidence = payload.get("phase_evidence")
    if not isinstance(phase_evidence, dict):
        return "elevator rehearsal evidence artifact phase_evidence must be an object"
    for phase in ELEVATOR_ASSIST_REHEARSAL_REQUIRED_PHASES:
        if phase not in phase_evidence:
            return f"elevator rehearsal evidence artifact missing phase_evidence.{phase}"
    not_proven = payload.get("not_proven")
    normalized = {
        str(item).strip().lower().replace(" ", "_")
        for item in not_proven
    } if isinstance(not_proven, list) else set()
    for required in ELEVATOR_ASSIST_REHEARSAL_REQUIRED_NOT_PROVEN:
        if required not in normalized:
            return f"elevator rehearsal evidence artifact not_proven missing {required}"
    return ""
