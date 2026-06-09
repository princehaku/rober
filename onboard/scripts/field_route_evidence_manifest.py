#!/usr/bin/env python3
"""生成现场路线 evidence manifest。

该工具只读扫描 map、route、keyframe、rosbag 和 replay 材料，不启动导航、不发布运动命令。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.field_evidence_manifest.v1"
READY_PREFLIGHT_STATUS = "ready_for_live_route_capture_not_proven"
KEYFRAME_SUFFIXES = {".jpg", ".jpeg", ".png", ".json"}
ARTIFACT_CANDIDATES = {
    "map_yaml": ["map.yaml", "route_data/map.yaml"],
    "route_csv": ["route.csv", "route_data/route.csv"],
    "keyframes": ["keyframes", "route_data/keyframes"],
    "rosbag": ["rosbag", "route_bag", "route_data/rosbag", "route_data/route_bag"],
    "replay_jsonl": ["replay.jsonl", "fixed_route_replay.jsonl", "route_data/fixed_route_replay.jsonl"],
}


def utc_now() -> str:
    # 统一 UTC 让本地 fixture、上位机和后续云端 archive 能按同一时间轴对齐。
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat()


def mtime_utc(timestamp: float) -> str:
    # manifest 进入审计时不依赖本机时区，避免 CST/UTC 混用造成误判。
    return _dt.datetime.fromtimestamp(timestamp, tz=_dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    # 使用分块读取，现场 rosbag 可能较大，避免一次性读入内存。
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(path: Path) -> list[Path]:
    # 固定排序后再摘要，确保同一目录在不同机器上生成稳定 digest。
    if path.is_file():
        return [path]
    return sorted((item for item in path.rglob("*") if item.is_file()), key=lambda item: item.relative_to(path).as_posix())


def digest_directory(path: Path, allowed_suffixes: set[str] | None = None) -> tuple[str | None, int, int, str | None, list[dict[str, Any]]]:
    # 目录摘要包含相对路径、大小和子文件 sha256，既可复核又不会把原始图像写进 JSON。
    files = []
    digest = hashlib.sha256()
    latest_mtime = 0.0
    total_size = 0
    for file_path in iter_files(path):
        if allowed_suffixes and file_path.suffix.lower() not in allowed_suffixes:
            continue
        size = file_path.stat().st_size
        relative = file_path.relative_to(path).as_posix()
        file_hash = sha256_file(file_path)
        total_size += size
        latest_mtime = max(latest_mtime, file_path.stat().st_mtime)
        digest.update(relative.encode("utf-8"))
        digest.update(str(size).encode("ascii"))
        digest.update(file_hash.encode("ascii"))
        files.append({"path": relative, "size_bytes": size, "sha256": file_hash})
    if not files:
        return None, 0, 0, None, []
    return digest.hexdigest(), total_size, len(files), mtime_utc(latest_mtime), files


def artifact_path(root: Path, name: str) -> Path | None:
    # 支持 route_data 子目录是为了兼容 preflight 模板中的默认采集输出结构。
    for candidate in ARTIFACT_CANDIDATES[name]:
        path = root / candidate
        if path.exists():
            return path
    if name == "replay_jsonl":
        matches = sorted(root.rglob("*replay*.jsonl"))
        return matches[0] if matches else None
    if name == "rosbag":
        matches = sorted([item for item in root.rglob("*.db3") if item.is_file()])
        return matches[0] if matches else None
    return None


def missing_artifact(root: Path, name: str, reason: str) -> dict[str, Any]:
    # 缺失项保留期望路径，现场排查时不用回查代码就能知道该补哪个文件。
    return {
        "required": True,
        "present": False,
        "path": str(root / ARTIFACT_CANDIDATES[name][0]),
        "size_bytes": 0,
        "mtime_utc": None,
        "sha256": None,
        "reason": reason,
    }


def scan_file_artifact(root: Path, name: str) -> dict[str, Any]:
    # map、route、replay 都必须是非空文件；空模板不能进入现场证据链。
    path = artifact_path(root, name)
    if path is None:
        return missing_artifact(root, name, "missing")
    if not path.is_file():
        return missing_artifact(root, name, "not_file")
    size = path.stat().st_size
    if size <= 0:
        return missing_artifact(root, name, "empty")
    return {
        "required": True,
        "present": True,
        "path": str(path),
        "size_bytes": size,
        "mtime_utc": mtime_utc(path.stat().st_mtime),
        "sha256": sha256_file(path),
        "reason": None,
    }


def scan_directory_artifact(root: Path, name: str, allowed_suffixes: set[str] | None = None) -> dict[str, Any]:
    # keyframes 只认可图片或 JSON，rosbag 则认可目录或单个非空 bag 文件。
    path = artifact_path(root, name)
    if path is None:
        return missing_artifact(root, name, "missing")
    if path.is_file():
        size = path.stat().st_size
        if size <= 0:
            return missing_artifact(root, name, "empty")
        return {
            "required": True,
            "present": True,
            "path": str(path),
            "size_bytes": size,
            "mtime_utc": mtime_utc(path.stat().st_mtime),
            "sha256": sha256_file(path),
            "reason": None,
            "file_count": 1,
        }
    if not path.is_dir():
        return missing_artifact(root, name, "not_directory")
    digest, total_size, file_count, latest_mtime, files = digest_directory(path, allowed_suffixes)
    if not files:
        reason = "no_keyframe_file" if allowed_suffixes else "empty"
        return missing_artifact(root, name, reason)
    if total_size <= 0:
        return missing_artifact(root, name, "empty")
    return {
        "required": True,
        "present": True,
        "path": str(path),
        "size_bytes": total_size,
        "mtime_utc": latest_mtime,
        "sha256": digest,
        "reason": None,
        "file_count": file_count,
        "files": files[:20],
    }


def scan_local_artifacts(root: Path) -> dict[str, Any]:
    # artifact gate 与 ROS2 运行解耦，缺真实硬件时也能用 fixture 验证 fail-closed 语义。
    return {
        "map_yaml": scan_file_artifact(root, "map_yaml"),
        "route_csv": scan_file_artifact(root, "route_csv"),
        "keyframes": scan_directory_artifact(root, "keyframes", KEYFRAME_SUFFIXES),
        "rosbag": scan_directory_artifact(root, "rosbag"),
        "replay_jsonl": scan_file_artifact(root, "replay_jsonl"),
    }


def read_preflight(path: Path | None) -> dict[str, Any]:
    # preflight 缺失也必须 fail closed；不能因为 artifact 完整就跳过现场 ready 条件。
    if path is None:
        return {"status": "missing_preflight_json", "dry_run": None, "blocked_reason": "missing_preflight_json", "read_ok": False}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "invalid_preflight_json", "dry_run": None, "blocked_reason": str(exc), "read_ok": False}
    if not isinstance(loaded, dict):
        return {"status": "invalid_preflight_json", "dry_run": None, "blocked_reason": "root_not_object", "read_ok": False}
    return {
        "schema": loaded.get("schema"),
        "status": str(loaded.get("status") or "missing_status"),
        "dry_run": bool(loaded.get("dry_run", False)),
        "blocked_reason": loaded.get("blocked_reason"),
        "mode": loaded.get("mode"),
        "read_ok": True,
    }


def artifacts_pass(artifacts: dict[str, Any]) -> bool:
    # gate_pass 只表示必需材料完整，delivery_success 仍由真实任务验收单独证明。
    return all(item.get("present") and not item.get("reason") for item in artifacts.values())


def artifact_blocked_reason(artifacts: dict[str, Any]) -> str | None:
    # 缺失优先于空文件上报，方便现场先补目录/文件，再处理内容质量。
    reasons = [str(item.get("reason")) for item in artifacts.values() if item.get("reason")]
    if not reasons:
        return None
    if "missing" in reasons:
        return "missing_required_artifact"
    if "empty" in reasons or "no_keyframe_file" in reasons:
        return "empty_required_artifact"
    return reasons[0]


def artifact_status(artifacts: dict[str, Any], ssh_status: str | None) -> str:
    # artifact_status 只描述材料健康，不把 preflight 是否 ready 混进 gate 语义。
    if ssh_status:
        return "blocked"
    if artifacts_pass(artifacts):
        return "gated"
    if artifact_blocked_reason(artifacts) in {"missing_required_artifact", "empty_required_artifact"}:
        return "missing"
    return "blocked"


def artifact_health(artifacts: dict[str, Any], ssh_status: str | None) -> dict[str, Any]:
    # artifact_health 保留计数与摘要，便于 consumer detail 直接解释“为什么还不能当成功证据”。
    required_count = len(artifacts)
    present_artifacts = [name for name, item in artifacts.items() if item.get("present") and not item.get("reason")]
    missing_artifacts = [name for name, item in artifacts.items() if not item.get("present")]
    blocked_artifacts = [name for name, item in artifacts.items() if item.get("reason") and str(item.get("reason")) not in {"missing", "empty", "no_keyframe_file"}]
    empty_artifacts = [name for name, item in artifacts.items() if str(item.get("reason")) in {"empty", "no_keyframe_file"}]
    status = artifact_status(artifacts, ssh_status)
    if status == "gated":
        summary = "all_required_artifacts_present"
    elif status == "missing":
        summary = "missing_required_artifacts"
    elif ssh_status:
        summary = "blocked_ssh_scan_unavailable"
    elif empty_artifacts:
        summary = "empty_required_artifacts"
    else:
        summary = "blocked_artifact_scan_unavailable"
    return {
        "status": status,
        "required_count": required_count,
        "present_count": len(present_artifacts),
        "missing_count": len(missing_artifacts),
        "blocked_count": len(blocked_artifacts),
        "empty_count": len(empty_artifacts),
        "present_artifacts": present_artifacts,
        "missing_artifacts": missing_artifacts,
        "blocked_artifacts": blocked_artifacts,
        "summary": summary,
    }


def preflight_ready(preflight: dict[str, Any]) -> bool:
    # 只有非 dry-run 且 ready 的 preflight 才能解除 manifest 的 not_proven 标记。
    return (
        preflight.get("read_ok") is True
        and preflight.get("status") == READY_PREFLIGHT_STATUS
        and preflight.get("dry_run") is False
        and not preflight.get("blocked_reason")
    )


def build_status(artifact_gate_pass: bool, artifacts: dict[str, Any], preflight: dict[str, Any], ssh_status: str | None) -> tuple[str, str | None]:
    # SSH 不可达先报网络入口；本地模式再表达 artifact gate 和 preflight 边界。
    if ssh_status:
        # SSH 模式连只读扫描都不可用时，根因是远端入口，不再把派生的 artifact 缺失当主因。
        return ssh_status, ssh_status
    artifact_reason = artifact_blocked_reason(artifacts)
    if not artifact_gate_pass:
        if artifact_reason == "empty_required_artifact":
            return "blocked_artifacts_empty", artifact_reason
        return "blocked_artifacts_missing", artifact_reason
    if preflight_ready(preflight):
        return "field_evidence_manifest_ready_not_delivery_proof", None
    reason = str(preflight.get("blocked_reason") or preflight.get("status") or "blocked_preflight_not_ready")
    return "field_evidence_manifest_ready_not_delivery_proof", reason


def build_manifest(args: argparse.Namespace, artifacts: dict[str, Any], preflight: dict[str, Any], ssh_status: str | None = None) -> dict[str, Any]:
    artifact_gate_pass = artifacts_pass(artifacts)
    status, blocked_reason = build_status(artifact_gate_pass, artifacts, preflight, ssh_status)
    proven_material = artifact_gate_pass and preflight_ready(preflight) and ssh_status is None
    source = "ssh_remote" if args.mode == "ssh" else "local_fixture"
    health = artifact_health(artifacts, ssh_status)
    manifest_gate = {
        "schema": SCHEMA,
        "status": "gated" if artifact_gate_pass else "blocked_not_proven",
        "gate_pass": artifact_gate_pass,
        "blocked_reason": blocked_reason,
        "source": source,
    }
    return {
        "schema": SCHEMA,
        "run_id": args.run_id,
        "generated_at": utc_now(),
        "source": source,
        "mode": args.mode,
        "artifact_root": args.artifact_root,
        "preflight_json": args.preflight_json,
        "preflight_status": preflight.get("status"),
        "preflight": preflight,
        "gate_pass": artifact_gate_pass,
        "artifact_status": health["status"],
        "artifact_health": health,
        "manifest_gate": manifest_gate,
        "status": status,
        "blocked_reason": blocked_reason,
        "not_proven": not proven_material,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "artifacts": artifacts,
    }


def remote_scanner_code() -> str:
    # SSH 模式把同一份本地扫描逻辑上传为 python -c，只读远端文件系统，不复制或删除材料。
    script_path = Path(__file__)
    text = script_path.read_text(encoding="utf-8")
    marker = "\nif __name__ == \"__main__\":"
    prefix = text.split(marker, 1)[0]
    return (
        prefix
        + "\nimport json as _json, sys as _sys\n"
        + "_root = Path(_sys.argv[1]).expanduser()\n"
        + "print(_json.dumps(scan_local_artifacts(_root), ensure_ascii=False, sort_keys=True))\n"
    )


def build_ssh_command(target: str, port: int, artifact_root: str, timeout_s: int) -> list[str]:
    # 远端命令使用 python3 -c 和 argv 参数，避免把 artifact_root 作为 shell 片段执行。
    remote = "python3 -c " + shlex.quote(remote_scanner_code()) + " " + shlex.quote(artifact_root)
    return [
        "ssh",
        "-o",
        f"ConnectTimeout={timeout_s}",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-p",
        str(port),
        target,
        remote,
    ]


def run_ssh_scan(args: argparse.Namespace) -> tuple[dict[str, Any], str | None, dict[str, Any]]:
    # SSH manifest 只执行远端只读扫描；不可达时仍写 JSON，避免现场证据链断档。
    command = build_ssh_command(args.ssh_target, args.ssh_port, args.artifact_root, args.timeout_s)
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=args.timeout_s + 3)
    except subprocess.TimeoutExpired as exc:
        result = {"command": command, "returncode": None, "stdout": exc.stdout or "", "stderr": exc.stderr or "", "timed_out": True}
        return {}, "blocked_ssh_unreachable", result
    except OSError as exc:
        result = {"command": command, "returncode": None, "stdout": "", "stderr": str(exc), "timed_out": False}
        return {}, "blocked_ssh_unreachable", result
    result = {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout[:1600],
        "stderr": completed.stderr[:1600],
        "timed_out": False,
    }
    if completed.returncode != 0:
        return {}, "blocked_ssh_unreachable", result
    try:
        artifacts = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {}, "blocked_artifact_digest_failed", result
    return artifacts, None, result


def write_manifest(manifest: dict[str, Any], output: Path) -> None:
    # 父目录自动创建，便于 automation 和现场脚本统一写入 /tmp 或 run 目录。
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a trashbot field evidence manifest.")
    parser.add_argument("--mode", choices=["local", "ssh"], required=True)
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--preflight-json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--ssh-target", default="root@192.168.1.11")
    parser.add_argument("--ssh-port", type=int, default=37878)
    parser.add_argument("--timeout-s", type=int, default=8)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args(argv)
    if args.timeout_s < 1:
        parser.error("--timeout-s must be >= 1")
    # run_id 默认来自 UTC 时间，保证每份 manifest 能被后续 archive 稳定索引。
    args.run_id = args.run_id or "field_evidence_" + _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    preflight = read_preflight(Path(args.preflight_json).expanduser() if args.preflight_json else None)
    ssh_status = None
    ssh_result = None
    if args.mode == "ssh":
        artifacts, ssh_status, ssh_result = run_ssh_scan(args)
        if not artifacts:
            artifacts = {name: missing_artifact(Path(args.artifact_root), name, "ssh_scan_unavailable") for name in ARTIFACT_CANDIDATES}
    else:
        artifacts = scan_local_artifacts(Path(args.artifact_root).expanduser())
    manifest = build_manifest(args, artifacts, preflight, ssh_status)
    if ssh_result is not None:
        manifest["ssh_scan"] = ssh_result
    write_manifest(manifest, Path(args.output))
    print(json.dumps({"schema": SCHEMA, "status": manifest["status"], "gate_pass": manifest["gate_pass"], "output": args.output}, ensure_ascii=False, sort_keys=True))
    return 0 if manifest["gate_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
