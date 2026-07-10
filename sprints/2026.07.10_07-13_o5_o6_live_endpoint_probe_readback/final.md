# O5/O6 Live Endpoint Probe Readback Final

## 复盘结论

本轮 epic sprint 完成。用户价值是把 O5/O6 从 SQLite shadow same-task readback 再往前推进一小步：同一 `task_id` 不再只能回读 terminal result / mission gate，还能回读 `cloud_external_probe` 和 `cloud_db_queue_external_probe` 摘要，从而更早暴露“endpoint 可读但非 production proof”和“DB/queue probe 仍未拿到真实外部材料”的差异。

产品北极星仍是可验证地可靠交付垃圾。本轮没有宣称真实送达成功；它只证明 live endpoint probe summary 可以在同一 `task_id` 下进入 O6 archive/readback，并且 hostile probe payload 会 fail-closed。

## OKR 映射和进度调整

- O5 / KR1 / KR6：继续。same-task smoke 已从 SQLite shadow readback 推进到 live endpoint probe additive readback，O5 从约 84% 保守上调到约 85%。
- O6 / KR2 / KR6：继续。archive/read model 新增 `cloud_external_probe` / `cloud_db_queue_external_probe` additive readback，并完成 consumer 回读，O6 从约 84% 保守上调到约 85%。
- O7 / KR3 / KR4：继续但不调整，维持约 85%。本轮没有新增 O7 UI、真实 browser、真实媒体或现场材料。
- O1：继续但不调整，维持约 85%。

本轮不归档任何 KR。当前区仍保留 O5/O6/O7/O1，因为真实 production cloud、production DB/queue、真实 live route execution、真实 delivery record、真实 operator confirmation、真实手机/browser 和真实 delivery success 均未完成。

## 实际交付

### Engineer 交付

- Robot Software：在 `o5_same_task_mission_archive_smoke.py` 复用既有 `cloud_external_probe` / `cloud_db_queue_external_probe` summary 逻辑，对本地 relay `/healthz`、`/readyz`、`/preflightz` 做 software proof probe。
- Robot Software：把两类 probe 摘要作为 `cloud_external_probe` / `cloud_db_queue_external_probe` additive section 写入同一 `task_id` 的 O6 archive/readback，并让 smoke summary 同时回显 same-task gate、cloud external probe、cloud DB/queue probe 的 readback 状态。
- Robot Software / O6：新增 `trashbot.o6.cloud_external_probe_readback.v1` 与 `trashbot.o6.cloud_db_queue_external_probe_readback.v1`，支持 archive detail、`field_evidence`、`artifact_bundle`、consumer detail 顶层 alias，以及 `include=cloud_external_probe,cloud_db_queue_external_probe` 回读。
- Robot Software：hostile probe payload fail-closed，只把对应 section 降级为 `blocked_not_proven`，不回显 URL、token、连接串、response body、本地路径或 traceback。
- Docs：更新 `docs/interfaces/o6_cloud_archive_api.md` 与 `docs/product/cloud_4g_infrastructure.md`，同步 additive readback 合同和 proof boundary。

### Product 交付

- 更新 `OKR.md` 的 O5/O6 当前状态、4.1 快照、最高优先级和 2026-07-10 收口记录。
- 更新 `docs/process/okr_progress_log.md`，追加本 sprint 详细历史。
- 补齐本 sprint `tech-done.md`、`side2side_check.md`、`final.md` 和 `artifacts/product_worker_report.md`。

## 验证证据

- Robot Software：`py_compile` 通过；`python3 -m unittest onboard.tests.test_o5_same_task_mission_archive_smoke` 输出 `Ran 3 tests in 2.338s OK`；`python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay` 输出 `Ran 167 tests in 64.655s OK`；`git diff --check` 通过。
- Product closeout：`test -f` 检查 `tech-done.md`、`side2side_check.md`、`final.md` 通过；`rg -n "live_endpoint_probe|cloud_external_probe|same_task|software_proof"` 命中本 sprint 收口文件、`OKR.md` 和 `docs/process/okr_progress_log.md`；`git diff --check` 通过。

## 证据边界

本轮 proof boundary 为 `software_proof_o5_o6_live_endpoint_probe_readback_only`。

它证明本地 relay 的 live endpoint probe summary 与 DB/queue probe 状态矩阵，可以在同一 `task_id` 下安全进入 O6 archive/readback，并被 consumer 回读。

它不证明真实 production cloud、production DB/queue、多实例一致性、真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实手机/browser、真实 annotation API/export 或真实 delivery success。

## 风险与阻塞

- 当前环境没有真实公网 endpoint、production DB/queue 或凭证，本轮只能停留在 software proof readback。
- O5/O6 若继续沿同一类 local/mock probe wrapper 迭代，会触发“用 support-only surface 反复包装成 OKR 增量”的红线。
- 当前仅证明本地 relay `/healthz`、`/readyz`、`/preflightz` 的安全回读，不等于真实云链路可用。

## 下一轮建议

1. 优先拿真实 production cloud 或 production DB/queue external probe 证据，让 `cloud_external_probe` / `cloud_db_queue_external_probe` 从 software proof 变成真实外部材料。
2. 如果 production cloud 仍不可得，转向消费真实或准现场 same-task mission materials，例如 live route execution、delivery record、operator confirmation、route bag、keyframe 或 replay JSONL，而不是继续扩 probe wrapper。
3. O5/O6 后续若只有本地 smoke，可保留作回归守护，但不再计 OKR 百分比增量。
