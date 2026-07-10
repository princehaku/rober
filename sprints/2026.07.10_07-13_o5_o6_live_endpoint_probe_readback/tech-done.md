# O5/O6 Live Endpoint Probe Readback Tech Done

## sprint_type

sprint_type: epic

## 实际改动

### Engineer 交付

- Robot Software 在 `o5_same_task_mission_archive_smoke.py` 复用既有 `cloud_external_probe` / `cloud_db_queue_external_probe` summary 逻辑，对本地 relay `/healthz`、`/readyz`、`/preflightz` 做 software proof live endpoint probe。
- Robot Software 把两类 probe 摘要作为 `cloud_external_probe` / `cloud_db_queue_external_probe` additive section 写入同一 `task_id` 的 O6 archive/readback，并让 smoke summary 同时回显 same-task gate、cloud external probe、cloud DB/queue probe 的 readback 状态。
- O6 新增 `trashbot.o6.cloud_external_probe_readback.v1` 与 `trashbot.o6.cloud_db_queue_external_probe_readback.v1`，支持 archive detail、`field_evidence`、`artifact_bundle`、consumer detail 顶层 alias，以及 `include=cloud_external_probe,cloud_db_queue_external_probe` 回读。
- hostile probe payload 走 fail-closed：只把对应 section 降级为 `blocked_not_proven`，不回显 URL、token、连接串、response body、本地路径或 traceback。
- 文档已同步更新 `docs/interfaces/o6_cloud_archive_api.md` 与 `docs/product/cloud_4g_infrastructure.md`，明确 additive readback section、include 入口和 `software_proof_o5_o6_live_endpoint_probe_readback_only` 边界。

### Product 交付

- 更新 `OKR.md` 的 O5/O6 当前状态、4.1 快照、最高优先级和 2026-07-10 收口记录。
- 更新 `docs/process/okr_progress_log.md`，新增本 sprint 的详细收口条目。
- 创建并补齐本 sprint `tech-done.md`、`side2side_check.md`、`final.md` 和 `artifacts/product_worker_report.md`。

## 验证结果

### Robot Software 验证

- `python3 -m py_compile onboard/scripts/o5_same_task_mission_archive_smoke.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 结果：通过
- `python3 -m unittest onboard.tests.test_o5_same_task_mission_archive_smoke`
  - 结果：通过
  - 关键输出：`Ran 3 tests in 2.338s`、`OK`
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
  - 结果：通过
  - 关键输出：`Ran 167 tests in 64.655s`、`OK`
- `git diff --check`
  - 结果：通过

### Product closeout 验证

- `test -f sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback/tech-done.md`
  - 结果：通过
- `test -f sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback/side2side_check.md`
  - 结果：通过
- `test -f sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback/final.md`
  - 结果：通过
- `rg -n "live_endpoint_probe|cloud_external_probe|same_task|software_proof" OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback`
  - 结果：通过
  - 关键命中：`software_proof_o5_o6_live_endpoint_probe_readback_only`、`cloud_external_probe_ready_not_production_proof`、`cloud_db_queue_external_probe_ready_not_production_proof`、`same_task`
- `git diff --check`
  - 结果：通过

## 偏差与修复

- 初版 `cloud_external_probe` 被 consumer 判成 `blocked_not_proven`，根因是通用“路径不安全”清洗逻辑误删 `/healthz`、`/readyz`、`/preflightz`；已改为 endpoint 白名单。
- hostile probe payload 初版导致 archive ingest 直接 `400`，根因是全局 unsafe gate 在 probe section 之前拦截；已调整为只降级当前 probe section。
- consumer detail 初版缺少 probe 顶层 alias；已补齐 field evidence section 与 top-level alias 映射，并加测试覆盖。

## OKR 判断

- O5：从约 84% 保守上调到约 85%。理由是 same-task smoke 已从 SQLite shadow readback 进一步推进到 live endpoint probe summary 的可回读合同。
- O6：从约 84% 保守上调到约 85%。理由是 archive/read model 新增 `cloud_external_probe` / `cloud_db_queue_external_probe` additive readback，并完成 consumer 回读。
- O7：维持约 85%，本轮没有新增 O7 UI、browser 或现场材料。
- 本轮不归档任何 KR，不声明真实外部材料完成。

## 剩余风险

- 本轮只证明 `software_proof_o5_o6_live_endpoint_probe_readback_only`。
- `cloud_external_probe_ready_not_production_proof` 只表示本地 relay 只读 endpoint 合同可被同一 `task_id` 安全消费，不代表真实公网 HTTPS/TLS、真实 production cloud、真实 4G/SIM。
- `cloud_db_queue_external_probe_ready_not_production_proof` 只表示 DB/queue probe 状态矩阵可被同一 `task_id` 安全消费，不代表真实 production DB/queue、多实例一致性、事务隔离、备份恢复。
- 仍不证明真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success、真实手机/browser 验收或真实 OSS/CDN live traffic。
