# O6 Event Evidence Archive Final

## sprint_type: epic

## 收口结论

O6 Event Evidence Archive Epic 已按设计完成 local/mock software proof。新增四个 endpoint：

- `POST /api/o6/archive/events`
- `GET /api/o6/archive/events`
- `POST /api/o6/archive/evidence`
- `GET /api/o6/archive/evidence`

实现保持单一 file-backed O6 store，不新增生产 DB/OSS/控制面依赖。events/evidence 均只允许附着已有 task，支持幂等 upsert、白名单查询、summary 返回和 fail-closed。`GET /api/o6/archive/tasks/<task_id>` 可继续读到兼容的 `events[]` / `evidence_refs[]`。

## OKR 回顾

本轮直接推进 `O6-KR2` 与 `O6-KR3` 的软件侧证据：

- `O6-KR2`：补齐任务内感知/路线/电梯/失败/恢复事件追加写入和查询。
- `O6-KR3`：补齐 evidence ref 摘要写入与查询，明确不保存原始图片/视频/音频内容。

本轮不更新 `OKR.md`，因为本 sprint 的实现范围限定在 O6 event/evidence API、接口文档和 sprint 收口；O6 百分比建议留给后续 Product Owner 基于连续软件证据统一调整。

## 验证结果

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
exit code: 0
```

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 142 tests in 46.752s
OK
```

```text
rg keyword acceptance: passed
git diff --check: passed
```

## 未完成事项与风险

- 未证明真实 cloud DB、production queue、OSS 上传、CDN 可读、公网 HTTPS/TLS、真实 4G、真实机器人控制、真实现场事件或真实摄像头采集。
- `archive_event_written=true` 只代表 local/mock event store 写入成功。
- `archive_evidence_written=true` 只代表 local/mock evidence ref 摘要写入成功；`real_oss_upload_success=false` 必须保持。
- 若后续 PC/O7 需要完整 object key、分页 cursor、WebSocket 事件流或 audit log，需要另起 sprint 设计。
