# Robot Software Worker Report

## 改动文件

- `onboard/scripts/o5_same_task_mission_archive_smoke.py`
- `onboard/tests/test_o5_same_task_mission_archive_smoke.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/cloud_4g_infrastructure.md`

## 实际实现内容

1. 在 `o5_same_task_mission_archive_smoke.py` 新增 live endpoint probe readback 串联：
   - 复用既有 `cloud_external_probe` artifact 生成/summary 逻辑，对本地 relay 的 `/healthz`、`/readyz`、`/preflightz` 做 software proof 探测。
   - 复用既有 `cloud_db_queue_external_probe` artifact 生成/summary 逻辑，生成 blocked-by-design 的 DB/queue probe 状态矩阵。
   - 把两类 probe 摘要以 `cloud_external_probe` / `cloud_db_queue_external_probe` additive section 写入同一 `task_id` 的 O6 archive/readback。
   - smoke summary 现在同时回显 same-task gate、cloud external probe、cloud DB/queue probe 的 readback 状态，并继续固定所有危险字段为 false。

2. 在 `remote_cloud_relay.py` 新增 O6 probe readback 合同：
   - 新增 `trashbot.o6.cloud_external_probe_readback.v1`
   - 新增 `trashbot.o6.cloud_db_queue_external_probe_readback.v1`
   - 支持 archive detail、`field_evidence`、`artifact_bundle`、consumer detail 顶层 alias，以及 `include=cloud_external_probe,cloud_db_queue_external_probe`
   - 对 hostile probe payload 走 fail-closed：只把对应 section 降级为 `blocked_not_proven`，不回显 URL、token、连接串、response body、本地路径或 traceback。

3. 同步补充文档：
   - `docs/interfaces/o6_cloud_archive_api.md` 写明两类 probe 的 additive readback section、include 入口和 proof boundary。
   - `docs/product/cloud_4g_infrastructure.md` 写明本轮 smoke 只证明 same-task archive/readback 可以安全消费 live endpoint probe 摘要，不代表真实 production cloud / DB / queue 成功。

## 验证命令与结果

### 1. `python3 -m py_compile onboard/scripts/o5_same_task_mission_archive_smoke.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`

- 结果：通过

### 2. `python3 -m unittest onboard.tests.test_o5_same_task_mission_archive_smoke`

- 结果：通过
- 关键输出：
  - `Ran 3 tests in 2.338s`
  - `OK`

### 3. `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`

- 结果：通过
- 关键输出：
  - `Ran 167 tests in 64.655s`
  - `OK`

### 4. `git diff --check`

- 结果：通过

## 失败定位（本轮已修复）

1. `cloud_external_probe` 初版被 consumer 判成 `blocked_not_proven`
   - 根因：endpoint path 使用了通用“路径不安全”清洗逻辑，`/healthz`、`/readyz`、`/preflightz` 被误删，导致 section 失去 ready 条件。
   - 修复：改成 endpoint 白名单，只允许上述三条 path 安全回读。

2. hostile probe payload 初版导致 `POST /api/o6/archive/field-evidence` 直接 `400`
   - 根因：全局 unsafe gate 在 probe section 之前拦截，破坏了“坏 probe 只降级自身摘要”的目标。
   - 修复：在全局扫描前剥离 `cloud_external_probe` / `cloud_db_queue_external_probe`，让 hostile probe 只把对应 section 降级为 `blocked_not_proven`。

3. consumer detail 初版缺少 probe 顶层 alias
   - 根因：`_o6_consumer_build_field_evidence_section` 未把两个新 section 提升到 consumer payload。
   - 修复：补充 field evidence section 与 top-level alias 映射，并加测试覆盖。

## 剩余风险

- 本轮只证明 `software_proof_o5_o6_live_endpoint_probe_readback_only`。
- `cloud_external_probe_ready_not_production_proof` 只表示本地 relay 只读 endpoint 合同可被同一 `task_id` 安全消费，不代表真实公网 HTTPS/TLS、真实 production cloud、真实 4G/SIM。
- `cloud_db_queue_external_probe_ready_not_production_proof` 只表示枚举化 DB/queue probe 状态矩阵可被同一 `task_id` 安全消费，不代表真实 production DB/queue、多实例一致性、事务隔离、备份恢复。
- 仍不证明真实 Nav2 live route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success。

## 协同需求

- `Product`：需要基于本轮 worker report 更新 sprint `tech-done.md / side2side_check.md / final.md` 和 OKR 口径，明确这是 contract/readback 进展，不是 production success。
- `Hardware`：本轮不需要。
- `Autonomy`：本轮不需要。
- `Full-Stack`：当前不强依赖；后续若 O7 要展示 probe readback，可直接消费新增 consumer section。
