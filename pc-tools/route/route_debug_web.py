#!/usr/bin/env python3
"""PC 端 fixed-route debug console。

该工具只读取本地 JSON 文件并提供只读 HTML/API，刻意不 import ROS2 包、不触发 Nav2、
不访问硬件或网络外部服务。它服务于 PC 工作站上的路线复盘和下一轮调试准备。
"""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


# schema 与 boundary 是 diagnostics/mobile 后续消费的稳定锚点，不能从输入文件推断。
CONSOLE_SCHEMA = "trashbot.pc_route_debug_console.v1"
CONSOLE_SCHEMA_VERSION = 1
CONSOLE_BOUNDARY = "software_proof_docker_pc_route_debug_console_gate"

# not_proven 必须显式包含真实运行、HIL 和 delivery success，防止软件 pass 被误读。
NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "real_route_capture",
    "keyframe_scene_validation",
    "wave_rover_motion",
    "real_serial_or_uart_feedback",
    "real_hil_pass",
    "dropoff_completion",
    "cancel_completion",
    "delivery_success",
)

# 输出面不需要凭证、硬件串口、ROS topic 或完整本机路径；统一先脱敏再展示。
SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "Authorization: [REDACTED]"),
    (re.compile(r"(?i)\bOSS_ACCESS_KEY[A-Z_]*\b\s*[:=]\s*[^,\s]+"), "OSS_ACCESS_KEY=[REDACTED]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/cmd_vel\b"), "[REDACTED_ROS_TOPIC]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)\b(baud|baudrate|baud_rate)\b\s*[:=]\s*\d+"), r"\1=[REDACTED_RATE]"),
    (re.compile(r"(?i)WAVE\s+ROVER"), "[REDACTED_PLATFORM]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
)


HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PC Route Debug Console</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f7f9;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #5b6778;
      --line: #d7dee7;
      --ok: #18794e;
      --warn: #8a5a00;
      --bad: #b42318;
      --soft: #eef2f6;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--text); }}
    main {{ width: min(1120px, calc(100% - 32px)); margin: 0 auto; padding: 24px 0 40px; }}
    header {{ display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: space-between; margin-bottom: 16px; }}
    h1 {{ margin: 0; font-size: 24px; line-height: 1.2; letter-spacing: 0; }}
    h2 {{ margin: 0 0 10px; font-size: 15px; letter-spacing: 0; }}
    .badge {{ border-radius: 999px; padding: 7px 12px; font-weight: 700; background: var(--soft); overflow-wrap: anywhere; }}
    .badge.ready {{ color: var(--ok); }}
    .badge.blocked {{ color: var(--bad); }}
    .badge.warning {{ color: var(--warn); }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    section {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; min-width: 0; }}
    section.full {{ grid-column: 1 / -1; }}
    dl {{ display: grid; grid-template-columns: minmax(130px, 0.34fr) minmax(0, 1fr); gap: 8px 12px; margin: 0; }}
    dt {{ color: var(--muted); font-size: 13px; }}
    dd {{ margin: 0; min-width: 0; overflow-wrap: anywhere; white-space: pre-wrap; }}
    ul {{ margin: 0; padding-left: 18px; }}
    li {{ margin: 3px 0; overflow-wrap: anywhere; }}
    pre {{ margin: 0; max-height: 360px; overflow: auto; padding: 12px; border-radius: 6px; background: #101820; color: #e6edf3; font-size: 12px; line-height: 1.45; white-space: pre-wrap; overflow-wrap: anywhere; }}
    @media (max-width: 720px) {{
      main {{ width: min(100% - 20px, 1120px); padding-top: 16px; }}
      .grid {{ grid-template-columns: 1fr; }}
      dl {{ grid-template-columns: 1fr; gap: 3px 0; }}
      h1 {{ font-size: 21px; }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>PC Route Debug Console</h1>
    <span class="badge {tone}">{overall_status}</span>
  </header>
  <div class="grid">
    <section class="full">
      <h2>Console Boundary</h2>
      <dl>
        <dt>schema</dt><dd>{schema}</dd>
        <dt>evidence_boundary</dt><dd>{boundary}</dd>
        <dt>delivery_success</dt><dd>{delivery_success}</dd>
        <dt>generated_at</dt><dd>{generated_at}</dd>
      </dl>
    </section>
    <section>
      <h2>Route Progress</h2>
      {route_progress}
    </section>
    <section>
      <h2>Current Target</h2>
      {current_target}
    </section>
    <section>
      <h2>Keyframe Preflight</h2>
      {keyframe_preflight}
    </section>
    <section>
      <h2>Failure</h2>
      {failure}
    </section>
    <section>
      <h2>Recent Task</h2>
      {recent_task}
    </section>
    <section>
      <h2>Not Proven</h2>
      {not_proven}
    </section>
    <section class="full">
      <h2>JSON API</h2>
      <pre>{raw_json}</pre>
    </section>
  </div>
</main>
</body>
</html>"""


def _utc_now() -> str:
    # UTC 让不同 PC 生成的材料可按字符串排序，不受本地时区影响。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 任意输入 JSON 都可能来自现场材料；展示前统一转文本并脱敏。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(path_or_ref: Any) -> str:
    # PC console 只需要说明引用来源，不应把用户机器完整目录暴露到 HTML/API。
    text = _safe_text(path_or_ref).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 嵌套摘要也递归过滤，避免 route_progress 或 task_record 内夹带敏感内容。
    if isinstance(value, dict):
        return {str(_safe_text(key)): _safe_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺文件和坏 JSON 都要生成 blocked payload，保证 operator 总能看到失败原因。
    if not path:
        return {}, "not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, f"{label}_missing"
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}, f"{label}_read_error"
    if not isinstance(payload, dict):
        return {}, f"{label}_not_object"
    return payload, ""


def _first_text(*values: Any, default: str = "") -> str:
    # onboard status 在不同阶段有 target/current_target 等别名；只取第一个非空字段。
    for value in values:
        text = _safe_text(value).strip()
        if text:
            return text
    return default


def _route_progress(status: dict[str, Any]) -> dict[str, Any]:
    # route_progress 是 O2/O3 复盘主键；缺失时用顶层字段保守补一个只读摘要。
    progress = status.get("route_progress") if isinstance(status.get("route_progress"), dict) else {}
    target = progress.get("target") if isinstance(progress.get("target"), dict) else status.get("target")
    if not isinstance(target, dict):
        target = status.get("current_target") if isinstance(status.get("current_target"), dict) else {}
    return {
        "route_id": _first_text(progress.get("route_id"), status.get("route_id"), default="unknown_route"),
        "route_file_basename": _first_text(
            progress.get("route_file_basename"),
            status.get("route_file_basename"),
            Path(_safe_text(status.get("route_file"))).name,
            default="",
        ),
        "checkpoint_id": _first_text(progress.get("checkpoint_id"), status.get("checkpoint_id"), default=""),
        "checkpoint": progress.get("checkpoint", status.get("checkpoint", status.get("current_index"))),
        "current_index": progress.get("current_index", status.get("current_index", status.get("checkpoint"))),
        "total_checkpoints": progress.get("total_checkpoints", status.get("total")),
        "target": _safe_value(target),
        "route_contract_version": _first_text(
            progress.get("route_contract_version"),
            status.get("route_contract_version"),
            default="fixed_route.v1",
        ),
        "source": _first_text(progress.get("source"), status.get("source"), default="fixed_route_status_json"),
        "failure_code": _first_text(progress.get("failure_code"), status.get("failure_code"), default=""),
        "evidence_ref": _safe_ref(_first_text(progress.get("evidence_ref"), status.get("evidence_ref"), default="")),
    }


def _keyframe_preflight(status: dict[str, Any]) -> dict[str, Any]:
    # keyframe_preflight 是关键帧门控复盘入口；只复制摘要，不扩散 keyframe 绝对路径。
    preflight = status.get("keyframe_preflight") if isinstance(status.get("keyframe_preflight"), dict) else {}
    return {
        "enabled": bool(preflight.get("enabled", status.get("enable_visual_gate", False))),
        "route_visual_ready": bool(preflight.get("route_visual_ready", False)),
        "total_checkpoints": preflight.get("total_checkpoints", status.get("total")),
        "loaded_keyframes": len(preflight.get("loaded_keyframes", []))
        if isinstance(preflight.get("loaded_keyframes"), list)
        else preflight.get("loaded_keyframes", 0),
        "missing_keyframes": _safe_value(preflight.get("missing_keyframes", [])),
        "invalid_keyframes": _safe_value(preflight.get("invalid_keyframes", [])),
        "visual_gate_status": _first_text(status.get("visual_gate_status"), default="not_checked"),
        "visual_gate_detail": _first_text(status.get("visual_gate_detail"), status.get("failure_reason"), default=""),
    }


def _matches_evidence_ref(payload: dict[str, Any], evidence_ref: str) -> bool:
    # task_record_dir 自动选择必须跟同一 evidence_ref 对齐，避免拿错历史任务。
    if not evidence_ref:
        return False
    if _safe_text(payload.get("evidence_ref")).strip() == evidence_ref:
        return True
    if _safe_text(payload.get("result_path")).strip() == evidence_ref:
        return True
    route_progress = payload.get("route_progress") if isinstance(payload.get("route_progress"), dict) else {}
    if _safe_text(route_progress.get("evidence_ref")).strip() == evidence_ref:
        return True
    nav_results = payload.get("nav_results") if isinstance(payload.get("nav_results"), list) else []
    for nav_result in reversed(nav_results):
        if not isinstance(nav_result, dict):
            continue
        evidence = nav_result.get("evidence") if isinstance(nav_result.get("evidence"), dict) else {}
        progress = evidence.get("route_progress") if isinstance(evidence.get("route_progress"), dict) else {}
        if _safe_text(progress.get("evidence_ref")).strip() == evidence_ref:
            return True
    return False


def _select_task_record(path: str, task_record_dir: str, evidence_ref: str) -> tuple[dict[str, Any], str, str]:
    # 显式 task-record 优先；目录查找只作为同 run 材料的便利入口。
    if path:
        payload, issue = _load_json(path, "task_record")
        return payload, _safe_ref(path) if payload else "", issue
    if not task_record_dir:
        return {}, "", "not_provided"
    root = Path(task_record_dir).expanduser()
    if not root.exists() or not root.is_dir():
        return {}, "", "task_record_dir_missing"
    for candidate in sorted(root.glob("*.json")):
        payload, issue = _load_json(str(candidate), "task_record")
        if issue or not payload:
            continue
        if _matches_evidence_ref(payload, evidence_ref):
            return payload, _safe_ref(str(candidate)), ""
    return {}, "", "task_record_dir_no_matching_evidence_ref"


def _task_summary(task_record: dict[str, Any], resolved_ref: str, issue: str) -> dict[str, Any]:
    # task_record 只做最近任务摘要，不在 PC console 中声明任务成功。
    nav_results = task_record.get("nav_results") if isinstance(task_record.get("nav_results"), list) else []
    last_nav = nav_results[-1] if nav_results and isinstance(nav_results[-1], dict) else {}
    evidence = last_nav.get("evidence") if isinstance(last_nav.get("evidence"), dict) else {}
    return {
        "provided": bool(task_record),
        "lookup_status": "found" if task_record else issue,
        "resolved_task_record": resolved_ref,
        "task_id": _safe_text(task_record.get("task_id", "")),
        "final_status": _first_text(task_record.get("final_status"), task_record.get("status"), default=""),
        "failure_code": _first_text(task_record.get("failure_code"), last_nav.get("failure_code"), default=""),
        "evidence_ref": _safe_ref(task_record.get("evidence_ref", "")),
        "has_route_progress": isinstance(task_record.get("route_progress"), dict) and bool(task_record.get("route_progress")),
        "has_nav_route_progress": isinstance(evidence.get("route_progress"), dict) and bool(evidence.get("route_progress")),
    }


def build_console_summary(status_json: str, task_record: str = "", task_record_dir: str = "") -> dict[str, Any]:
    """读取 fixed-route status 与可选 task_record，生成 PC console 只读摘要。"""

    status, status_issue = _load_json(status_json, "status_json")
    progress = _route_progress(status) if status else {}
    evidence_ref_raw = _safe_text((status.get("route_progress") or {}).get("evidence_ref") if status else "").strip()
    if not evidence_ref_raw and status:
        evidence_ref_raw = _safe_text(status.get("evidence_ref", "")).strip()
    task_payload, task_ref, task_issue = _select_task_record(task_record, task_record_dir, evidence_ref_raw)
    blocked = bool(status_issue and status_issue != "not_provided")
    overall_status = "blocked_status_json_unavailable" if blocked else "available_software_proof"
    if not status_json:
        overall_status = "blocked_status_json_required"
    return {
        "schema": CONSOLE_SCHEMA,
        "schema_version": CONSOLE_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "status": overall_status,
        "evidence_boundary": CONSOLE_BOUNDARY,
        "inputs": {
            "status_json_ref": _safe_ref(status_json),
            "status_json_load_status": "loaded" if status and not status_issue else status_issue,
            "task_record_ref": _safe_ref(task_record) if task_record else "",
            "task_record_dir_ref": _safe_ref(task_record_dir) if task_record_dir else "",
        },
        "route_progress": progress,
        "keyframe_preflight": _keyframe_preflight(status) if status else {},
        "current_position": _safe_value(status.get("current_position", status.get("pose", {}))) if status else {},
        "current_checkpoint": progress.get("checkpoint") if progress else None,
        "target": _safe_value(progress.get("target", {})) if progress else {},
        "match_status": _first_text(
            status.get("visual_gate_status") if status else "",
            status.get("state") if status else "",
            default="blocked" if blocked else "not_checked",
        ),
        "failure": {
            "failure_code": _first_text(status.get("failure_code") if status else "", default=""),
            "failure_reason": _first_text(status.get("failure_reason") if status else "", default=status_issue),
            "last_error": _first_text(status.get("last_error") if status else "", default=""),
            "last_transition": _first_text(status.get("last_transition") if status else "", default=""),
            "last_nav_result": _first_text(status.get("last_nav_result") if status else "", default=""),
        },
        "recent_task": _task_summary(task_payload, task_ref, task_issue),
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "console_controls": "read_only",
    }


def _html_table(payload: dict[str, Any]) -> str:
    # HTML 渲染只接受已脱敏 payload；这里仍 escape，防止坏 JSON 注入页面。
    rows = []
    for key, value in payload.items():
        text = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
        rows.append(f"<dt>{html.escape(str(key))}</dt><dd>{html.escape(text)}</dd>")
    return "<dl>" + "".join(rows) + "</dl>"


def render_html(summary: dict[str, Any]) -> str:
    # 页面和 JSON API 使用同一份 summary，避免 HTML 与 API 证据口径漂移。
    tone = "blocked" if str(summary.get("status", "")).startswith("blocked") else "ready"
    raw_json = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
    return HTML_TEMPLATE.format(
        tone=tone,
        overall_status=html.escape(_safe_text(summary.get("status"))),
        schema=html.escape(_safe_text(summary.get("schema"))),
        boundary=html.escape(_safe_text(summary.get("evidence_boundary"))),
        delivery_success=html.escape(str(summary.get("delivery_success"))),
        generated_at=html.escape(_safe_text(summary.get("generated_at"))),
        route_progress=_html_table(summary.get("route_progress", {})),
        current_target=_html_table(summary.get("target", {})),
        keyframe_preflight=_html_table(summary.get("keyframe_preflight", {})),
        failure=_html_table(summary.get("failure", {})),
        recent_task=_html_table(summary.get("recent_task", {})),
        not_proven="<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in summary.get("not_proven", [])) + "</ul>",
        raw_json=html.escape(raw_json),
    )


def make_handler(status_json: str, task_record: str = "", task_record_dir: str = ""):
    class Handler(BaseHTTPRequestHandler):
        # server 只暴露本地只读页面和 JSON，不支持任何 POST/控制入口。
        def _send(self, content_type: str, body: bytes) -> None:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 - http.server 使用固定方法名。
            path = urlparse(self.path).path
            summary = build_console_summary(status_json, task_record, task_record_dir)
            if path in ("/", "/index.html"):
                self._send("text/html; charset=utf-8", render_html(summary).encode("utf-8"))
                return
            if path in ("/api/status", "/api/summary"):
                body = json.dumps(summary, ensure_ascii=False, sort_keys=True).encode("utf-8")
                self._send("application/json; charset=utf-8", body)
                return
            self.send_response(404)
            self.end_headers()

    return Handler


def _write_output(output: str, summary: dict[str, Any]) -> None:
    # output 可用于把 PC console 摘要交给 diagnostics worker，仍然只写脱敏 JSON。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve or print a read-only PC fixed-route debug console")
    parser.add_argument("--status-json", required=True, help="fixed_route debug status JSON file")
    parser.add_argument("--task-record", default="", help="optional task/task_record JSON file")
    parser.add_argument("--task-record-dir", default="", help="optional directory to locate task_record by evidence_ref")
    parser.add_argument("--output", default="", help="optional path to write the console summary JSON")
    parser.add_argument("--host", default="127.0.0.1", help="bind host for the local read-only console")
    parser.add_argument("--port", type=int, default=8766, help="bind port for the local read-only console")
    parser.add_argument("--once-json", action="store_true", help="print one JSON summary and exit")
    args = parser.parse_args()

    summary = build_console_summary(args.status_json, args.task_record, args.task_record_dir)
    _write_output(args.output, summary)
    if args.once_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    server = HTTPServer((args.host, args.port), make_handler(args.status_json, args.task_record, args.task_record_dir))
    print(f"PC route debug console: http://{args.host}:{args.port} boundary={CONSOLE_BOUNDARY}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
