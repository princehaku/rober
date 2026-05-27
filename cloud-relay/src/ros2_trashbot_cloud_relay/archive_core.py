"""O6 云端归档、标注和推理的本地 software-proof 核心。

该模块只实现 cloud-relay 本地/Docker 可验证的最小 API 数据层。生产期应替换为
真实 DB/queue，但字段、schema 和 fail-closed 证据边界先在这里固定下来。
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import threading
from urllib.parse import parse_qs, unquote


ARCHIVE_SCHEMA = "trashbot.archive.v1"
ANNOTATION_SCHEMA = "trashbot.annotation.v1"
INFERENCE_SCHEMA = "trashbot.inference.v1"
ARCHIVE_STORE_SCHEMA = "trashbot.o6.archive_store.v1"
ARCHIVE_EVIDENCE_BOUNDARY = "software_proof_o6_cloud_archive_core"
PRODUCTION_DB_GAP = "not_proven_production_db"
# 默认落系统临时目录，避免本地 smoke 在仓库根目录遗留 runtime state。
DEFAULT_ARCHIVE_STATE = str(Path(tempfile.gettempdir()) / "o6_cloud_archive_state.json")


def utc_now_iso() -> str:
    """用 UTC ISO 时间统一写入，避免本地时区影响任务/事件排序。"""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_text(value: object, default: str = "") -> str:
    """把外部输入收敛成短字符串，避免把复杂对象或路径原样进入索引字段。"""

    text = str(value or default).strip()
    return text[:160]


def normalize_evidence_ref(value: object) -> dict:
    """只保存 OSS/外部证据引用，不保存图片或视频大对象本体。"""

    if isinstance(value, dict):
        ref = {
            "kind": safe_text(value.get("kind"), "oss_object_ref"),
            "uri": safe_text(value.get("uri") or value.get("object_key")),
            "checksum": safe_text(value.get("checksum")),
            "source": safe_text(value.get("source"), "software_proof"),
            "proof_status": safe_text(value.get("proof_status"), "not_proven"),
        }
    else:
        ref = {
            "kind": "oss_object_ref",
            "uri": safe_text(value),
            "checksum": "",
            "source": "software_proof",
            "proof_status": "not_proven",
        }
    # URI 可为空，表示该记录暂时只有结构化事件，没有大对象证据。
    return ref


def base_markers() -> dict:
    """所有 O6 响应都带同一组证据标记，防止误判为生产 DB 已接入。"""

    return {
        "source": "software_proof",
        "proof_status": "not_proven",
        "evidence_boundary": ARCHIVE_EVIDENCE_BOUNDARY,
        "not_proven": [PRODUCTION_DB_GAP, "real_oss_upload", "real_inference_model_runtime"],
        "production_ready": False,
        "production_db_connected": False,
    }


class ArchiveStore:
    """用单 JSON 文件模拟 O6 数据层，接口形状对齐未来 production DB。"""

    def __init__(self, path: str | os.PathLike[str]):
        # 这里用锁保护文件读写，保证 unittest/本地 HTTP 并发时不会写坏 JSON。
        self.path = Path(path)
        self._lock = threading.RLock()

    def _empty(self) -> dict:
        # tasks/events/annotations/inferences 分表保存，便于未来迁移到关系型表。
        return {
            "schema": ARCHIVE_STORE_SCHEMA,
            "schema_version": 1,
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            "tasks": [],
            "events": [],
            "annotations": [],
            "inferences": [],
        }

    def _load(self) -> dict:
        with self._lock:
            if not self.path.exists():
                return self._empty()
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict) or data.get("schema") != ARCHIVE_STORE_SCHEMA:
                raise ValueError("archive state schema is invalid")
            return data

    def _save(self, data: dict) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            data["updated_at"] = utc_now_iso()
            tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
            with tmp_path.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            tmp_path.replace(self.path)

    def create_task(self, payload: dict) -> dict:
        # robot_id/task_id 是所有 PC/手机查询和机器人上报的最小复合键。
        robot_id = safe_text(payload.get("robot_id"))
        task_id = safe_text(payload.get("task_id"))
        if not robot_id or not task_id:
            raise ValueError("robot_id and task_id are required")
        data = self._load()
        now = utc_now_iso()
        existing = self._find_task(data, robot_id, task_id)
        task = {
            "schema": ARCHIVE_SCHEMA,
            "robot_id": robot_id,
            "task_id": task_id,
            "task_type": safe_text(payload.get("task_type"), "trash_delivery"),
            "status": safe_text(payload.get("status"), "recorded"),
            "date": safe_text(payload.get("date"), now[:10]),
            "created_at": safe_text(payload.get("created_at"), now),
            "updated_at": now,
            "route_id": safe_text(payload.get("route_id")),
            "source": safe_text(payload.get("source"), "software_proof"),
            "proof_status": safe_text(payload.get("proof_status"), "not_proven"),
            "evidence_ref": normalize_evidence_ref(payload.get("evidence_ref")),
            "summary": payload.get("summary") if isinstance(payload.get("summary"), dict) else {},
        }
        if existing is None:
            data["tasks"].append(task)
        else:
            existing.update(task)
            task = existing
        self._save(data)
        return {"ok": True, **base_markers(), "task": task}

    def list_tasks(self, filters: dict[str, str]) -> dict:
        data = self._load()
        tasks = [
            task
            for task in data["tasks"]
            if self._matches(task, filters, ("robot_id", "task_id", "date", "status"))
        ]
        return {"ok": True, "schema": ARCHIVE_SCHEMA, **base_markers(), "tasks": tasks, "count": len(tasks)}

    def get_task(self, robot_id: str, task_id: str) -> tuple[int, dict]:
        data = self._load()
        task = self._find_task(data, robot_id, task_id)
        if task is None:
            return 404, {"ok": False, "schema": ARCHIVE_SCHEMA, **base_markers(), "error": "task_not_found"}
        events = [event for event in data["events"] if event["robot_id"] == robot_id and event["task_id"] == task_id]
        annotations = [
            item for item in data["annotations"] if item["robot_id"] == robot_id and item["task_id"] == task_id
        ]
        inferences = [
            item for item in data["inferences"] if item["robot_id"] == robot_id and item["task_id"] == task_id
        ]
        return 200, {
            "ok": True,
            "schema": ARCHIVE_SCHEMA,
            **base_markers(),
            "task": task,
            "events": events,
            "annotations": annotations,
            "inferences": inferences,
        }

    def create_event(self, payload: dict) -> dict:
        # event_id 可由上车端生成；缺失时用计数派生，便于 mock publisher 最小接入。
        robot_id = safe_text(payload.get("robot_id"))
        task_id = safe_text(payload.get("task_id"))
        event_type = safe_text(payload.get("event_type"))
        if not robot_id or not task_id or not event_type:
            raise ValueError("robot_id, task_id and event_type are required")
        data = self._load()
        event_id = safe_text(payload.get("event_id"), f"event-{len(data['events']) + 1}")
        event = {
            "schema": ARCHIVE_SCHEMA,
            "robot_id": robot_id,
            "task_id": task_id,
            "event_id": event_id,
            "event_type": event_type,
            "created_at": safe_text(payload.get("created_at"), utc_now_iso()),
            "source": safe_text(payload.get("source"), "software_proof"),
            "proof_status": safe_text(payload.get("proof_status"), "not_proven"),
            "evidence_ref": normalize_evidence_ref(payload.get("evidence_ref")),
            "payload": payload.get("payload") if isinstance(payload.get("payload"), dict) else {},
        }
        data["events"].append(event)
        self._save(data)
        return {"ok": True, **base_markers(), "event": event}

    def list_events(self, filters: dict[str, str]) -> dict:
        data = self._load()
        events = [
            event
            for event in data["events"]
            if self._matches(event, filters, ("robot_id", "task_id", "event_id", "event_type"))
        ]
        return {"ok": True, "schema": ARCHIVE_SCHEMA, **base_markers(), "events": events, "count": len(events)}

    def create_annotation(self, payload: dict) -> dict:
        # 标注先作为独立记录保存，后续 PC 端可按 task/frame/item 查询。
        robot_id = safe_text(payload.get("robot_id"))
        task_id = safe_text(payload.get("task_id"))
        if not robot_id or not task_id:
            raise ValueError("robot_id and task_id are required")
        data = self._load()
        annotation = {
            "schema": ANNOTATION_SCHEMA,
            "annotation_id": safe_text(payload.get("annotation_id"), f"annotation-{len(data['annotations']) + 1}"),
            "robot_id": robot_id,
            "task_id": task_id,
            "item_id": safe_text(payload.get("item_id")),
            "label_type": safe_text(payload.get("label_type")),
            "label_value": payload.get("label_value"),
            "annotation_status": safe_text(payload.get("annotation_status"), "submitted"),
            "created_at": safe_text(payload.get("created_at"), utc_now_iso()),
            "source": safe_text(payload.get("source"), "software_proof"),
            "proof_status": safe_text(payload.get("proof_status"), "not_proven"),
            "evidence_ref": normalize_evidence_ref(payload.get("evidence_ref")),
            "metadata": payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
        }
        data["annotations"].append(annotation)
        self._save(data)
        return {"ok": True, **base_markers(), "annotation": annotation}

    def list_annotations(self, filters: dict[str, str]) -> dict:
        data = self._load()
        annotations = [
            item
            for item in data["annotations"]
            if self._matches(item, filters, ("robot_id", "task_id", "annotation_id", "annotation_status"))
        ]
        return {
            "ok": True,
            "schema": ANNOTATION_SCHEMA,
            **base_markers(),
            "annotations": annotations,
            "count": len(annotations),
        }

    def create_inference(self, payload: dict) -> dict:
        # 推理记录写回事件索引，方便 O7 按任务时间线展示模型输出。
        robot_id = safe_text(payload.get("robot_id"))
        task_id = safe_text(payload.get("task_id"))
        inference_type = safe_text(payload.get("inference_type"))
        if not robot_id or not task_id or not inference_type:
            raise ValueError("robot_id, task_id and inference_type are required")
        data = self._load()
        inference = {
            "schema": INFERENCE_SCHEMA,
            "inference_id": safe_text(payload.get("inference_id"), f"inference-{len(data['inferences']) + 1}"),
            "robot_id": robot_id,
            "task_id": task_id,
            "event_id": safe_text(payload.get("event_id")),
            "inference_type": inference_type,
            "inference_status": safe_text(payload.get("inference_status"), "recorded"),
            "model_ref": safe_text(payload.get("model_ref"), "mock_cpu_or_external_api_pending"),
            "result": payload.get("result") if isinstance(payload.get("result"), dict) else {},
            "created_at": safe_text(payload.get("created_at"), utc_now_iso()),
            "source": safe_text(payload.get("source"), "software_proof"),
            "proof_status": safe_text(payload.get("proof_status"), "not_proven"),
            "evidence_ref": normalize_evidence_ref(payload.get("evidence_ref")),
        }
        data["inferences"].append(inference)
        data["events"].append(
            {
                "schema": ARCHIVE_SCHEMA,
                "robot_id": robot_id,
                "task_id": task_id,
                "event_id": inference["event_id"] or f"event-inference-{len(data['events']) + 1}",
                "event_type": f"inference.{inference_type}",
                "created_at": inference["created_at"],
                "source": inference["source"],
                "proof_status": inference["proof_status"],
                "evidence_ref": inference["evidence_ref"],
                "payload": {"inference_id": inference["inference_id"], "result": inference["result"]},
            }
        )
        self._save(data)
        return {"ok": True, **base_markers(), "inference": inference}

    def list_inferences(self, filters: dict[str, str]) -> dict:
        data = self._load()
        inferences = [
            item
            for item in data["inferences"]
            if self._matches(item, filters, ("robot_id", "task_id", "inference_id", "inference_status"))
        ]
        return {
            "ok": True,
            "schema": INFERENCE_SCHEMA,
            **base_markers(),
            "inferences": inferences,
            "count": len(inferences),
        }

    def _find_task(self, data: dict, robot_id: str, task_id: str) -> dict | None:
        for task in data["tasks"]:
            if task.get("robot_id") == robot_id and task.get("task_id") == task_id:
                return task
        return None

    def _matches(self, row: dict, filters: dict[str, str], fields: tuple[str, ...]) -> bool:
        # 空 filter 不参与筛选，确保查询 API 能自然返回当前 proof store 全量数据。
        for field in fields:
            expected = safe_text(filters.get(field))
            if expected and safe_text(row.get(field)) != expected:
                return False
        return True


def archive_state_path(remote_state_path: str | None = None) -> str:
    """解析 O6 state 路径；无显式配置时不允许落到仓库根目录。"""

    explicit = os.environ.get("TRASHBOT_O6_ARCHIVE_STATE", "").strip()
    if explicit:
        return explicit
    if remote_state_path:
        path = Path(remote_state_path)
        # remote relay 已有明确 state 文件时，O6 跟随同目录，方便 Docker volume 一次挂载。
        return str(path.with_name(f"{path.stem}.o6_archive.json"))
    # 没有 remote state 的单测/本地 smoke 只能使用 /tmp，防止污染源码树。
    return DEFAULT_ARCHIVE_STATE


def parse_json_body(handler) -> dict:
    """HTTP handler 公用 JSON parser，坏 JSON 必须返回结构化 400。"""

    length = int(handler.headers.get("Content-Length", "0") or "0")
    body = handler.rfile.read(length) if length else b"{}"
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("malformed_json") from exc
    if not isinstance(payload, dict):
        raise TypeError("JSON body must be an object")
    return payload


def query_filters(parsed) -> dict[str, str]:
    """把 query string 变成单值 filter，避免 handler 层到处处理 list。"""

    query = parse_qs(parsed.query)
    return {key: values[0] for key, values in query.items() if values}


def install_o6_archive_routes(behavior_module) -> None:
    """给现有 remote relay handler 增加 O6 路由，不改 onboard 源码。"""

    if getattr(behavior_module, "_trashbot_o6_archive_routes_installed", False):
        return
    original_make_handler = behavior_module.make_handler

    def make_handler_with_o6(store, bearer_token):
        BaseHandler = original_make_handler(store, bearer_token)
        archive_store = ArchiveStore(archive_state_path(os.environ.get("TRASHBOT_REMOTE_CLOUD_STATE", "")))

        class RelayHandlerWithO6(BaseHandler):
            """在 remote.v1 控制面前置拦截 O6 路由，其余路径交还原 handler。"""

            def do_GET(self):
                if self.path.startswith("/api/o6/"):
                    handle_o6_get(self, archive_store)
                    return
                super().do_GET()

            def do_POST(self):
                if self.path.startswith("/api/o6/"):
                    handle_o6_post(self, archive_store)
                    return
                super().do_POST()

        return RelayHandlerWithO6

    behavior_module.make_handler = make_handler_with_o6
    behavior_module._trashbot_o6_archive_routes_installed = True


def handle_o6_get(handler, store: ArchiveStore) -> None:
    """处理 O6 只读 API；所有入口复用 remote relay bearer gate。"""

    parsed = behavior_urlparse(handler.path)
    if not handler._authorized():
        handler._reject_auth()
        return
    filters = query_filters(parsed)
    if parsed.path == "/api/o6/archive/tasks":
        handler._send_json(200, store.list_tasks(filters))
        return
    if parsed.path.startswith("/api/o6/archive/tasks/"):
        task_id = unquote(parsed.path.removeprefix("/api/o6/archive/tasks/").strip("/"))
        status_code, payload = store.get_task(safe_text(filters.get("robot_id")), task_id)
        handler._send_json(status_code, payload)
        return
    if parsed.path == "/api/o6/archive/events":
        handler._send_json(200, store.list_events(filters))
        return
    if parsed.path == "/api/o6/annotations":
        handler._send_json(200, store.list_annotations(filters))
        return
    if parsed.path == "/api/o6/inference":
        handler._send_json(200, store.list_inferences(filters))
        return
    handler._send_json(404, {"ok": False, **base_markers(), "error": "o6_path_not_found"})


def handle_o6_post(handler, store: ArchiveStore) -> None:
    """处理 O6 写 API；写入本地 proof store，不触发机器人控制。"""

    parsed = behavior_urlparse(handler.path)
    if not handler._authorized():
        handler._reject_auth()
        return
    try:
        payload = parse_json_body(handler)
        if parsed.path == "/api/o6/archive/tasks":
            handler._send_json(200, store.create_task(payload))
            return
        if parsed.path == "/api/o6/archive/events":
            handler._send_json(200, store.create_event(payload))
            return
        if parsed.path == "/api/o6/annotations":
            handler._send_json(200, store.create_annotation(payload))
            return
        if parsed.path == "/api/o6/inference":
            handler._send_json(200, store.create_inference(payload))
            return
    except (TypeError, ValueError) as exc:
        code = "malformed_json" if str(exc) == "malformed_json" else "bad_request"
        handler._send_json(400, {"ok": False, **base_markers(), "error": code, "message": safe_text(exc)})
        return
    handler._send_json(404, {"ok": False, **base_markers(), "error": "o6_path_not_found"})


def behavior_urlparse(path: str):
    """封装 urlparse，便于测试时不依赖 onboard 私有 helper。"""

    from urllib.parse import urlparse

    return urlparse(path)
