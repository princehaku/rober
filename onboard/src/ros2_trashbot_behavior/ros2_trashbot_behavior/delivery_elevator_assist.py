import re


ELEVATOR_ASSIST_PROMPT = "你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,"
ELEVATOR_ASSIST_PROOF_GATE = "software_proof_docker_elevator_assist_default_mainline_gate"
ELEVATOR_ASSIST_REHEARSAL_SCHEMA = "trashbot.elevator_assist_rehearsal_evidence.v1"
ELEVATOR_ASSIST_REHEARSAL_PROOF_GATE = "software_proof_docker_elevator_evidence_driven_mainline_gate"
ELEVATOR_ASSIST_OPENCV_BASELINE_SCHEMA = "trashbot.elevator_opencv_baseline.v1"
ELEVATOR_ASSIST_OPENCV_BASELINE_PROOF_GATE = "software_guard_elevator_opencv_baseline_state_chain_gate"
ELEVATOR_ASSIST_OPENCV_BASELINE_MIN_CONFIDENCE = 0.58
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


def _normalized_text(value):
    return str(value or "").strip()


def _normalized_lower(value):
    return _normalized_text(value).lower()


def _safe_reasons(value):
    if not isinstance(value, list):
        return []
    # uncertain_reasons 会进入 task_record 和手机摘要，统一转短字符串，避免对象泄露 raw artifact。
    return [_normalized_text(item) for item in value if _normalized_text(item)]


def _safe_confidence(value):
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, confidence))


def validate_opencv_baseline_artifact(payload):
    # OpenCV baseline 是 perception software guard，不是实景完成证据；校验失败必须 fail closed。
    if not isinstance(payload, dict):
        return "elevator opencv baseline artifact must be a JSON object"
    if payload.get("schema") != ELEVATOR_ASSIST_OPENCV_BASELINE_SCHEMA:
        return "elevator opencv baseline artifact schema mismatch"
    if payload.get("proof_status") != "not_proven":
        return "elevator opencv baseline artifact proof_status must be not_proven"
    required_fields = (
        "door_state",
        "inside_outside",
        "target_floor_candidate",
        "safe_to_exit",
        "confidence",
        "uncertain_reasons",
        "not_proven",
    )
    for field in required_fields:
        if field not in payload:
            return f"elevator opencv baseline artifact missing {field}"
    if _normalized_lower(payload.get("door_state")) not in {"open", "closed", "uncertain"}:
        return "elevator opencv baseline artifact door_state unsupported"
    if _normalized_lower(payload.get("inside_outside")) not in {"inside", "outside", "uncertain"}:
        return "elevator opencv baseline artifact inside_outside unsupported"
    if _normalized_lower(payload.get("safe_to_exit")) not in {"safe", "unsafe", "uncertain"}:
        return "elevator opencv baseline artifact safe_to_exit unsupported"
    if not isinstance(payload.get("uncertain_reasons"), list):
        return "elevator opencv baseline artifact uncertain_reasons must be a list"
    normalized_not_proven = {
        _normalized_lower(item).replace(" ", "_")
        for item in payload.get("not_proven", [])
    } if isinstance(payload.get("not_proven"), list) else set()
    for required in (
        "real_camera_elevator_recognition",
        "real_floor_ocr",
        "real_safe_exit",
        "real_cross_floor_delivery",
    ):
        if required not in normalized_not_proven:
            return f"elevator opencv baseline artifact not_proven missing {required}"
    return ""


def opencv_baseline_to_phase_evidence(payload, *, target_floor):
    # 单帧 baseline 只提供当前视觉语义；这里映射成行为层阶段证据，而不是伪造时序闭环。
    door_state = _normalized_lower(payload.get("door_state"))
    inside_outside = _normalized_lower(payload.get("inside_outside"))
    safe_to_exit = _normalized_lower(payload.get("safe_to_exit"))
    candidate = _normalized_text(payload.get("target_floor_candidate"))
    target = _normalized_text(target_floor)
    confidence = _safe_confidence(payload.get("confidence"))
    reasons = _safe_reasons(payload.get("uncertain_reasons"))
    target_confirmed = bool(candidate and target and candidate == target)

    phase_evidence = {
        "waiting_elevator_open": {
            "status": "door_open" if door_state == "open" else "door_closed_or_unknown",
            "door_state": door_state,
            "confidence": confidence,
            "source": "opencv_baseline",
        },
        "entering_elevator": {
            "status": "inside_elevator" if inside_outside == "inside" else "inside_outside_unconfirmed",
            "inside_outside": inside_outside,
            "confidence": confidence,
            "source": "opencv_baseline",
        },
        "requesting_floor_help": {
            "status": "prompt_ready" if inside_outside == "inside" else "blocked_until_inside_confirmed",
            "speaker_prompt_required": inside_outside == "inside",
            "source": "opencv_baseline",
        },
        "waiting_target_floor": {
            "status": "target_floor_confirmed" if target_confirmed else "target_floor_unconfirmed",
            "target_floor": target,
            "target_floor_candidate": candidate,
            "confidence": confidence,
            "source": "opencv_baseline",
        },
        "exiting_elevator": {
            "status": "safe_to_exit" if safe_to_exit == "safe" else "unsafe_to_exit",
            "safe_to_exit": safe_to_exit,
            "confidence": confidence,
            "source": "opencv_baseline",
        },
    }

    blockers = []
    if door_state != "open":
        blockers.append("door_not_open")
    if inside_outside != "inside":
        blockers.append("inside_outside_unconfirmed")
    if not target_confirmed:
        blockers.append("target_floor_unconfirmed")
    if safe_to_exit != "safe":
        blockers.append("unsafe_to_exit")
    if confidence < ELEVATOR_ASSIST_OPENCV_BASELINE_MIN_CONFIDENCE:
        blockers.append("low_confidence")
    if reasons:
        blockers.extend(f"uncertain:{reason}" for reason in reasons)

    manual_takeover_reason = blockers[0] if blockers else ""
    phone_summary = (
        f"OpenCV 电梯识别：门={door_state or 'unknown'}，位置={inside_outside or 'unknown'}，"
        f"目标楼层候选={candidate or '未确认'}，驶出={safe_to_exit or 'unknown'}，"
        f"置信度={confidence:.2f}。"
    )
    if blockers:
        phone_summary += " 需要人工接管；不证明真实电梯、真实 Nav2、HIL 或送达成功。"
    else:
        phone_summary += " 已满足软件护栏；仍不证明真实电梯、真实 Nav2、HIL 或送达成功。"

    snapshot = {
        "schema": ELEVATOR_ASSIST_OPENCV_BASELINE_SCHEMA,
        "sample_id": _normalized_text(payload.get("sample_id")),
        "image_ref": _normalized_text(payload.get("image_ref")),
        "door_state": door_state,
        "inside_outside": inside_outside,
        "target_floor": target,
        "target_floor_candidate": candidate,
        "safe_to_exit": safe_to_exit,
        "confidence": confidence,
        "uncertain_reasons": reasons,
        "manual_takeover_reason": manual_takeover_reason,
        "not_proven": list(payload.get("not_proven", [])) if isinstance(payload.get("not_proven"), list) else [],
    }
    return {
        "phase_evidence": phase_evidence,
        "snapshot": snapshot,
        "manual_takeover_reason": manual_takeover_reason,
        "phone_safe_summary": phone_summary,
        "success": not blockers,
        "blockers": blockers,
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
