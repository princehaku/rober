# Cloud Command Result Reconciliation Tech Done

## 1. Sprint 声明

- sprint_type: epic
- sprint_id: `2026.05.26_08-09_cloud-command-result-reconciliation`
- closeout 时间：2026-05-26 05:47 Asia/Shanghai
- 产品北极星：普通手机用户发出任务级命令后，可以看到可信的命令生命周期核对状态，而不是把 queued、processing 或 terminal ACK 误读成真实送达成功。

## 2. 实际改动

### Task A：Robot Software Engineer

Robot worker 已完成 cloud relay 结果核对入口：

- 新增 `GET /api/commands/{command_id}/result?robot_id=<robot_id>`。
- 新增 schema `trashbot.cloud_command_result_reconciliation.v1`。
- 新增 capability `cloud_command_result_reconciliation`。
- 新增 evidence boundary `software_proof_docker_cloud_command_result_reconciliation_gate`。
- 覆盖 `queued`、`processing`、`terminal_result_pending`、`missing_or_expired`、`store_unavailable`。
- 继续保持 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`，terminal ACK 不写成 delivery/dropoff/cancel success。

Task A worker 报告验证结果：

```text
Ran 7 tests ... OK
git diff --check passed
```

### Task B：User Touchpoint Full-Stack Engineer

Full-Stack worker 已完成 mobile/web 命令结果核对只读面板：

- 新增命令结果核对只读展示入口、fixture 和相关手机流程文档。
- 覆盖四类中文 copy：queued、processing、terminal_result_pending、unavailable。
- UI 继续保持只读和 fail closed，不自动重放、不 resubmit、不请求 raw diagnostics、不开放控制授权。
- 文案明确“已入队 / 处理中 / 已终态 ACK”都不是送达成功。

Task B worker 报告验证结果：

```text
Ran 4 tests ... OK
git diff --check passed
```

## 3. 验收对照

| 验收项 | 结果 |
| --- | --- |
| 按 `robot_id + command_id` 查询命令 lifecycle summary | 已完成，Robot route 为 `GET /api/commands/{command_id}/result?robot_id=<robot_id>` |
| 覆盖 queued / processing / terminal / missing / store unavailable | 已完成，Robot 测试覆盖 queued、processing、terminal_result_pending、missing_or_expired、store_unavailable |
| mobile/web 中文 copy 不写成送达成功 | 已完成，Full-Stack 覆盖 queued / processing / terminal_result_pending / unavailable |
| false-state flags 保留 | 已完成，保留 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false` |
| docs/product 同步 | 已由两个 worker 在各自范围内更新；Product closeout 不再修改 docs/product |
| closeout/OKR 留档 | 本文件、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md` 已更新 |

## 4. 偏差和处理

- 本轮没有扩大到 production DB/queue、多实例一致性或真实公网链路。
- 本轮没有把 terminal ACK 升级成 verified delivery/dropoff/cancel result。
- Product closeout 未改产品代码、测试代码、mobile/web、cloud-relay、硬件配置或 `.idea/rober.iml`。

## 5. 剩余风险

- 本轮证据边界仍是 `software_proof_docker_cloud_command_result_reconciliation_gate`。
- 不证明公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、true phone/browser proof、HIL、Nav2/fixed-route、WAVE ROVER/UART 或 delivery success。
- Objective 5 可因命令 lifecycle/result reconciliation 从约 72% 小幅提升到约 76%；Objective 1/2/3/4 不因本轮功能提升而上调。
