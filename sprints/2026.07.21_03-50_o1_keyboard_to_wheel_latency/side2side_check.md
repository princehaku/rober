# O1 Keyboard-to-Wheel Latency - Side-to-Side Check

## 验收元数据

- `sprint_type: epic`
- Product owner：`product-okr-owner`
- 实现 owner：`full-stack-software-engineer`
- `PRODUCT_ACCEPTANCE=ACCEPT_SOFTWARE_HOT_PATH_PHYSICAL_PENDING`
- proof boundary：`deterministic_segmented_software_hot_path_accepted_not_physical_wheel_latency`
- `live_nonzero_request_count=0`
- `zero_speed_request_count=0`
- `control_invocation_count=0`
- `physical_latency_not_measured=true`
- `mission_objective_0_satisfied=false`
- KR：`不归档`
- OKR：O1/O7 `flat`

Product 本轮只读核对 plan、实现留档、software artifact、当前 diff、测试声明和 shared-hunk audit；未重跑工程测试，未执行 SSH、部署、HTTP control、ROS、串口、Nav2 或任何 live/nonzero 命令。

## 需求与实现对照

| 验收项 | 当前证据 | Product 判断 |
|---|---|---|
| Vue/Node trace | keydown 生成 `trashbot.keyboard_wheel_latency_trace.v1`；Node 白名单校验并输出同进程 monotonic local spans | 接受 software trace contract；不接受为跨机或物理测量 |
| Upper startup prewarm | service 监听前预热 rclpy node/publisher/DDS graph；realtime_hold 首帧前不承担旧固定 wait | 接受代码与 software model 证明旧 `150ms` 配置预算移出 hot path |
| subscriber race | publish 前 `spin_once(0.0)` + current subscription check；无 subscriber 时 `frames_published=0`、`accepted=false`、`latency_pass=false`、CLI=false | 接受 fail-closed repair |
| subscriber 恢复 | bridge 后启动/重启并 matched 后，context 从 degraded 恢复 ready，首帧在任何 sleep 前发布 | 接受 fake graph 回归；真实 DDS 恢复尚未测 |
| 并发边界 | rclpy spin/publish 使用短临界区锁，burst sleep 在锁外 | 接受代码和 targeted test 证据 |
| bridge timing | callback/build/HTTP-or-serial transport start/end monotonic spans | 接受进程内诊断；transport return 不是 wheel onset |
| HTTP keepalive/no retry | ESP32 HTTP `/js` 在单 owner lock 中复用连接；失败关闭连接供下一独立请求重建，不重放当前 command | 接受软件合同；默认 HTTP transport 未改变 |
| stop/watchdog | keyup/all-release、pointer、blur、page hidden、button、watchdog 保留；release stop 不等待 pending motion response | 接受回归合同；真实 stop latency 尚未测 |
| 物理主目标 | 无 fresh authorization、外部 observer 或 wheel-onset timestamp | `physical_latency_not_measured=true`，主目标继续 pending |

## Software benchmark 口径

- `software_latency_summary.json` 有 `120` 个 deterministic warm fake-clock samples，drop/error=`0/0`。
- modeled `keydown_to_fake_transport_write_ms` p50/p95/max 均为 `9.2ms`。
- modeled baseline `159.2ms` 由旧 `150ms` realtime_hold subscription wait 配置预算加同一 deterministic segment fixture 构成；modeled improvement=`94.22%`。
- `9.2ms`、`159.2ms` 和 `94.22%` 都是 software model，不是浏览器调度、真实网络、Wi-Fi、DDS、ESP32 firmware 或物理轮子实测。
- cross-process direct subtraction=false；本轮没有 clock calibration，因此不得合成真实 keydown-to-wheel 数值。

## 验证证据核对

Engineer 留档的最终验证为：

- workstation targeted latency：`3 passed`；keyboard/manual/stop/watchdog/latency targeted：`22 passed / 237 skipped`；全量 `535 passed`；build/lint 通过。
- subscriber race targeted：`5 passed`。
- 最终 reconciliation：Upper full `141 passed / 1 skipped`；bridge `32 passed`；Upper + Nav2 shared
  `337 passed / 1 skipped`；current/candidate_v3 shutdown targeted 各 `17 passed`；冻结 85ba original regression
  `119 passed / 1 skipped`。
- Python `py_compile` 与 scoped `git diff --check` 通过。
- Docker/Humble：repair 前同一实现轮次 `Summary: 6 packages finished [49.3s]`。repair 只修改 Upper Python graph gate/tests，Docker 未重跑；Product 接受其为保留的软件构建证据，不把它外推为 repair 的容器/HIL/live 复验。

Product 未重跑上述命令；验收依据为 `tech-done.md` 的 Engineer 记录、当前测试代码覆盖和 frozen software summary。

## 迟到链对照

| Sprint | 当前事实 | Product 判断 |
|---|---|---|
| 04-31 | 只读 version gate 在部署前拒绝 c8 混合 Upper；deploy/restart/sample=`0/0/0` | 接受 fail-closed preflight，不是 latency sample |
| 04-48 | 85ba latency-only candidate 可复现；symlink alias 在 first target move 前失败 | 接受 candidate 软件产物，不接受部署或现场路径 |
| 05-08 | alias-safe replacement 成功；旧 Upper 卡 `deactivating/stop-sigterm`；完整 rollback | 接受 blocker 收敛与恢复，不接受新版本 health 或 sample |
| 05-24 | shutdown admission、单 stop owner、watchdog/release/runtime stop lock、rclpy teardown fail-closed 离线全绿；candidate_v3 唯一部署输入 | 接受软件修复，真实 systemd SIGTERM 仍 pending |

四轮合计 zero/nonzero/control sample=`0/0/0`。04-48 的 `adadb0...` 与 05-24 candidate_v2 都不是下一次部署输入；
只允许使用 candidate_v3 `ceaf8...`，且仍不得把软件修复外推成 physical latency、HIL 或 safe-to-control。

## Shared hunk 与工作区边界

- `shared_hunk_baseline.md` 保存 Upper/test/runtime-doc 的开工 SHA、既有 Nav2 hunk families 与最终 SHA。
- 当前 HEAD 已包含 `feat(nav): add sensor-owned readiness gates`；只读 anchor 核对仍可见 `path_goal_frame_id`、sensor-owned lifecycle、managed runtime、planner/controller 等 Nav2 合同。
- repair 后 shared suite `328 passed / 1 skipped`；未发现 checkout/reset/stash/rebase 或覆盖既有 Nav2 hunk 的证据。
- 本 Epic 不接管前序 `01-54` micro；其 v6 authorization 已消费且不得复用。

## 不接受的声明

以下结论仍为 false/unknown：真实 keydown-to-wheel latency、真实 network/Wi-Fi/DDS latency、physical wheel onset、wheel direction、HIL、`safe_to_control`、route execution、delivery success。HTTP response、首次 publisher call、bridge transport return、deterministic `9.2ms` 或旧 first-jog IMU delta 均不能替代物理 observer。

## Side-to-side 结论

`ACCEPT_SOFTWARE_HOT_PATH_AND_BOUNDED_SHUTDOWN_PHYSICAL_PENDING`。本轮实质完成 trace、prewarm、零等待 current graph
gate、realtime_hold no-CLI fail-closed、subscriber 恢复、HTTP keepalive/no-retry、stop/watchdog 软件回归，以及后续
bounded-shutdown candidate_v3 软件修复；用户所述“按键到轮子动”仍未由 physical evidence 闭合，因此 O1/O7 flat、
Mission Objective 0 未满足、KR 不归档。
