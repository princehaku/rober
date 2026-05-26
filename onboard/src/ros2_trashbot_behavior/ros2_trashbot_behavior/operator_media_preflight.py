import argparse
import importlib.util
import json
import os
from pathlib import Path


# schema 必须稳定，cloud/PC 依赖它区分“板端 media preflight”与真实 RTC runtime。
O7_BOARD_MEDIA_PREFLIGHT_SCHEMA = "trashbot.o7_board_media_preflight.v1"
# evidence boundary 明确本文件只做软件前置检查，不能被解释成上车或 HIL 证据。
O7_BOARD_MEDIA_PREFLIGHT_BOUNDARY = "software_proof_o7_board_media_preflight_contract"


# import 检查只回答 Python 依赖是否可见；find_spec 不会打开摄像头、声卡或网络连接。
MEDIA_IMPORT_CHECKS = {
    "rtc": ["aiortc"],
    "video": ["cv2"],
    "audio": ["sounddevice", "pyaudio"],
    "asr": ["speech_recognition"],
    "tts": ["pyttsx3"],
}


# 环境变量检查只看“是否显式配置”，不读取密钥值，也不把 URL/凭证写进摘要。
MEDIA_ENV_CHECKS = {
    "rtc": ["TRASHBOT_RTC_SIGNALING_URL", "TRASHBOT_RTC_STUN_URLS", "TRASHBOT_RTC_TURN_URLS"],
    "video": ["TRASHBOT_MEDIA_CAMERA_PATH"],
    "audio": ["TRASHBOT_MEDIA_AUDIO_INPUT", "TRASHBOT_MEDIA_AUDIO_OUTPUT"],
    "asr": ["TRASHBOT_ASR_PROVIDER", "TRASHBOT_ASR_MODEL"],
    "tts": ["TRASHBOT_TTS_PROVIDER", "TRASHBOT_TTS_VOICE"],
}


# 这些 marker 代表控制面、串口或敏感凭证；一旦出现必须 redacted + blocked。
UNSAFE_TEXT_MARKERS = (
    "/cmd_vel",
    "/dev/ttyusb",
    "authorization",
    "bearer",
    "token",
    "secret",
    "password",
)


# 后续真实上车 smoke 至少要补齐这些证据；preflight 缺口直接转发给 realtime status。
DEFAULT_NEXT_REQUIRED_EVIDENCE = [
    "orange_pi_camera_device_enumeration",
    "orange_pi_audio_input_output_enumeration",
    "rtc_signaling_stun_turn_trace",
    "camera_frame_evidence_with_timestamp",
    "asr_partial_and_final_transcript_trace",
    "tts_audio_playback_trace",
    "cpu_encoding_budget_trace",
    "on_robot_media_smoke_with_no_chassis_motion",
]


def _safe_text(value, default=""):
    # 所有外部输入都先转成短文本，避免把凭证、ROS topic 或串口路径写进可转发摘要。
    text = str(value or "").strip()
    lower = text.lower()
    if not text:
        return default
    if any(marker in lower for marker in UNSAFE_TEXT_MARKERS):
        return "redacted_unsafe_input"
    return text[:160]


def _safe_list(values):
    # JSON contract 需要稳定 list；字符串不能被拆成字符，也不能携带危险内部路径。
    if not isinstance(values, (list, tuple)):
        return []
    safe_values = [_safe_text(item) for item in values]
    return [item for item in safe_values if item]


def _import_available(module_name):
    # 使用 find_spec 而不是 import，避免 cv2/音频库初始化真实设备或加载重型 native 资源。
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def _path_summary(label, path_value, *, allow_device_probe=False):
    # 默认只检查调用者显式传入的路径是否存在，不枚举 /dev，也不打开摄像头/声卡。
    safe_label = _safe_text(label, default="path")
    safe_path = _safe_text(path_value)
    if not safe_path:
        return {"name": safe_label, "configured": False, "state": "not_configured"}
    if safe_path == "redacted_unsafe_input":
        return {
            "name": safe_label,
            "configured": True,
            # 只保留 redacted 标记，让消费者知道有输入但不能看到原始危险值。
            "path": safe_path,
            "state": "blocked",
            "reason": "unsafe_input_redacted",
        }
    exists = Path(safe_path).exists()
    summary = {
        "name": safe_label,
        "configured": True,
        "path": safe_path,
        "exists": exists,
        "state": "not_proven" if exists else "blocked",
    }
    if not exists:
        summary["reason"] = "configured_path_missing"
    if allow_device_probe:
        # 显式 probe 也只做 stat/access 级别确认；真实采集必须留给上车 smoke。
        summary["device_probe_attempted"] = True
        summary["device_probe_result"] = "shallow_path_check_only"
        summary["readable"] = os.access(safe_path, os.R_OK) if exists else False
    else:
        summary["device_probe_attempted"] = False
    return summary


def _capability_summary(name, imports, env_keys):
    # 每个媒体能力只报告前置条件，不把 import/env 的存在升级成 runtime ready。
    import_results = {module: _import_available(module) for module in imports}
    env_results = {key: bool(os.environ.get(key, "").strip()) for key in env_keys}
    blocked_reasons = []
    if not any(import_results.values()):
        blocked_reasons.append("python_import_missing")
    if env_keys and not any(env_results.values()):
        blocked_reasons.append("configuration_missing")
    return {
        "state": "blocked" if blocked_reasons else "not_proven",
        "import_available": import_results,
        "configured_env": env_results,
        "blocked_reasons": blocked_reasons,
        "not_proven": [
            f"real_{name}_runtime",
            f"orange_pi_{name}_device_or_service",
        ],
    }


def build_o7_board_media_preflight(
    *,
    camera_path="",
    audio_input_path="",
    audio_output_path="",
    allow_device_probe=False,
    extra_paths=None,
):
    """构建板端 media preflight 摘要；默认不打开 RTC、摄像头、麦克风或喇叭。"""
    # 每次调用都重新生成 import/env 状态，便于 Orange Pi 上车前后对比依赖缺口。
    capability_checks = {
        name: _capability_summary(name, imports, MEDIA_ENV_CHECKS.get(name, []))
        for name, imports in MEDIA_IMPORT_CHECKS.items()
    }
    # 路径必须由调用方显式传入；默认不枚举 /dev，避免误碰串口或媒体设备。
    path_checks = [
        _path_summary("camera_path", camera_path, allow_device_probe=allow_device_probe),
        _path_summary("audio_input_path", audio_input_path, allow_device_probe=allow_device_probe),
        _path_summary("audio_output_path", audio_output_path, allow_device_probe=allow_device_probe),
    ]
    # extra_paths 用于后续 smoke 脚本追加证据路径，同样走统一安全过滤。
    for index, path_value in enumerate(_safe_list(extra_paths), start=1):
        path_checks.append(
            _path_summary(f"extra_path_{index}", path_value, allow_device_probe=allow_device_probe)
        )
    # blocked 列表只聚合前置条件缺口，不包含任何“可运行/已成功”的暗示。
    blocked_items = [
        name for name, check in capability_checks.items() if check["state"] == "blocked"
    ]
    blocked_items.extend(
        check["name"] for check in path_checks if check.get("state") == "blocked"
    )
    next_required = list(DEFAULT_NEXT_REQUIRED_EVIDENCE)
    if blocked_items:
        next_required.insert(0, "resolve_blocked_preflight_items")
    return {
        # schema 字段是消费者的最小解析入口，必须排在固定顶层对象里。
        "schema": O7_BOARD_MEDIA_PREFLIGHT_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": O7_BOARD_MEDIA_PREFLIGHT_BOUNDARY,
        "source": "operator_media_preflight",
        # overall_state 只能 blocked/not_proven；依赖或路径存在也不升级成 ready。
        "overall_state": "blocked" if blocked_items else "not_proven",
        # 控制字段固定 false，防止媒体 preflight 被误用为手控或导航准入。
        "safe_to_control": False,
        "primary_actions_enabled": False,
        "device_probe_allowed": bool(allow_device_probe),
        "device_probe_attempted": bool(allow_device_probe),
        "capabilities": capability_checks,
        "path_checks": path_checks,
        "blocked": blocked_items,
        # not_proven 明确列出真实媒体运行时缺口，供 PC/cloud 直接展示。
        "not_proven": [
            "real_rtc_session",
            "real_camera_video_source",
            "real_audio_capture",
            "real_audio_playback",
            "real_asr_stream",
            "real_tts_playback",
            "orange_pi_media_runtime",
            "on_robot_media_smoke",
        ],
        "next_required_evidence": next_required,
        "software_proof_only": True,
    }


def _parser():
    # CLI 参数保持显式输入模型：调用方不给路径，就不会触碰任何设备路径。
    parser = argparse.ArgumentParser(description="Emit O7 board media preflight JSON.")
    parser.add_argument("--camera-path", default=os.environ.get("TRASHBOT_MEDIA_CAMERA_PATH", ""))
    parser.add_argument("--audio-input-path", default=os.environ.get("TRASHBOT_MEDIA_AUDIO_INPUT", ""))
    parser.add_argument("--audio-output-path", default=os.environ.get("TRASHBOT_MEDIA_AUDIO_OUTPUT", ""))
    parser.add_argument("--path", action="append", default=[], help="Additional explicit path to check.")
    parser.add_argument(
        "--allow-device-probe",
        action="store_true",
        help="Allow shallow stat/access checks; still never opens media devices.",
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    # CLI 输出单行 JSON，便于 shell smoke、cloud relay 和 PC tools 原样采集。
    summary = build_o7_board_media_preflight(
        camera_path=args.camera_path,
        audio_input_path=args.audio_input_path,
        audio_output_path=args.audio_output_path,
        allow_device_probe=args.allow_device_probe,
        extra_paths=args.path,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
